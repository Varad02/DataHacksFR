# Databricks notebook -- Distributed PGV/PGA Extraction
# Works on Serverless compute (no sparkContext needed)
# Files must be uploaded to /Volumes/workspace/default/datahacks/

# COMMAND ----------
import numpy as np
import pandas as pd
from pathlib import Path

DT = 0.1  # seconds, 10 Hz sampling
SEISMO_PATH = "/Volumes/workspace/default/datahacks/seismos_16_receivers.npy"
OUTPUT_TABLE = "workspace.default.pgv_pga_features"

print(f"Loading seismograms from {SEISMO_PATH}")
seismograms = np.load(SEISMO_PATH, mmap_mode="r")
n_receivers, n_timesteps, n_sources = seismograms.shape
print(f"Shape: {seismograms.shape}  ({n_receivers} receivers x {n_sources} sources)")

# COMMAND ----------
# Extract PGV, PGA, Arias Intensity for all (receiver, source) pairs
print("Extracting features...")
records = []
for r in range(n_receivers):
    for s in range(n_sources):
        trace = seismograms[r, :, s]
        accel = np.gradient(trace, DT)
        records.append({
            "receiver_id": int(r),
            "source_id":   int(s),
            "pgv":   float(np.max(np.abs(trace))),
            "pga":   float(np.max(np.abs(accel))),
            "arias": float((np.pi / (2 * 9.81)) * np.trapezoid(accel**2, dx=DT)),
        })

features_df = pd.DataFrame(records)
print(f"Extracted {len(features_df):,} rows")
print(features_df.describe())

# COMMAND ----------
# Save as Delta table via Spark (just the write -- no RDDs)
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()

spark_df = spark.createDataFrame(features_df)
spark_df.write.format("delta").mode("overwrite").saveAsTable(OUTPUT_TABLE)
print(f"Saved to Delta table: {OUTPUT_TABLE}")

# Also save parquet back to volume for local download
out_path = "/Volumes/workspace/default/datahacks/pgv_pga_features.parquet"
features_df.to_parquet(out_path, index=False)
print(f"Saved parquet to {out_path}")
