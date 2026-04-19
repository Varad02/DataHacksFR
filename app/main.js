// Seismic Risk Atlas -- Leaflet choropleth map
// Loads risk_data.geojson (same directory) produced by notebooks/07_export_map_geojson.py

const map = L.map("map").setView([34.05, -118.05], 11);  // Whittier Narrows / East LA

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "&copy; OpenStreetMap contributors",
  opacity: 0.6,
}).addTo(map);

function getColor(loss) {
  return loss > 200000 ? "#800026" :
         loss > 100000 ? "#BD0026" :
         loss > 50000  ? "#E31A1C" :
         loss > 20000  ? "#FC4E2A" :
         loss > 10000  ? "#FD8D3C" :
                         "#FED976";
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
  return "$" + Math.round(n).toLocaleString();
}

function fmtPct(n) {
  if (n == null || isNaN(n)) return "N/A";
  return (n * 100).toFixed(1) + "%";
}

let activeLayer = null;

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
    const resp = await fetch("risk_data.geojson");
    if (!resp.ok) throw new Error("GeoJSON not found");
    const geojson = await resp.json();

    L.geoJSON(geojson, { style, onEachFeature }).addTo(map);
    console.log(`Loaded ${geojson.features.length} tracts`);
  } catch (e) {
    console.error("Could not load risk_data.geojson:", e);
    document.getElementById("explanation").textContent =
      "Error loading map data. Make sure risk_data.geojson is in the app/ directory.";
  }
}

loadData();
