# Decision Log

**Question:** Do households that received marketing campaigns spend more on average than households that did not?


**Step 1 - tool call:** `get_schema` 
**Result:**
```
TABLE campaign_desc: DESCRIPTION (TEXT), CAMPAIGN (INTEGER), START_DAY (INTEGER), END_DAY (INTEGER)
TABLE campaigns: DESCRIPTION (TEXT), household_key (INTEGER), CAMPAIGN (INTEGER)
TABLE coupon_redemptions: household_key (INTEGER), DAY (INTEGER), COUPON_UPC (INTEGER), CAMPAIGN (INTEGER)
TABLE coupons: COUPON_UPC (INTEGER), PRODUCT_ID (INTEGER), CAMPAIGN (INTEGER)
TABLE households: AGE_DESC (TEXT), MARITAL_STATUS_CODE (TEXT), INCOME_DESC (TEXT), HOMEOWNER_DESC (TEXT), HH_COMP_DESC (TEXT), HOUSEHOLD_SIZE_DESC (TEXT), KID_CATEGORY_DESC (TEXT), household_key (INTEGER)
TABLE products: PRODUCT_ID (INTEGER), MANUFACTURER (INTEGER), DEPARTMENT (TEXT), BRAND (TEXT), COMMODITY_DESC (TEXT), SUB_COMMODITY_DESC (TEXT), CURR_SIZE_OF_PRODUCT (TEXT)
TABLE transactions: household_key (INTEGER), BASKET_ID (INTEGER), DAY (INTEGER), PRODUCT_ID (INTEGER), QUANTITY (INTEGER), SALES_VALUE (REAL), STORE_ID (INTEGER), RETAIL_DISC (REAL), TRANS_TIME (INTEGER), WEEK_NO (INTEGER), COUPON_DISC (REAL), COUPON_MATCH_DISC (REAL)
```

**Step 2 - tool call:** `run_sql` 
```sql
SELECT 
    (SELECT COUNT(DISTINCT household_key) FROM campaigns) AS households_in_campaign,
    (SELECT COUNT(DISTINCT household_key) FROM households) AS total_households

```
**Result:**
```
households_in_campaign | total_households
1584 | 801
```

**Step 3 - tool call:** `run_sql` 
```sql
SELECT COUNT(DISTINCT household_key) FROM households
```
**Result:**
```
COUNT(DISTINCT household_key)
801
```

**Step 4 - tool call:** `run_sql` 
```sql
SELECT COUNT(DISTINCT household_key) FROM transactions
```
**Result:**
```
COUNT(DISTINCT household_key)
2500
```

**Step 5 - tool call:** `run_sql` 
```sql
SELECT 
    COUNT(DISTINCT household_key) AS total_households_with_transactions
FROM transactions
```
**Result:**
```
total_households_with_transactions
2500
```

**Step 6 - tool call:** `run_sql` 
```sql
SELECT 
    AVG(total_spend) as avg_spend
FROM (
    SELECT SUM(SALES_VALUE) as total_spend
    FROM transactions
    WHERE household_key IN (SELECT DISTINCT household_key FROM campaigns)
    GROUP BY household_key
)
UNION ALL
SELECT 
    AVG(total_spend) as avg_spend
FROM (
    SELECT SUM(SALES_VALUE) as total_spend
    FROM transactions
    WHERE household_key NOT IN (SELECT DISTINCT household_key FROM campaigns)
    GROUP BY household_key
)
```
**Result:**
```
avg_spend
4491.992859848485
1028.5440938864629
```

**Step 7 - agent reasoning:** To determine if households that received marketing campaigns spent more on average than those that did not, we compared the average total transaction value for both groups:

*   **Households that received marketing campaigns:** These households spent an average of approximately **$4,491.99** per household.
*   **Households that did not receive marketing campaigns:** These households spent an average of approximately **$1,028.54** per household.

On average, households that were included in marketing campaigns spent significantly more—roughly 4.4 times more—than households that were not targeted by campaigns.

---

## Final Answer

To determine if households that received marketing campaigns spent more on average than those that did not, we compared the average total transaction value for both groups:

*   **Households that received marketing campaigns:** These households spent an average of approximately **$4,491.99** per household.
*   **Households that did not receive marketing campaigns:** These households spent an average of approximately **$1,028.54** per household.

On average, households that were included in marketing campaigns spent significantly more—roughly 4.4 times more—than households that were not targeted by campaigns.
