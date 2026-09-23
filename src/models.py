import sys
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from db.databases import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    
    # Thiet lap moi quan he
    orders = relationship("Order", back_populates="owner")
    
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    
    order_items = relationship("OrderItem", back_populates="product")
    
class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Khoa ngoai
    total_price = Column(Float, nullable=False)
    status = Column(String, default="Pending")
    
    # Lien ket nguoc lai voi bang User
    owner = relationship("User", back_populates="orders")
    # 1 order chua nhieu dong chi tiet san pham
    items = relationship("OrderItem", back_populates="order")

class OrderItem(Base):
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_purchase = Column(Float, nullable=False)
    
    # Lien ket nguoc lai
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")