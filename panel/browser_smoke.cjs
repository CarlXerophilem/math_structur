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
    await page.goto(baseURL, { waitUntil: "networkidle" });
    await page.locator("#general-status").filter({ hasText: "已分解" }).waitFor({ timeout: 20000 });
    assert.equal(await page.locator("button.tab").count(), 2);
    assert.equal(await page.locator("button, a").filter({ hasText: /export|download|导出/i }).count(), 0);
    assert.match(await page.locator(".project-tagline").innerText(), /Convincing, reusable target-matching skills/);
    assert.ok(await page.locator("#standard-formula .katex").count() > 0);
    assert.ok(await page.locator("#target-function .katex").count() > 0);
    assert.equal(await page.locator("#space-chain > div").count(), 6);
    const pluginText = await page.locator("#plugin-route").innerText();
    assert.match(pluginText, /反应分解器/);
    assert.match(pluginText, /特定基算子复合器\s+未调用/);
    assert.match(pluginText, /几何插件/);
    assert.match(await page.locator("#objective-vector").innerText(), /非平凡性=未核验/);
    assert.match(await page.locator("#reaction-language").innerText(), /当前只列候选，不排名/);

    const originalEquation = (await page.locator("#input-equation").innerText()).trim();
    const equation = (await page.locator("#normalized-equation").innerText()).trim();
    const audit = (await page.locator("#input-audit").innerText()).trim();
    const kernel = (await page.locator("#basis-matrix > code").innerText()).trim();
    assert.match(originalEquation, /原始查询（未守恒）：CO2\(g\) \+ H2\(g\)/);
    assert.match(equation, /配平结果（Aν=0）：2 CO2\(g\) \+ 6 H2\(g\)/);
    assert.match(audit, /原始守恒检查=未通过/);
    assert.match(audit, /@best=条件欠定，拒绝排名/);
    assert.match(kernel, /Aν = \(0, 0, 0\)/);

    const candidates = await page.locator("#candidate-list .candidate").count();
    assert.equal(candidates, 4);
    assert.match(await page.locator("#candidate-list").innerText(), /Pd1\/Fe3O4/);
    assert.equal(await page.locator("#candidate-list a").count(), 4);
    const atomLabels = await page.locator("#geometry-2d text").allTextContents();
    assert.ok(atomLabels.includes("Pd"));
    assert.ok(atomLabels.includes("Fe"));
    assert.match(await page.locator("#geometry-smiles").innerText(), /ethanol=CCO/);
    assert.match(await page.locator("#geometry-symmetry").innerText(), /不主张空间群/);
    assert.ok(await page.locator("#reference-list a").count() >= 9);
    receipt.assertions.general = { original_equation: originalEquation, balanced_equation: equation, audit, kernel, candidates, atom_elements: [...new Set(atomLabels)], spaces: 6, plugins: ["ReactionDecomposer", "BasisOperatorComposer:not_invoked", "GeometryPlugin"], katex: true };
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
