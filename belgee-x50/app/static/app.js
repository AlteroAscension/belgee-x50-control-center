const $ = (id) => document.getElementById(id);
const titles = {
  overview: "Обзор", navigation: "Навигация", trips: "Поездки",
  simulator: "Симулятор", devices: "Устройства",
};

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
