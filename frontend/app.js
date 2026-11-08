const periods = {
  "2026-10": {
    name: "Octubre 2026",
    shortName: "OCT 2026",
    total: 11820000,
    delta: 898000,
    change: 8.2,
    unitTotal: 142350,
    unitChange: 7.8,
    common: 128400,
    particular: 13950,
    due: "Vence el 10 de noviembre",
    dueShort: "10 nov 2026",
    history: [9100000, 9470000, 10050000, 10294000, 10922000, 11820000],
    categories: [
      { name: "Sueldos y cargas", kind: "Recurrente", amount: 3890000, change: 4.8, tone: "sage" },
      { name: "Servicios públicos", kind: "Recurrente", amount: 2780000, change: 12.1, tone: "terracotta" },
      { name: "Mantenimiento", kind: "Recurrente", amount: 1920000, change: 18.7, tone: "ochre" },
      { name: "Limpieza", kind: "Recurrente", amount: 1120000, change: 3.4, tone: "mint" },
      { name: "Seguros", kind: "Recurrente", amount: 880000, change: 6.1, tone: "slate" },
      { name: "Otros gastos", kind: "Varios", amount: 1230000, change: 2.5, tone: "stone" },
    ],
    increases: [
      { name: "Mantenimiento", detail: "Ascensores y bombas", delta: 302000, percentage: 18.7 },
      { name: "Servicios públicos", detail: "Agua y electricidad", delta: 300000, percentage: 12.1 },
      { name: "Sueldos y cargas", detail: "Actualización salarial", delta: 178000, percentage: 4.8 },
    ],
  },
  "2026-09": {
    name: "Septiembre 2026",
    shortName: "SEP 2026",
    total: 10922000,
    delta: 628000,
    change: 6.1,
    unitTotal: 132100,
    unitChange: 5.2,
    common: 119500,
    particular: 12600,
    due: "Vence el 10 de octubre",
    dueShort: "10 oct 2026",
    history: [9100000, 9470000, 10050000, 10294000, 10922000, 11820000],
    categories: [
      { name: "Sueldos y cargas", kind: "Recurrente", amount: 3712000, change: 3.2, tone: "sage" },
      { name: "Servicios públicos", kind: "Recurrente", amount: 2480000, change: 8.4, tone: "terracotta" },
      { name: "Mantenimiento", kind: "Recurrente", amount: 1618000, change: 6.9, tone: "ochre" },
      { name: "Limpieza", kind: "Recurrente", amount: 1083000, change: 2.2, tone: "mint" },
      { name: "Seguros", kind: "Recurrente", amount: 829000, change: 4.1, tone: "slate" },
      { name: "Otros gastos", kind: "Varios", amount: 1200000, change: 15.4, tone: "stone" },
    ],
    increases: [
      { name: "Servicios públicos", detail: "Agua y electricidad", delta: 192000, percentage: 8.4 },
      { name: "Otros gastos", detail: "Varios conceptos", delta: 160000, percentage: 15.4 },
      { name: "Sueldos y cargas", detail: "Actualización salarial", delta: 115000, percentage: 3.2 },
    ],
  },
  "2026-08": {
    name: "Agosto 2026",
    shortName: "AGO 2026",
    total: 10294000,
    delta: 244000,
    change: 2.4,
    unitTotal: 125600,
    unitChange: 1.9,
    common: 115300,
    particular: 10300,
    due: "Vence el 10 de septiembre",
    dueShort: "10 sep 2026",
    history: [9100000, 9470000, 10050000, 10294000, 10922000, 11820000],
    categories: [
      { name: "Sueldos y cargas", kind: "Recurrente", amount: 3597000, change: 3.9, tone: "sage" },
      { name: "Servicios públicos", kind: "Recurrente", amount: 2288000, change: 3.0, tone: "terracotta" },
      { name: "Mantenimiento", kind: "Recurrente", amount: 1514000, change: 1.5, tone: "ochre" },
      { name: "Limpieza", kind: "Recurrente", amount: 1059000, change: 1.3, tone: "mint" },
      { name: "Seguros", kind: "Recurrente", amount: 796000, change: 0.8, tone: "slate" },
      { name: "Otros gastos", kind: "Varios", amount: 1040000, change: 0, tone: "stone" },
    ],
    increases: [
      { name: "Sueldos y cargas", detail: "Actualización salarial", delta: 134000, percentage: 3.9 },
      { name: "Servicios públicos", detail: "Agua y electricidad", delta: 68000, percentage: 3.1 },
      { name: "Mantenimiento", detail: "Abonos y reparaciones", delta: 22000, percentage: 1.5 },
    ],
  },
};

const statements = [
  { period: "Octubre 2026", file: "Liquidación_octubre_2026.pdf", total: 11820000, change: 8.2, status: "Atención", statusTone: "review", kind: "PDF" },
  { period: "Septiembre 2026", file: "Liquidación_septiembre_2026.xlsx", total: 10922000, change: 6.1, status: "Analizada", statusTone: "ok", kind: "XLS" },
  { period: "Agosto 2026", file: "Liquidación_agosto_2026.pdf", total: 10294000, change: 2.4, status: "Analizada", statusTone: "ok", kind: "PDF" },
];

