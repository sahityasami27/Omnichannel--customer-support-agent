import sys
from datetime import datetime, timedelta

print("Loading database engine...")
try:
    from backend.app.database import engine, Base, SessionLocal
    from backend.app.models import CustomerModel, OrderModel, ShipmentModel
except Exception as e:
    print(f"Error loading models: {e}")
    sys.exit(1)

print(f"Target Database: {engine.url}")

print("1. Dropping all corrupted tables...")
Base.metadata.drop_all(bind=engine)

print("2. Building fresh tables...")
Base.metadata.create_all(bind=engine)

print("3. Inserting e-commerce data...")
db = SessionLocal()
now = datetime.utcnow()

try:
    # 1. Insert Customers
    customers = [
        CustomerModel(id="cust_001", name="Alice Johnson", email="alice.j@verizon.net", tier="Standard"),
        CustomerModel(id="cust_005", name="Elena Rostova", email="elena.r@designstudio.co", tier="Gold"),
        CustomerModel(id="cust_006", name="David Kim", email="dkim@cloudscale.dev", tier="VIP"),
    ]
    db.add_all(customers)

    # 2. Insert Orders
    orders = [
        OrderModel(id="ord_105", customer_id="cust_005", items="LG UltraFine 5K Monitor", total=1450.00, status="Delayed", placed_at=now),
        OrderModel(id="ord_109", customer_id="cust_005", items="iPad Pro 13-inch OLED", total=1928.00, status="Delivered", placed_at=now),
        OrderModel(id="ord_107", customer_id="cust_001", items="Anker 737 Power Bank", total=149.99, status="Delivered", placed_at=now),
        OrderModel(id="ord_101", customer_id="cust_001", items="Logitech MX Master 3S Mouse", total=119.50, status="Delivered", placed_at=now),
        OrderModel(id="ord_106", customer_id="cust_006", items="RTX 4090 Workstation", total=2850.00, status="Delivered", placed_at=now),
        OrderModel(id="ord_110", customer_id="cust_006", items="Pro Studio Audio Rack", total=4200.00, status="Delivered", placed_at=now),
    ]
    db.add_all(orders)

    # 3. Insert Shipments
    shipments = [
        ShipmentModel(id="shp_505", order_id="ord_105", carrier="FedEx Ground", status="Weather Delay", last_update=now),
        ShipmentModel(id="shp_509", order_id="ord_109", carrier="DHL Express", status="Delivered", last_update=now),
        ShipmentModel(id="shp_507", order_id="ord_107", carrier="USPS Ground", status="Delivered", last_update=now),
        ShipmentModel(id="shp_501", order_id="ord_101", carrier="FedEx Express", status="Delivered", last_update=now),
        ShipmentModel(id="shp_506", order_id="ord_106", carrier="UPS Express", status="Delivered", last_update=now),
        ShipmentModel(id="shp_510", order_id="ord_110", carrier="UPS Freight", status="Delivered", last_update=now),
    ]
    db.add_all(shipments)

    db.commit()
    count = db.query(OrderModel).count()
    print(f"\n✅ SUCCESS! Verified {count} orders saved into the SQLite database.")
except Exception as e:
    print(f"\n❌ SEED FAILED: {e}")
    db.rollback()
finally:
    db.close()