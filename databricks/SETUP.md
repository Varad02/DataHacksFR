# Databricks Setup Guide

## 1. Create a workspace

Sign up at databricks.com (Community Edition is free and sufficient for the prototype run).

## 2. Create a cluster

- Runtime: 14.x LTS (Spark 3.5, Python 3.11)
- Node type: Standard_DS3_v2 or similar (2-4 workers)
- For the full 176GB dataset: memory-optimized nodes (Standard_E8s_v3 or similar)

## 3. Upload data to DBFS

```bash
# Install Databricks CLI
pip install databricks-cli

# Configure with your workspace URL and token
databricks configure --token

# Upload prototype dataset
databricks fs cp data/raw/scripps/seismos_16_receivers.npy dbfs:/seismic/seismos_16_receivers.npy
databricks fs cp data/raw/scripps/receiver_locations.csv dbfs:/seismic/receiver_locations.csv
databricks fs cp data/processed/property_risk_joined.parquet dbfs:/seismic/property_risk_joined.parquet

# For full dataset (176GB -- only if available)
databricks fs cp data/raw/scripps/velocity_time_series.npy dbfs:/seismic/velocity_time_series.npy
```

## 4. Import notebooks

In the Databricks UI:
- Workspace > Import > select `01_pgv_extraction.py` and `02_spatial_join_spark.py`
- Attach to your cluster and run in order

## 5. Create the database

Run this in a notebook cell before running the extraction:

```sql
CREATE DATABASE IF NOT EXISTS seismic;
```

## 6. Download results

```bash
databricks fs cp dbfs:/seismic/pgv_pga_features.parquet data/processed/pgv_pga_features_full.parquet
```

## Why Databricks

The full Scripps dataset is 176GB -- a single `(8181, 600, 500)` float64 array. Extracting PGV/PGA for all 8181 x 500 = 4,090,500 (receiver, source) pairs sequentially on a laptop would take hours. On a 4-worker Databricks cluster, the RDD is parallelized across nodes and completes in minutes.

The prototype run on `seismos_16_receivers.npy` (8000 pairs) demonstrates the exact same workflow and can be run on Community Edition at no cost.
