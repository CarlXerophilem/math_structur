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
    await page.locator("#general-status").filter({ hasText: "已分解" }).waitFor({ timeout: 240000 });
    assert.equal(await page.locator("#solver-provider").inputValue(), "qwen");
    const domainIntent = (await page.locator("#recognition-domain-intent").innerText()).trim();
    const model = (await page.locator("#recognition-model").innerText()).trim();
    const validation = (await page.locator("#recognition-validation").innerText()).trim();
    const budget = (await page.locator("#call-budget").innerText()).trim();
    assert.match(domainIntent, /reaction／catalyst_search/);
    assert.match(model, /Qwen3-8B-Jailbroken/);
    assert.match(validation, /通过：识别闸门、配平与 Aν=0/);
    assert.match(budget, /调用 1 \/ 1/);
    const inputAudit = (await page.locator("#input-audit").innerText()).trim();
    assert.match(inputAudit, /未通过/);
    assert.match(inputAudit, /拒绝排名/);
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
      input_audit: inputAudit,
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
