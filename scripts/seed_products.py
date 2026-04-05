"""
scripts/seed_products.py
-------------------------
Seeds products from product.json in the project root.

Supported JSON formats:
  - Array of objects:  [{...}, {...}]
  - Object with key:   {"products": [{...}]}
  - Any nested list found automatically

Required fields per product:  name, price
Optional:  category, unit, barcode, stock, low_stock_threshold

Usage:
    python scripts/seed_products.py
    python scripts/seed_products.py --file /path/to/custom.json
    python scripts/seed_products.py --dry-run
"""

import sys, os, json, argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import get_session
from app.models.product import Product
from app.models.stock_movement import StockMovement
from app.models.user import User


def find_products_in_json(data):
    """Recursively find the first list of objects in any JSON structure."""
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return data
    if isinstance(data, dict):
        # Common key names
        for key in ["products", "items", "data", "records", "inventory"]:
            if key in data and isinstance(data[key], list):
                return data[key]
        # Try any key containing a list of dicts
        for v in data.values():
            result = find_products_in_json(v)
            if result:
                return result
    return []


def normalise(raw: dict) -> dict:
    """Map common field name variants to our schema."""
    def get(*keys):
        for k in keys:
            if k in raw:
                return raw[k]
        return None

    name  = get("name", "product_name", "title", "item_name", "Name")
    price = get("price", "selling_price", "unit_price",
                "Price", "cost", "amount")
    cat   = get("category", "Category", "type", "department", "group") or "Other"
    unit  = get("unit", "Unit", "uom", "unit_of_measure") or "piece"
    bc    = get("barcode", "Barcode", "sku", "SKU", "code", "Code")
    stock = get("stock", "Stock", "quantity", "qty",
                "opening_stock", "initial_stock") or 0
    low   = get("low_stock_threshold", "low_stock", "reorder_point",
                "min_stock") or 5

    if not name:
        return None
    try:
        price = float(str(price).replace(",", "").strip())
    except (TypeError, ValueError):
        price = 0.0

    return {
        "name":                str(name).strip(),
        "price":               price,
        "category":            str(cat).strip(),
        "unit":                str(unit).strip(),
        "barcode":             str(bc).strip() if bc else None,
        "stock":               float(str(stock).replace(",", "") or 0),
        "low_stock_threshold": float(str(low) or 5),
    }


def seed(json_path: str, dry_run: bool = False):
    if not os.path.exists(json_path):
        print(f"✕  File not found: {json_path}")
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        raw = json.load(f)

    items = find_products_in_json(raw)
    if not items:
        print("✕  Could not find a list of products in the JSON file.")
        print("   Expected: an array of objects, or {\"products\": [...]}")
        sys.exit(1)

    print(f"\n  Found {len(items)} records in {os.path.basename(json_path)}\n")

    # Get or create system admin for stock movement log
    with get_session() as session:
        admin = session.query(User).filter_by(role="admin").first()
        admin_id = admin.id if admin else 1

    created  = 0
    updated  = 0
    skipped  = 0
    errors   = 0

    for i, raw_item in enumerate(items):
        data = normalise(raw_item)
        if not data:
            print(f"  ⚠  Row {i+1}: missing name — skipping")
            skipped += 1
            continue

        if data["price"] <= 0:
            print(f"  ⚠  '{data['name']}': price is 0 — will be imported but flagged")

        if dry_run:
            print(f"  [DRY RUN] Would import: {data['name']}"
                  f"  price={data['price']}"
                  f"  stock={data['stock']}"
                  f"  cat={data['category']}")
            created += 1
            continue

        try:
            with get_session() as session:
                existing = (
                    session.query(Product)
                    .filter(Product.name.ilike(data["name"]))
                    .first()
                )

                if existing:
                    # Update price and threshold, leave stock alone
                    existing.price               = data["price"]
                    existing.category            = data["category"]
                    existing.unit                = data["unit"]
                    existing.low_stock_threshold = data["low_stock_threshold"]
                    if data["barcode"] and not existing.barcode:
                        existing.barcode = data["barcode"]
                    print(f"  ↻  Updated : {data['name']}")
                    updated += 1
                else:
                    p = Product(
                        name                = data["name"],
                        category            = data["category"],
                        price               = data["price"],
                        unit                = data["unit"],
                        barcode             = data["barcode"],
                        stock               = data["stock"],
                        low_stock_threshold = data["low_stock_threshold"],
                        is_active           = True,
                        created_by          = admin_id,
                    )
                    session.add(p)
                    session.flush()

                    if data["stock"] > 0:
                        session.add(StockMovement(
                            product_id      = p.id,
                            user_id         = admin_id,
                            movement_type   = "opening_stock",
                            quantity_change = data["stock"],
                            stock_before    = 0,
                            stock_after     = data["stock"],
                            reason          = "Seeded from product.json",
                        ))

                    print(f"  ✓  Imported: {data['name']}"
                          f"  ({data['category']}, "
                          f"{data['unit']}, "
                          f"KES {data['price']:,.2f}, "
                          f"stock={data['stock']:g})")
                    created += 1

        except Exception as e:
            print(f"  ✕  Error on '{data.get('name','?')}': {e}")
            errors += 1

    print(f"\n{'─'*50}")
    if dry_run:
        print(f"  DRY RUN complete — no changes written")
        print(f"  Would import: {created}  skipped: {skipped}")
    else:
        print(f"  ✓  Imported : {created}")
        print(f"  ↻  Updated  : {updated}")
        print(f"  ⚠  Skipped  : {skipped}")
        print(f"  ✕  Errors   : {errors}")
    print(f"{'─'*50}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed PosFlow products from a JSON file"
    )
    parser.add_argument(
        "--file", "-f",
        default=os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "product.json"
        ),
        help="Path to JSON file (default: product.json in project root)"
    )
    parser.add_argument(
        "--dry-run", "-d",
        action="store_true",
        help="Preview what would be imported without writing to DB"
    )
    args = parser.parse_args()

    print(f"\n  PosFlow Product Seeder")
    print(f"  File: {args.file}")
    if args.dry_run:
        print("  Mode: DRY RUN (no changes will be written)")
    seed(args.file, dry_run=args.dry_run)
