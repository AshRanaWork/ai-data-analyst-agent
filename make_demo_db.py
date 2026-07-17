"""Build a small demo database (the 801 households with demographics)
so the agent can be deployed publicly. Output: ecommerce_demo.db (~40MB)."""

import os
import sqlite3

SRC, DST = "ecommerce.db", "ecommerce_demo.db"

if os.path.exists(DST):
    os.remove(DST)

src = sqlite3.connect(SRC)
src.execute(f"ATTACH DATABASE '{DST}' AS demo")

# Small tables: copy fully
for t in ["households", "products", "campaign_desc", "coupons"]:
    src.execute(f"CREATE TABLE demo.{t} AS SELECT * FROM {t}")

# Household-keyed tables: keep only the 801 households with demographics
for t in ["transactions", "campaigns", "coupon_redemptions"]:
    src.execute(
        f"CREATE TABLE demo.{t} AS SELECT * FROM {t} "
        f"WHERE household_key IN (SELECT household_key FROM households)"
    )

src.commit()
src.execute("DETACH DATABASE demo")
src.close()

size_mb = os.path.getsize(DST) / 1_048_576
print(f"Created {DST} ({size_mb:.1f} MB)")