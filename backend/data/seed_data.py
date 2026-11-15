from datetime import datetime, timedelta
from backend.app.database import SessionLocal, engine, Base
from backend.app.models import (
    CustomerModel,
    OrderModel,
    ShipmentModel,
    PolicyModel,
    TicketModel,
)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Force clear everything if we are resetting
    db.query(ShipmentModel).delete()
    db.query(OrderModel).delete()
    db.query(TicketModel).delete()
    db.query(CustomerModel).delete()
    db.query(PolicyModel).delete()
    db.commit()

    now = datetime.utcnow()

    customers = [
        CustomerModel(id="cust_001", name="Alice Johnson", email="alice.j@verizon.net", tier="Standard"),
        CustomerModel(id="cust_002", name="Bob Smith", email="bob.smith@enterprise.io", tier="VIP"),
        CustomerModel(id="cust_003", name="Priya Nair", email="priya.nair@techcorp.in", tier="VIP"),
        CustomerModel(id="cust_004", name="Marcus Vance", email="mvance@outlook.com", tier="Standard"),
        CustomerModel(id="cust_005", name="Elena Rostova", email="elena.r@designstudio.co", tier="Gold"),
        CustomerModel(id="cust_006", name="David Kim", email="dkim@cloudscale.dev", tier="VIP"),
    ]
    db.add_all(customers)

    orders = [
        OrderModel(id="ord_101", customer_id="cust_001", items="Logitech MX Master 3S Mouse", total=119.50, status="Delivered", placed_at=now - timedelta(days=6), delivered_at=now - timedelta(days=3)),
        OrderModel(id="ord_102", customer_id="cust_002", items="MacBook Pro 16-inch", total=3499.00, status="Shipped", placed_at=now - timedelta(days=3)),
        OrderModel(id="ord_103", customer_id="cust_003", items="Sony WH-1000XM5 Headphones", total=398.00, status="Delivered", placed_at=now - timedelta(days=9), delivered_at=now - timedelta(days=5)),
        OrderModel(id="ord_104", customer_id="cust_004", items="Keychron Q1 Pro Keyboard", total=215.00, status="Processing", placed_at=now - timedelta(days=1)),
        OrderModel(id="ord_105", customer_id="cust_005", items="LG UltraFine 5K Monitor", total=1450.00, status="Delayed", placed_at=now - timedelta(days=8)),
        OrderModel(id="ord_106", customer_id="cust_006", items="RTX 4090 Workstation", total=2850.00, status="Delivered", placed_at=now - timedelta(days=4), delivered_at=now - timedelta(days=1)),
        OrderModel(id="ord_107", customer_id="cust_001", items="Anker 737 Power Bank", total=149.99, status="Delivered", placed_at=now - timedelta(days=65), delivered_at=now - timedelta(days=61)),
        OrderModel(id="ord_108", customer_id="cust_003", items="Herman Miller Aeron Chair", total=1695.00, status="In Transit", placed_at=now - timedelta(days=4)),
        OrderModel(id="ord_109", customer_id="cust_005", items="iPad Pro 13-inch OLED", total=1928.00, status="Delivered", placed_at=now - timedelta(days=12), delivered_at=now - timedelta(days=9)),
        OrderModel(id="ord_110", customer_id="cust_006", items="Pro Studio Audio Rack", total=4200.00, status="Delivered", placed_at=now - timedelta(days=5), delivered_at=now - timedelta(days=2)),
    ]
    db.add_all(orders)

    shipments = [
        ShipmentModel(id="shp_501", order_id="ord_101", carrier="FedEx Express", status="Delivered", last_update=now - timedelta(days=3)),
        ShipmentModel(id="shp_502", order_id="ord_102", carrier="UPS Next Day Air", status="In Transit", last_update=now - timedelta(hours=6)),
        ShipmentModel(id="shp_503", order_id="ord_103", carrier="DHL Express", status="Delivered", last_update=now - timedelta(days=5)),
        ShipmentModel(id="shp_504", order_id="ord_104", carrier="USPS Priority", status="Label Created", last_update=now - timedelta(hours=12)),
        ShipmentModel(id="shp_505", order_id="ord_105", carrier="FedEx Ground", status="Weather Delay", last_update=now - timedelta(hours=18)),
        ShipmentModel(id="shp_506", order_id="ord_106", carrier="UPS Express", status="Delivered", last_update=now - timedelta(days=1)),
        ShipmentModel(id="shp_507", order_id="ord_107", carrier="USPS Ground", status="Delivered", last_update=now - timedelta(days=61)),
        ShipmentModel(id="shp_508", order_id="ord_108", carrier="FedEx Freight", status="Out for Delivery", last_update=now - timedelta(hours=2)),
        ShipmentModel(id="shp_509", order_id="ord_109", carrier="DHL Express", status="Delivered", last_update=now - timedelta(days=9)),
        ShipmentModel(id="shp_510", order_id="ord_110", carrier="UPS Freight", status="Delivered", last_update=now - timedelta(days=2)),
    ]
    db.add_all(shipments)
    db.commit()
    db.close()