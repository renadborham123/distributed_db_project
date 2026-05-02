import logging
from pathlib import Path
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.db_router import MongoShardRepository, ShardRouter
from backend.models import Cart, CartCreate, CartItemAdd, Order, Product, ProductCreate


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

app = FastAPI(
    title="Distributed E-Commerce Demo",
    description="A simple FastAPI + MongoDB demo that simulates sharding with two MongoDB databases.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

repository = MongoShardRepository()
router = ShardRouter(repository=repository)

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/frontend", StaticFiles(directory=frontend_dir), name="frontend")


@app.get("/", include_in_schema=False)
def serve_frontend() -> FileResponse:
    return FileResponse(frontend_dir / "index.html")


@app.post("/products", response_model=Product)
def create_product(product_data: ProductCreate) -> Product:
    return router.create_product(product_data)


@app.get("/products", response_model=List[Product])
def list_products() -> List[Product]:
    return router.list_products()


@app.post("/carts", response_model=Cart)
def create_cart(cart_data: CartCreate) -> Cart:
    try:
        return router.create_cart(cart_data.product_ids)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.get("/carts/{cart_id}", response_model=Cart)
def get_cart(cart_id: int) -> Cart:
    cart = repository.get_cart(cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail=f"Cart {cart_id} does not exist.")
    return cart


@app.post("/carts/{cart_id}/items", response_model=Cart)
def add_to_cart(cart_id: int, cart_item: CartItemAdd) -> Cart:
    try:
        return router.add_to_cart(cart_id, cart_item.product_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@app.post("/orders/{cart_id}")
def place_order(cart_id: int) -> Dict[str, object]:
    try:
        result = router.place_order(cart_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error

    order: Order = result["order"]  # type: ignore[assignment]
    cart: Cart = result["cart"]  # type: ignore[assignment]
    products: List[Product] = result["products"]  # type: ignore[assignment]

    return {
        "message": "Order placed successfully.",
        "order": order.model_dump(),
        "cart": cart.model_dump(),
        "products": [product.model_dump() for product in products],
    }


@app.get("/cluster/status")
def cluster_status() -> Dict[str, object]:
    return repository.get_replica_set_status()
