# Databricks notebook -- Spatial Join at Scale
# Runs after 01_pgv_extraction.py
# Uses all 8181 receivers instead of the 16-receiver prototype

# COMMAND ----------
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sqrt, pow as spow, min as smin, first, avg
import pandas as pd
import numpy as np

spark = SparkSession.builder.getOrCreate()

# COMMAND ----------
# Load features from Delta table written by 01_pgv_extraction.py
features_df = spark.table("workspace.default.pgv_pga_features")
print(f"Features: {features_df.count():,} rows")

# Load receiver locations (upload receiver_locations.csv to DBFS)
receivers_pdf = pd.read_csv("/Volumes/workspace/default/datahacks/receiver_locations.csv")
receivers_df = spark.createDataFrame(receivers_pdf)

# Load census tracts with centroids (upload la_county_acs.csv + centroids)
tracts_pdf = pd.read_parquet("/Volumes/workspace/default/datahacks/property_risk_joined.parquet")
tracts_df = spark.createDataFrame(tracts_pdf[["tract", "lat", "lon", "median_year_built",
                                               "home_value_final", "median_income"]])

# COMMAND ----------
# Nearest-receiver spatial join using Spark
# For each tract centroid, find nearest receiver by Euclidean distance in lat/lon
tracts_receivers = tracts_df.crossJoin(receivers_df.select(
    col("receiver_id"), col("lat").alias("r_lat"), col("lon").alias("r_lon")
))

tracts_receivers = tracts_receivers.withColumn(
    "dist",
    sqrt(spow(col("lat") - col("r_lat"), 2) + spow(col("lon") - col("r_lon"), 2))
)

# Keep nearest receiver per tract
from pyspark.sql.window import Window
from pyspark.sql.functions import rank

w = Window.partitionBy("tract").orderBy("dist")
nearest = (
    tracts_receivers
    .withColumn("rank", rank().over(w))
    .filter(col("rank") == 1)
    .drop("rank", "dist", "r_lat", "r_lon")
)

print(f"Tract-receiver assignments: {nearest.count()}")

# COMMAND ----------
# Join all 500 source scenarios onto each tract via its receiver
mean_shaking = features_df.groupBy("receiver_id").agg(
    avg("pga").alias("pga"),
    avg("pgv").alias("pgv"),
)

joined = nearest.join(mean_shaking, on="receiver_id", how="left")
joined.write.format("delta").mode("overwrite").saveAsTable("workspace.default.tract_shaking_full")
print("Saved workspace.default.tract_shaking_full")
