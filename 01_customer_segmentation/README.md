# Customer Segmentation \& Cohort Analysis

### RFM-Based Customer Value Tiering for Retail E-commerce



 📊 **Tableau Dashboard:** \[Customer Segmentation \& Cohort Analysis](https://public.tableau.com/app/profile/dilsha.alex/viz/CustomerSegmentationCohortAnalysisDashbaord/Dashboard)



## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Dataset](#2-dataset)
3. [Project Structure](#3-project-structure)
4. [Running Instructions](#4-running-instructions)
5. [Approach \& Methodology](#5-approach--methodology)
6. [Core Code Snippets](#6-core-code-snippets)
7. [Results](#7-results)
8. [Tableau Dashboard Guide](#8-tableau-dashboard-guide)
9. [Business Conclusions](#9-business-conclusions)



## 1\. Problem Statement

Retail businesses lose 20–30% of their customer base annually. Marketing budgets that treat all customers identically waste spend on one-time buyers while under-investing in high-value repeat customers.

**Business Question:**

> Can we segment customers by purchasing behaviour to identify who deserves retention investment, who is at risk of churning, and who has already lapsed — so marketing spend can be allocated accordingly?

**Approach:** Apply RFM (Recency, Frequency, Monetary) segmentation and monthly cohort retention analysis to \~500,000 UK retail transactions, producing four actionable customer tiers with tailored retention strategies per tier.

**Role relevance:** Data Analyst



## 2\. Dataset

**Source:** [UCI Online Retail II](https://archive.ics.uci.edu/dataset/502/online+retail+ii)

|**Property**|**Detail**|
|-|-|
|Records|\~541,910 transactions (Year 2010–2011 sheet)|
|Period|December 2010 – December 2011|
|Customers|\~3,920 unique UK customers (after cleaning)|
|Key Fields|Invoice, StockCode, Quantity, InvoiceDate, Price, Customer ID, Country|

**Download:** Visit the UCI link above → download `online\_retail\_II.xlsx` → place in project root.



## 3\. Project Structure

```
01\_customer\_segmentation/
│
├── README.md
├── requirements.txt
│
├── src/                                 ← Primary pipeline (Python)
│   ├── 01\_load\_data.py             ← Load Excel → PostgreSQL
│   ├── 02\_clean\_and\_rfm.py         ← Clean data + compute RFM in Python
│   ├── 03\_cohort\_analysis.py       ← Build cohort retention table
│   ├── 04\_kmeans\_clustering.py     ← K-Means validation + charts
│   └── 05\_export\_tableau\_data.py   ← Export CSVs for Tableau Public
│
├── sql/                                 ← Alternative pipeline (SQL reference)
│   ├── 01\_create\_schema.sql        ← Create all PostgreSQL tables
│   ├── 02\_clean\_data.sql           ← Clean raw → cleaned\_transactions
│   ├── 03\_rfm\_aggregation.sql      ← Compute RFM + segment labels
│   ├── 04\_cohort\_analysis.sql      ← Build cohort retention table
│   └── 05\_export\_for\_tableau.sql   ← Export CSVs via psql COPY
│
├── notebooks/
│   └── customer\_segmentation\_rfm.ipynb  ← Interactive full pipeline
│
└── outputs/
    └── tableau\_exports/            ← CSVs for Tableau Public
        ├── rfm\_segments.csv
        ├── segment\_summary.csv
        ├── cohort\_retention.csv
        └── avg\_retention\_curve.csv
```



## 4\. Running Instructions

### Prerequisites

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create PostgreSQL database
createdb retail\_db

# 3. Place online\_retail\_II.xlsx in the project root
```

### Run Pipeline (Python — recommended)

```bash
python src/01\_load\_data.py           # Load Excel data into PostgreSQL
python src/02\_clean\_and\_rfm.py       # Clean + compute RFM scores
python src/03\_cohort\_analysis.py     # Build cohort retention table
python src/04\_kmeans\_clustering.py   # Validate with K-Means, save charts
python src/05\_export\_tableau\_data.py # Export CSVs for Tableau
```

### Alternative: Run via SQL (reference only)

> The SQL scripts cover the same cleaning and aggregation logic as Python and are provided as a reference for the database layer. They do not replace the Python pipeline — K-Means clustering and chart generation require Python.

```bash
# Prerequisite: Python pipeline step 01 must have run first to populate raw\_transactions
psql -d retail\_db -f sql/01\_create\_schema.sql
psql -d retail\_db -f sql/02\_clean\_data.sql
psql -d retail\_db -f sql/03\_rfm\_aggregation.sql
psql -d retail\_db -f sql/04\_cohort\_analysis.sql
psql -d retail\_db -f sql/05\_export\_for\_tableau.sql
```

### Or run interactively

```bash
jupyter notebook notebooks/customer\_segmentation\_rfm.ipynb
```

### Environment variable (optional)

```bash
export DATABASE\_URL="postgresql://user:password@localhost:5432/retail\_db"
```



## 5\. Approach \& Methodology

```
Raw Transactions (Excel)
        │
        ▼
┌─────────────────────┐
│ Stage 1: Ingest     │  Load Excel → PostgreSQL via SQLAlchemy
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ Stage 2: Clean      │  Remove cancellations, nulls, negatives, non-UK
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ Stage 3: RFM        │  Aggregate R/F/M per customer
│ Computation         │  Quartile scoring (1–4), segment labels
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ Stage 4: K-Means    │  Validate segments against natural clusters
│ Validation          │  Elbow + Silhouette confirm k=4
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ Stage 5: Cohort     │  Group by first-purchase month
│ Analysis            │  Track monthly retention per cohort
└─────────────────────┘
        │
        ▼
┌─────────────────────┐
│ Stage 6: Export     │  CSVs → Tableau Public dashboard
└─────────────────────┘
```

**Key methodological decisions:**

|**Decision**|**Rationale**|
|-|-|
|Quantile scoring over fixed thresholds|Adapts to any dataset's distribution; always produces balanced segments|
|`.rank(method='first')` before qcut on Frequency|Breaks integer ties before binning to ensure equal bin sizes|
|Snapshot date fixed at 2011-12-10|One day after last transaction — ensures reproducible recency values|
|Score thresholds: ≥10 Champions, ≥7 Loyal, ≥4 At-Risk, else Dormant|Based on RFM total (3–12 range); thresholds reflect natural score clusters|
|Walk-forward cohort indexing|Each cohort only compared to itself; prevents cross-cohort size bias|



## 6\. Core Code Snippets

### RFM Computation

```python
SNAPSHOT\_DATE = pd.Timestamp('2011-12-10')

rfm = (
    df.groupby('Customer ID')
    .agg(
        last\_purchase  = ('InvoiceDate', 'max'),
        frequency      = ('Invoice',     'nunique'),   # unique orders, not rows
        monetary\_value = ('Revenue',     'sum')
    )
    .reset\_index()
)
rfm\['recency\_days'] = (SNAPSHOT\_DATE - rfm\['last\_purchase']).dt.days
```

### Quartile Scoring \& Segment Assignment

```python
# R: lower days = better → reversed labels
rfm\_s\['R\_score'] = pd.qcut(rfm\_s\['recency\_days'], q=4,
                            labels=\[4,3,2,1], duplicates='drop').astype(int)

# F: rank first to handle integer ties
rfm\_s\['F\_score'] = pd.qcut(rfm\_s\['frequency'].rank(method='first'), q=4,
                            labels=\[1,2,3,4], duplicates='drop').astype(int)

# M: higher = better
rfm\_s\['M\_score'] = pd.qcut(rfm\_s\['monetary\_value'], q=4,
                            labels=\[1,2,3,4], duplicates='drop').astype(int)

rfm\_s\['RFM\_total'] = rfm\_s\['R\_score'] + rfm\_s\['F\_score'] + rfm\_s\['M\_score']

def assign\_segment(score):
    if score >= 10: return 'Champions'
    elif score >= 7: return 'Loyal'
    elif score >= 4: return 'At-Risk'
    else:            return 'Dormant'

rfm\_s\['segment'] = rfm\_s\['RFM\_total'].apply(assign\_segment)
```

### Cohort Retention

```python
df\['order\_month']  = df\['InvoiceDate'].dt.to\_period('M')
cohort\_map         = df.groupby('Customer ID')\['order\_month'].min()
df\['cohort\_month'] = df\['Customer ID'].map(cohort\_map)
df\['cohort\_index'] = (df\['order\_month'] - df\['cohort\_month']).apply(lambda x: x.n)

retention = (
    df.groupby(\['cohort\_month', 'cohort\_index'])\['Customer ID'].nunique()
    .unstack()
    .pipe(lambda x: x.divide(x\[0], axis=0))
    .mul(100).round(1)
)
```



## 7\. Results

### Segment Summary

|**Segment**|**Customers**|**Customer %**|**Avg Recency**|**Avg Orders**|**Avg Spend**|**Revenue Share**|
|-|-|-|-|-|-|-|
|🏆 Champions|1,141|29%|19 days|10|£4,850|76%|
|💛 Loyal|1,148|29%|60 days|3|£1,018|16%|
|⚠️ At-Risk|1,353|35%|144 days|1|£415|8%|
|💤 Dormant|278|7%|266 days|1|£157|1%|

**Key finding:** Champions + Loyal (58% of customers) generate **92% of total revenue.**

### Cohort Retention Pattern

```
Month 0  → 100%   (first purchase — by definition)
Month 1  →  \~21%  ← sharpest drop; highest-leverage intervention window
Month 2  →  \~22%
Month 3  →  \~23%
Month 6  →  \~25%
Month 11 →  \~31%
```

### K-Means Validation

* Elbow inflection confirmed at **k=4**
* Silhouette score at k=4: **0.561**
* K-Means confirms score-based segment boundaries reflect natural clusters in the data



## 8\. Tableau Dashboard Guide

### Files to connect in Tableau Public

|**CSV File**|**Used for**|
|-|-|
|`rfm\_segments.csv`|Individual customer RFM view|
|`segment\_summary.csv`|Bar charts, segment overview|
|`cohort\_retention.csv`|Cohort retention heatmap|
|`avg\_retention\_curve.csv`|Retention decay line chart|

### Dashboard sheets

1. **Customer Distribution by Segment** — bar chart of customer count per segment
2. **Revenue by Segment** — bar chart of total revenue per segment
3. **Cohort Retention Heatmap** — cohort month (rows) × months since acquisition (cols), colour = retention %
4. **Average Retention Curve** — line chart of avg retention % by months since first purchase



## 9\. Business Conclusions

1. **58% of customers (Champions + Loyal) generate 92% of revenue.** Champions and Loyal segments deliver disproportionate return — equal-treatment marketing campaigns leave significant retention ROI unrealised.
2. **At-Risk segment (35% of customers) represents recoverable revenue.** These customers purchased regularly but have not returned in 60–150 days. A targeted win-back campaign before the 90-day mark is the optimal intervention window.
3. **Month 0→1 is the single highest-leverage retention moment.** Retention drops sharply from 100% to \~21% after the first purchase. An early follow-up offer within 7–14 days is the most cost-effective intervention available.
4. **Dormant customers (7%) show very low re-engagement potential.** Excluding them from paid campaigns reduces wasted spend and allows budget reallocation to higher-value segments.

### Recommended Actions

|**Segment**|**Strategy**|**Trigger**|
|-|-|-|
|Champions|VIP programme, early product access|Ongoing|
|Loyal|Upsell bundles, referral incentives|Monthly campaign|
|At-Risk|Automated win-back email + 10% time-limited discount|Day 90 since last purchase|
|Dormant|Low-cost email only; exclude from paid ads|Quarterly at most|

### Potential Extensions

* Integrate segment tags into a CRM (e.g. HubSpot, Salesforce) for automated campaign triggers
* Add CLV (Customer Lifetime Value) prediction using a BG/NBD probabilistic model
* Schedule weekly RFM refresh as an Airflow DAG for always-current segment membership





***Tools:** Python 3.10 · pandas · NumPy · scikit-learn · PostgreSQL · Matplotlib · Seaborn · Tableau Public*  


