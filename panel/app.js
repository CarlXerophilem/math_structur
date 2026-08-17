"use strict";

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const SVG_NS = "http://www.w3.org/2000/svg";
const colors = {
  Cu: "#c8784f", Co: "#477d92", Pd: "#8695a0", Fe: "#a45e4d", Ir: "#6f7894",
  In: "#8f84a8", O: "#d85c52", C: "#263d50", H: "#f7f7f2", Ni: "#5d9a7d",
  Zn: "#8ba4b0", K: "#a77bb4", Mo: "#587a91", S: "#dfbe45"
};

let geometry = { nodes: [], edges: [] };
let rotation = { yaw: -0.45, pitch: 0.38, zoom: 1 };
let drag = null;

function svgEl(name, attributes = {}, text = null) {
  const node = document.createElementNS(SVG_NS, name);
  for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
  if (text !== null) node.textContent = text;
  return node;
}

function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function badge(node, text, kind = "") {
  node.textContent = text;
  node.classList.remove("is-good", "is-bad", "is-unknown");
  if (kind) node.classList.add(`is-${kind}`);
}

function renderMath(node, tex, displayMode = false) {
  const source = String(tex || "").trim();
  clear(node);
  if (!source) {
    node.textContent = "—";
    return;
  }
  if (window.katex?.render) {
    window.katex.render(source, node, { displayMode, throwOnError: false, strict: "ignore", trust: false });
  } else {
    node.textContent = source;
  }
}

async function api(path, body = null, timeout = 135000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  const options = body === null ? {} : {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  };
  try {
    const response = await fetch(path, { ...options, signal: controller.signal });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || `HTTP ${response.status}`);
    return payload;
  } finally {
    clearTimeout(timer);
  }
}

$$('.tab').forEach(tab => tab.addEventListener("click", () => {
  const mode = tab.dataset.mode;
  $$('.tab').forEach(item => {
    const active = item === tab;
    item.classList.toggle("is-active", active);
    item.setAttribute("aria-selected", String(active));
  });
  $$('.mode-panel').forEach(panel => {
    const active = panel.dataset.panel === mode;
    panel.hidden = !active;
    panel.classList.toggle("is-active", active);
  });
}));

async function detectRuntime() {
  try {
    const [health, harness] = await Promise.all([api("/api/health"), api("/api/harness/status")]);
    $("#server-dot").classList.add("is-live");
    $("#server-status").textContent = health.panel;
    $("#qwen-status").textContent = harness.qwen_local.ready ? "本地" : "未启动";
    $("#codex-status").textContent = harness.codex.ready ? "就绪" : "关闭";
    $("#deepseek-status").textContent = harness.deepseek_harness.ready ? "就绪" : "关闭";
    $("#alphaxiv-status").textContent = harness.alphaxiv_mcp.ready ? "MCP 就绪" : "关闭";
    $("#lean-runtime-status").textContent = harness.lean.ready ? "就绪" : "关闭";
    $("#call-budget").textContent = `调用 ${health.model_calls} / ${harness.max_calls_per_run}`;
  } catch (error) {
    $("#server-status").textContent = "offline";
    $("#lean-detail").textContent = String(error);
  }
}

function generalPayload() {
  const optionalValue = selector => {
    const value = $(selector).value.trim();
    return value || null;
  };
  return {
    problem: $("#problem-input").value.trim(),
    domain: $("#problem-domain").value,
    basis: $("#basis-select").value,
    dimension: Number($("#basis-dimension").value),
    provider: $("#solver-provider").value,
    database_mode: $("#database-mode").value,
    possibilities: {
      temperature: optionalValue("#possibility-temperature"),
      pressure: optionalValue("#possibility-pressure"),
      candidate_domain: optionalValue("#possibility-candidate-domain"),
      metrics: optionalValue("#possibility-metrics"),
      baseline: optionalValue("#possibility-baseline")
    }
  };
}

