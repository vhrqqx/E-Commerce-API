from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List

# Schema cho nguoi dung
class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72, description="Mật khẩu phải từ 6 đến 72 ký tự")
class UserResponse(BaseModel):
    id: int
    email: str
    is_admin: bool
    model_config = ConfigDict(from_attributes=True)
    
# Schema cho Product
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Tên sản phẩm không được để trống")
    price: float = Field(..., ge=0, description="Giá sản phẩm phải lớn hơn hoặc bằng 0")
    stock: int = Field(..., ge=0, description="Tồn kho phải lớn hơn hoặc bằng 0")
    descripton: str | None = None
class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    stock: int

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., gt=0, description="Số lượng mua phải lớn hơn 0")
    
class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(..., min_length=1, description="Đơn hàng phải có ít nhất 1 sản phẩm")
    
class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int
    price_at_purchase: int
    
    model_config = ConfigDict(from_attributes=True)
    
class OrderResponse(BaseModel):
    id: int
    user_id: int
    total_price: float
    status: str
    items: List[OrderItemResponse]
    
    model_config = ConfigDict(from_attributes=True)

class OrderStatusResponse(BaseModel):
    order_id: int
    status: str
    
class TokenRepsonse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    
class RefreshRequest(BaseModel):
    refresh_token: str