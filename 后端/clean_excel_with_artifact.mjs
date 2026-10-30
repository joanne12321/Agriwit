import fs from "node:fs/promises";
import path from "node:path";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const inputPath = path.resolve("数据集_Sheet1 (1)(1).xlsx");
const outputDir = path.resolve("outputs", "20260914_dataset_cleaning");
const outputPath = path.join(outputDir, "数据集_Sheet1_cleaned.xlsx");
const reportPath = path.join(outputDir, "数据集_Sheet1_cleaning_report.json");
const previewPath = path.join(outputDir, "清洗结果_preview.png");

const replacements = [
  ["比进口车厘子新鲜一百倍", "新鲜度表现突出"],
  ["一百倍", "更有新鲜感"],
  ["100%", "足量"],
  ["百分之百", "足量"],
  ["天花板", "品质突出"],
  ["顶级", "品质突出"],
  ["极品", "特色鲜明"],
  ["独一无二", "特色鲜明"],
  ["世界第一", "具有代表性"],
  ["中国第一", "具有代表性"],
  ["全网第一", "具有代表性"],
  ["销量第一", "销量表现较好"],
  ["第一", "具有代表性"],
  ["唯一", "少见的"],
  ["我吃过最甜的", "甜度表现突出的"],
  ["最甜", "甜度突出"],
  ["最好吃", "口感较好"],
  ["最便宜", "价格友好"],
  ["最受欢迎", "受到不少消费者关注"],
  ["最优", "较优"],
  ["绝对", "比较"],
  ["无敌", "很有特色"],
  ["封神", "表现亮眼"],
  ["神仙味道", "独特风味"],
  ["一定会回来一而再再而三地回购", "不少消费者会再次考虑购买"],
  ["一定会回来", "有机会再次购买"],
  ["一定会回购", "有机会再次购买"],
  ["孕妈妈放心吃", "孕产家庭可结合自身情况选择"],
  ["孕妈放心吃", "孕产家庭可结合自身情况选择"],
  ["放心吃", "适合日常食用"],
  ["抗癌", "营养特点"],
  ["降血压", "日常饮食"],
  ["减肥", "体重管理期间"],
  ["壮阳", "日常食用"],
  ["排毒", "日常饮食"],
  ["治疗", "日常食用"],
  ["根治", "日常调理"],
  ["药效", "食用体验"],
  ["特效", "特色"],
  ["纯天然", "自然风味"],
  ["坏果肯定赔", "坏果按售后规则处理"],
];

const riskPatterns = [
  /第一|唯一|独家|顶级|极品|天花板|无敌|封神|100%|百分之百/,
  /抗癌|降血压|治疗|根治|特效|药效|减肥|壮阳|排毒/,
  /纯天然|绝对|世界级|国家级|全网首发|孕妇放心吃|孕妈妈放心吃/,
  /保证|必然|肯定会|一定会/,
];

