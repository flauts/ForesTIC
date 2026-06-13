import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const dataPath = path.join(root, "data", "synthetic_forest.json");
const outputPath = path.join(root, "data", "pasaporte_datos_sinteticos.xlsx");

const raw = JSON.parse(await fs.readFile(dataPath, "utf8"));
const workbook = Workbook.create();

const sheets = [
  ["resumen_demo", buildSummary()],
  ["titulos_habilitantes", raw.titulos_habilitantes],
  ["planes_operativos", raw.planes_operativos],
  ["parcelas_corta", raw.parcelas_corta],
  ["censo_forestal", raw.censo_forestal],
  ["muestra_supervisada", raw.muestra_supervisada],
  ["trozas", raw.trozas],
  ["gtf", raw.gtf],
  ["balance_extraccion", raw.balance_extraccion],
  ["alertas", raw.alertas],
];

for (const [name, rows] of sheets) {
  addSheet(name, rows);
}

const inspect = await workbook.inspect({
  kind: "workbook,sheet,table",
  maxChars: 3000,
  tableMaxRows: 5,
  tableMaxCols: 8,
});
console.log(inspect.ndjson);

const errors = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A",
  options: { useRegex: true, maxResults: 50 },
  summary: "formula error scan",
});
console.log(errors.ndjson);

const preview = await workbook.render({
  sheetName: "resumen_demo",
  autoCrop: "all",
  scale: 1,
  format: "png",
});
await fs.writeFile(
  path.join(root, "data", "pasaporte_datos_sinteticos_preview.png"),
  new Uint8Array(await preview.arrayBuffer()),
);

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(`saved ${outputPath}`);

function buildSummary() {
  return [
    {
      escenario: "Verde",
      gtf_id: "GTF-2026-001",
      cod_arbol_principal: "BEL-2025-0100",
      resultado_esperado: "Verde",
      motivo_demo: "COD_ARBOL existe, muestra conforme, GTF vigente, balance disponible y sin alertas.",
    },
    {
      escenario: "Amarillo",
      gtf_id: "GTF-2026-002",
      cod_arbol_principal: "BEL-2025-0200",
      resultado_esperado: "Amarillo",
      motivo_demo: "Falta muestra OSINFOR directa y el balance disponible esta cerca del limite.",
    },
    {
      escenario: "Rojo",
      gtf_id: "GTF-2026-003",
      cod_arbol_principal: "BEL-2025-9999",
      resultado_esperado: "Rojo",
      motivo_demo: "COD_ARBOL inexistente, GTF vencida y alerta critica vigente.",
    },
  ];
}

function addSheet(name, rows) {
  const sheet = workbook.worksheets.add(name);
  sheet.showGridLines = false;

  if (!rows.length) {
    sheet.getRange("A1").values = [["sin_datos"]];
    return;
  }

  const headers = Object.keys(rows[0]);
  const matrix = [
    headers,
    ...rows.map((row) =>
      headers.map((header) => {
        const value = row[header];
        return Array.isArray(value) || typeof value === "object" ? JSON.stringify(value) : value;
      }),
    ),
  ];

  const lastColumn = columnName(headers.length);
  const rangeAddress = `A1:${lastColumn}${matrix.length}`;
  const range = sheet.getRange(rangeAddress);
  range.values = matrix;
  range.format.borders = { preset: "all", style: "thin", color: "#D9E2D7" };
  range.format.font = { color: "#1F2A23" };
  sheet.getRange(`A1:${lastColumn}1`).format = {
    fill: "#163D2B",
    font: { bold: true, color: "#FFFFFF" },
    wrapText: true,
  };
  sheet.getRange(rangeAddress).format.wrapText = true;
  range.format.autofitColumns();
  range.format.autofitRows();

  if (sheet.tables?.add) {
    sheet.tables.add(rangeAddress, true, `${name.replace(/[^A-Za-z0-9]/g, "_")}Table`);
  }

  sheet.freezePanes.freezeRows(1);
}

function columnName(index) {
  let result = "";
  let current = index;
  while (current > 0) {
    const remainder = (current - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    current = Math.floor((current - 1) / 26);
  }
  return result;
}
