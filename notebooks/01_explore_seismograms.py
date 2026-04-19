import marimo

__generated_with = "0.10.0"
app = marimo.App()


@app.cell
def _():
    import marimo as mo
    import numpy as np
    import matplotlib.pyplot as plt
    from pathlib import Path
    ROOT = Path(__file__).resolve().parent.parent
    return ROOT, mo, np, plt


@app.cell
def _(mo):
    mo.md("## 01 -- Explore Scripps Seismograms (16-receiver prototype)")


@app.cell
def _(ROOT, np):
    seismograms = np.load(ROOT / "data/raw/scripps/seismos_16_receivers.npy", mmap_mode="r")
    print(f"Shape: {seismograms.shape}")
    print(f"dtype: {seismograms.dtype}")
    return (seismograms,)


@app.cell
def _(np, plt, seismograms):
    # receiver 0, all timesteps, source 0 -- east-component velocity in m/s
    trace = seismograms[0, :, 0]
    t = np.arange(len(trace)) * 0.1  # dt=0.1s, 10 Hz
    fig, ax = plt.subplots(figsize=(12, 3))
    ax.plot(t, trace)
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Velocity (m/s)")
    ax.set_title("Receiver 0 / Source 0 -- east-component")
    fig


@app.cell
def _(ROOT, plt):
    import pandas as pd
    receivers = pd.read_csv(ROOT / "data/raw/scripps/receiver_locations.csv")
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    ax2.scatter(receivers["lon"], receivers["lat"], s=1, alpha=0.4)
    ax2.set_title(f"Receiver grid -- {len(receivers)} locations")
    ax2.set_xlabel("Longitude")
    ax2.set_ylabel("Latitude")
    fig2


if __name__ == "__main__":
    app.run()
