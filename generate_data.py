import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os

fake = Faker('en_IN')
random.seed(42)
np.random.seed(42)

os.makedirs('data', exist_ok=True)

# ─────────────────────────────────────────
# 1. WAREHOUSES TABLE
# ─────────────────────────────────────────
WAREHOUSE_CITIES = [
    'Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Chennai',
    'Kolkata', 'Pune', 'Ahmedabad', 'Jaipur', 'Lucknow'
]

warehouses = []
for i in range(1, 11):
    capacity = random.randint(5000, 20000)
    used = random.randint(int(capacity * 0.4), int(capacity * 0.95))
    warehouses.append({
        'warehouse_id':   f'WH{i:03d}',
        'warehouse_name': f'{WAREHOUSE_CITIES[i-1]} Warehouse',
        'city':           WAREHOUSE_CITIES[i-1],
        'capacity_units': capacity,
        'used_units':     used,
        'utilization_pct': round(used / capacity * 100, 1),
        'manager':        fake.name(),
    })

df_warehouses = pd.DataFrame(warehouses)
df_warehouses.to_csv('data/warehouses.csv', index=False)
print(f"✓ Warehouses: {len(df_warehouses)} rows")

# ─────────────────────────────────────────
# 2. SUPPLIERS TABLE
# ─────────────────────────────────────────
COUNTRIES = ['India', 'China', 'USA', 'Germany', 'Japan',
             'South Korea', 'Taiwan', 'Vietnam', 'Bangladesh', 'Mexico']
SUPPLIER_CATEGORIES = ['Electronics', 'Clothing', 'Home & Kitchen',
                       'Books', 'Sports', 'Beauty', 'Raw Materials', 'Packaging']

suppliers = []
for i in range(1, 51):
    reliability = round(random.uniform(60, 99), 1)
    suppliers.append({
        'supplier_id':        f'SUP{i:03d}',
        'supplier_name':      fake.company(),
        'country':            random.choice(COUNTRIES),
        'category':           random.choice(SUPPLIER_CATEGORIES),
        'reliability_score':  reliability,
        'avg_lead_days':      random.randint(3, 45),
        'defect_rate_pct':    round(random.uniform(0.1, 8.0), 2),
        'contract_start':     fake.date_between(
                                  start_date=datetime(2020, 1, 1),
                                  end_date=datetime(2022, 12, 31)),
        'is_active':          random.choices([True, False], [0.9, 0.1])[0],
    })

df_suppliers = pd.DataFrame(suppliers)
df_suppliers.to_csv('data/suppliers.csv', index=False)
print(f"✓ Suppliers: {len(df_suppliers)} rows")

# ─────────────────────────────────────────
# 3. PRODUCTS TABLE
# ─────────────────────────────────────────
CATEGORIES = {
    'Electronics':    40,
    'Clothing':       60,
    'Home & Kitchen': 50,
    'Books':          40,
    'Sports':         50,
    'Beauty':         60,
}

PRODUCT_NAMES = {
    'Electronics':    ['Laptop', 'Smartphone', 'Headphones', 'Tablet',
                       'Smartwatch', 'Charger', 'Speaker', 'Camera'],
    'Clothing':       ['T-Shirt', 'Jeans', 'Jacket', 'Kurta',
                       'Saree', 'Sneakers', 'Hoodie', 'Formal Shirt'],
    'Home & Kitchen': ['Pressure Cooker', 'Mixer', 'Bedsheet',
                       'Air Purifier', 'Dinner Set', 'Water Bottle'],
    'Books':          ['Self-Help', 'Fiction Novel', 'Textbook',
                       'Biography', 'Cookbook', 'Comic Book'],
    'Sports':         ['Yoga Mat', 'Cricket Bat', 'Dumbbell',
                       'Running Shoes', 'Football', 'Badminton Racket'],
    'Beauty':         ['Moisturizer', 'Sunscreen', 'Lipstick',
                       'Face Wash', 'Hair Oil', 'Perfume'],
}

