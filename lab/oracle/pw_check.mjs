#!/usr/bin/env node
/**
 * Hold-out Chromium oracle for a few lab payloads.
 * Expects JSONL {payload} on stdin; writes JSONL {payload, executed}.
 */
import { existsSync } from "node:fs";
import { createInterface } from "node:readline";

async function launchBrowser(chromium) {
  const systemChrome =
    process.env.PW_CHROME ||
    ["/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"].find(
      (p) => existsSync(p)
    );

  const candidates = [{ name: "playwright", opts: { headless: true } }];
  if (systemChrome) {
    candidates.push({
      name: "system",
      opts: { headless: true, executablePath: systemChrome },
    });
  }

  let lastErr;
  for (const c of candidates) {
    try {
      const browser = await chromium.launch(c.opts);
      process.stderr.write(`pw_browser=${c.name}\n`);
      return browser;
    } catch (err) {
      lastErr = err;
    }
  }
  throw lastErr;
}

async function main() {
  let chromium;
  try {
    ({ chromium } = await import("playwright"));
  } catch {
    process.stderr.write("playwright_not_installed\n");
    process.exit(2);
  }

  let browser;
  try {
    browser = await launchBrowser(chromium);
  } catch (err) {
    process.stderr.write(
      "playwright_browser_missing: " + String(err).split("\n")[0] + "\n"
    );
    process.stderr.write(
      "fix: npx playwright install chromium   (hoac dat PW_CHROME=/usr/bin/chromium)\n"
    );
    process.exit(2);
  }
  const rl = createInterface({ input: process.stdin, crlfDelay: Infinity });
  for await (const line of rl) {
    const trimmed = line.trim();
    if (!trimmed) continue;
    const msg = JSON.parse(trimmed);
    const page = await browser.newPage();
    const payload = String(msg.payload ?? "");
    const html =
      "<!DOCTYPE html><html><head><script>" +
      "window.__XSS_ORACLE=false;" +
      "function __trip(){window.__XSS_ORACLE=true;}" +
      "window.alert=__trip;window.prompt=__trip;window.confirm=__trip;" +
      "</script></head><body>" +
      payload +
      "</body></html>";
    let executed = false;
    try {
      await page.setContent(html, { waitUntil: "domcontentloaded", timeout: 5000 });
      await new Promise((r) => setTimeout(r, 80));
      await page.evaluate(() => {
        document.querySelectorAll("a[href], area[href]").forEach((el) => {
          const href = el.getAttribute("href") || "";
          if (/^\s*javascript:/i.test(href)) {
            try {
              el.click();
            } catch {
              /* ignore */
            }
          }
        });
      });
      executed = await page.evaluate(() => Boolean(window.__XSS_ORACLE));
    } catch (err) {
      executed = false;
      process.stdout.write(
        JSON.stringify({
          payload: msg.payload,
          executed,
          error: String(err).slice(0, 200),
        }) + "\n"
      );
      await page.close();
      continue;
    }
    process.stdout.write(JSON.stringify({ payload: msg.payload, executed }) + "\n");
    await page.close();
  }
  await browser.close();
}

await main();
