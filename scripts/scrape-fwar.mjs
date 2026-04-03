#!/usr/bin/env node
// scripts/scrape-fwar.mjs
// Scrapes FanGraphs fWAR leaderboard via Capsolver + Playwright
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

// ── CAPSOLVER: Solve Cloudflare challenge and get cf_clearance cookie ────────
async function solveCloudflare(targetUrl) {
  if (!CAPSOLVER_KEY) {
    console.log("  No CAPSOLVER_API_KEY set, skipping");
    return null;
  }

  console.log("  Calling Capsolver AntiCloudflareTask...");
  const createRes = await fetch("https://api.capsolver.com/createTask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      clientKey: CAPSOLVER_KEY,
      task: {
        type: "AntiCloudflareTask",
        websiteURL: targetUrl,
        proxy: "",  // proxyless
      },
    }),
  }).then((r) => r.json());

  // If AntiCloudflareTask isn't supported, try AntiTurnstileTaskProxyLess
  if (createRes.errorId && createRes.errorDescription) {
    console.log(`  AntiCloudflareTask failed: ${createRes.errorDescription}`);
    console.log("  Trying AntiTurnstileTaskProxyLess...");
    
    const fallbackRes = await fetch("https://api.capsolver.com/createTask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        clientKey: CAPSOLVER_KEY,
        task: {
          type: "AntiTurnstileTaskProxyLess",
          websiteURL: targetUrl,
          websiteKey: "0x4AAAAAAAA",  // generic Cloudflare key
          metadata: { action: "managed", type: "challenge" },
        },
      }),
    }).then((r) => r.json());
    
    if (fallbackRes.errorId) {
      console.error(`  Fallback also failed: ${fallbackRes.errorDescription}`);
      return null;
    }
    return await pollTask(fallbackRes.taskId);
  }

  if (!createRes.taskId) {
    console.error("  No taskId returned");
    return null;
  }

  return await pollTask(createRes.taskId);
}

async function pollTask(taskId) {
  for (let i = 0; i < 60; i++) {
    await new Promise((r) => setTimeout(r, 3000));
    const result = await fetch("https://api.capsolver.com/getTaskResult", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clientKey: CAPSOLVER_KEY, taskId }),
    }).then((r) => r.json());

    if (result.status === "ready") {
      console.log("  ✓ Capsolver solved challenge");
      return result.solution;
    }
    if (result.status === "failed") {
      console.error("  Capsolver task failed:", result.errorDescription);
      return null;
    }
    if (i % 5 === 0) console.log(`  Polling... (${i * 3}s)`);
  }
  console.error("  Capsolver timeout (180s)");
  return null;
}

// ── MAIN SCRAPE LOGIC ───────────────────────────────────────────────────────
async function scrape() {
  const browser = await chromium.launch({
    headless: true,
    args: ["--no-sandbox", "--disable-blink-features=AutomationControlled", "--disable-dev-shm-usage"],
  });

  const context = await browser.newContext({
    userAgent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    viewport: { width: 1920, height: 1080 },
    locale: "en-US",
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => false });
  });

  const results = { hitters: null, pitchers: null };

  try {
    // Step 1: Try direct navigation first (might work without challenge)
    console.log("→ Attempting direct fetch...");
    results.hitters = await tryDirectFetch(context, "bat");
    results.pitchers = await tryDirectFetch(context, "pit");

    // Step 2: If blocked, solve Cloudflare and retry with cookies
    if (!results.hitters) {
      console.log("\n→ Direct fetch blocked. Solving Cloudflare challenge...");
      const solution = await solveCloudflare("https://www.fangraphs.com/leaders/major-league");

      if (solution) {
        // Apply cookies from solution
        if (solution.cookies) {
          const cookies = parseCookies(solution.cookies, ".fangraphs.com");
          if (cookies.length > 0) {
            await context.addCookies(cookies);
            console.log(`  Applied ${cookies.length} cookies from Capsolver`);
          }
        }
        // Also try cf_clearance directly
        if (solution.cf_clearance) {
          await context.addCookies([{
            name: "cf_clearance",
            value: solution.cf_clearance,
            domain: ".fangraphs.com",
            path: "/",
          }]);
          console.log("  Applied cf_clearance cookie");
        }
        if (solution.token) {
          console.log("  Got solution token (will use in-page)");
        }
      }

      // Retry fetches with new cookies
      console.log("\n→ Retrying with Capsolver cookies...");
      results.hitters = await tryDirectFetch(context, "bat");
      results.pitchers = await tryDirectFetch(context, "pit");
    }

    // Step 3: If still blocked, try full page navigation with cookies set
    if (!results.hitters) {
      console.log("\n→ Trying full page navigation...");
      results.hitters = await tryPageNavigation(context, "bat");
      results.pitchers = await tryPageNavigation(context, "pit");
    }

  } finally {
    await context.close();
    await browser.close();
  }

  return results;
}