products = []
pid = 1
for cat, count in CATEGORIES.items():
    supplier_pool = df_suppliers[
        df_suppliers['category'].isin([cat, 'Raw Materials', 'Packaging'])
    ]['supplier_id'].tolist()
    if not supplier_pool:
        supplier_pool = df_suppliers['supplier_id'].tolist()

    for i in range(count):
        unit_cost = round(random.uniform(50, 15000), 2)
        reorder_pt = random.randint(50, 300)
        products.append({
            'product_id':       f'PROD{pid:04d}',
            'product_name':     f"{random.choice(PRODUCT_NAMES[cat])} "
                                f"{random.choice(['Pro','Plus','Lite','Max',''])}".strip(),
            'category':         cat,
            'supplier_id':      random.choice(supplier_pool),
            'warehouse_id':     random.choice(df_warehouses['warehouse_id'].tolist()),
            'unit_cost':        unit_cost,
            'selling_price':    round(unit_cost * random.uniform(1.2, 2.5), 2),
            'reorder_point':    reorder_pt,
            'reorder_quantity': reorder_pt * random.randint(2, 5),
            'weight_kg':        round(random.uniform(0.1, 25.0), 2),
        })
        pid += 1

df_products = pd.DataFrame(products)
df_products.to_csv('data/products.csv', index=False)
print(f"✓ Products: {len(df_products)} rows")

# ─────────────────────────────────────────
# 4. INVENTORY TABLE
# ─────────────────────────────────────────
inventory = []
for _, prod in df_products.iterrows():
    current_stock = random.randint(0, 1000)
    reorder_pt = prod['reorder_point']

    if current_stock == 0:
        status = 'Out of Stock'
    elif current_stock < reorder_pt:
        status = 'Low Stock'
    elif current_stock > reorder_pt * 4:
        status = 'Overstock'
    else:
        status = 'Healthy'

    inventory.append({
        'inventory_id':    f'INV{prod["product_id"]}',
        'product_id':      prod['product_id'],
        'warehouse_id':    prod['warehouse_id'],
        'current_stock':   current_stock,
        'reorder_point':   reorder_pt,
        'reorder_quantity':prod['reorder_quantity'],
        'stock_status':    status,
        'last_updated':    fake.date_between(
                               start_date=datetime(2024, 10, 1),
                               end_date=datetime(2024, 12, 31)),
        'days_of_supply':  round(current_stock / max(random.randint(5, 50), 1), 1),
    })

df_inventory = pd.DataFrame(inventory)
df_inventory.to_csv('data/inventory.csv', index=False)
print(f"✓ Inventory: {len(df_inventory)} rows")

# ─────────────────────────────────────────
# 5. PURCHASE ORDERS TABLE
# ─────────────────────────────────────────
PO_STATUSES = ['Delivered', 'Delivered', 'Delivered',
               'In Transit', 'Pending', 'Cancelled']

purchase_orders = []
for i in range(1, 2001):
    prod        = df_products.sample(1).iloc[0]
    supplier_id = prod['supplier_id']
    supplier    = df_suppliers[df_suppliers['supplier_id'] == supplier_id].iloc[0]

    order_date    = fake.date_between(
                        start_date=datetime(2023, 1, 1),
                        end_date=datetime(2024, 12, 31))
    lead_days     = int(supplier['avg_lead_days'] * random.uniform(0.7, 1.5))
    expected_date = order_date + timedelta(days=lead_days)

    status = random.choice(PO_STATUSES)
    actual_date = None
    delay_days  = 0
    if status == 'Delivered':
        delay       = random.choices([-2,-1,0,1,2,3,5,7,10],
                                      weights=[5,8,20,15,15,12,10,8,7])[0]
        delay_days  = max(0, delay)
        actual_date = expected_date + timedelta(days=delay)

    qty      = random.randint(50, 500)
    unit_cost = prod['unit_cost']

    purchase_orders.append({
        'po_id':            f'PO{i:05d}',
        'product_id':       prod['product_id'],
        'supplier_id':      supplier_id,
        'warehouse_id':     prod['warehouse_id'],
        'order_date':       order_date,
        'expected_date':    expected_date,
        'actual_date':      actual_date,
        'quantity_ordered': qty,
        'unit_cost':        unit_cost,
        'total_cost':       round(qty * unit_cost, 2),
        'status':           status,
        'delay_days':       delay_days,
        'lead_time_days':   lead_days,
    })

