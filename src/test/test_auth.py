import json

def test_register_user(client):
    """Kiểm thử đăng ký tài khoản mới thành công."""
    response = client.post("/register", json={"email" : "user2@example.com", "password": "12345user"})
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "user2@example.com"
    assert "id" in data
    assert "password" not in data
    
def test_duplicate_email(client):
    payload = {"email" : "duplicate@example.com", "password" : "12345user"}
    client.post("/register", json=payload)
    
    response = client.post("/register", json=payload)
    assert response.status_code == 400
    assert "đã được sử dụng" in response.json()["detail"]

def test_login_and_get_token(client):
    client.post("/register", json={"email" : "user3@example.com", "password" : "user3123"})
    
    login_result = client.post("/login", data={"username" : "user3@example.com", "password" : "user3123"})
    assert login_result.status_code == 200
    tokens = login_result.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"
    token = tokens["access_token"]
    profile_res = client.get("/users/me", headers={"Authorization" : f"Bearer {token}"})
    assert profile_res.status_code == 200
    assert profile_res.json()["email"] == "user3@example.com"
    
def test_access_protected_without_token(client):
    response = client.get("/users/me")
    assert response.status_code == 401