const categoryTones = Object.freeze({
  sage: "#6e9678",
  terracotta: "#d48a69",
  ochre: "#d1ac59",
  mint: "#94ad9a",
  slate: "#8797a1",
  stone: "#c8c5ad",
  default: "#94ad9a",
});
const statementTones = Object.freeze({ review: "status-review", ok: "status-ok" });

const money = new Intl.NumberFormat("es-AR", {
  style: "currency",
  currency: "ARS",
  maximumFractionDigits: 0,
});
const percent = new Intl.NumberFormat("es-AR", {
  maximumFractionDigits: 1,
  minimumFractionDigits: 1,
});

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) element.textContent = value;
}

function signedMoney(value) {
  const sign = value > 0 ? "+" : value < 0 ? "−" : "";
  return `${sign}${money.format(Math.abs(value))}`;
}

function renderChart(periodKey, history) {
  const host = document.getElementById("chart-columns");
  if (!host) return;
  const labels = ["MAY", "JUN", "JUL", "AGO", "SEP", "OCT"];
  const activeIndex = periodKey === "2026-08" ? 3 : periodKey === "2026-09" ? 4 : 5;
  const max = Math.max(...history) * 1.08;
  const columns = history.map((amount, index) => {
    const column = document.createElement("div");
    column.className = `chart-column${index === activeIndex ? " selected" : ""}`;
    const bar = document.createElement("div");
    bar.className = "chart-bar";
    bar.style.height = `${Math.max(8, (amount / max) * 100)}%`;
    bar.setAttribute("aria-hidden", "true");
    const month = document.createElement("span");
    month.className = "chart-month";
    month.textContent = labels[index];
    column.setAttribute("aria-label", `${labels[index]}: ${money.format(amount)}`);
    column.append(bar, month);
    return column;
  });
  host.replaceChildren(...columns);
}

function renderCategories(categories, total) {
  const host = document.getElementById("categories-list");
  if (!host) return;
  const rows = categories.map((category) => {
    const row = document.createElement("div");
    row.className = "category-row";
    const info = document.createElement("div");
    info.className = "category-info";
    const name = document.createElement("span");
    name.className = "category-name";
    name.textContent = category.name;
    const kind = document.createElement("span");
    kind.className = "category-kind";
    kind.textContent = category.kind;
    info.append(name, kind);

    const track = document.createElement("div");
    track.className = "progress-track";
    track.setAttribute("aria-hidden", "true");
    const fill = document.createElement("div");
    fill.className = "progress-fill";
    fill.style.width = `${Math.min(100, (category.amount / total) * 100)}%`;
    fill.style.backgroundColor = categoryTones[category.tone] || categoryTones.default;
    track.append(fill);

    const numbers = document.createElement("div");
    numbers.className = "category-numbers";
    const amount = document.createElement("span");
    amount.className = "category-amount";
    amount.textContent = money.format(category.amount);
    const change = document.createElement("span");
    change.className = `category-change ${category.change >= 0 ? "up" : "down"}`;
    change.textContent = `${category.change > 0 ? "↑" : category.change < 0 ? "↓" : "–"} ${percent.format(Math.abs(category.change))}%`;
    numbers.append(amount, change);
    row.append(info, track, numbers);
    return row;
  });
  host.replaceChildren(...rows);
}

function renderIncreases(increases) {
  const host = document.getElementById("increase-list");
  if (!host) return;
  const rows = increases.map((item, index) => {
    const row = document.createElement("li");
    row.className = "increase-item";
    const rank = document.createElement("span");
    rank.className = "increase-rank";
    rank.textContent = String(index + 1).padStart(2, "0");
    const title = document.createElement("span");
    const name = document.createElement("span");
    name.className = "increase-name";
    name.textContent = item.name;
    const detail = document.createElement("span");
    detail.className = "increase-meta";
    detail.textContent = item.detail;
    title.append(name, detail);
    const value = document.createElement("span");
    value.className = "increase-value";
    value.textContent = signedMoney(item.delta);
    const rate = document.createElement("span");
    rate.className = "increase-percent";
    rate.textContent = `+${percent.format(item.percentage)}%`;
    value.append(rate);
    row.append(rank, title, value);
    return row;
  });
  host.replaceChildren(...rows);
}

