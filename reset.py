# reset.py
from backend.app.database import engine, Base, SessionLocal
from backend.app.models import OrderModel
from backend.data.seed_data import init_db

print("1. Dropping old database tables...")
Base.metadata.drop_all(bind=engine)

print("2. Re-seeding database from seed_data.py...")
init_db()

# Verify the data was actually written
db = SessionLocal()
order_count = db.query(OrderModel).count()
print(f"3. Verification: Found {order_count} orders in SQLite!")
db.close()