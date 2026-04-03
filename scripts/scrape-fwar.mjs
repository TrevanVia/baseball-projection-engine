#!/usr/bin/env node
// scripts/scrape-fwar.mjs
// Scrapes FanGraphs fWAR leaderboard via Playwright + Capsolver extension
// Runs daily at 2am ET via GitHub Actions
// Writes to src/live_leaderboard.json

import { chromium } from "playwright";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_PATH = path.join(__dirname, "..", "src", "live_leaderboard.json");
const EXT_DIR = path.join(__dirname, "capsolver-ext");
const YEAR = new Date().getFullYear();

// Inject Capsolver API key into extension
function prepareExtension() {
  const apiKey = process.env.CAPSOLVER_API_KEY;
  if (!apiKey) {
    console.warn("⚠ No CAPSOLVER_API_KEY — running without Turnstile solver");
    return null;
  }
  const bgPath = path.join(EXT_DIR, "background.js");
  let bg = fs.readFileSync(bgPath, "utf8");
  bg = bg.replace(/CAPSOLVER_API_KEY_PLACEHOLDER/g, apiKey);
  // Write to a temp copy so we don't pollute the repo
  const tmpDir = path.join(__dirname, ".capsolver-tmp");
  fs.mkdirSync(tmpDir, { recursive: true });
  fs.cpSync(EXT_DIR, tmpDir, { recursive: true });
  fs.writeFileSync(path.join(tmpDir, "background.js"), bg);
  return tmpDir;
}

// Build FanGraphs API URL
function fgUrl(stats, qual) {
  return `https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=${stats}&lg=all&qual=${qual}&season=${YEAR}&month=0&hand=&team=0&pageItems=8&sortCol=WAR&sortDir=desc`;
}

// Try to fetch leaderboard data — first via API intercept, then page scrape
async function scrape() {
  const extDir = prepareExtension();

  // Launch with extension if available, otherwise bare Chromium
  const launchOpts = {
    headless: false, // Cloudflare often blocks headless
    args: [
      "--no-sandbox",
      "--disable-blink-features=AutomationControlled",
    ],
  };
  if (extDir) {
    launchOpts.args.push(
      `--disable-extensions-except=${extDir}`,
      `--load-extension=${extDir}`
    );
  }

  const browser = await chromium.launchPersistentContext(
    path.join(__dirname, ".browser-data"),
    launchOpts
  );

  const results = { hitters: null, pitchers: null };

  try {
    // ── HITTERS ─────────────────────────────────────────────────────────
    results.hitters = await fetchLeaderboard(browser, "bat");
    // ── PITCHERS ────────────────────────────────────────────────────────
    results.pitchers = await fetchLeaderboard(browser, "pit");
  } finally {
    await browser.close();
    // Clean up temp extension dir
    if (extDir) fs.rmSync(extDir, { recursive: true, force: true });
    fs.rmSync(path.join(__dirname, ".browser-data"), { recursive: true, force: true });
  }

  return results;
}

