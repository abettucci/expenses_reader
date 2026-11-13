import { unzipSync } from "fflate";
import * as pdfjsLib from "pdfjs-dist/build/pdf.mjs";

const MAX_FILE_BYTES = 15 * 1024 * 1024;
const MAX_PDF_PAGES = 80;
const MAX_ROWS = 20_000;
const MAX_PDF_TEXT_ITEMS = 250_000;
const MAX_SPREADSHEET_CELLS = 100_000;
const ALLOWED_EXTENSIONS = Object.freeze([".pdf", ".xlsx"]);
const ALLOWED_MIME_TYPES = Object.freeze({
  ".pdf": new Set(["", "application/pdf", "application/x-pdf", "application/octet-stream"]),
  ".xlsx": new Set(["", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/zip", "application/octet-stream"]),
});

class ImportError extends Error {
  constructor(message) {
    super(message);
    this.name = "ImportError";
  }
}

pdfjsLib.GlobalWorkerOptions.workerSrc = "/pdf.worker.mjs";

function normalize(value) {
  return String(value ?? "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLocaleLowerCase("es-AR")
    .trim();
}

function parseAmount(value) {
  if (typeof value === "number" && Number.isFinite(value)) return value;
  if (typeof value !== "string") return null;
  let cleaned = value.trim().replace(/[\s$]/g, "").replace(/ARS/gi, "");
  const negative = cleaned.startsWith("(") && cleaned.endsWith(")");
  cleaned = cleaned.replace(/[()]/g, "");
  const comma = cleaned.lastIndexOf(",");
  const dot = cleaned.lastIndexOf(".");
  const decimalIndex = Math.max(comma, dot);
  if (decimalIndex >= 0 && cleaned.length - decimalIndex - 1 <= 2) {
    const integerPart = cleaned.slice(0, decimalIndex).replace(/[.,]/g, "");
    const decimalPart = cleaned.slice(decimalIndex + 1).replace(/[.,]/g, "");
    cleaned = `${integerPart}.${decimalPart}`;
  } else {
    cleaned = cleaned.replace(/[.,]/g, "");
  }
  const amount = Number(cleaned);
  if (!Number.isFinite(amount)) return null;
  return negative ? -amount : amount;
}

function isSummaryDescription(description) {
  const value = normalize(description);
  return /^(total|totales|subtotal|gran total|total a pagar|saldo anterior)\b/.test(value);
}

function createExpense(description, amount) {
  const cleanDescription = String(description ?? "").replace(/\s+/g, " ").trim();
  const parsedAmount = parseAmount(amount);
  if (cleanDescription.length < 2 || cleanDescription.length > 180) return null;
  if (parsedAmount === null || parsedAmount === 0 || isSummaryDescription(cleanDescription)) return null;
  return { description: cleanDescription, amount: parsedAmount };
}

function parseTrailingAmount(line) {
  const match = line.match(/(?:\(?-?\s*\$?\s*)?(?:\d{1,3}(?:[.\s]\d{3})+|\d+)(?:[,.]\d{1,2})?\)?\s*$/);
  if (!match) return null;
  const amount = parseAmount(match[0]);
  const description = line.slice(0, match.index).replace(/[\s:;|\-–]+$/, "").trim();
  if (amount === null || !description) return null;
  return createExpense(description, amount);
}

function groupPdfTextItems(items) {
  const lineMap = new Map();
  for (const item of items) {
    if (!item || typeof item.str !== "string" || !item.str.trim()) continue;
    const y = Math.round(Number(item.transform?.[5] ?? 0) / 3) * 3;
    let line = lineMap.get(y);
    if (!line) {
      line = { y, parts: [] };
      lineMap.set(y, line);
    }
    line.parts.push({ x: Number(item.transform?.[4] ?? 0), text: item.str.trim() });
  }
  return [...lineMap.values()]
    .sort((left, right) => right.y - left.y)
    .map((line) => line.parts.sort((left, right) => left.x - right.x).map((part) => part.text).join(" "));
}

// Layout-aware reader for consorcio statements: detail amounts sit in one column
// marked with "$". Descriptions are the text to the left of that column.
function findAmountColumn(items) {
  const counts = new Map();
  for (const item of items) {
    const x = Math.round(Number(item.transform?.[4] ?? 0));
    if (typeof item.str === "string" && item.str.trim().startsWith("$") && x >= 300 && x <= 450) {
      counts.set(x, (counts.get(x) ?? 0) + 1);
    }
  }
  let best = null;
  for (const [x, count] of counts) {
    if (count >= 5 && (!best || count > best.count)) best = { x, count };
  }
  return best ? best.x : null;
}

function moneyText(row) {
  return row.parts
    .slice()
    .sort((left, right) => left.x - right.x)
    .map((part) => part.text)
    .join("")
    .replace(/\s+/g, "")
    .replace(/\$/g, "");
}

function isMoneyRow(row, column) {
  return row.parts.length > 0
    && Math.min(...row.parts.map((part) => part.x)) <= column + 12
    && /^-?\d[\d.]*(,\d{1,2})?$/.test(moneyText(row));
}

function parseAmountColumnPage(items, column) {
  const amountRows = new Map();
  const labels = [];
  for (const item of items) {
    const text = String(item.str ?? "").trim();
    if (!text) continue;
    const x = Number(item.transform?.[4] ?? 0);
    const y = Math.round(Number(item.transform?.[5] ?? 0));
    if (x >= column - 4 && x <= column + 70) {
      const key = Math.round(y / 3) * 3;
      if (!amountRows.has(key)) amountRows.set(key, { y: key, parts: [] });
      amountRows.get(key).parts.push({ x, text });
    } else if (x >= 45 && x < column - 4) {
      labels.push({ x, y, text });
    }
  }
  // A provider's first line sits just above its amount, and wrapped lines follow below it.
  // Attach each label to the nearest amount line at or below it, or else to the nearest one.
  const rows = [...amountRows.values()]
    .map((row) => ({ ...row, labels: [] }))
    .filter((row) => isMoneyRow(row, column));
  for (const label of labels) {
    let nearest = null;
    for (const row of rows) {
      const distance = Math.abs(row.y - label.y);
      if (distance > 12) continue;
      const rank = row.y <= label.y ? 0 : 1;
      if (!nearest || rank < nearest.rank || (rank === nearest.rank && distance < nearest.distance)) {
        nearest = { row, distance, rank };
      }
    }
    if (nearest) nearest.row.labels.push(label);
  }
  const expenses = [];
  for (const row of rows) {
    row.parts.sort((left, right) => left.x - right.x);
    // Detail amounts start at the "$" column; larger x means a header value, not an expense.
    if (row.parts[0].x > column + 12) continue;
    const amountText = row.parts
      .map((part) => part.text)
      .join("")
      .replace(/\s+/g, "")
      .replace(/\$/g, "");
    if (!/^-?\d[\d.]*(,\d{1,2})?$/.test(amountText)) continue;
    const description = row.labels
      .sort((left, right) => right.y - left.y || left.x - right.x)
      .map((part) => part.text)
      .join(" ")
      .replace(/\s+/g, " ")
      .replace(/(\s\.){2,}\s*$/, "")
      .trim();
    if (!/\p{L}{2,}/u.test(description)) continue;
    // Rows starting with a unit code ("0116 - 1 - 14 - NAME", "1-11 NAME") belong to the per-unit
    // prorating and payment tables, not to building expenses.
    if (/^(\d{4}\s*-|\d{1,2}-\d{1,2}\b)/.test(description)) continue;
    const expense = createExpense(description.slice(0, 180), parseAmount(amountText));
    if (expense) expenses.push(expense);
  }
  return expenses;
}

async function readPdf(buffer) {
  const document = await pdfjsLib.getDocument({
    data: new Uint8Array(buffer),
    isEvalSupported: false,
    useSystemFonts: false,
  }).promise;
  try {
    if (document.numPages > MAX_PDF_PAGES) throw new ImportError(`El PDF supera el límite de ${MAX_PDF_PAGES} páginas.`);
    const pages = [];
    for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
      const page = await document.getPage(pageNumber);
      const content = await page.getTextContent();
      if (content.items.length > MAX_PDF_TEXT_ITEMS) throw new ImportError("El PDF tiene demasiados fragmentos de texto para procesar.");
      pages.push(content.items);
      page.cleanup();
    }
    // Consorcio statements: pages with a "$" amount column hold the expense detail; other pages
    // (per-unit prorating tables, notices) are skipped. Plain text PDFs fall back to line parsing.
    const amountColumn = findAmountColumn(pages.flat());
    const expenses = [];
    for (const items of pages) {
      let pageExpenses;
      if (amountColumn !== null) {
        pageExpenses = parseAmountColumnPage(items, amountColumn);
      } else {
        pageExpenses = groupPdfTextItems(items).map(parseTrailingAmount).filter(Boolean);
      }
      for (const expense of pageExpenses) {
        expenses.push(expense);
        if (expenses.length > MAX_ROWS) throw new ImportError(`El PDF tiene más de ${MAX_ROWS} renglones para revisar.`);
      }
    }
    if (!expenses.length) {
      throw new ImportError("No encontré renglones de gastos con texto seleccionable. Si el PDF es un escaneo, hace falta OCR.");
    }
    return expenses;
  } finally {
    await document.destroy();
  }
}

function checkZipLimits(bytes) {
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
  const start = Math.max(0, bytes.length - 65_557);
  let endRecord = -1;
  for (let offset = bytes.length - 22; offset >= start; offset -= 1) {
    if (view.getUint32(offset, true) === 0x06054b50) { endRecord = offset; break; }
  }
  if (endRecord < 0) throw new ImportError("El Excel no contiene una estructura .xlsx válida.");
  const entryCount = view.getUint16(endRecord + 10, true);
  const directoryOffset = view.getUint32(endRecord + 16, true);
  if (entryCount === 0xffff || directoryOffset === 0xffffffff || entryCount > 2_000) {
    throw new ImportError("El Excel usa una estructura comprimida no admitida o demasiados archivos internos.");
  }
  let offset = directoryOffset;
  let uncompressedTotal = 0;
  for (let entry = 0; entry < entryCount; entry += 1) {
    if (offset + 46 > bytes.length || view.getUint32(offset, true) !== 0x02014b50) {
      throw new ImportError("El índice interno del Excel está dañado.");
    }
    const flags = view.getUint16(offset + 8, true);
    const method = view.getUint16(offset + 10, true);
    const compressedSize = view.getUint32(offset + 20, true);
    const uncompressedSize = view.getUint32(offset + 24, true);
    const nameLength = view.getUint16(offset + 28, true);
    const extraLength = view.getUint16(offset + 30, true);
    const commentLength = view.getUint16(offset + 32, true);
    if ((flags & 1) !== 0 || ![0, 8].includes(method) || uncompressedSize === 0xffffffff) {
      throw new ImportError("El Excel está cifrado o usa un formato comprimido no admitido.");
    }
    if (uncompressedSize > 24 * 1024 * 1024) throw new ImportError("Una parte interna del Excel supera el límite de 24 MB.");
    uncompressedTotal += uncompressedSize;
    if (uncompressedTotal > 80 * 1024 * 1024) throw new ImportError("El Excel se expandiría a más de 80 MB al abrirse.");
    const nameStart = offset + 46;
    const entryName = new TextDecoder().decode(bytes.subarray(nameStart, nameStart + nameLength));
    if (entryName.startsWith("/") || entryName.includes("\\") || entryName.split("/").includes("..") || /[\u0000-\u001f]/.test(entryName)) {
      throw new ImportError("El Excel tiene nombres internos no válidos.");
    }
    offset = nameStart + nameLength + extraLength + commentLength;
  }
}

function parseXml(bytes, filePath) {
  if (!bytes) throw new ImportError("El Excel no tiene los componentes necesarios para leer gastos.");
  const source = new TextDecoder().decode(bytes);
  if (/<!DOCTYPE|<!ENTITY/i.test(source)) throw new ImportError("El Excel contiene declaraciones XML no admitidas.");
  const document = new DOMParser().parseFromString(source, "application/xml");
  if (document.getElementsByTagName("parsererror").length) throw new ImportError("El XML interno del Excel está dañado.");
  return document;
}

function getSpreadsheetParts(buffer) {
  const bytes = new Uint8Array(buffer);
  checkZipLimits(bytes);
  let files;
  try {
    files = unzipSync(bytes);
  } catch {
    throw new ImportError("No pude abrir la estructura comprimida del Excel.");
  }
  const hasFile = (name) => Object.prototype.hasOwnProperty.call(files, name);
  const workbookDocument = parseXml(hasFile("xl/workbook.xml") ? files["xl/workbook.xml"] : null, "xl/workbook.xml");
  const relationshipsDocument = parseXml(hasFile("xl/_rels/workbook.xml.rels") ? files["xl/_rels/workbook.xml.rels"] : null, "xl/_rels/workbook.xml.rels");
  const firstSheet = workbookDocument.getElementsByTagNameNS("*", "sheet")[0];
  const relationshipId = firstSheet?.getAttribute("r:id") || firstSheet?.getAttributeNS("http://schemas.openxmlformats.org/officeDocument/2006/relationships", "id");
  const relationship = [...relationshipsDocument.getElementsByTagNameNS("*", "Relationship")]
    .find((item) => item.getAttribute("Id") === relationshipId && item.getAttribute("TargetMode") !== "External");
  const target = relationship?.getAttribute("Target") || "";
  if (!target || target.includes("\\") || target.split("/").includes("..") || /^[a-z]+:/i.test(target)) {
    throw new ImportError("No pude reconocer la primera hoja del Excel.");
  }
  const relativeTarget = target.startsWith("/") ? target.slice(1) : target;
  const sheetPath = relativeTarget.startsWith("xl/") ? relativeTarget : `xl/${relativeTarget}`;
  if (!/^xl\/worksheets\/[A-Za-z0-9_.-]+\.xml$/.test(sheetPath) || !hasFile(sheetPath)) {
    throw new ImportError("La primera hoja del Excel no está disponible.");
  }
  const sheetDocument = parseXml(files[sheetPath], sheetPath);
  const sharedStrings = hasFile("xl/sharedStrings.xml")
    ? [...parseXml(files["xl/sharedStrings.xml"], "xl/sharedStrings.xml").getElementsByTagNameNS("*", "si")]
      .map((item) => [...item.getElementsByTagNameNS("*", "t")].map((part) => part.textContent || "").join(""))
    : [];
  return { sheetDocument, sharedStrings };
}

function columnIndex(reference) {
  const match = String(reference).match(/^([A-Z]{1,3})\d+$/);
  if (!match) return -1;
  let value = 0;
  for (const letter of match[1]) value = value * 26 + letter.charCodeAt(0) - 64;
  return value - 1;
}

function spreadsheetRows(sheetDocument, sharedStrings) {
  const rowElements = [...sheetDocument.getElementsByTagNameNS("*", "row")];
  if (rowElements.length > MAX_ROWS + 20) throw new ImportError(`La hoja supera el límite de ${MAX_ROWS} filas.`);
  let cellCount = 0;
  return rowElements.map((rowElement) => {
    const values = [];
    for (const cell of rowElement.getElementsByTagNameNS("*", "c")) {
      cellCount += 1;
      if (cellCount > MAX_SPREADSHEET_CELLS) throw new ImportError("La planilla tiene demasiadas celdas para procesar.");
      const index = columnIndex(cell.getAttribute("r"));
      if (index < 0 || index >= 60) continue;
      const type = cell.getAttribute("t");
      const valueElement = cell.getElementsByTagNameNS("*", "v")[0];
      let value = valueElement?.textContent || "";
      if (type === "s") {
        const sharedIndex = Number(value);
        value = Number.isInteger(sharedIndex) ? sharedStrings[sharedIndex] ?? "" : "";
      } else if (type === "inlineStr") {
        value = [...cell.getElementsByTagNameNS("*", "t")].map((part) => part.textContent || "").join("");
      } else if (type === "b") {
        value = value === "1";
      } else if (type === "n" || !type) {
        const number = Number(value);
        if (value !== "" && Number.isFinite(number)) value = number;
      }
      values[index] = value;
    }
    return values;
  });
}

function findHeader(rows) {
  const descriptionPattern = /concepto|detalle|descripcion|rubro|gasto|item|servicio/;
  const amountPattern = /importe|monto|total|debe|haber|valor|pesos|saldo/;
  const maxHeaderRow = Math.min(20, rows.length);
  for (let rowNumber = 0; rowNumber < maxHeaderRow; rowNumber += 1) {
    const row = rows[rowNumber];
    let descriptionColumn = null;
    let amountColumn = null;
    let score = 0;
    for (let column = 0; column < Math.min(60, row.length); column += 1) {
      const value = normalize(row[column]);
      if (!value) continue;
      if (descriptionPattern.test(value)) { descriptionColumn = column; score += 1; }
      if (amountPattern.test(value)) { amountColumn = column; score += 1; }
    }
    if (score >= 2 && descriptionColumn !== null && amountColumn !== null && descriptionColumn !== amountColumn) {
      return { rowNumber, descriptionColumn, amountColumn };
    }
  }
  return null;
}

async function readWorkbook(buffer) {
  const { sheetDocument, sharedStrings } = getSpreadsheetParts(buffer);
  const rows = spreadsheetRows(sheetDocument, sharedStrings);
  if (!rows.length) throw new ImportError("El Excel no tiene filas con datos.");
  const header = findHeader(rows);
  let descriptionColumn = header?.descriptionColumn ?? null;
  let amountColumn = header?.amountColumn ?? null;
  let startRow = header ? header.rowNumber + 1 : 0;

  if (!header) {
    const sampleEnd = Math.min(rows.length, 25);
    let bestPair = null;
    let bestScore = 0;
    for (let textColumn = 0; textColumn < 20; textColumn += 1) {
      for (let numberColumn = 0; numberColumn < 20; numberColumn += 1) {
        if (textColumn === numberColumn) continue;
        let score = 0;
        for (let rowNumber = 0; rowNumber < sampleEnd; rowNumber += 1) {
          const description = rows[rowNumber][textColumn];
          const amount = parseAmount(rows[rowNumber][numberColumn]);
          if (typeof description === "string" && description.trim().length > 2 && amount !== null && amount !== 0) score += 1;
        }
        if (score > bestScore) { bestPair = { textColumn, numberColumn }; bestScore = score; }
      }
    }
    if (!bestPair || bestScore < 2) throw new ImportError("No pude reconocer las columnas de concepto e importe. Revisá que sea un .xlsx con gastos en filas.");
    descriptionColumn = bestPair.textColumn;
    amountColumn = bestPair.numberColumn;
  }

  const expenses = [];
  for (let rowNumber = startRow; rowNumber < rows.length; rowNumber += 1) {
    const row = rows[rowNumber];
    const expense = createExpense(row[descriptionColumn], row[amountColumn]);
    if (expense) expenses.push(expense);
    if (expenses.length > MAX_ROWS) throw new Error(`La hoja supera el límite de ${MAX_ROWS} gastos.`);
  }
  if (!expenses.length) throw new ImportError("Encontré la hoja, pero no pude extraer gastos. Revisá las columnas antes de importar.");
  return expenses;
}

export async function readExpenseFile(file) {
  if (!(file instanceof File)) throw new ImportError("Elegí un archivo para continuar.");
  if (file.size <= 0 || file.size > MAX_FILE_BYTES) throw new ImportError("El archivo debe pesar entre 1 byte y 15 MB.");
  const filename = file.name;
  if (filename.length > 180 || /[\\/\u0000-\u001f]/.test(filename) || filename.includes("..")) {
    throw new ImportError("El nombre del archivo no es válido.");
  }
  const extension = ALLOWED_EXTENSIONS.find((item) => filename.toLocaleLowerCase("es-AR").endsWith(item));
  if (!extension) throw new ImportError("Por ahora se admiten archivos PDF con texto y Excel .xlsx. Guardá las planillas .xls como .xlsx.");
  const mimeType = String(file.type || "").toLocaleLowerCase("en-US");
  if (!ALLOWED_MIME_TYPES[extension].has(mimeType)) throw new ImportError("El tipo de archivo no coincide con un PDF o Excel .xlsx admitido.");

  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer, 0, Math.min(buffer.byteLength, 8));
  if (extension === ".pdf") {
    const signature = new TextDecoder().decode(bytes);
    if (!signature.startsWith("%PDF-")) throw new ImportError("El contenido no parece ser un PDF válido.");
    try {
      return { expenses: await readPdf(buffer), kind: "PDF" };
    } catch (error) {
      if (error instanceof ImportError) throw error;
      throw new ImportError("No pude leer el PDF. Puede estar dañado o protegido.");
    }
  }
  if (bytes[0] !== 0x50 || bytes[1] !== 0x4b) throw new ImportError("El contenido no parece ser un Excel .xlsx válido.");
  try {
    return { expenses: await readWorkbook(buffer), kind: "XLSX" };
  } catch (error) {
    if (error instanceof ImportError) throw error;
    throw new ImportError("No pude leer el Excel. Verificá que no esté dañado y que use el formato .xlsx.");
  }
}

export function getExpenseFileLimits() {
  return { maxBytes: MAX_FILE_BYTES, extensions: [...ALLOWED_EXTENSIONS] };
}
