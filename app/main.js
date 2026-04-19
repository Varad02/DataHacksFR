// Seismic Risk Atlas -- Leaflet choropleth map
// Loads risk_data.geojson (same directory) produced by notebooks/07_export_map_geojson.py

const map = L.map("map").setView([34.05, -118.05], 11); // Whittier Narrows / East LA

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
  opacity: 0.6,
}).addTo(map);

const palette = ["#FED976", "#FD8D3C", "#FC4E2A", "#E31A1C", "#BD0026", "#800026"];
let lossBreaks = [0, 1, 2, 3, 4, 5, 6];

function quantile(values, q) {
  if (!values.length) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  if (sorted[base + 1] !== undefined) {
    return sorted[base] + rest * (sorted[base + 1] - sorted[base]);
  }
  return sorted[base];
}

function computeLossBreaks(geojson) {
  const losses = geojson.features
    .map((f) => Number(f?.properties?.mean_loss_per_household))
    .filter((x) => Number.isFinite(x) && x >= 0);

  if (!losses.length) return [0, 1, 2, 3, 4, 5, 6];

  const q = [0, 0.2, 0.4, 0.6, 0.8, 0.95, 1].map((p) => quantile(losses, p));

  // Enforce monotonic increasing thresholds to avoid duplicate legend steps.
  for (let i = 1; i < q.length; i += 1) {
    if (q[i] <= q[i - 1]) q[i] = q[i - 1] + 1e-6;
  }
  return q;
}

function getColor(loss) {
  for (let i = lossBreaks.length - 1; i >= 1; i -= 1) {
    if (loss >= lossBreaks[i - 1]) return palette[i - 1];
  }
  return palette[0];
}

function style(feature) {
  const loss = feature.properties.mean_loss_per_household || 0;
  return {
    fillColor: getColor(loss),
    weight: 0.5,
    opacity: 1,
    color: "#999",
    fillOpacity: 0.75,
  };
}

function fmt$(n) {
  if (n == null || isNaN(n)) return "N/A";
  if (n >= 1000) return "$" + Math.round(n).toLocaleString();
  return "$" + Number(n).toFixed(2);
}

function fmtPct(n) {
  if (n == null || isNaN(n)) return "N/A";
  return (n * 100).toFixed(1) + "%";
}

let activeLayer = null;

function renderLegend() {
  const legendEl = document.getElementById("legend");
  const labels = [];
  for (let i = 0; i < palette.length; i += 1) {
    const low = lossBreaks[i];
    const high = lossBreaks[i + 1];
    if (i === palette.length - 1) {
      labels.push(`>= ${fmt$(low)}`);
    } else {
      labels.push(`${fmt$(low)} - ${fmt$(high)}`);
    }
  }

  legendEl.innerHTML = `
    <h4>Expected loss / household</h4>
    ${palette
      .map(
        (color, i) =>
          `<div class="legend-row"><div class="legend-swatch" style="background:${color}"></div>${labels[i]}</div>`
      )
      .join("")}
  `;
}

function onEachFeature(feature, layer) {
  layer.on("click", async () => {
    // Reset previous highlight
    if (activeLayer) activeLayer.setStyle(style(activeLayer.feature));
    activeLayer = layer;
    layer.setStyle({ weight: 2, color: "#333", fillOpacity: 0.9 });

    const p = feature.properties;

    document.getElementById("tract-name").textContent =
      p.NAME || ("Tract " + p.tract);
    document.getElementById("tract-name").className = "";

    document.getElementById("stats").innerHTML = `
      <b>Expected loss / household:</b> ${fmt$(p.mean_loss_per_household)}<br>
      <b>Damage ratio:</b> ${fmtPct(p.damage_ratio)}<br>
      <b>Median home value:</b> ${fmt$(p.median_home_value)}<br>
      <b>Median income:</b> ${fmt$(p.median_income)}<br>
      <b>PGA (scaled):</b> ${p.pga_g != null ? p.pga_g.toFixed(3) + "g" : "N/A"}
    `;

    const explEl = document.getElementById("explanation");
    explEl.textContent = "Generating summary...";
    explEl.className = "placeholder";

    try {
      const resp = await fetch("http://localhost:8000/api/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tract: p.tract,
          name: p.NAME || "",
          mean_loss_per_household: p.mean_loss_per_household || 0,
          median_home_value: p.median_home_value || 500000,
          median_income: p.median_income || 70000,
          damage_ratio: p.damage_ratio || 0,
        }),
      });
      if (!resp.ok) throw new Error("API error");
      const { summary } = await resp.json();
      explEl.textContent = summary;
      explEl.className = "";
    } catch {
      explEl.textContent = "AI summary unavailable -- start api/explain.py to enable.";
      explEl.className = "placeholder";
    }
  });
}

async function loadData() {
  try {
    const resp = await fetch("./risk_data.geojson");
    if (!resp.ok) throw new Error("GeoJSON not found");
    const geojson = await resp.json();

    lossBreaks = computeLossBreaks(geojson);
    renderLegend();

    const layer = L.geoJSON(geojson, { style, onEachFeature }).addTo(map);
    map.fitBounds(layer.getBounds(), { padding: [16, 16] });
    console.log(`Loaded ${geojson.features.length} tracts`);
  } catch (e) {
    console.error("Could not load risk_data.geojson:", e);
    document.getElementById("explanation").textContent =
      "Error loading map data. Make sure risk_data.geojson is in the app/ directory.";
  }
}

loadData();