async function runGeneral() {
  const button = $("#general-form .run-button");
  button.disabled = true;
  badge($("#general-status"), "running", "unknown");
  try {
    const result = await api("/api/solver/run", generalPayload());
    renderGeneral(result);
  } catch (error) {
    badge($("#general-status"), "error", "bad");
    $("#reactants-products").textContent = String(error);
  } finally {
    button.disabled = false;
    detectRuntime();
  }
}

$("#general-form").addEventListener("submit", event => {
  event.preventDefault();
  runGeneral();
});

function statusKind(value) {
  if (["solved", "rendered", "passed", "proved_finite", "equivalent", "retrieved", "retrieved_and_sorted", "live_verified"].includes(value)) return "good";
  if (["invalid", "mismatch", "refuted", "failed", "error"].includes(value)) return "bad";
  return "unknown";
}

function statusLabel(value) {
  const labels = {
    retrieved: "已检索", retrieved_and_sorted: "已检索并排序", solved: "已求解", rendered: "已呈现", passed: "已通过",
    equivalent: "等价", mismatch: "不匹配", invalid: "无效", refuted: "已否证",
    unknown: "未知", underdetermined: "欠定", ready: "就绪", invoked: "已调用",
    not_invoked: "未调用", optional: "可选", fixed_obligation: "固定验证义务",
    gated: "受闸门约束", required: "必需", awaiting_typed_geometry: "等待类型化几何",
    obligation_only: "仅生成验证义务", partial_formalization: "部分形式化",
    proved_finite: "有限域穷举通过", undefined: "未定义", error: "错误",
    abstract_verified: "摘要已核验", metadata_only: "仅元数据", not_retrieved: "未取得记录",
    unknown_no_comparable_record: "无可比来源记录", verified_snapshot: "已核验快照",
    official_fields_verified_live_records_authorized: "官方字段已核验，实时记录需授权",
    authentication_required_for_live_reading: "实时读取需认证",
    download_contract_verified_not_loaded: "数据合同已核验，本轮未加载",
    live_error_snapshot_retained: "实时接口失败，已保留快照"
  };
  return labels[value] || value || "未知";
}

