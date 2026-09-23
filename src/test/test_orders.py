import models
import json
from security import create_access_token

def test_order_stock_and_cancel(client,db_session):
    buyer = models.User(email="customer@example.com", hashed_password="fakehash", is_admin=False)
    product = models.Product(name="Tai nghe bluetooth", price=50.0, stock=10)
    db_session.add_all([buyer, product])
    db_session.commit()
    db_session.refresh(buyer)
    db_session.refresh(product)
    
    token = create_access_token(user_id=buyer.id)
    headers = {"Authorization" : f"Bearer {token}"}
    
    # Starting order
    order_payload = {
        "items" : [{"product_id" : product.id, "quantity" : 4}]
    }
    create_order = client.post("/orders", json=order_payload, headers=headers)
    assert create_order.status_code == 201
    order_data = create_order.json()
    order_id = order_data["id"]
    assert order_data["status"] == "Pending"
    
    db_session.refresh(product)
    assert product.stock == 6
    
    exceed_payload = {
        "items" : [{"product_id" : product.id, "quantity" : 10}]
    }
    create_exceed = client.post("/orders", json=exceed_payload, headers=headers)
    assert create_exceed.status_code == 400
    
    # Cancel order
    cancel_order = client.put(f"/orders/{order_id}/cancel", headers=headers)
    assert cancel_order.status_code == 200
    assert cancel_order.json()["status"] == "Cancelled"
    
    db_session.refresh(product)
    assert product.stock == 10
    
def test_cancel_unauthorized_user(client, db_session):
    user_a = models.User(email="usera@example.com", hashed_password="pwd", is_admin=False)
    user_b = models.User(email="userb@example.com", hashed_password="pwd", is_admin=False)
    product = models.Product(name="Chuot gaming", price=20.0, stock=5)
    db_session.add_all([user_a, user_b, product])
    db_session.commit()
    token_a = create_access_token(user_id=user_a.id)
    order_res = client.post("/orders", json={"items" : [{"product_id" : product.id, "quantity" : 1}]}, headers={"Authorization" : f"Bearer {token_a}"})
    order_id = order_res.json()["id"]
    token_b = create_access_token(user_id=user_b.id)
    cancel_order_unauthorized = client.put(f"/orders/{order_id}/cancel", headers={"Authorization" : f"Bearer {token_b}"})
    assert cancel_order_unauthorized.status_code == 403