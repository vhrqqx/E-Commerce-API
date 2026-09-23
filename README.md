# 🛒 E-Commerce Backend Service

Hệ thống backend RESTful API cho nền tảng thương mại điện tử (E-commerce) được xây dựng bằng **FastAPI**, tuân thủ nghiêm ngặt các nguyên lý kiến trúc backend hiện đại: Stateless Authentication, In-Memory Caching, Concurrency Control (Chống bán lố) và Containerization.

---

## 🚀 Công nghệ sử dụng (Tech Stack)

* **Ngôn ngữ:** Python 3.11
* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (High performance, async-ready)
* **Cơ sở dữ liệu quan hệ (RDBMS):** [PostgreSQL](https://www.postgresql.org/) kết hợp **SQLAlchemy 2.0 ORM**
* **Database Migrations:** [Alembic](https://alembic.sqlalchemy.org/)
* **In-Memory Cache & Blacklist:** [Redis](https://redis.io/)
* **Kiểm thử tự động:** [pytest](https://docs.pytest.org/), `httpx` (SQLite in-memory isolation)
* **Ảo hóa & Triển khai:** [Docker](https://www.docker.com/), Docker Compose

---

## 📌 Các tính năng & Điểm nhấn kỹ thuật

1. **Authentication & Authorization (JWT):**
   * Triển khai Access Token (ngắn hạn) và Refresh Token (dài hạn).
   * Cơ chế **Token Blacklist bằng Redis** với TTL (Time-To-Live) tự hủy để vô hiệu hóa token ngay khi người dùng đăng xuất (`/logout`).
   * Phân quyền Role-based Access Control (RBAC): Phân chia rành mạch giữa `Admin` và `Customer`.

2. **Xử lý đồng thời & Toàn vẹn dữ liệu (Concurrency Control):**
   * Sử dụng **Pessimistic Locking (`SELECT ... FOR UPDATE`)** thông qua SQLAlchemy `.with_for_update()` trong quá trình tạo đơn hàng để triệt tiêu hoàn toàn lỗi **Race Condition (Overselling - bán âm kho)** khi nhiều người cùng mua một sản phẩm tại cùng một thời điểm.
   * Quản lý giao dịch (ACID Transactions): Tự động trừ kho khi tạo đơn và hoàn trả tồn kho khi đơn hàng bị hủy (`Rollback/Cancel`).

3. **Tối ưu hóa hiệu năng (Caching):**
   * Áp dụng mô hình **Cache-Aside Pattern** trên Redis cho endpoint danh sách sản phẩm (`GET /products`).
   * Tự động vô hiệu hóa Cache (Cache Invalidation) khi Admin thêm, sửa hoặc xóa sản phẩm.

4. **Kiểm thử tự động (Automated Testing):**
   * Bộ kiểm thử Unit Test và Integration Test độc lập hoàn toàn bằng `pytest`.
   * Sử dụng SQLite trên RAM (`sqlite:///:memory:`) và cơ chế Dependency Override của FastAPI để chạy test mà không ảnh hưởng tới Database thật.

---

## 📂 Cấu trúc thư mục dự án

```text
eCommerceService/
├── alembic/                # Lịch sử và cấu hình database migrations
├── src/
│   ├── db/                 # Cấu hình kết nối PostgreSQL và Redis Client
│   ├── models/             # SQLAlchemy ORM Models (User, Product, Order, OrderItem)
│   ├── schemas/            # Pydantic Schemas (Request/Response validation)
│   ├── routers/            # API Endpoints (Auth, Products, Orders, Users)
│   ├── security.py         # Logic mã hóa mật khẩu, tạo/giải mã JWT, OAuth2 Bearer
│   └── main.py             # Điểm khởi chạy ứng dụng FastAPI
├── tests/                  # Bộ test tự động (conftest.py, test_auth, test_orders)
├── .dockerignore
├── alembic.ini
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md