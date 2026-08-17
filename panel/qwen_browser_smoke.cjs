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
    browser: "system Chrome via Playwright; isolated profile",
    provider: "qwen",
    assertions: {},
    requests: [],
    console_errors: [],
    page_errors: [],
    request_failures: []
  };
  const chromePath = discoverChrome();
  const browser = await chromium.launch(chromePath ? { executablePath: chromePath, headless: true } : { channel: "chrome", headless: true });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1100 } });
  const page = await context.newPage();
  page.on("console", message => {
    if (message.type() === "error") receipt.console_errors.push(message.text());
  });
  page.on("pageerror", error => receipt.page_errors.push(String(error)));
  page.on("requestfailed", request => receipt.request_failures.push({ url: request.url(), error: request.failure()?.errorText || "unknown" }));
  page.on("request", request => receipt.requests.push({ method: request.method(), url: request.url() }));
  try {
    const url = new URL(baseURL);
    url.searchParams.set("provider", "qwen");
    await page.goto(url.toString(), { waitUntil: "domcontentloaded" });
    await page.locator("#general-status").filter({ hasText: "已检索并排序" }).waitFor({ timeout: 240000 });
    assert.equal(await page.locator("#solver-provider").inputValue(), "qwen");
    const domainIntent = (await page.locator("#recognition-domain-intent").innerText()).trim();
    const model = (await page.locator("#recognition-model").innerText()).trim();
    const validation = (await page.locator("#recognition-validation").innerText()).trim();
    const budget = (await page.locator("#call-budget").innerText()).trim();
    assert.match(domainIntent, /reaction／catalyst_search/);
    assert.match(model, /Qwen3-8B-Jailbroken/);
    assert.match(validation, /通过：受限识别与确定性字段合同/);
    assert.match(budget, /调用 1 \/ 1/);
    const originalQuery = (await page.locator("#input-equation").innerText()).trim();
    const entities = (await page.locator("#reactants-products").innerText()).trim();
    const reactionEnergy = (await page.locator("#reaction-energy").innerText()).trim();
    const sortSemantics = (await page.locator("#sort-semantics").innerText()).trim();
    const possibilities = (await page.locator("#possibility-list").innerText()).trim();
    const geometryTitle = (await page.locator("#geometry-title").innerText()).trim();
    const geometryRecord = (await page.locator("#geometry-smiles").innerText()).trim();
    const discoveryStatus = (await page.locator("#discovery-status").innerText()).trim();
    const nextAction = (await page.locator("#discovery-next-action").innerText()).trim();
    const falsification = (await page.locator("#discovery-falsification").innerText()).trim();
    const candidates = await page.locator("#candidate-list .candidate").count();
    assert.equal(originalQuery, "原始查询：CO2gas+H2gas -- CH3CH2OHgas @best");
    assert.match(entities, /CO2\(gas\) \[CID 280;/);
    assert.match(entities, /H2\(gas\) \[CID 783;/);
    assert.match(entities, /C2H6O\(gas\) \[CID 702;/);
    assert.match(reactionEnergy, /^反应能量：—/);
    assert.match(sortSemantics, /已按检索相关性与数据完备度排序/);
    assert.match(sortSemantics, /不表示催化性能最佳；证据等级不变/);
    assert.match(possibilities, /温度=未指定（可选）/);
    assert.match(possibilities, /比较基线=未指定（可选）/);
    assert.match(possibilities, /blocking=false/);
    assert.match(geometryTitle, /Fe₃O₄ 支撑体公共晶体记录 mp-19306/);
    assert.match(geometryTitle, /不是 Pd 活性位构型/);
    assert.match(geometryRecord, /scope=support-only/);
    assert.match(discoveryStatus, /过程信号，不等于科学发现/);
    assert.match(nextAction, /Catalysis-Hub/);
assert.match(falsification, /拒绝或缩小/);
    assert.equal(candidates, 5);
    assert.match(await page.locator("#candidate-list").innerText(), /能量=null/);
    await page.screenshot({ path: path.join(artifactDir, "panel_desktop_qwen_recognition.png"), fullPage: true });
    const nonLocal = receipt.requests.filter(entry => !["127.0.0.1", "localhost"].includes(new URL(entry.url).hostname));
    assert.deepEqual(nonLocal, []);
    assert.deepEqual(receipt.console_errors, []);
    assert.deepEqual(receipt.page_errors, []);
    assert.deepEqual(receipt.request_failures, []);
    receipt.assertions = {
      domain_intent: domainIntent,
      model,
      exact_validation: validation,
      model_calls: budget,
      original_query: originalQuery,
      entities,
      reaction_energy: null,
      sort_semantics: "sort_only",
      possibilities_blocking: false,
      candidates,
      geometry_record: "mp-19306",
      geometry_scope: "support_only",
      scientific_discovery: false,
      next_action: nextAction,
      external_browser_requests: 0
    };
    receipt.status = "passed";
  } catch (error) {
    receipt.status = "failed";
    receipt.error = String(error && error.stack ? error.stack : error);
    throw error;
  } finally {
    fs.writeFileSync(path.resolve(artifactDir, "..", "qwen_recognition_browser_acceptance.json"), JSON.stringify(receipt, null, 2) + "\n", "utf8");
    await browser.close();
  }
}

main().then(() => {
  process.stdout.write("Qwen browser recognition acceptance passed\n");
}).catch(error => {
  process.stderr.write(String(error && error.stack ? error.stack : error) + "\n");
  process.exitCode = 1;
});