function renderGeneral(result) {
  const normalized = result.normalized_problem || {};
  const standardMath = result.standard_math || {};
  const targetFunction = result.target_function || {};
  const recognition = result.recognition || {};
  const receipt = result.model_receipt || {};
  const recognizedDomain = recognition.domain || recognition.recognized_domain || normalized.type || "未识别";
  const recognizedIntent = recognition.intent || recognition.recognized_intent || normalized.directive || normalized.objective_state || "未识别";
  const recognizedModel = recognition.model || recognition.model_name || receipt.model || (receipt.provider === "qwen" ? "Qwen3-8B-Jailbroken" : Number(receipt.calls || 0) === 0 ? "确定性检索内核（无模型调用）" : receipt.provider || "未调用模型");
  const gateStatus = recognition.gate?.status;
  const exactValidation = recognition.exact_validation || recognition.exact_verification || recognition.validator_status || (gateStatus === "passed" ? "通过：受限识别与确定性字段合同" : gateStatus === "rejected" ? "拒绝：模型识别与确定性提示不一致" : standardMath.status || "待核验");
  badge($("#general-status"), statusLabel(result.status), statusKind(result.status));
  $("#recognition-domain-intent").textContent = `识别域／意图：${recognizedDomain}／${recognizedIntent}`;
  $("#recognition-model").textContent = `模型：${recognizedModel}`;
  $("#recognition-validation").textContent = `精确核验：${exactValidation}`;
  renderMath($("#standard-formula"), standardMath.display || standardMath.logic, true);
  $("#input-equation").textContent = `原始查询：${normalized.statement || result.input || "—"}`;
  const reactants = result.reactants || normalized.reactants || [];
  const products = result.products || normalized.products || [];
  const entityText = entity => `${entity.formula || entity.token}${entity.phase ? `(${entity.phase})` : ""}${entity.pubchem_cid ? ` [CID ${entity.pubchem_cid}; SMILES ${entity.smiles || "—"}]` : ""}`;
  $("#reactants-products").textContent = reactants.length && products.length
    ? `反应物：${reactants.map(entityText).join(" + ")}  →  产物：${products.map(entityText).join(" + ")}`
    : "反应物／产物：等待受限实体识别";
  const energy = result.reaction_energy || {};
  $("#reaction-energy").textContent = energy.value === null || energy.value === undefined
    ? "反应能量：—（暂无同时含数值、单位、能量类型、方法、参考态和来源的记录）"
    : `反应能量：${energy.value} ${energy.unit} · ${energy.kind} · ${energy.method} · ${energy.reference_state} · ${energy.source_record}`;
  const sort = result.sort || {};
  $("#sort-semantics").textContent = `@best：${sort.requested ? "已按检索相关性与数据完备度排序" : "未请求，保留来源顺序"}；不表示催化性能最佳；证据等级不变`;
  renderMath($("#target-function"), targetFunction.display || "J:\\mathcal X\\to\\mathbb R\\cup\\{\\mathrm{unknown}\\}", false);
  renderPossibilities(result.possibilities || {});
  $("#reaction-language").textContent = normalized.reaction_natural_language || "—";

  const basis = result.basis || {};
  $("#basis-operator").textContent = basis.operator || "Π_B : X → R^k";
  badge($("#basis-state"), `${basis.display_name || basis.name || "基空间"} / k=${basis.dimension || "?"}`, "unknown");
  renderSpaces(result.spaces || []);
  renderPlugins(result.plugin_route || []);
  renderMatrix(basis.matrix);
  renderTasks(result.machine_problems || []);
  renderCandidates(result.search_targets || []);
  renderDatabases(result.database_connectors || [], result.database_receipt || {});
  renderDiscovery(result.discovery_signal || {});
  renderGeometry(result.geometry || { nodes: [], edges: [] });
  renderReferences(result.references || []);

  const lean = result.lean || {};
  badge($("#lean-status"), statusLabel(lean.status || "obligation"), statusKind(lean.status));
  $("#lean-proposition").textContent = lean.proposition || "—";
  clear($("#lean-assumptions"));
  for (const item of lean.assumptions || []) {
    const token = document.createElement("code");
    token.textContent = item;
    $("#lean-assumptions").appendChild(token);
  }
  $("#lean-detail").textContent = JSON.stringify(result.model_receipt || { provider: result.source || "local", calls: 0 }, null, 2);
  $("#call-budget").textContent = `调用 ${receipt.calls || 0} / ${receipt.max_calls || 1}`;
}

function renderDiscovery(signal) {
  badge($("#discovery-status"), signal.scientific_discovery ? "科学发现" : "过程信号，不等于科学发现", signal.status === "observed" ? "unknown" : "bad");
  $("#discovery-observation").textContent = signal.observation || signal.type || "—";
  $("#discovery-process").textContent = signal.process_signal || "—";
  $("#discovery-next-action").textContent = signal.next_action || "—";
  $("#discovery-falsification").textContent = signal.falsification || "—";
}

function renderPossibilities(possibilities) {
  const host = $("#possibility-list");
  clear(host);
  const labels = { temperature: "温度", pressure: "压力", candidate_domain: "候选域", metrics: "观测指标", baseline: "比较基线" };
  for (const [key, label] of Object.entries(labels)) {
    const item = possibilities[key] || {};
    const token = document.createElement("code");
    token.textContent = `${label}=${item.value ?? "未指定（可选）"}`;
    host.appendChild(token);
  }
  const boundary = document.createElement("code");
  boundary.textContent = "blocking=false";
  host.appendChild(boundary);
}

function renderSpaces(spaces) {
  const host = $("#space-chain");
  clear(host);
  spaces.forEach((space, index) => {
    if (index) {
      const arrow = document.createElement("span");
      arrow.textContent = "→";
      host.appendChild(arrow);
    }
    const token = document.createElement("div");
    const id = document.createElement("b");
    id.textContent = space.id || "?";
    const label = document.createElement("small");
    label.textContent = space.label || "空间";
    const map = document.createElement("code");
    map.textContent = space.map || "映射";
    token.append(id, label, map);
    host.appendChild(token);
  });
}

