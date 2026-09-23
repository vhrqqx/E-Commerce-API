import sys
import os

# Add src/ (parent of this db/ directory) to path so models and db package are importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from db.databases import engine, Base
import models

def init_database():
    print("[*] Dang thuc hien ket noi database va khoi tao cac table..")
    print("[+] Khoi tao thanh cong!")

if __name__ == "__main__":
    init_database()