df_po = pd.DataFrame(purchase_orders)
df_po.to_csv('data/purchase_orders.csv', index=False)
print(f"✓ Purchase orders: {len(df_po)} rows")

# ─────────────────────────────────────────
# 6. SHIPMENTS TABLE
# ─────────────────────────────────────────
CARRIERS    = ['BlueDart', 'DTDC', 'Delhivery', 'FedEx',
               'Ecom Express', 'XpressBees', 'India Post']
SHIP_STATUS = ['Delivered', 'Delivered', 'Delivered',
               'In Transit', 'Delayed', 'Returned']
ROUTES      = [f'{a} → {b}'
               for a in WAREHOUSE_CITIES[:5]
               for b in WAREHOUSE_CITIES[5:]
               if a != b]

shipments = []
for i, po in df_po.iterrows():
    if po['status'] in ['Pending', 'Cancelled']:
        continue

    ship_date    = po['order_date'] + timedelta(days=random.randint(1, 3))
    expected_del = ship_date + timedelta(days=random.randint(2, 10))
    status       = random.choice(SHIP_STATUS)

    actual_del  = None
    delay_days  = 0
    if status == 'Delivered':
        delay      = random.choices([0,1,2,3,5,7],
                                     weights=[30,20,18,14,10,8])[0]
        delay_days = delay
        actual_del = expected_del + timedelta(days=delay)
    elif status == 'Delayed':
        delay_days = random.randint(3, 15)

    shipments.append({
        'shipment_id':        f'SHIP{i+1:05d}',
        'po_id':              po['po_id'],
        'carrier':            random.choice(CARRIERS),
        'route':              random.choice(ROUTES),
        'ship_date':          ship_date,
        'expected_delivery':  expected_del,
        'actual_delivery':    actual_del,
        'status':             status,
        'delay_days':         delay_days,
        'on_time':            1 if delay_days == 0 else 0,
        'shipping_cost':      round(random.uniform(500, 8000), 2),
        'weight_kg':          round(random.uniform(1, 500), 2),
    })

df_shipments = pd.DataFrame(shipments)
df_shipments.to_csv('data/shipments.csv', index=False)
print(f"✓ Shipments: {len(df_shipments)} rows")

# ─────────────────────────────────────────
# SAVE ALL TO EXCEL
# ─────────────────────────────────────────
with pd.ExcelWriter('data/supply_chain_data.xlsx', engine='openpyxl') as writer:
    df_warehouses.to_excel(writer, sheet_name='Warehouses',       index=False)
    df_suppliers.to_excel(writer,  sheet_name='Suppliers',        index=False)
    df_products.to_excel(writer,   sheet_name='Products',         index=False)
    df_inventory.to_excel(writer,  sheet_name='Inventory',        index=False)
    df_po.to_excel(writer,         sheet_name='Purchase Orders',  index=False)
    df_shipments.to_excel(writer,  sheet_name='Shipments',        index=False)

print("\n✓ All done! Files saved in /data folder:")
print("  - warehouses.csv")
print("  - suppliers.csv")
print("  - products.csv")
print("  - inventory.csv")
print("  - purchase_orders.csv")
print("  - shipments.csv")
print("  - supply_chain_data.xlsx  (all sheets combined)")