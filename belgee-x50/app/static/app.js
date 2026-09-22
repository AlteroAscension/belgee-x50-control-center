const $ = (id) => document.getElementById(id);
const titles = {
  overview: "Обзор", navigation: "Навигация", trips: "Поездки",
  simulator: "Симулятор", devices: "Устройства",
};
let trajectoryMap, trajectoryLayer, selectedTrajectory;
let trajectoryItems = [];

for (const button of document.querySelectorAll("#nav button")) {
  button.addEventListener("click", () => {
    document.querySelector("#nav .active")?.classList.remove("active");
    document.querySelector(".page.active")?.classList.remove("active");
    button.classList.add("active");
    $(button.dataset.page).classList.add("active");
    $("page-title").textContent = titles[button.dataset.page];
  });
}

const fmt = (value, digits = 0) =>
  value === null || value === undefined ? "—" :
  Number(value).toLocaleString("ru-RU", { maximumFractionDigits: digits });

function onlineValue(value) {
  if (value === true || value === "on") return true;
  if (value === false || value === "off" || value === "unavailable") return false;
  return null;
}

function render(data) {
  const vehicle = data.vehicle || {};
  const navigation = data.navigation || {};
  $("speed").textContent = fmt(vehicle.speed_kmh);
  $("odometer").textContent = fmt(vehicle.odometer_km, 1);
  $("range").textContent = fmt(vehicle.range_km);
  $("ignition").textContent = vehicle.ignition ?? "—";
  $("fake-gps").textContent =
    onlineValue(navigation.fake_gps) === true ? "ВКЛ" :
    onlineValue(navigation.fake_gps) === false ? "ВЫКЛ" : "—";
  const progress = navigation.route_progress_m;
  const length = navigation.route_length_m;
  $("route-progress").textContent = progress == null ? "—" :
    `${fmt(progress / 1000, 1)} / ${fmt((length || 0) / 1000, 1)} км`;
  $("position").textContent =
    vehicle.latitude == null ? "—" :
    `${Number(vehicle.latitude).toFixed(4)}, ${Number(vehicle.longitude).toFixed(4)}`;

  const connection = $("connection");
  connection.className = `connection ${data.available ? "online" : "offline"}`;
  connection.innerHTML = `<span></span>${data.available ? "Integration online" : "Нет live-данных"}`;
  $("last-updated").textContent = data.last_updated
    ? `Обновлено ${new Date(data.last_updated).toLocaleTimeString("ru-RU")}`
    : (data.error || "Нет данных");

  const names = {
    home_assistant: "Home Assistant", gateway: "X50 Gateway",
    relay: "X50 Relay", navigation: "X50 Navigation",
  };
  const components = data.components || {};
  $("component-list").innerHTML = Object.entries(names).map(([key, name]) => {
    const component = components[key] || {};
    const online = onlineValue(component.online);
    return `<div class="component">
      <span class="status-dot ${online === true ? "ok" : online === false ? "bad" : ""}"></span>
      <div><b>${name}</b><small>${component.version || (online === true ? "доступен" : online === false ? "нет связи" : "нет данных")}</small></div>
    </div>`;
  }).join("");
  $("device-details").innerHTML = `
    <dl>
      <div><dt>Состояние HA API</dt><dd>${data.error || "Подключено"}</dd></div>
      <div><dt>Получено сущностей HA</dt><dd>${data.entity_count ?? 0}</dd></div>
      <div><dt>Режим приложения</dt><dd>Только чтение</dd></div>
      <div><dt>Схема UI</dt><dd>${data.schema || "—"}</dd></div>
    </dl>`;
  trajectoryItems = data.trajectories || [];
  renderTrajectoryList(trajectoryItems);
}

function api(path) { return `${location.pathname.replace(/\/?$/, "/")}${path.replace(/^\//, "")}`; }
function renderTrajectoryList(items) {
  const list = $("trajectory-list");
  if (!list) return;
  if (!items.length) { list.innerHTML = '<p class="muted">Нет сохранённых траекторий</p>'; return; }
  list.innerHTML = items.map((item) => `<button data-trajectory="${item.id}" class="${item.id === selectedTrajectory ? "active" : ""}"><b>${new Date(item.started_at_ms || item.observed_at_ms || 0).toLocaleString("ru-RU")}</b><small>${fmt(item.distance_m, 1)} м · ${item.point_count || 0} точек · ${item.segment_count || 1} фрагм.</small></button>`).join("");
  list.querySelectorAll("button").forEach((button) => button.onclick = () => loadTrajectory(button.dataset.trajectory));
}
async function loadTrajectory(id) {
  const response = await fetch(api(`/api/trajectories/${encodeURIComponent(id)}`));
  if (!response.ok) return;
  selectedTrajectory = id; drawTrajectory(await response.json()); renderTrajectoryList(trajectoryItems);
}
function ensureTrajectoryMap() {
  if (trajectoryMap || !window.L) return;
  trajectoryMap = L.map("trajectory-map");
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "© OpenStreetMap" }).addTo(trajectoryMap);
  trajectoryLayer = L.layerGroup().addTo(trajectoryMap); trajectoryMap.setView([55.75, 37.62], 10);
}
function drawTrajectory(payload) {
  ensureTrajectoryMap(); if (!trajectoryMap) return;
  trajectoryLayer.clearLayers();
  const trajectory = payload.trajectory || {}, anchor = trajectory.anchor || {};
  if (!anchor.has_anchor || !Number.isFinite(Number(anchor.start_latitude)) || !Number.isFinite(Number(anchor.start_longitude))) {
    $("trajectory-note").textContent = "У этой поездки нет GPS/маршрутной привязки: сохранены только относительные точки."; return;
  }
  const lat0 = Number(anchor.start_latitude), lon0 = Number(anchor.start_longitude), bearing = Number(anchor.start_bearing_deg) * Math.PI / 180;
  const segments = new Map();
  for (const point of trajectory.points || []) {
    const x = Number(point.x_m), y = Number(point.y_m); if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
    const east = x * Math.cos(bearing) - y * Math.sin(bearing), north = x * Math.sin(bearing) + y * Math.cos(bearing);
    const lat = lat0 + north / 111320, lon = lon0 + east / (111320 * Math.cos(lat0 * Math.PI / 180));
    const segment = Number.isFinite(Number(point.segment_id)) ? Number(point.segment_id) : 0;
    if (!segments.has(segment)) segments.set(segment, []); segments.get(segment).push([lat, lon]);
  }
  const bounds = [];
  for (const points of segments.values()) { if (!points.length) continue; L.polyline(points, { color:"#d946ef", weight:5, opacity:.94, lineCap:"round" }).addTo(trajectoryLayer); bounds.push(...points); }
  if (bounds.length) trajectoryMap.fitBounds(bounds, { padding:[24,24], maxZoom:17 });
  $("trajectory-note").textContent = `Точек: ${trajectory.points?.length || 0}; фрагментов: ${segments.size}. Между фрагментами линия намеренно не проводится.`;
}

function connect() {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const socket = new WebSocket(`${protocol}//${location.host}${location.pathname.replace(/\/?$/, "/")}api/ws`);
  socket.onmessage = (event) => render(JSON.parse(event.data));
  socket.onclose = () => {
    $("connection").className = "connection offline";
    $("connection").innerHTML = "<span></span>Переподключение…";
    setTimeout(connect, 2500);
  };
}

connect();