function renderStatements() {
  const host = document.getElementById("statement-rows");
  if (!host) return;
  const rows = statements.map((statement) => {
    const row = document.createElement("tr");
    const periodCell = document.createElement("td");
    periodCell.className = "period-cell";
    periodCell.textContent = statement.period;

    const fileCell = document.createElement("td");
    const fileWrap = document.createElement("span");
    fileWrap.className = "file-cell";
    const fileIcon = document.createElement("span");
    fileIcon.className = "file-icon";
    fileIcon.textContent = statement.kind;
    const fileName = document.createElement("span");
    fileName.className = "file-name";
    fileName.textContent = statement.file;
    fileWrap.append(fileIcon, fileName);
    fileCell.append(fileWrap);

    const totalCell = document.createElement("td");
    totalCell.className = "amount-cell";
    totalCell.textContent = money.format(statement.total);
    const changeCell = document.createElement("td");
    changeCell.className = "table-change";
    changeCell.textContent = `↑ ${percent.format(statement.change)}%`;
    const statusCell = document.createElement("td");
    const status = document.createElement("span");
    status.className = `status-chip ${statementTones[statement.statusTone] || statementTones.ok}`;
    status.textContent = statement.status;
    statusCell.append(status);
    const actionCell = document.createElement("td");
    const action = document.createElement("button");
    action.className = "row-action";
    action.type = "button";
    action.textContent = "···";
    action.setAttribute("aria-label", `Opciones para ${statement.period}`);
    action.addEventListener("click", () => showToast("El archivo original todavía no está conectado."));
    actionCell.append(action);
    row.append(periodCell, fileCell, totalCell, changeCell, statusCell, actionCell);
    return row;
  });
  host.replaceChildren(...rows);
}

function renderPeriod(periodKey) {
  const period = Object.prototype.hasOwnProperty.call(periods, periodKey)
    ? periods[periodKey]
    : periods["2026-10"];
  const deltaSign = period.delta >= 0 ? "+" : "−";
  const up = period.change >= 0;
  setText("building-total", money.format(period.total));
  setText("building-change", `${up ? "↑" : "↓"} ${percent.format(Math.abs(period.change))}%`);
  setText("building-delta", `${deltaSign}${money.format(Math.abs(period.delta))}`);
  setText("unit-total", money.format(period.unitTotal));
  setText("unit-total-large", money.format(period.unitTotal));
  setText("unit-total-row", money.format(period.unitTotal));
  setText("unit-common", money.format(period.common));
  setText("unit-particular", money.format(period.particular));
  setText("unit-due", period.due);
  setText("unit-due-date", period.dueShort);
  setText("unit-change", `${period.unitChange >= 0 ? "↑" : "↓"} ${percent.format(Math.abs(period.unitChange))}%`);
  setText("unit-period", period.shortName);
  setText("category-total", money.format(period.total));
  renderChart(periodKey, period.history);
  renderCategories(period.categories, period.total);
  renderIncreases(period.increases);
  const changePill = document.getElementById("building-change");
  const unitChange = document.getElementById("unit-change");
  if (changePill) changePill.className = `change-pill ${up ? "up" : "down"}`;
  if (unitChange) unitChange.className = `change-text ${period.unitChange >= 0 ? "up-text" : "down-text"}`;
}

let toastTimer;
function showToast(message) {
  const toast = document.getElementById("toast");
  if (!toast) return;
  toast.textContent = message;
  toast.hidden = false;
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => { toast.hidden = true; }, 2800);
}

function bindInteractions() {
  document.getElementById("period-select")?.addEventListener("change", (event) => {
    renderPeriod(event.currentTarget.value);
  });

  const dialog = document.getElementById("source-dialog");
  document.getElementById("add-statement")?.addEventListener("click", () => dialog?.showModal());
  document.getElementById("dialog-close")?.addEventListener("click", () => dialog?.close());
  document.getElementById("dialog-done")?.addEventListener("click", () => dialog?.close());
  dialog?.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  const popover = document.getElementById("notification-popover");
  const notificationButton = document.getElementById("notification-button");
  notificationButton?.addEventListener("click", () => {
    const willOpen = popover?.hidden ?? false;
    if (popover) popover.hidden = !willOpen;
    notificationButton.setAttribute("aria-expanded", String(willOpen));
  });
  document.addEventListener("click", (event) => {
    if (!popover || popover.hidden) return;
    if (event.target instanceof Element && event.target.closest("#notification-popover, #notification-button")) return;
    popover.hidden = true;
    notificationButton?.setAttribute("aria-expanded", "false");
  });

  document.getElementById("dismiss-banner")?.addEventListener("click", () => {
    document.querySelector(".demo-banner")?.remove();
  });
  document.getElementById("all-statements")?.addEventListener("click", () => {
    showToast("El historial completo se habilita al conectar el backend.");
  });
  document.getElementById("trend-range")?.addEventListener("click", () => {
    showToast("Mostrando los últimos 6 meses de datos de muestra.");
  });
  document.querySelectorAll("[data-nav]").forEach((link) => {
    link.addEventListener("click", () => {
      document.querySelectorAll("[data-nav]").forEach((item) => item.classList.remove("is-active"));
      link.classList.add("is-active");
    });
  });
}

renderPeriod(document.getElementById("period-select")?.value || "2026-10");
renderStatements();
bindInteractions();
