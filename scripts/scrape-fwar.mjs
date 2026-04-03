#!/usr/bin/env node
// scripts/scrape-fwar.mjs
// Scrapes FanGraphs fWAR leaderboard via Playwright
// Runs daily at 2am ET via GitHub Actions
// Writes to src/live_leaderboard.json

import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_PATH = path.join(__dirname, "..", "src", "live_leaderboard.json");
const YEAR = new Date().getFullYear();
const CAPSOLVER_KEY = process.env.CAPSOLVER_API_KEY || "";

function fgUrl(stats, qual) {
  return `https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=${stats}&lg=all&qual=${qual}&season=${YEAR}&month=0&hand=&team=0&pageItems=8&sortCol=WAR&sortDir=desc`;
}

// Solve Cloudflare Turnstile via Capsolver REST API (no browser extension needed)
async function solveTurnstile(pageUrl, siteKey) {
  if (!CAPSOLVER_KEY) return null;
  console.log("  Calling Capsolver API for Turnstile...");
  const createRes = await fetch("https://api.capsolver.com/createTask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      clientKey: CAPSOLVER_KEY,
      task: { type: "AntiTurnstileTaskProxyLess", websiteURL: pageUrl, websiteKey: siteKey },
    }),
  }).then((r) => r.json());

  if (!createRes.taskId) {
    console.error("  Capsolver task creation failed:", createRes.errorDescription);
    return null;
  }

  for (let i = 0; i < 30; i++) {
    await new Promise((r) => setTimeout(r, 2000));
    const result = await fetch("https://api.capsolver.com/getTaskResult", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clientKey: CAPSOLVER_KEY, taskId: createRes.taskId }),
    }).then((r) => r.json());

    if (result.status === "ready") {
      console.log("  Capsolver solved Turnstile");
      return result.solution?.token;
    }
  }
  console.error("  Capsolver timeout");
  return null;
}

async function scrape() {
  const browser = await chromium.launch({
    headless: true,
    args: [
      "--no-sandbox",
      "--disable-blink-features=AutomationControlled",
      "--disable-dev-shm-usage",
    ],
  });

  const context = await browser.newContext({
    userAgent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    viewport: { width: 1920, height: 1080 },
    locale: "en-US",
  });

  // Mask webdriver property to avoid detection
  await context.addInitScript(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => false });
  });

  const results = { hitters: null, pitchers: null };

  try {
    results.hitters = await fetchLeaderboard(context, "bat");
    results.pitchers = await fetchLeaderboard(context, "pit");
  } finally {
    await context.close();
    await browser.close();
  }

  return results;
}