// Strategy A: Direct API fetch in a page context
async function tryDirectFetch(context, stats) {
  const page = await context.newPage();
  try {
    for (const qual of ["y", "0"]) {
      const url = fgUrl(stats, qual);
      const data = await page.evaluate(async (u) => {
        try {
          const r = await fetch(u, { credentials: "include" });
          if (!r.ok) return { error: r.status };
          const text = await r.text();
          try { return JSON.parse(text); } catch { return { error: "not json", body: text.slice(0, 200) }; }
        } catch (e) { return { error: e.message }; }
      }, url);

      if (data?.data?.length > 0) {
        console.log(`  ✓ Direct fetch ${stats} (qual=${qual}): ${data.data.length} rows`);
        return data;
      }
      if (data?.error) console.log(`  Direct fetch ${stats} qual=${qual}: ${data.error}`);
    }
  } finally {
    await page.close();
  }
  return null;
}

// Strategy B: Full page navigation with API response intercept
async function tryPageNavigation(context, stats) {
  const page = await context.newPage();
  let apiData = null;

  page.on("response", async (response) => {
    if (response.url().includes("fangraphs.com/api/leaders") &&
        response.url().includes(`stats=${stats}`) &&
        response.status() === 200) {
      try { apiData = await response.json(); } catch {}
    }
  });

  const url = `https://www.fangraphs.com/leaders/major-league?pos=all&stats=${stats}&lg=all&qual=0&type=8&season=${YEAR}&month=0&season1=${YEAR}&ind=0&team=0&rost=0&age=0&filter=&players=0&sort=21,d&page=1_8`;

  try {
    await page.goto(url, { waitUntil: "networkidle", timeout: 30000 });
    await page.waitForTimeout(5000);
  } catch {}

  if (apiData?.data?.length > 0) {
    console.log(`  ✓ Page navigation ${stats}: ${apiData.data.length} rows`);
    await page.close();
    return apiData;
  }

  // Debug output
  const title = await page.title();
  const bodyText = await page.evaluate(() => document.body?.innerText?.slice(0, 300));
  console.log(`  ✗ Page nav ${stats} failed. Title: "${title}"`);
  console.log(`  Page text: ${bodyText}`);
  
  const ssPath = path.join(__dirname, `debug-${stats}.png`);
  await page.screenshot({ path: ssPath, fullPage: true });
  console.log(`  Screenshot: ${ssPath}`);

  await page.close();
  return null;
}

function parseCookies(cookieStr, domain) {
  if (!cookieStr) return [];
  // Handle both string and object formats from Capsolver
  if (typeof cookieStr === "object" && !Array.isArray(cookieStr)) {
    return Object.entries(cookieStr).map(([name, value]) => ({
      name, value: String(value), domain, path: "/",
    }));
  }
  if (typeof cookieStr === "string") {
    return cookieStr.split(";").map(c => c.trim()).filter(Boolean).map(c => {
      const [name, ...rest] = c.split("=");
      return { name: name.trim(), value: rest.join("=").trim(), domain, path: "/" };
    });
  }
  return [];
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
