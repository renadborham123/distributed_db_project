from typing import List

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Display name for the product")
    price: float = Field(..., gt=0, description="Simple numeric price")
    description: str = Field(..., min_length=1, description="Short product description")


class Product(ProductCreate):
    id: int


class CartCreate(BaseModel):
    product_ids: List[int] = Field(default_factory=list)


class Cart(BaseModel):
    id: int
    product_ids: List[int] = Field(default_factory=list)


class CartItemAdd(BaseModel):
    product_id: int


class Order(BaseModel):
    id: int
    cart_id: int
    total_price: float