async function fetchLeaderboard(context, stats) {
  const page = await context.newPage();

  // Intercept API response
  let apiData = null;
  page.on("response", async (response) => {
    const url = response.url();
    if (url.includes("fangraphs.com/api/leaders") && url.includes(`stats=${stats}`) && response.status() === 200) {
      try { apiData = await response.json(); } catch {}
    }
  });

  const leaderboardUrl = `https://www.fangraphs.com/leaders/major-league?pos=all&stats=${stats}&lg=all&qual=0&type=8&season=${YEAR}&month=0&season1=${YEAR}&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=&enddate=&sort=21,d&page=1_8`;

  console.log(`→ Navigating to FanGraphs ${stats} leaderboard...`);

  try {
    await page.goto(leaderboardUrl, { waitUntil: "domcontentloaded", timeout: 30000 });
  } catch (e) {
    console.log(`  Navigation error: ${e.message}`);
  }

  // Check for Cloudflare challenge
  await page.waitForTimeout(3000);
  const title = await page.title();

  if (title.includes("Just a moment") || title.includes("Attention")) {
    console.log("  Cloudflare challenge detected");

    // Try to find Turnstile sitekey and solve via Capsolver API
    const siteKey = await page.evaluate(() => {
      const el = document.querySelector("[data-sitekey], .cf-turnstile");
      return el?.getAttribute("data-sitekey") || null;
    });

    if (siteKey && CAPSOLVER_KEY) {
      const token = await solveTurnstile(leaderboardUrl, siteKey);
      if (token) {
        await page.evaluate((t) => {
          const input = document.querySelector('[name="cf-turnstile-response"]');
          if (input) { input.value = t; input.dispatchEvent(new Event("change", { bubbles: true })); }
          const form = document.querySelector("#challenge-form, form");
          if (form) form.submit();
        }, token);
        await page.waitForTimeout(5000);
      }
    } else {
      // Wait for JS challenge to auto-resolve
      console.log("  Waiting for JS challenge to auto-resolve...");
      try {
        await page.waitForFunction(
          () => !document.title.includes("Just a moment") && !document.title.includes("Attention"),
          { timeout: 20000 }
        );
      } catch {
        console.log("  Challenge did not resolve");
      }
    }
    await page.waitForTimeout(3000);
  }

  // Check if API intercept caught data
  if (apiData?.data?.length > 0) {
    console.log(`  ✓ API intercept: ${apiData.data.length} ${stats} rows`);
    await page.close();
    return apiData;
  }

  // Strategy 2: Direct fetch inside browser (cookies set by navigation)
  console.log("  Trying in-browser fetch...");
  for (const qual of ["y", "0"]) {
    const url = fgUrl(stats, qual);
    const directData = await page.evaluate(async (u) => {
      try { const r = await fetch(u); if (!r.ok) return null; return await r.json(); }
      catch { return null; }
    }, url);

    if (directData?.data?.length > 0) {
      console.log(`  ✓ In-browser fetch (qual=${qual}): ${directData.data.length} rows`);
      await page.close();
      return directData;
    }
  }

  // Strategy 3: Scrape HTML table
  console.log("  Trying HTML table scrape...");
  const rows = await page.evaluate(() => {
    const trs = document.querySelectorAll("table tbody tr, .leaders-major__table tbody tr");
    if (!trs.length) return null;
    return Array.from(trs).slice(0, 8).map(row => {
      const name = row.querySelector("a[href*='/players/']")?.textContent?.trim();
      const team = row.querySelector("a[href*='/teams/']")?.textContent?.trim() ||
                   row.querySelector("td:nth-child(3)")?.textContent?.trim();
      if (!name) return null;
      const cells = Array.from(row.querySelectorAll("td")).map(c => c.textContent.trim());
      return { name, team, cells };
    }).filter(Boolean);
  });

  if (rows?.length > 0) {
    console.log(`  ✓ HTML scrape: ${rows.length} rows`);
    await page.close();
    return { data: rows, scraped: true };
  }

  // Debug: screenshot + page text on failure
  const ssPath = path.join(__dirname, `debug-${stats}.png`);
  await page.screenshot({ path: ssPath, fullPage: true });
  console.log(`  ✗ No data. Screenshot saved: ${ssPath}`);
  const bodyText = await page.evaluate(() => document.body?.innerText?.slice(0, 500));
  console.log(`  Page text: ${bodyText}`);

  await page.close();
  return null;
}

function formatOutput(raw) {
  const parseTm = (t) => (t || "").replace(/<[^>]+>/g, "").trim();

  const hitters = (raw.hitters?.data || []).slice(0, 8).map((p) => ({
    name: p.PlayerName || p.name,
    tm: parseTm(p.Team || p.team || ""),
    war: parseFloat(((p.WAR ?? p.war) || 0).toFixed?.(1) ?? p.WAR),
    hr: Math.round(p.HR || p.hr || 0),
    wrc: Math.round(p["wRC+"] || p.wrc || 0),
  }));

  const pitchers = (raw.pitchers?.data || []).slice(0, 8).map((p) => ({
    name: p.PlayerName || p.name,
    tm: parseTm(p.Team || p.team || ""),
    war: parseFloat(((p.WAR ?? p.war) || 0).toFixed?.(1) ?? p.WAR),
    era: parseFloat(((p.ERA ?? p.era) || 0).toFixed?.(2) ?? p.ERA),
    k9: parseFloat(((p["K/9"] ?? p.k9) || 0).toFixed?.(1) ?? 0),
    ip: parseFloat(((p.IP ?? p.ip) || 0).toFixed?.(1) ?? 0),
  }));

  return { generated: new Date().toISOString(), season: YEAR, hitters, pitchers };
}

// ── MAIN ────────────────────────────────────────────────────────────────
(async () => {
  console.log(`\n🏟  Scraping FanGraphs ${YEAR} fWAR leaderboard...\n`);

  try {
    const raw = await scrape();

    if (!raw.hitters && !raw.pitchers) {
      console.error("✗ No data scraped. Keeping existing file.");
      process.exit(1);
    }

    const output = formatOutput(raw);

    if (output.hitters.length === 0 && output.pitchers.length === 0) {
      console.error("✗ Formatted data empty. Keeping existing file.");
      process.exit(1);
    }

    fs.writeFileSync(OUT_PATH, JSON.stringify(output, null, 2));
    console.log(`\n✅ Wrote ${OUT_PATH}`);
    console.log(`   ${output.hitters.length} hitters, ${output.pitchers.length} pitchers`);
    if (output.hitters[0]) console.log(`   #1 hitter: ${output.hitters[0].name} — ${output.hitters[0].war} fWAR`);
    if (output.pitchers[0]) console.log(`   #1 pitcher: ${output.pitchers[0].name} — ${output.pitchers[0].war} fWAR`);
  } catch (err) {
    console.error("✗ Scrape failed:", err.message);
    process.exit(1);
  }
})();