const headerIndex = (headers, name) => headers.findIndex((v) => String(v ?? "").trim() === name);
const text = (value) => (value == null ? "" : String(value)).replace(/\s+/g, " ").trim();
function columnName(index) {
  let value = index + 1;
  let result = "";
  while (value > 0) {
    const remainder = (value - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    value = Math.floor((value - 1) / 26);
  }
  return result;
}

function cleanText(value) {
  let result = text(value);
  const actions = [];
  for (const [oldValue, newValue] of replacements) {
    if (result.includes(oldValue)) {
      result = result.split(oldValue).join(newValue);
      actions.push(`${oldValue}->${newValue}`);
    }
  }
  return { result, actions };
}

function inferAngle(title, body, notes) {
  const source = `${title} ${body} ${notes}`;
  const mapping = [
    ["采摘", "新鲜采摘"],
    ["现摘", "新鲜采摘"],
    ["产地", "产地特色"],
    ["家乡", "家乡风味"],
    ["口感", "口感特点"],
    ["甜", "甜味口感"],
    ["脆", "脆爽口感"],
    ["糯", "软糯口感"],
    ["送礼", "送礼场景"],
    ["冷链", "冷链配送"],
    ["手工", "手工工艺"],
    ["低盐", "低盐制作"],
  ];
  const angles = [];
  for (const [needle, angle] of mapping) {
    if (source.includes(needle) && !angles.includes(angle)) angles.push(angle);
  }
  return angles.slice(0, 5).join("、") || "产品特色";
}

function cleanRow(row, index, ix) {
  const title = text(row[ix.title]);
  const body = text(row[ix.body]);
  const notes = text(row[ix.notes]);
  const actions = [];
  const titleClean = cleanText(title);
  const bodyClean = cleanText(body);
  if (titleClean.actions.length) actions.push(...titleClean.actions.map((v) => `标题:${v}`));
  if (bodyClean.actions.length) actions.push(...bodyClean.actions.map((v) => `正文:${v}`));

  const audience = text(row[ix.audience]);
  const festival = text(row[ix.festival]);
  const angle = text(row[ix.angle]);
  const cleanedAudience = audience || "日常采购消费者";
  const cleanedFestival = festival || "日常场景";
  const cleanedAngle = angle || inferAngle(titleClean.result, bodyClean.result, notes);
  if (!audience) actions.push("补充通用受众：日常采购消费者");
  if (!festival) actions.push("补充通用场景：日常场景");
  if (!angle) actions.push("根据原文关键词补充宣传角度");

  const flags = [];
  if (!text(row[ix.platform])) flags.push("缺少平台");
  if (!titleClean.result) flags.push("缺少标题");
  if (!bodyClean.result) flags.push("缺少正文");
  if (!text(row[ix.product])) flags.push("缺少商品名");
  if (!text(row[ix.category])) flags.push("缺少商品类别");
  if (bodyClean.result.length < 50) flags.push("正文过短");
  if (bodyClean.result.length > 800) flags.push("正文过长，需拆分");
  if (riskPatterns.some((pattern) => pattern.test(`${titleClean.result} ${bodyClean.result}`))) {
    flags.push("仍有疑似风险表达");
  }
  if (actions.length && !flags.includes("仍有疑似风险表达")) actions.push("已修正明显夸大或功效暗示");

  return {
    original: row,
    cleaned: [
      titleClean.result,
      bodyClean.result,
      cleanedAudience,
      cleanedFestival,
      cleanedAngle,
      flags.length ? "需人工审核" : "可用于SFT",
      actions.length ? actions.join("；") : "未发现需要自动修改的问题",
      flags.length ? flags.join("；") : "无",
    ],
    flags,
    actions,
  };
}

await fs.mkdir(outputDir, { recursive: true });
const input = await FileBlob.load(inputPath);
const workbook = await SpreadsheetFile.importXlsx(input);
const sourceSheet = workbook.worksheets.getItemAt(0);
const used = sourceSheet.getUsedRange();
const values = used.values;
const headers = values[0].map((v) => text(v));
const rows = values.slice(1).filter((row) => row.some((v) => text(v) !== ""));

const ix = {
  platform: headerIndex(headers, "平台"),
  title: headerIndex(headers, "标题"),
  body: headerIndex(headers, "正文"),
  category: headerIndex(headers, "商品类别"),
  product: headerIndex(headers, "商品名"),
  audience: headerIndex(headers, "目标受众"),
  festival: headerIndex(headers, "适用节日"),
  angle: headerIndex(headers, "宣传角度"),
  notes: headerIndex(headers, "备注"),
};
for (const [key, value] of Object.entries(ix)) {
  if (value < 0) throw new Error(`原始表缺少必要表头：${key}`);
}

const cleaned = rows.map((row, index) => cleanRow(row, index + 2, ix));
const seenBodies = new Set();
let duplicateAfterCleaning = 0;
for (const item of cleaned) {
  const body = item.cleaned[1];
  if (body && seenBodies.has(body)) {
    item.flags.push("清洗后正文重复");
    item.cleaned[5] = "需人工审核";
    item.cleaned[7] = item.flags.join("；");
    duplicateAfterCleaning += 1;
  }
  if (body) seenBodies.add(body);
}

const outputHeaders = [
  ...headers,
  "清洗后标题",
  "清洗后正文",
  "清洗后目标受众",
  "清洗后适用节日",
  "清洗后宣传角度",
  "清洗状态",
  "清洗说明",
  "原始问题",
];
const outputRows = cleaned.map((item) => [...item.original, ...item.cleaned]);
const lastColumn = columnName(outputHeaders.length - 1);
const firstCleanColumn = columnName(headers.length);
const lastOriginalColumn = columnName(headers.length - 1);

let resultSheet = workbook.worksheets.getItemOrNullObject?.("清洗结果");
if (!resultSheet || resultSheet.isNullObject) resultSheet = workbook.worksheets.add("清洗结果");
resultSheet.showGridLines = false;
resultSheet.getRangeByIndexes(0, 0, outputRows.length + 1, outputHeaders.length).values = [
  outputHeaders,
  ...outputRows,
];
resultSheet.freezePanes.freezeRows(1);
resultSheet.getRange(`A1:${lastColumn}1`).format = {
  fill: "#1F4E78",
  font: { name: "Arial", bold: true, color: "#FFFFFF", size: 10 },
  wrapText: true,
  verticalAlignment: "center",
};
resultSheet.getUsedRange().format.font = { name: "Arial", size: 10 };
resultSheet.getRange(`A1:${lastColumn}1`).format.font = {
  name: "Arial", bold: true, color: "#FFFFFF", size: 10,
};
resultSheet.getRange(`A2:${lastColumn}${outputRows.length + 1}`).format.verticalAlignment = "center";
resultSheet.getRange(`B2:C${outputRows.length + 1}`).format.wrapText = true;
resultSheet.getRange(`${firstCleanColumn}2:${lastColumn}${outputRows.length + 1}`).format.wrapText = true;
resultSheet.getRange(`A1:${lastColumn}${outputRows.length + 1}`).format.borders = {
  preset: "outside",
  style: "thin",
  color: "#D9E2F3",
};
for (const col of ["A", "D", "E", "F", "G", "H", "I", "J"]) resultSheet.getRange(`${col}:${col}`).format.columnWidth = 16;
resultSheet.getRange("K:K").format.columnWidth = 12;
for (const col of ["B", "C", "M", "R", "S"]) resultSheet.getRange(`${col}:${col}`).format.columnWidth = 34;
for (const col of ["L", "N", "O", "P", "Q"]) resultSheet.getRange(`${col}:${col}`).format.columnWidth = 18;
resultSheet.getRange(`A1:${lastColumn}1`).format.rowHeight = 30;

const ready = cleaned.filter((item) => item.cleaned[5] === "可用于SFT").length;
const flagCounts = {};
for (const item of cleaned) for (const flag of item.flags) flagCounts[flag] = (flagCounts[flag] || 0) + 1;
const actionCounts = {};
for (const item of cleaned) for (const action of item.actions) actionCounts[action] = (actionCounts[action] || 0) + 1;
const report = {
  sourceFile: inputPath,
  outputFile: outputPath,
  totalRecords: cleaned.length,
  autoModifiedRecords: cleaned.filter((item) => item.actions.length > 0).length,
  readyForSft: ready,
  needsManualReview: cleaned.length - ready,
  duplicateAfterCleaning,
  remainingIssueCounts: flagCounts,
  cleaningActions: actionCounts,
  policy: "保留原意，修正明显绝对化、夸大、功效暗示和过度承诺；不凭空编造产地、认证、奖项、营养功效等事实；正文过短、过长、重复或仍有疑似风险的记录保留并标记人工审核。",
};

workbook.recalculate();
const inspection = await workbook.inspect({
  kind: "table",
  sheetId: "清洗结果",
  range: "A1:R8",
  include: "values",
  tableMaxRows: 8,
  tableMaxCols: 18,
  maxChars: 12000,
});
await fs.writeFile(path.join(outputDir, "清洗结果_inspect.ndjson"), inspection.ndjson ?? String(inspection), "utf8");
const preview = await workbook.render({ sheetName: "清洗结果", range: "A1:R12", scale: 1, format: "png" });
await fs.writeFile(previewPath, new Uint8Array(await preview.arrayBuffer()));
const exported = await SpreadsheetFile.exportXlsx(workbook);
await exported.save(outputPath);
await fs.writeFile(reportPath, JSON.stringify(report, null, 2), "utf8");
console.log(JSON.stringify(report, null, 2));