function renderPlugins(routes) {
  const host = $("#plugin-route");
  clear(host);
  for (const route of routes) {
    const row = document.createElement("div");
    const name = document.createElement("b");
    name.textContent = route.label || route.plugin || "插件";
    const state = document.createElement("span");
    state.textContent = statusLabel(route.status);
    const scope = document.createElement("small");
    scope.textContent = route.scope || "—";
    row.append(name, state, scope);
    host.appendChild(row);
  }
}

function renderMatrix(matrix) {
  const host = $("#basis-matrix");
  clear(host);
  if (!matrix || !Array.isArray(matrix.A)) {
    host.textContent = "当前检索空间由类型化字段与来源记录定义，不使用数值矩阵。";
    return;
  }
  const table = document.createElement("table");
  table.className = "matrix-table";
  const head = document.createElement("tr");
  const corner = document.createElement("th");
  corner.textContent = "A";
  head.appendChild(corner);
  for (const column of matrix.columns || []) {
    const th = document.createElement("th");
    th.textContent = column;
    head.appendChild(th);
  }
  table.appendChild(head);
  matrix.A.forEach((row, index) => {
    const tr = document.createElement("tr");
    const th = document.createElement("th");
    th.textContent = matrix.rows?.[index] || String(index);
    tr.appendChild(th);
    row.forEach(value => {
      const td = document.createElement("td");
      td.textContent = String(value);
      tr.appendChild(td);
    });
    table.appendChild(tr);
  });
  host.appendChild(table);
}

function renderTasks(tasks) {
  const host = $("#machine-tasks");
  clear(host);
  for (const task of tasks) {
    const row = document.createElement("div");
    row.className = "task";
    const id = document.createElement("b");
    id.textContent = task.id;
    const operator = document.createElement("code");
    operator.textContent = task.operator;
    const state = document.createElement("small");
    state.textContent = task.status;
    row.append(id, operator, state);
    host.appendChild(row);
  }
}

function renderCandidates(candidates) {
  const host = $("#candidate-list");
  clear(host);
  badge($("#candidate-count"), String(candidates.length), candidates.length ? "unknown" : "bad");
  for (const candidate of candidates) {
    const row = document.createElement("div");
    row.className = "candidate";
    const name = candidate.url ? document.createElement("a") : document.createElement("b");
    name.textContent = `${candidate.rank ? `${candidate.rank}. ` : ""}${candidate.label || candidate.name || "candidate"}`;
    if (candidate.url) {
      name.href = candidate.url;
      name.target = "_blank";
      name.rel = "noopener noreferrer";
    }
    const state = document.createElement("span");
    const candidateState = candidate.state || candidate.status || "query";
    state.textContent = statusLabel(candidateState);
    const query = document.createElement("code");
    const energy = candidate.reaction_energy || {};
    query.textContent = `${candidate.query || candidate.evidence || "—"}；证据=${candidateState}；能量=${energy.value ?? "null"}`;
    row.append(name, state, query);
    host.appendChild(row);
  }
}

function renderDatabases(connectors, receipt) {
  const host = $("#database-list");
  clear(host);
  badge($("#database-mode-receipt"), `${receipt.mode_used || receipt.mode_requested || "—"} · 请求 ${receipt.external_requests ?? 0}`, receipt.errors?.length ? "bad" : "unknown");
  for (const connector of connectors) {
    const row = document.createElement("div");
    row.className = "database-row";
    const name = document.createElement("a");
    name.href = connector.url;
    name.target = "_blank";
    name.rel = "noopener noreferrer";
    name.textContent = connector.name || connector.id;
    const state = document.createElement("span");
    state.textContent = statusLabel(connector.status);
    const scope = document.createElement("small");
    scope.textContent = connector.scope || "—";
    const fields = document.createElement("code");
    fields.textContent = (connector.fields || connector.schema_fields_present || []).join(" · ") || "字段未取得";
    row.append(name, state, scope, fields);
    host.appendChild(row);
  }
}