async function fetchLeaderboard(browser, stats) {
  const page = await browser.newPage();

  // Intercept the API response
  let apiData = null;
  page.on("response", async (response) => {
    const url = response.url();
    if (
      url.includes("fangraphs.com/api/leaders") &&
      url.includes(`stats=${stats}`) &&
      response.status() === 200
    ) {
      try {
        apiData = await response.json();
      } catch {}
    }
  });

  // Strategy 1: Navigate to leaderboard page (triggers API call, Capsolver handles Cloudflare)
  const leaderboardUrl = `https://www.fangraphs.com/leaders/major-league?pos=all&stats=${stats}&lg=all&qual=0&type=8&season=${YEAR}&month=0&season1=${YEAR}&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=&enddate=&sort=21,d&page=1_8`;

  console.log(`→ Navigating to FanGraphs ${stats} leaderboard...`);
  await page.goto(leaderboardUrl, { waitUntil: "networkidle", timeout: 60000 });

  // Wait for Cloudflare challenge to resolve (if any)
  // Capsolver extension handles this automatically
  await page.waitForTimeout(5000);

  // If Cloudflare challenge page is still showing, wait longer
  const title = await page.title();
  if (title.includes("Just a moment") || title.includes("Attention")) {
    console.log("  Cloudflare challenge detected, waiting for Capsolver...");
    await page.waitForFunction(
      () => !document.title.includes("Just a moment") && !document.title.includes("Attention"),
      { timeout: 45000 }
    );
    await page.waitForTimeout(3000);
  }

  // If API intercept caught the data, use it
  if (apiData?.data?.length > 0) {
    console.log(`  ✓ API intercept: ${apiData.data.length} ${stats} rows`);
    await page.close();
    return apiData;
  }

  // Strategy 2: Try direct API fetch within the browser context (cookies are set now)
  console.log("  API intercept missed, trying direct fetch in browser context...");
  for (const qual of ["y", "0"]) {
    const directData = await page.evaluate(async (url) => {
      try {
        const r = await fetch(url);
        if (!r.ok) return null;
        return await r.json();
      } catch { return null; }
    }, fgUrl(stats, qual));

    if (directData?.data?.length > 0) {
      console.log(`  ✓ In-browser fetch (qual=${qual}): ${directData.data.length} rows`);
      await page.close();
      return directData;
    }
  }

  // Strategy 3: Scrape the HTML table as last resort
  console.log("  Trying HTML table scrape...");
  const tableData = await page.evaluate((type) => {
    const rows = document.querySelectorAll(".leaders-major__table tbody tr, table.rgMasterTable tbody tr");
    if (!rows.length) return null;
    return Array.from(rows).slice(0, 8).map(row => {
      const cells = row.querySelectorAll("td");
      if (cells.length < 3) return null;
      // FG table columns vary, but name is typically first text cell
      const name = row.querySelector("a[href*='/players/']")?.textContent?.trim();
      const team = row.querySelector("a[href*='/teams/']")?.textContent?.trim();
      if (!name) return null;
      // Pull all numeric cells
      const nums = Array.from(cells).map(c => c.textContent.trim());
      return { name, team, cells: nums };
    }).filter(Boolean);
  }, stats);

  if (tableData?.length > 0) {
    console.log(`  ✓ HTML scrape: ${tableData.length} rows`);
    await page.close();
    return { data: tableData, scraped: true };
  }

  console.log(`  ✗ No data captured for ${stats}`);
  await page.close();
  return null;
}

// Parse raw FG API data into clean leaderboard format
function formatOutput(raw) {
  const parseTm = (t) => (t || "").replace(/<[^>]+>/g, "").trim();

  const hitters = (raw.hitters?.data || []).slice(0, 8).map((p) => ({
    name: p.PlayerName,
    tm: parseTm(p.Team),
    war: parseFloat((p.WAR || 0).toFixed(1)),
    hr: Math.round(p.HR || 0),
    wrc: Math.round(p["wRC+"] || 0),
  }));

  const pitchers = (raw.pitchers?.data || []).slice(0, 8).map((p) => ({
    name: p.PlayerName,
    tm: parseTm(p.Team),
    war: parseFloat((p.WAR || 0).toFixed(1)),
    era: parseFloat((p.ERA || 0).toFixed(2)),
    k9: parseFloat((p["K/9"] || 0).toFixed(1)),
    ip: parseFloat((p.IP || 0).toFixed(1)),
  }));

  return {
    generated: new Date().toISOString(),
    season: YEAR,
    hitters,
    pitchers,
  };
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
    if (output.hitters[0]) {
      console.log(`   #1 hitter: ${output.hitters[0].name} — ${output.hitters[0].war} fWAR`);
    }
    if (output.pitchers[0]) {
      console.log(`   #1 pitcher: ${output.pitchers[0].name} — ${output.pitchers[0].war} fWAR`);
    }
  } catch (err) {
    console.error("✗ Scrape failed:", err.message);
    process.exit(1);
  }
})();
