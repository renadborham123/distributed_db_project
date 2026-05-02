import logging
import os
from typing import Dict, List, Optional

from pymongo import MongoClient, ReturnDocument

from backend.models import Cart, Order, Product, ProductCreate


logger = logging.getLogger(__name__)


class MongoShardRepository:
    """
    Database access layer.

    We simulate sharding by using multiple MongoDB databases:
    - ecommerce_shard_0
    - ecommerce_shard_1

    Product records are stored in one shard only, based on the routing rule.
    Carts and orders live in a small shared database because the goal of this
    demo is to highlight product sharding rather than fully distributed joins.
    """

    def __init__(self) -> None:
        mongo_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.client = MongoClient(mongo_url)
        self.metadata_db = self.client["ecommerce_metadata"]
        self.shared_db = self.client["ecommerce_shared"]
        self.shard_dbs = {
            0: self.client["ecommerce_shard_0"],
            1: self.client["ecommerce_shard_1"],
        }

        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        self.metadata_db["counters"].create_index("name", unique=True)
        self.shared_db["carts"].create_index("id", unique=True)
        self.shared_db["orders"].create_index("id", unique=True)

        for shard_db in self.shard_dbs.values():
            shard_db["products"].create_index("id", unique=True)

    def next_id(self, counter_name: str) -> int:
        counter = self.metadata_db["counters"].find_one_and_update(
            {"name": counter_name},
            {"$inc": {"value": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return int(counter["value"])

    def insert_product(self, shard_number: int, product_data: ProductCreate, product_id: int) -> Product:
        product = Product(id=product_id, **product_data.model_dump())
        self.shard_dbs[shard_number]["products"].insert_one(product.model_dump())
        return product

    def get_product(self, shard_number: int, product_id: int) -> Optional[Product]:
        document = self.shard_dbs[shard_number]["products"].find_one({"id": product_id}, {"_id": 0})
        return Product(**document) if document else None

    def list_products_from_all_shards(self) -> List[Product]:
        products: List[Product] = []
        for shard_number, shard_db in self.shard_dbs.items():
            logger.info("Reading products from shard_%s", shard_number)
            for document in shard_db["products"].find({}, {"_id": 0}).sort("id", 1):
                products.append(Product(**document))
        return sorted(products, key=lambda product: product.id)

    def create_cart(self, product_ids: List[int]) -> Cart:
        cart = Cart(id=self.next_id("cart_id"), product_ids=product_ids)
        self.shared_db["carts"].insert_one(cart.model_dump())
        return cart

    def get_cart(self, cart_id: int) -> Optional[Cart]:
        document = self.shared_db["carts"].find_one({"id": cart_id}, {"_id": 0})
        return Cart(**document) if document else None

    def update_cart_products(self, cart_id: int, product_ids: List[int]) -> Optional[Cart]:
        updated = self.shared_db["carts"].find_one_and_update(
            {"id": cart_id},
            {"$set": {"product_ids": product_ids}},
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        )
        return Cart(**updated) if updated else None

    def create_order(self, cart_id: int, total_price: float) -> Order:
        order = Order(id=self.next_id("order_id"), cart_id=cart_id, total_price=round(total_price, 2))
        self.shared_db["orders"].insert_one(order.model_dump())
        return order

    def get_replica_set_status(self) -> Dict[str, object]:
        """
        Returns lightweight replica-set information for the frontend/report.

        If the app is connected to a standalone MongoDB server, we still return
        a readable response so the UI can explain that replication is not active.
        """

        try:
            status = self.client.admin.command("replSetGetStatus")
            members = []

            for member in status.get("members", []):
                members.append(
                    {
                        "name": member.get("name"),
                        "state": member.get("stateStr"),
                        "health": member.get("health"),
                    }
                )

            return {
                "ok": True,
                "set": status.get("set"),
                "members": members,
            }
        except Exception as error:
            logger.warning("Replica set status unavailable: %s", error)
            return {
                "ok": False,
                "message": (
                    "Replica set status is unavailable. The app is probably connected "
                    "to a standalone MongoDB instance instead of the 3-node replica set."
                ),
            }


class ShardRouter:
    """
    Routing layer.

    Every product operation must pass through this class. It decides which shard
    should store or serve a product by applying a simple modulo rule:

        shard_number = product_id % number_of_shards

    This mirrors how a distributed system needs a router/coordinator so the app
    knows which node holds the requested data.
    """

    def __init__(self, repository: MongoShardRepository, shard_count: int = 2) -> None:
        self.repository = repository
        self.shard_count = shard_count

    def get_shard_number(self, product_id: int) -> int:
        shard_number = product_id % self.shard_count
        logger.info("Product %s routed to shard_%s", product_id, shard_number)
        return shard_number

    def create_product(self, product_data: ProductCreate) -> Product:
        product_id = self.repository.next_id("product_id")
        shard_number = self.get_shard_number(product_id)
        return self.repository.insert_product(shard_number, product_data, product_id)

    def get_product(self, product_id: int) -> Optional[Product]:
        shard_number = self.get_shard_number(product_id)
        return self.repository.get_product(shard_number, product_id)

    def list_products(self) -> List[Product]:
        return self.repository.list_products_from_all_shards()

    def create_cart(self, product_ids: List[int]) -> Cart:
        for product_id in product_ids:
            if not self.get_product(product_id):
                raise ValueError(f"Product {product_id} does not exist.")
        return self.repository.create_cart(product_ids)

    def add_to_cart(self, cart_id: int, product_id: int) -> Cart:
        if not self.get_product(product_id):
            raise ValueError(f"Product {product_id} does not exist.")

        cart = self.repository.get_cart(cart_id)
        if not cart:
            raise ValueError(f"Cart {cart_id} does not exist.")

        updated_product_ids = [*cart.product_ids, product_id]
        updated_cart = self.repository.update_cart_products(cart_id, updated_product_ids)
        if not updated_cart:
            raise ValueError(f"Cart {cart_id} does not exist.")
        return updated_cart

    def place_order(self, cart_id: int) -> Dict[str, object]:
        cart = self.repository.get_cart(cart_id)
        if not cart:
            raise ValueError(f"Cart {cart_id} does not exist.")

        products: List[Product] = []
        total_price = 0.0

        for product_id in cart.product_ids:
            product = self.get_product(product_id)
            if not product:
                raise ValueError(f"Product {product_id} does not exist.")
            products.append(product)
            total_price += product.price

        order = self.repository.create_order(cart_id=cart.id, total_price=total_price)
        return {"order": order, "cart": cart, "products": products}