function renderReferences(references) {
  const host = $("#reference-list");
  clear(host);
  for (const reference of references) {
    const li = document.createElement("li");
    const a = document.createElement("a");
    a.href = reference.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    a.textContent = `${reference.id ? `[${reference.id}] ` : ""}${reference.title}`;
    const small = document.createElement("small");
    small.textContent = `${reference.year || ""} · ${reference.role || "source"}`;
    li.append(a);
    if (reference.doi) {
      const doi = document.createElement("a");
      doi.href = reference.doi;
      doi.target = "_blank";
      doi.rel = "noopener noreferrer";
      doi.className = "doi-link";
      doi.textContent = "DOI";
      li.appendChild(doi);
    }
    li.appendChild(small);
    host.appendChild(li);
  }
}

function renderGeometry(value) {
  geometry = value;
  $("#geometry-title").textContent = value.title || value.kind || "—";
  $("#geometry-quotient").textContent = value.quotient || "坐标不可用";
  $("#geometry-count").textContent = `|V|=${value.nodes?.length || 0}; |E|=${value.edges?.length || 0}`;
  $("#geometry-symmetry").textContent = value.symmetry || "对称信息未取得，不作推断";
  $("#geometry-smiles").textContent = value.smiles || "结构标识=N/A";
  draw2D();
  draw3D();
}

function nodeMap() {
  return new Map((geometry.nodes || []).map(node => [node.id, node]));
}

function draw2D() {
  const svg = $("#geometry-2d");
  clear(svg);
  const map = nodeMap();
  const px = node => 360 + node.x * 125;
  const py = node => 305 - node.z * 110 - node.y * 45;
  for (const [aId, bId] of geometry.edges || []) {
    const a = map.get(aId), b = map.get(bId);
    if (!a || !b) continue;
    svg.appendChild(svgEl("line", { x1: px(a), y1: py(a), x2: px(b), y2: py(b), stroke: "#94a5ad", "stroke-width": 7, "stroke-linecap": "round", opacity: .58 }));
  }
  for (const node of geometry.nodes || []) {
    const fill = colors[node.element] || "#8395a0";
    svg.appendChild(svgEl("circle", { cx: px(node), cy: py(node), r: node.element === "H" ? 16 : 23, fill, stroke: "white", "stroke-width": 4 }));
    svg.appendChild(svgEl("text", { x: px(node), y: py(node) + 5, "text-anchor": "middle", fill: node.element === "H" ? "#42525b" : "white", "font-size": 13, "font-weight": 900 }, node.element));
  }
}

function rotatePoint(node) {
  const cy = Math.cos(rotation.yaw), sy = Math.sin(rotation.yaw);
  const cp = Math.cos(rotation.pitch), sp = Math.sin(rotation.pitch);
  const x1 = node.x * cy + node.z * sy;
  const z1 = -node.x * sy + node.z * cy;
  const y1 = node.y * cp - z1 * sp;
  const z2 = node.y * sp + z1 * cp;
  return { ...node, x: x1, y: y1, z: z2 };
}

function draw3D() {
  const canvas = $("#geometry-3d");
  const rect = canvas.getBoundingClientRect();
  const width = Math.max(300, Math.round(rect.width || 720));
  const height = Math.round(width * 430 / 720);
  const ratio = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const ctx = canvas.getContext("2d");
  ctx.scale(ratio, ratio);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#eef3f3";
  ctx.fillRect(0, 0, width, height);
  const rotated = new Map((geometry.nodes || []).map(node => [node.id, rotatePoint(node)]));
  const project = node => {
    const scale = 104 * rotation.zoom * (5 / Math.max(2.5, 5 - node.z * .15));
    return { x: width / 2 + node.x * scale, y: height * .62 - (node.z * .55 + node.y) * scale, scale };
  };
  ctx.lineCap = "round";
  for (const [aId, bId] of geometry.edges || []) {
    const a = rotated.get(aId), b = rotated.get(bId);
    if (!a || !b) continue;
    const pa = project(a), pb = project(b);
    ctx.strokeStyle = "rgba(124, 145, 154, .62)";
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.moveTo(pa.x, pa.y);
    ctx.lineTo(pb.x, pb.y);
    ctx.stroke();
  }
  [...rotated.values()].sort((a, b) => a.z - b.z).forEach(node => {
    const point = project(node);
    const radius = (node.element === "H" ? 12 : 18) * rotation.zoom;
    ctx.beginPath();
    ctx.arc(point.x, point.y, radius, 0, Math.PI * 2);
    ctx.fillStyle = colors[node.element] || "#8395a0";
    ctx.fill();
    ctx.lineWidth = 3;
    ctx.strokeStyle = "white";
    ctx.stroke();
    ctx.fillStyle = node.element === "H" ? "#42525b" : "white";
    ctx.font = `800 ${Math.max(10, radius * .7)}px system-ui`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(node.element, point.x, point.y + 1);
  });
}

