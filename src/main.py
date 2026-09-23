from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
import redis
import json
from db.redis_config import redis_client
from datetime import datetime, timedelta, timezone

import models
import schemas
import jwt
from security import SECRET_KEY, ALGORITHM
from db.databases import engine, get_db
from security import hash_pwd, verify_pwd, create_access_token, get_current_user, get_current_admin, oauth2scheme

app = FastAPI(title="Mini E-commerce API")

@app.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới"
)
def register_user(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Kiem tra xem email da ton tai trong db chua
    existing_user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email này đã được sử dụng. Vui lòng chọn email khác!"
        )
        # Bat dau hash password
    hashed_pwd = hash_pwd(user_data.password)
        
        # Tao instance cho User
    new_user = models.User(
        email = user_data.email,
        hashed_password = hashed_pwd,
        is_admin = False
    )
        
        # Luu user vao db
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
@app.post(
    "/login", response_model=schemas.Token, summary="Đăng nhập nhận Access Token"
)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user or not verify_pwd(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email hoặc mật khẩu không chính xác!",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user_id=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.UserResponse)
def read_user_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/products", response_model=List[schemas.ProductResponse], summary="Xem danh sách tất cả sản phẩm")
def get_products(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """
    Hỗ trợ phân trang đơn giản:
    - skip: Bỏ qua bao nhiêu sản phẩm đầu tiên
    - limit: Lấy tối đa bao nhiêu sản phẩm trong 1 lần gọi
    """
    cached_key = "products:all"
    if redis_client:
        try:
            cached_data = redis_client.get(cached_key)
            if cached_data:
                return json.load(cached_data)
        except redis.RedisError:
            pass
    
        
    product = db.query(models.Product).all()
    if redis_client and product:
        try:
            product_data = [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price": p.price,
                    "stock": p.stock
                } for p in product
            ]
            redis_client.setex(cached_key, 60, json.dumps(product_data))
        except redis.RedisError:
            pass
    return product

# For admin
@app.post("/create-products", response_model=schemas.ProductResponse, summary="Tạo sản phẩm mới (Chỉ Admin)")
def create_product(product_data: schemas.ProductCreate, admin_user: models.User = Depends(get_current_admin), db: Session = Depends(get_db)):
    new_product = models.Product(name=product_data.name, description=product_data.descripton, price=product_data.price, stock=product_data.stock)
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    if redis_client:
        try:
            redis_client.delete("product:all")
        except redis.RedisError:
            pass
    return new_product

@app.post("/orders", response_model=schemas.OrderResponse, status_code=status.HTTP_201_CREATED, summary="Tạo order mới")
def create_order(order_data: schemas.OrderCreate, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    total_price = 0.0
    order_items_to_create = []
    try:
        for item in order_data.items:
            product = db.query(models.Product).filter(models.Product.id == item.product_id).with_for_update().first()
            
            # Kiểm tra xem có sản phẩm đấy không
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Không tìm thấy sản phẩm. Vui lòng kiểm tra lại!"
                )

            # Kiểm tra xem sản phẩm có tồn tại hay không
            if product.stock < item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Sản phẩm '{product.name}' chỉ còn {product.stock} cái trong kho, không đủ đáp ứng số lượng {item.quantity}!"
                )
            
            product.stock -= item.quantity
            item_total_price = product.price * item.quantity
            total_price += item_total_price
            
            order_item = models.OrderItem(product_id=product.id, quantity=item.quantity, price_at_purchase=product.price)
            order_items_to_create.append(order_item)
        # Tao don hang
        new_order = models.Order(user_id=user.id, total_price=round(total_price, 2), status="Pending", items=order_items_to_create)
        
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        return new_order
    except Exception:
        db.rollback()
        raise

@app.get("/orders/my-orders", response_model=List[schemas.OrderResponse], summary="Xem lịch sử đơn hàng")
def get_order_history(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(models.Order).filter(models.Order.user_id == user.id).all()
    return orders

# Huy don hang
@app.put("/orders/{order_id}/cancel", response_model=schemas.OrderResponse, summary="Hủy đơn hàng")
def cancel_order(order_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Không tìm thấy đơn hàng {order_id}"
        )
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền hủy đơn hàng người khác"
        )
    # Kiem tra trang thai don hang
    if order.status == "Cancelled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Đơn hàng đã được hủy trước đó!"
        )
    # Kiem tra xem don hang co o trang thai Pending hay khong
    if order.status != "Pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Không thể hủy đơn hàng vì đơn hàng đã chuyển sang trạng thái {order.status}!"
        )
    for items in order.items:
        product = db.query(models.Product).filter(models.Product.id == items.product_id).first()
        if product:
            product.stock += items.quantity
    order.status = "Cancelled"
    # Commit va update like bang trong db
    db.commit()
    db.refresh(order)
    
    return order

app.get("/order/{order_id}/status", response_model=schemas.OrderStatusResponse,summary="Kiểm tra trạng thái đơn hàng")
def get_order_status(order_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Không tồn tại đơn hàng vui lòng kiểm tra lại!"
        )
    if order.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem đơn hàng của người khác!"
        )
    return {
        "order_id" : order_id,
        "status": order.status
    }

@app.post("/refresh", response_model=schemas.TokenRepsonse)
def refresh_token(request_data: schemas.RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(request_data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không đúng!"
            )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token không hợp lệ!"
            )
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Refresh Token đã hết hạn hoặc không hợp lệ!")
    new_token = create_access_token(user_id=int(user_id))
    return {
        "access_token" : new_token,
        "refresh_token" : request_data.refresh_token,
        "token_type" : "bearer"
    }

@app.post("/logout", summary="Đăng xuất và vô hiệu hóa token")
def logout(token: str = Depends(oauth2scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        expire = payload.get("exp")
        
        if not jti or not expire:
            raise HTTPException(
                status_code=400, detail="Token không hợp lệ để đăng xuất!"
            )
        
        
        now = datetime.now(timezone.utc).timestamp()
        remaining_seconds = int(expire - now)
        
        if remaining_seconds > 0:
            redis_client.setex(f"blacklist:{jti}", remaining_seconds, "revoked")
        return {"message" : "Đăng xuất thành công"}
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc đã hết hạn!")