import redis
import os
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=0,
        decode_responses=True,
        socket_connect_timeout=1.5,
        socket_timeout=1.5
    )

    redis_client.ping()
    print("Ket noi server Redis thanh cong!")
except redis.ConnectionError:
    print("Khong the ket noi toi Redis Server")
    redis_client = None