$$('.segmented button').forEach(button => button.addEventListener("click", () => {
  $$('.segmented button').forEach(item => item.classList.toggle("is-active", item === button));
  const view = button.dataset.view;
  $("#geometry-2d").toggleAttribute("hidden", view !== "2d");
  $("#geometry-3d").toggleAttribute("hidden", view !== "3d");
  if (view === "3d") draw3D();
}));

const canvas = $("#geometry-3d");
canvas.addEventListener("pointerdown", event => {
  drag = { x: event.clientX, y: event.clientY, yaw: rotation.yaw, pitch: rotation.pitch };
  canvas.setPointerCapture(event.pointerId);
});
canvas.addEventListener("pointermove", event => {
  if (!drag) return;
  rotation.yaw = drag.yaw + (event.clientX - drag.x) * .01;
  rotation.pitch = Math.max(-1.25, Math.min(1.25, drag.pitch + (event.clientY - drag.y) * .01));
  draw3D();
});
canvas.addEventListener("pointerup", () => { drag = null; });
canvas.addEventListener("wheel", event => {
  event.preventDefault();
  rotation.zoom = Math.max(.55, Math.min(1.8, rotation.zoom * (event.deltaY > 0 ? .92 : 1.08)));
  draw3D();
}, { passive: false });
window.addEventListener("resize", () => { if (!canvas.hidden) draw3D(); });

$("#lean-check-global").addEventListener("click", async () => {
  badge($("#lean-status"), "running", "unknown");
  $("#lean-runtime-status").textContent = "running";
  try {
    const result = await api("/api/lean/check", {});
    badge($("#lean-status"), result.status, statusKind(result.status));
    $("#lean-runtime-status").textContent = result.status;
    $("#lean-detail").textContent = JSON.stringify(result.results, null, 2);
  } catch (error) {
    badge($("#lean-status"), "error", "bad");
    $("#lean-runtime-status").textContent = "error";
    $("#lean-detail").textContent = String(error);
  }
});

$("#iterate-kind").addEventListener("change", event => {
  const kind = event.target.value;
  $("#template-wrap").classList.toggle("is-hidden", kind !== "basis");
  $("#x-wrap").classList.toggle("is-hidden", kind !== "basis");
  $("#branch-wrap").classList.toggle("is-hidden", kind !== "basis");
  $("#tolerance-wrap").classList.toggle("is-hidden", kind !== "basis");
  $("#finite-fields").classList.toggle("is-hidden", kind !== "finite");
  $("#inverse-fields").classList.toggle("is-hidden", kind !== "inverse");
});

function parseMap(value) {
  if (!/^\s*\d+(\s*,\s*\d+)*\s*$/.test(value)) throw new Error("finite map: comma-separated nonnegative integers required");
  return value.split(",").map(item => Number(item.trim()));
}

