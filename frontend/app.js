import { readExpenseFile } from "./importer.js";

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

const importedStatements = [];
const importedPeriods = new Map();
let pendingImport = null;
let hasImportedData = false;

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

function renderChart(periodKey, period) {
  const host = document.getElementById("chart-columns");
  if (!host) return;
  const history = period.history;
  const labels = period.historyLabels || ["MAY", "JUN", "JUL", "AGO", "SEP", "OCT"];
  const activeIndex = period.historyKeys?.indexOf(periodKey)
    ?? (periodKey === "2026-08" ? 3 : periodKey === "2026-09" ? 4 : 5);
  const max = Math.max(...history, 1) * 1.08;
  const yLabels = document.querySelectorAll(".chart-y-labels span");
  yLabels.forEach((label, index) => {
    const value = max * (1 - index / Math.max(1, yLabels.length - 1));
    label.textContent = value >= 1_000_000
      ? `$ ${(value / 1_000_000).toLocaleString("es-AR", { maximumFractionDigits: 1 })} M`
      : money.format(value);
  });
  const columns = history.map((amount, index) => {
    const column = document.createElement("div");
    column.className = `chart-column${index === activeIndex ? " selected" : ""}`;
    const bar = document.createElement("div");
    bar.className = "chart-bar";
    bar.style.height = `${Math.max(8, (amount / max) * 100)}%`;
    bar.setAttribute("aria-hidden", "true");
    const month = document.createElement("span");
    month.className = "chart-month";
    month.textContent = labels[index] || "—";
    column.setAttribute("aria-label", `${labels[index] || "Período"}: ${money.format(amount)}`);
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
    fill.style.width = `${Math.min(100, (Math.abs(category.amount) / Math.max(Math.abs(total), 1)) * 100)}%`;
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
  const rows = increases.length ? increases.map((item, index) => {
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
  }) : (() => {
    const row = document.createElement("li");
    row.className = "increase-empty";
    row.textContent = "Cargá también el período anterior para detectar aumentos.";
    return [row];
  })();
  host.replaceChildren(...rows);
}

function renderStatements() {
  const host = document.getElementById("statement-rows");
  if (!host) return;
  const allStatements = hasImportedData ? [...importedStatements].sort((left, right) => right.periodKey.localeCompare(left.periodKey)).map((statement) => ({
    period: importedPeriods.get(statement.periodKey)?.name || statement.periodKey,
    periodKey: statement.periodKey,
    file: statement.file,
    total: importedPeriods.get(statement.periodKey)?.total ?? 0,
    change: importedPeriods.get(statement.periodKey)?.change ?? 0,
    status: "Importada en esta sesión",
    statusTone: "review",
    kind: statement.kind,
  })) : [
    ...statements,
    ...importedStatements.map((statement) => ({
      period: importedPeriods.get(statement.periodKey)?.name || statement.periodKey,
      periodKey: statement.periodKey,
      file: statement.file,
      total: importedPeriods.get(statement.periodKey)?.total ?? 0,
      change: importedPeriods.get(statement.periodKey)?.change ?? 0,
      status: "Importada en este navegador",
      statusTone: "review",
      kind: statement.kind,
    })),
  ].sort((left, right) => (right.periodKey || "").localeCompare(left.periodKey || ""));
  const rows = allStatements.map((statement) => {
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
    const importedPeriod = statement.periodKey ? importedPeriods.get(statement.periodKey) : null;
    changeCell.textContent = importedPeriod?.hasComparison === false
      ? "Sin comparación"
      : `${statement.change > 0 ? "↑" : statement.change < 0 ? "↓" : "–"} ${percent.format(Math.abs(statement.change))}%`;
    if (statement.change < 0) changeCell.classList.add("down");
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
    action.addEventListener("click", () => showToast(statement.periodKey
      ? "El archivo se procesa en memoria y no se conserva después de cerrar la página."
      : "Este documento pertenece a los datos de muestra."));
    actionCell.append(action);
    row.append(periodCell, fileCell, totalCell, changeCell, statusCell, actionCell);
    return row;
  });
  host.replaceChildren(...rows);
}

function renderPeriod(periodKey) {
  const period = importedPeriods.get(periodKey) || (Object.prototype.hasOwnProperty.call(periods, periodKey)
    ? periods[periodKey]
    : periods["2026-10"]);
  const deltaSign = period.delta >= 0 ? "+" : "−";
  const up = period.change >= 0;
  const hasComparison = period.hasComparison !== false;
  setText("building-total", money.format(period.total));
  setText("building-change", hasComparison ? `${up ? "↑" : "↓"} ${percent.format(Math.abs(period.change))}%` : "Sin comparación");
  setText("building-delta", hasComparison ? `${deltaSign}${money.format(Math.abs(period.delta))}` : "—");
  const hasUnitData = Number.isFinite(period.unitTotal) && period.unitTotal > 0;
  setText("unit-card-label", hasUnitData ? "MI UNIDAD · 04 B" : "DESGLOSE POR UNIDAD");
  setText("unit-section-label", hasUnitData ? "TU LIQUIDACIÓN" : "DATOS DE UNIDAD");
  setText("unit-name", hasUnitData ? "Unidad 04 · B" : "No detectados en el archivo");
  setText("unit-status", hasUnitData ? "Al día" : "Sin dato");
  setText("unit-total", hasUnitData ? money.format(period.unitTotal) : "Sin dato");
  setText("unit-total-large", hasUnitData ? money.format(period.unitTotal) : "Sin dato");
  setText("unit-total-row", hasUnitData ? money.format(period.unitTotal) : "Sin dato");
  setText("unit-common", hasUnitData ? money.format(period.common) : "No detectado");
  setText("unit-particular", hasUnitData ? money.format(period.particular) : "No detectado");
  setText("unit-due", hasUnitData ? period.due : "No detectada en el archivo");
  setText("unit-due-date", hasUnitData ? period.dueShort : "—");
  setText("unit-change", hasUnitData ? `${period.unitChange >= 0 ? "↑" : "↓"} ${percent.format(Math.abs(period.unitChange))}%` : "Sin comparación");
  setText("unit-period", period.shortName);
  setText("category-total", money.format(period.total));
  setText("chart-selected-period", `${period.name} es el período seleccionado`);
  renderChart(periodKey, period);
  renderCategories(period.categories, period.total);
  renderIncreases(period.increases);
  const changePill = document.getElementById("building-change");
  const unitChange = document.getElementById("unit-change");
  if (changePill) changePill.className = `change-pill ${!hasComparison ? "neutral" : up ? "up" : "down"}`;
  if (unitChange) unitChange.className = `change-text ${period.unitChange >= 0 ? "up-text" : "down-text"}`;
  setText("insight-note-copy", period.hasComparison
    ? "Comparación calculada con los dos períodos que cargaste. Revisá los renglones extraídos antes de compartir."
    : importedPeriods.has(periodKey)
      ? "Para detectar aumentos, cargá también la liquidación del período anterior. Revisá el detalle extraído."
      : "Las cifras de esta vista son ilustrativas. Cargá tus archivos para analizarlos.");
}

const monthShortNames = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"];

function monthName(periodKey) {
  const [year, month] = periodKey.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString("es-AR", { month: "long", year: "numeric" });
}

function adjacentPeriod(periodKey) {
  const [year, month] = periodKey.split("-").map(Number);
  const date = new Date(year, month - 2, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function compactKey(value) {
  return String(value).normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es-AR").trim();
}

function buildImportedPeriods() {
  importedPeriods.clear();
  const sorted = [...importedStatements].sort((left, right) => left.periodKey.localeCompare(right.periodKey));
  const totals = new Map(sorted.map((statement) => [statement.periodKey, statement.expenses.reduce((sum, row) => sum + row.amount, 0)]));
  for (const statement of sorted) {
    const previousKey = adjacentPeriod(statement.periodKey);
    const previous = sorted.find((candidate) => candidate.periodKey === previousKey);
    const total = totals.get(statement.periodKey) || 0;
    const previousTotal = previous ? totals.get(previousKey) : null;
    const categoriesByKey = new Map();
    for (const row of statement.expenses) {
      const key = compactKey(row.description);
      const item = categoriesByKey.get(key) || { name: row.description, amount: 0 };
      item.amount += row.amount;
      categoriesByKey.set(key, item);
    }
    const previousCategories = new Map();
    if (previous) {
      for (const row of previous.expenses) {
        const key = compactKey(row.description);
        previousCategories.set(key, (previousCategories.get(key) || 0) + row.amount);
      }
    }
    const categories = [...categoriesByKey.entries()]
      .map(([key, item], index) => {
        const prior = previousCategories.get(key) || 0;
        const change = prior > 0 ? ((item.amount - prior) / prior) * 100 : 0;
        return { ...item, change, kind: "Extraído del archivo", tone: Object.keys(categoryTones)[index % 6] };
      })
      .sort((left, right) => right.amount - left.amount);
    const increases = previous
      ? categories.map((category) => {
        const prior = previousCategories.get(compactKey(category.name)) || 0;
        const delta = category.amount - prior;
        return { name: category.name, detail: "Variación del concepto", delta, percentage: prior > 0 ? (delta / prior) * 100 : 0 };
      }).filter((item) => item.delta > 0).sort((left, right) => right.delta - left.delta).slice(0, 5)
      : [];
    const delta = previousTotal === null ? 0 : total - previousTotal;
    const historyStatements = sorted.filter((item) => item.periodKey <= statement.periodKey).slice(-6);
    importedPeriods.set(statement.periodKey, {
      name: monthName(statement.periodKey),
      shortName: `${monthShortNames[Number(statement.periodKey.slice(-2)) - 1]} ${statement.periodKey.slice(0, 4)}`,
      total,
      delta,
      change: previousTotal > 0 ? (delta / previousTotal) * 100 : 0,
      history: historyStatements.map((item) => totals.get(item.periodKey) || 0),
      historyLabels: historyStatements.map((item) => monthShortNames[Number(item.periodKey.slice(-2)) - 1]),
      historyKeys: historyStatements.map((item) => item.periodKey),
      categories,
      increases,
      hasComparison: Boolean(previous),
      unitTotal: null,
      common: null,
      particular: null,
      due: "No detectada en el archivo",
      dueShort: "—",
      unitChange: 0,
    });
  }
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

function defaultPeriod() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

function guessPeriod(filename) {
  const normalized = compactKey(filename);
  const numeric = normalized.match(/\b(20\d{2})[-_. ](0[1-9]|1[0-2])\b/);
  if (numeric) return `${numeric[1]}-${numeric[2]}`;
  const monthIndex = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    .findIndex((month) => normalized.includes(month));
  const year = normalized.match(/\b(20\d{2})\b/);
  if (monthIndex >= 0 && year) return `${year[1]}-${String(monthIndex + 1).padStart(2, "0")}`;
  return defaultPeriod();
}

function renderImportPreview() {
  if (!pendingImport) return;
  const host = document.getElementById("import-preview");
  if (!host) return;
  host.replaceChildren();
  const selectedRows = [...pendingImport.selectedIndices]
    .map((index) => pendingImport.expenses[index])
    .filter(Boolean);
  const total = selectedRows.reduce((sum, row) => sum + row.amount, 0);
  setText("review-summary", `${selectedRows.length} renglones seleccionados · ${money.format(total)} sumados`);
  const visibleCount = Math.min(60, pendingImport.expenses.length);
  for (let index = 0; index < visibleCount; index += 1) {
    const expense = pendingImport.expenses[index];
    const row = document.createElement("label");
    row.className = "preview-row";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = pendingImport.selectedIndices.has(index);
    checkbox.setAttribute("aria-label", `Incluir ${expense.description}`);
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) pendingImport.selectedIndices.add(index);
      else pendingImport.selectedIndices.delete(index);
      renderImportPreview();
    });
    const description = document.createElement("span");
    description.className = "preview-description";
    description.textContent = expense.description;
    const amount = document.createElement("strong");
    amount.textContent = money.format(expense.amount);
    row.append(checkbox, description, amount);
    host.append(row);
  }
  if (pendingImport.expenses.length > visibleCount) {
    const note = document.createElement("p");
    note.className = "preview-limit-note";
    note.textContent = `Se muestran los primeros ${visibleCount}; los ${pendingImport.expenses.length - visibleCount} restantes también están seleccionados.`;
    host.append(note);
  }
}

async function prepareFile(file) {
  const status = document.getElementById("upload-status");
  if (!file) return;
  if (status) status.textContent = "Leyendo el archivo en este navegador…";
  const chooseButton = document.getElementById("upload-dropzone");
  if (chooseButton) chooseButton.disabled = true;
  try {
    const result = await readExpenseFile(file);
    pendingImport = {
      fileName: file.name,
      kind: result.kind,
      expenses: result.expenses,
      selectedIndices: new Set(result.expenses.map((_, index) => index)),
    };
    setText("review-file-name", file.name);
    setText("review-file-kind", result.kind);
    const periodField = document.getElementById("import-period");
    if (periodField) periodField.value = guessPeriod(file.name);
    document.getElementById("upload-step").hidden = true;
    document.getElementById("review-step").hidden = false;
    document.getElementById("dialog-done").hidden = true;
    setText("dialog-copy", "Revisá lo extraído y corregí qué renglones entran en el análisis.");
    renderImportPreview();
  } catch (error) {
    if (status) status.textContent = error instanceof Error && error.name === "ImportError"
      ? error.message
      : "No pude leer ese archivo. Verificá que sea un PDF con texto o un Excel .xlsx válido.";
    const fileInput = document.getElementById("statement-file");
    if (fileInput) fileInput.value = "";
  } finally {
    if (chooseButton) chooseButton.disabled = false;
  }
}

function resetImportDialog() {
  pendingImport = null;
  const fileInput = document.getElementById("statement-file");
  if (fileInput) fileInput.value = "";
  document.getElementById("upload-step").hidden = false;
  document.getElementById("review-step").hidden = true;
  document.getElementById("dialog-done").hidden = false;
  setText("dialog-copy", "Los archivos se procesan en este navegador. No se envían a un servidor.");
  setText("upload-status", "");
}

function updateNotifications(periodKey) {
  const host = document.getElementById("notification-items");
  const period = importedPeriods.get(periodKey);
  if (!host || !period) return;
  host.replaceChildren();
  const notes = [{ title: "Liquidación analizada", detail: `${period.name} · ${money.format(period.total)}`, tone: "" }];
  const biggestIncrease = period.increases[0];
  if (biggestIncrease) {
    notes.push({
      title: `Aumentó ${biggestIncrease.name}`,
      detail: `${signedMoney(biggestIncrease.delta)} frente al mes anterior`,
      tone: "coral",
    });
  }
  for (const note of notes) {
    const item = document.createElement("div");
    item.className = "popover-item";
    const bullet = document.createElement("span");
    bullet.className = `popover-bullet${note.tone ? ` ${note.tone}` : ""}`;
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = note.title;
    const detail = document.createElement("small");
    detail.textContent = note.detail;
    copy.append(title, detail);
    item.append(bullet, copy);
    host.append(item);
  }
  setText("popover-demo", "Avisos de esta sesión. Todavía no se envían a otros vecinos.");
}

function confirmImport() {
  if (!pendingImport) return;
  const periodKey = document.getElementById("import-period")?.value || "";
  if (!/^20\d{2}-(0[1-9]|1[0-2])$/.test(periodKey)) {
    showToast("Elegí un período válido.");
    return;
  }
  const expenses = [...pendingImport.selectedIndices]
    .map((index) => pendingImport.expenses[index])
    .filter(Boolean);
  if (!expenses.length) {
    showToast("Seleccioná al menos un renglón para analizar.");
    return;
  }
  const existingIndex = importedStatements.findIndex((item) => item.periodKey === periodKey);
  if (existingIndex >= 0 && !window.confirm(`Ya cargaste una liquidación de ${monthName(periodKey)}. ¿Querés reemplazarla?`)) return;
  const statement = { periodKey, file: pendingImport.fileName, kind: pendingImport.kind, expenses };
  if (existingIndex >= 0) importedStatements.splice(existingIndex, 1, statement);
  else importedStatements.push(statement);
  hasImportedData = true;
  buildImportedPeriods();

  const periodSelect = document.getElementById("period-select");
  if (periodSelect) {
    periodSelect.replaceChildren();
    for (const imported of [...importedStatements].sort((left, right) => right.periodKey.localeCompare(left.periodKey))) {
      const importedOption = document.createElement("option");
      importedOption.value = imported.periodKey;
      importedOption.textContent = monthName(imported.periodKey);
      periodSelect.append(importedOption);
    }
    periodSelect.value = periodKey;
  }
  setText("demo-banner-label", "Importación local.");
  setText("demo-banner-copy", "Los datos se pierden al cerrar o actualizar la página.");
  setText("building-name", "Consorcio cargado");
  setText("building-location", "Datos de esta sesión");
  setText("breadcrumb-building", "Consorcio cargado");
  setText("review-card-label", "PERÍODOS CARGADOS");
  setText("review-card-count", String(importedStatements.length));
  setText("review-card-status", "Revisar");
  setText("review-card-copy", "Confirmá los importes extraídos antes de compartir el resumen.");
  document.getElementById("dismiss-banner")?.setAttribute("aria-label", "Cerrar aviso");
  renderPeriod(periodKey);
  renderStatements();
  updateNotifications(periodKey);
  resetImportDialog();
  document.getElementById("source-dialog")?.close();
  showToast("Período analizado. Revisá los importes y la comparación.");
}

function summaryText() {
  const periodKey = document.getElementById("period-select")?.value || "";
  const period = importedPeriods.get(periodKey);
  if (!period) return "Este panel muestra datos ilustrativos; todavía no cargaste una liquidación real.";
  const previous = period.hasComparison
    ? `Variación total frente al mes anterior: ${signedMoney(period.delta)} (${percent.format(Math.abs(period.change))}%).`
    : "Todavía no hay un período anterior cargado para comparar.";
  const top = period.increases.slice(0, 3).map((item) => `${item.name}: ${signedMoney(item.delta)} (${percent.format(item.percentage)}%)`).join("; ");
  return `Resumen de ${period.name}. Gasto extraído: ${money.format(period.total)}. ${previous}${top ? ` Mayores aumentos: ${top}.` : ""} Datos revisados por el vecino antes de compartir.`;
}

async function shareSummary() {
  const text = summaryText();
  try {
    if (navigator.share) await navigator.share({ title: "Resumen de expensas", text });
    else if (navigator.clipboard?.writeText) {
      await navigator.clipboard.writeText(text);
      showToast("Resumen copiado. Ya podés compartirlo con los vecinos.");
    } else {
      showToast("Tu navegador no permite compartir desde esta página.");
    }
  } catch (error) {
    if (error?.name !== "AbortError") showToast("No se pudo abrir la opción para compartir.");
  }
}

function bindInteractions() {
  document.getElementById("period-select")?.addEventListener("change", (event) => {
    renderPeriod(event.currentTarget.value);
  });

  const dialog = document.getElementById("source-dialog");
  document.getElementById("add-statement")?.addEventListener("click", () => dialog?.showModal());
  dialog?.addEventListener("close", resetImportDialog);
  document.getElementById("dialog-close")?.addEventListener("click", () => dialog?.close());
  document.getElementById("dialog-done")?.addEventListener("click", () => dialog?.close());
  dialog?.addEventListener("click", (event) => {
    if (event.target === dialog) dialog.close();
  });

  const fileInput = document.getElementById("statement-file");
  const dropzone = document.getElementById("upload-dropzone");
  dropzone?.addEventListener("click", () => fileInput?.click());
  fileInput?.addEventListener("change", (event) => prepareFile(event.currentTarget.files?.[0]));
  dropzone?.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("is-dragging");
  });
  dropzone?.addEventListener("dragleave", () => dropzone.classList.remove("is-dragging"));
  dropzone?.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("is-dragging");
    prepareFile(event.dataTransfer?.files?.[0]);
  });
  document.getElementById("back-to-upload")?.addEventListener("click", () => {
    document.getElementById("review-step").hidden = true;
    document.getElementById("upload-step").hidden = false;
    document.getElementById("dialog-done").hidden = false;
    setText("dialog-copy", "Los archivos se procesan en este navegador. No se envían a un servidor.");
    setText("upload-status", "");
  });
  document.getElementById("confirm-import")?.addEventListener("click", confirmImport);
  document.getElementById("drive-option")?.addEventListener("click", () => showToast("Google Drive necesita una conexión OAuth y un backend; todavía no está conectado."));
  document.getElementById("gmail-option")?.addEventListener("click", () => showToast("Gmail necesita una conexión OAuth y un backend; todavía no está conectado."));
  document.getElementById("share-summary")?.addEventListener("click", shareSummary);

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
    showToast(importedStatements.length ? "El gráfico muestra los períodos que cargaste en esta sesión." : "Cargá los períodos para comparar la evolución de tus gastos.");
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
