"""
สคริปต์สร้างตาราง PostgreSQL จาก SQLAlchemy models
รัน: python create_db.py
"""

import sys

from app.database import Base, engine

# import ทุก model เพื่อให้ Base รู้ว่ามีตารางอะไรบ้าง
import app.models.user
import app.models.document
import app.models.chat
import app.models.plan


def main():
    try:
        Base.metadata.create_all(bind=engine)

        from sqlalchemy import inspect
        tables = inspect(engine).get_table_names()

        print("✓ Tables created successfully")
        print(f"  Tables: {', '.join(tables)}")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