$("#iterate-form").addEventListener("submit", async event => {
  event.preventDefault();
  const kind = $("#iterate-kind").value;
  const payload = { kind };
  if (kind === "basis") {
    Object.assign(payload, {
      template: $("#function-template").value,
      x: Number($("#iterate-x").value),
      tolerance: Number($("#iterate-tolerance").value),
      domain: $("#iterate-domain").value,
      branch: $("#iterate-branch").value
    });
  } else if (kind === "finite") {
    try {
      payload.f = parseMap($("#finite-f").value);
      payload.g = parseMap($("#finite-g").value);
    } catch (error) {
      renderIterate({ result: { status: "invalid", oracle_trace: [String(error)] } });
      return;
    }
  } else {
    payload.relation = $("#inverse-relation").value;
    payload.assumptions = $("#inverse-assumptions").value;
  }
  badge($("#iterate-status"), "running", "unknown");
  try {
    renderIterate(await api("/api/iterate/check", payload));
  } catch (error) {
    renderIterate({ result: { status: "error", oracle_trace: [String(error)] } });
  }
});

function fmtComplex(value) {
  if (!value) return "—";
  const re = Number(value.real || 0), im = Number(value.imag || 0);
  return `${re.toFixed(6)} ${im < 0 ? "−" : "+"} ${Math.abs(im).toFixed(6)}i`;
}

function renderIterate(payload) {
  const result = payload.result || {};
  badge($("#iterate-status"), statusLabel(result.status || payload.status), statusKind(result.status || payload.status));
  $("#iterate-compiled").textContent = result.compiled_value ? fmtComplex(result.compiled_value) : result.counterexample ? JSON.stringify(result.counterexample) : "—";
  $("#iterate-reference").textContent = result.reference_value ? fmtComplex(result.reference_value) : "—";
  $("#iterate-error").textContent = typeof result.absolute_error === "number" ? result.absolute_error.toExponential(6) : result.reason || result.status || "—";
  $("#iterate-trace").textContent = (result.oracle_trace || []).join("\n") || result.reason || "—";
  $("#iterate-obligation").textContent = payload.obligation || "定义域 → 复合闭合性 → 等式";
  drawAst(payload.ast, result.counterexample);
}

function drawAst(ast, counterexample = null) {
  const svg = $("#iterate-ast");
  clear(svg);
  if (!ast) {
    svg.appendChild(svgEl("text", { x: 360, y: 190, "text-anchor": "middle", fill: "#245f83", "font-size": 24, "font-family": "Cambria Math" }, counterexample ? JSON.stringify(counterexample) : "proof obligation"));
    return;
  }
  const nodes = [], edges = [];
  function walk(node, depth, left, right, parent = null) {
    const id = nodes.length;
    const x = (left + right) / 2;
    const y = 68 + depth * 94;
    nodes.push({ id, node, x, y });
    if (parent !== null) edges.push([parent, id]);
    const children = [node.left, node.right].filter(Boolean);
    children.forEach((child, index) => walk(child, depth + 1, left + (right - left) * index / children.length, left + (right - left) * (index + 1) / children.length, id));
  }
  walk(ast, 0, 45, 675);
  edges.forEach(([a, b]) => svg.appendChild(svgEl("line", { x1: nodes[a].x, y1: nodes[a].y, x2: nodes[b].x, y2: nodes[b].y, stroke: "#8da0aa", "stroke-width": 3 })));
  nodes.forEach(({ node, x, y }) => {
    const label = node.op === "basis" ? "B" : node.op;
    const isOperator = label === "B";
    svg.appendChild(svgEl("circle", { cx: x, cy: y, r: isOperator ? 31 : 25, fill: isOperator ? "#0d2538" : "#e9c46a", stroke: "white", "stroke-width": 4 }));
    svg.appendChild(svgEl("text", { x, y: y + 5, "text-anchor": "middle", fill: isOperator ? "white" : "#0d2538", "font-size": isOperator ? 12 : 15, "font-weight": 900 }, label));
  });
}

async function start() {
  await detectRuntime();
  const providerOverride = new URLSearchParams(window.location.search).get("provider");
  if (["local", "qwen", "codex", "deepseek", "auto"].includes(providerOverride)) {
    $("#solver-provider").value = providerOverride;
  }
  await runGeneral();
  drawAst({ op: "basis", left: { op: "1" }, right: { op: "x" } });
}

start();
