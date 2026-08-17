"use strict";

const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");
const { chromium } = require("playwright");

const baseURL = process.env.PANEL_URL || "http://127.0.0.1:8766/";
const artifactDir = process.env.PANEL_ARTIFACT_DIR || path.resolve(__dirname, "..", "artifacts", "panel");
fs.mkdirSync(artifactDir, { recursive: true });

function discoverChrome() {
  const candidates = [
    process.env.CHROME_PATH,
    process.env.LOCALAPPDATA && path.join(process.env.LOCALAPPDATA, "Google", "Chrome", "Application", "chrome.exe"),
    process.env.ProgramFiles && path.join(process.env.ProgramFiles, "Google", "Chrome", "Application", "chrome.exe"),
    process.env["ProgramFiles(x86)"] && path.join(process.env["ProgramFiles(x86)"], "Google", "Chrome", "Application", "chrome.exe")
  ].filter(Boolean);
  return candidates.find(candidate => fs.existsSync(candidate)) || null;
}

async function main() {
  const receipt = {
    checked_at: new Date().toISOString(),
    base_url: baseURL,
    browser: "system Chrome via Playwright; isolated profile",
    assertions: {},
    requests: [],
    console_errors: [],
    page_errors: [],
    request_failures: []
  };

  const chromePath = discoverChrome();
  const browser = await chromium.launch(chromePath ? { executablePath: chromePath, headless: true } : { channel: "chrome", headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();

  page.on("console", message => {
    if (message.type() === "error") receipt.console_errors.push(message.text());
  });
  page.on("pageerror", error => receipt.page_errors.push(String(error)));
  page.on("requestfailed", request => receipt.request_failures.push({ url: request.url(), error: request.failure()?.errorText || "unknown" }));
  page.on("request", request => receipt.requests.push({ method: request.method(), url: request.url() }));

  try {
    const localURL = new URL(baseURL);
    localURL.searchParams.set("provider", "local");
    await page.goto(localURL.toString(), { waitUntil: "domcontentloaded" });
    await page.locator("#solver-provider").selectOption("local");
    await page.waitForLoadState("networkidle");
    assert.equal(await page.locator("#solver-provider").inputValue(), "local");
    await page.locator("#general-status").filter({ hasText: "已检索并排序" }).waitFor({ timeout: 20000 });
    assert.equal(await page.locator("button.tab").count(), 2);
    assert.equal(await page.locator("button, a").filter({ hasText: /export|download|导出/i }).count(), 0);
    assert.match(await page.locator(".project-tagline").innerText(), /Convincing, reusable target-matching skills/);
    assert.ok(await page.locator("#standard-formula .katex").count() > 0);
    assert.ok(await page.locator("#target-function .katex").count() > 0);
    assert.equal(await page.locator("#space-chain > div").count(), 6);
    const pluginText = await page.locator("#plugin-route").innerText();
    assert.match(pluginText, /反应实体解析器/);
    assert.match(pluginText, /文献分析/);
    assert.match(pluginText, /公共数据库路由/);
    assert.match(pluginText, /几何插件/);
    assert.match(pluginText, /@best 排序器/);
    assert.match(pluginText, /只改顺序，不改证据等级/);
    assert.match(await page.locator("#reaction-language").innerText(), /温度、压力等保持为可选可能性，不阻止返回候选/);
    assert.match(await page.locator("#recognition-domain-intent").innerText(), /识别域／意图/);
    assert.match(await page.locator("#recognition-model").innerText(), /确定性检索内核（无模型调用）/);
    assert.match(await page.locator("#recognition-validation").innerText(), /typed_retrieval_contract/);

    const originalEquation = (await page.locator("#input-equation").innerText()).trim();
    const entities = (await page.locator("#reactants-products").innerText()).trim();
    const energy = (await page.locator("#reaction-energy").innerText()).trim();
    const sortSemantics = (await page.locator("#sort-semantics").innerText()).trim();
    const possibilities = (await page.locator("#possibility-list").innerText()).trim();
    const kernel = (await page.locator("#basis-matrix").innerText()).trim();
    assert.equal(originalEquation, "原始查询：CO2gas+H2gas -- CH3CH2OHgas @best");
    assert.match(entities, /反应物：CO2\(gas\) \[CID 280;/);
    assert.match(entities, /H2\(gas\) \[CID 783;/);
    assert.match(entities, /产物：C2H6O\(gas\) \[CID 702;/);
    assert.match(energy, /^反应能量：—/);
    assert.match(energy, /数值、单位、能量类型、方法、参考态和来源/);
    assert.match(sortSemantics, /@best：已按检索相关性与数据完备度排序/);
    assert.match(sortSemantics, /不表示催化性能最佳；证据等级不变/);
    assert.match(possibilities, /温度=未指定（可选）/);
    assert.match(possibilities, /比较基线=未指定（可选）/);
    assert.match(possibilities, /blocking=false/);
    assert.equal(kernel, "当前检索空间由类型化字段与来源记录定义，不使用数值矩阵。");

    const contract = await page.evaluate(async () => {
      const response = await fetch("/api/solver/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: "local",
          problem: "CO2gas+H2gas -- CH3CH2OHgas @best",
          domain: "reaction",
          basis: "literature_energy_geometry_space",
          dimension: 4,
          database_mode: "verified_snapshot"
        })
      });
      if (!response.ok) throw new Error(`solver HTTP ${response.status}`);
      return response.json();
    });
    assert.deepEqual(contract.reactants.map(item => item.formula), ["CO2", "H2"]);
    assert.deepEqual(contract.products.map(item => item.formula), ["C2H6O"]);
    for (const key of ["value", "unit", "kind", "method", "reference_state", "source_record"]) {
      assert.equal(contract.reaction_energy[key], null);
    }
    assert.equal(contract.sort.semantics, "sort_only");
    assert.equal(contract.sort.scientific_optimum_claim, false);
    assert.equal(contract.sort.changes_evidence_grade, false);
    assert.equal(contract.possibilities.blocking, false);
    for (const key of ["temperature", "pressure", "candidate_domain", "metrics", "baseline"]) {
      assert.equal(contract.possibilities[key].value, null);
    }
    assert.equal(contract.database_receipt.mode_used, "verified_snapshot");
    assert.equal(contract.database_receipt.external_requests, 0);
    assert.deepEqual(contract.database_receipt.reaction_energy_records, []);
    assert.equal(contract.model_receipt.calls, 0);
    assert.equal(contract.geometry.record_id, "mp-19306");
    assert.equal(contract.geometry.source_database, "Materials Project OPTIMADE");
    assert.equal(contract.geometry.source_scope, "support_only");
    assert.equal(contract.geometry.coordinate_status, "public_database_record_support_only");
    assert.deepEqual([...new Set(contract.geometry.nodes.map(node => node.element))].sort(), ["Fe", "O"]);
    assert.equal(contract.search_targets.length, 5);
    assert.ok(contract.search_targets.every(item => item.reaction_energy.value === null));
    assert.equal(contract.discovery_signal.type, "source_coverage_gap_and_problem_definition_revision");
    assert.equal(contract.discovery_signal.scientific_discovery, false);
    assert.match(contract.discovery_signal.next_action, /Catalysis-Hub/);
assert.match(contract.discovery_signal.falsification, /拒绝或缩小/);

    const candidates = await page.locator("#candidate-list .candidate").count();
    assert.equal(candidates, 5);
    assert.match(await page.locator("#candidate-list").innerText(), /Pd1\/Fe3O4/);
    assert.match(await page.locator("#candidate-list").innerText(), /检索匹配分=90/);
    assert.match(await page.locator("#candidate-list").innerText(), /能量=null/);
    assert.equal(await page.locator("#candidate-list a").count(), 5);
    assert.equal(await page.locator("#database-list a").count(), 7);
    const databaseText = await page.locator("#database-list").innerText();
    for (const label of ["alphaXiv MCP/API", "PubChem PUG REST", "Materials Project OPTIMADE", "Catalysis-Hub GraphQL", "Open Catalyst 2020", "Crossref REST", "OpenAlex Works"]) {
      assert.match(databaseText, new RegExp(label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
    }
    const atomLabels = await page.locator("#geometry-2d text").allTextContents();
    assert.deepEqual([...new Set(atomLabels)].sort(), ["Fe", "O"]);
    assert.match(await page.locator("#geometry-title").innerText(), /mp-19306/);
    assert.match(await page.locator("#geometry-title").innerText(), /不是 Pd 活性位构型/);
    assert.match(await page.locator("#geometry-smiles").innerText(), /record=mp-19306/);
    assert.match(await page.locator("#geometry-smiles").innerText(), /scope=support-only/);
    assert.match(await page.locator("#geometry-symmetry").innerText(), /不推断对称群/);
    assert.match(await page.locator("#discovery-status").innerText(), /过程信号，不等于科学发现/);
    assert.match(await page.locator("#discovery-next-action").innerText(), /Catalysis-Hub/);
assert.match(await page.locator("#discovery-falsification").innerText(), /拒绝或缩小/);
    assert.ok(await page.locator("#reference-list a").count() >= 10);
    receipt.assertions.general = {
      original_query: originalEquation,
      entities,
      reaction_energy: null,
      sort_semantics: "sort_only",
      possibilities_blocking: false,
      kernel,
      candidates,
      database_connectors: 7,
      geometry_record: "mp-19306",
      geometry_scope: "support_only",
      scientific_discovery: false,
      next_action: contract.discovery_signal.next_action,
      atom_elements: [...new Set(atomLabels)].sort(),
      spaces: 6,
      plugins: ["ReactionEntityParser", "LiteratureConnector", "PublicDatabaseRouter", "GeometryPlugin", "StableSorter"],
      katex: true,
      verified_snapshot_external_requests: 0
    };
    await page.screenshot({ path: path.join(artifactDir, "panel_desktop_general_2d.png"), fullPage: true });
    await page.setViewportSize({ width: 1440, height: 1600 });
    const equationBox = await page.locator(".equation-card").boundingBox();
    const basisBox = await page.locator(".basis-card").boundingBox();
    assert.ok(equationBox && basisBox);
    const slice = {
      x: Math.max(0, Math.min(equationBox.x, basisBox.x) - 10),
      y: Math.max(0, Math.min(equationBox.y, basisBox.y) - 10),
      width: Math.min(1440, Math.max(equationBox.x + equationBox.width, basisBox.x + basisBox.width) - Math.min(equationBox.x, basisBox.x) + 20),
      height: Math.max(equationBox.y + equationBox.height, basisBox.y + basisBox.height) - Math.min(equationBox.y, basisBox.y) + 20
    };
    await page.screenshot({ path: path.join(artifactDir, "panel_desktop_general_slice.png"), clip: slice });
    receipt.assertions.general.slice = Object.fromEntries(Object.entries(slice).map(([key, value]) => [key, Math.round(value)]));
    await page.setViewportSize({ width: 1440, height: 1000 });

    await page.locator('[data-view="3d"]').click();
    assert.equal(await page.locator("#geometry-3d").isVisible(), true);
    const visibility = await page.evaluate(() => ({
      svg_hidden: document.querySelector("#geometry-2d").hasAttribute("hidden"),
      svg_display: getComputedStyle(document.querySelector("#geometry-2d")).display,
      svg_height: document.querySelector("#geometry-2d").getBoundingClientRect().height,
      canvas_hidden: document.querySelector("#geometry-3d").hasAttribute("hidden"),
      canvas_display: getComputedStyle(document.querySelector("#geometry-3d")).display
    }));
    assert.equal(visibility.svg_hidden, true);
    assert.equal(visibility.svg_display, "none");
    assert.equal(visibility.svg_height, 0);
    const box = await page.locator("#geometry-3d").boundingBox();
    assert.ok(box && box.width > 300 && box.height > 150);
    await page.locator(".geometry-card").screenshot({ path: path.join(artifactDir, "panel_desktop_general_3d.png") });
    await page.mouse.move(box.x + box.width * .45, box.y + box.height * .45);
    await page.mouse.down();
    await page.mouse.move(box.x + box.width * .65, box.y + box.height * .55);
    await page.mouse.up();
    receipt.assertions.geometry_3d = { visible: true, width: Math.round(box.width), height: Math.round(box.height), interaction: "drag", visibility };

    await page.locator('[data-mode="iterate"]').click();
    const operatorBoundary = await page.locator(".expander-boundary").innerText();
    assert.match(operatorBoundary, /特定基算子复合器/);
    assert.match(operatorBoundary, /B: ℂ × ℂ× → ℂ/);
    assert.match(operatorBoundary, /Arg\(v\)∈\(−π,π\]/);
    assert.match(await page.locator(".expander-boundary").innerText(), /不主张统一代数/);
    assert.match(await page.locator("#domain-wrap").innerText(), /当前测试域 Df/);
    assert.match(await page.locator(".ast-card h2").innerText(), /基算子复合表达树/);
    await page.locator("#iterate-form button[type=submit]").click();
    await page.locator("#iterate-status").filter({ hasText: "不匹配" }).waitFor();
    const iterateError = (await page.locator("#iterate-error").innerText()).trim();
    assert.equal(iterateError, "6.283185e+0");
    await page.locator("#lean-check-global").click();
    await page.locator("#lean-runtime-status").filter({ hasText: "partial_formalization" }).waitFor({ timeout: 70000 });
    const leanDetail = (await page.locator("#lean-detail").innerText()).trim();
    assert.match(leanDetail, /source_contains_axiom/);
    receipt.assertions.iterate = {
      status: (await page.locator("#iterate-status").innerText()).trim(),
      absolute_error: iterateError,
      lean: (await page.locator("#lean-runtime-status").innerText()).trim(),
      operator_contract: "B: C x C^times -> C; pointwise principal Log; Arg(v) in (-pi,pi]",
      current_test_domain: (await page.locator("#iterate-domain option:checked").innerText()).trim(),
      tree_label: (await page.locator(".ast-card h2").innerText()).trim()
    };
    await page.screenshot({ path: path.join(artifactDir, "panel_desktop_iterate.png"), fullPage: true });

    await page.setViewportSize({ width: 390, height: 844 });
    await page.locator('[data-mode="general"]').click();
    await page.locator('[data-view="2d"]').click();
    await page.waitForTimeout(250);
    const overflow = await page.evaluate(() => ({
      viewport_width: document.documentElement.clientWidth,
      scroll_width: document.documentElement.scrollWidth
    }));
    assert.ok(overflow.scroll_width <= overflow.viewport_width + 1, `mobile horizontal overflow: ${JSON.stringify(overflow)}`);
    receipt.assertions.mobile = overflow;
    await page.screenshot({ path: path.join(artifactDir, "panel_mobile_general.png"), fullPage: true });

    const nonLocalRequests = receipt.requests.filter(entry => {
      const url = new URL(entry.url);
      return !["127.0.0.1", "localhost"].includes(url.hostname);
    });
    assert.deepEqual(nonLocalRequests, []);
    assert.deepEqual(receipt.console_errors, []);
    assert.deepEqual(receipt.page_errors, []);
    assert.deepEqual(receipt.request_failures, []);
    receipt.assertions.external_network_requests = 0;
    receipt.assertions.model_calls = (await page.locator("#call-budget").innerText()).trim();
    assert.match(receipt.assertions.model_calls, /调用 0 \/ 1/);
    receipt.status = "passed";
  } catch (error) {
    receipt.status = "failed";
    receipt.failure = error?.stack || String(error);
    throw error;
  } finally {
    fs.writeFileSync(path.join(artifactDir, "browser_acceptance.json"), JSON.stringify(receipt, null, 2) + "\n", "utf8");
    await context.close();
    await browser.close();
  }

  process.stdout.write(`Browser acceptance passed: ${path.join(artifactDir, "browser_acceptance.json")}\n`);
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
