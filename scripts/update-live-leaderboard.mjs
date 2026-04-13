#!/usr/bin/env node
// scripts/update-live-leaderboard.mjs
// Run locally: node scripts/update-live-leaderboard.mjs
// Fetches FanGraphs fWAR leaderboard and writes to src/live_leaderboard.json
// Works from your Mac because your browser/network isn't blocked by Cloudflare

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import https from 'https';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(__dirname, '..', 'src', 'live_leaderboard.json');
const YEAR = new Date().getFullYear();

function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://www.fangraphs.com/leaders/major-league',
      }
    }, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); }
        catch { reject(new Error(`Not JSON (${res.statusCode}): ${data.slice(0, 100)}`)); }
      });
    }).on('error', reject);
  });
}

const parseTm = t => (t || '').replace(/<[^>]+>/g, '').trim();

async function run() {
  console.log(`\nFetching ${YEAR} fWAR leaderboard from FanGraphs...\n`);

  let hitters = [], pitchers = [];

  for (const qual of ['y', '0']) {
    if (hitters.length > 0) break;
    try {
      const bat = await fetchJSON(`https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=bat&lg=all&qual=${qual}&season=${YEAR}&month=0&hand=&team=0&pageItems=8&sortCol=WAR&sortDir=desc`);
      const h = (bat.data || []).slice(0, 8);
      if (h.length > 0) {
        hitters = h.map(p => ({
          name: p.PlayerName, tm: parseTm(p.Team),
          war: +p.WAR.toFixed(1), hr: Math.round(p.HR || 0), wrc: Math.round(p['wRC+'] || 0),
        }));
        console.log(`✓ Hitters (qual=${qual}): ${hitters.length} rows`);
      }
    } catch (e) { console.log(`  Hitters qual=${qual}: ${e.message}`); }
  }

  for (const qual of ['y', '0']) {
    if (pitchers.length > 0) break;
    try {
      const pit = await fetchJSON(`https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=pit&lg=all&qual=${qual}&season=${YEAR}&month=0&hand=&team=0&pageItems=8&sortCol=WAR&sortDir=desc`);
      const p = (pit.data || []).slice(0, 8);
      if (p.length > 0) {
        pitchers = p.map(x => ({
          name: x.PlayerName, tm: parseTm(x.Team),
          war: +x.WAR.toFixed(1), era: +x.ERA.toFixed(2), k9: +(x['K/9'] || 0).toFixed(1), ip: +x.IP.toFixed(1),
        }));
        console.log(`✓ Pitchers (qual=${qual}): ${pitchers.length} rows`);
      }
    } catch (e) { console.log(`  Pitchers qual=${qual}: ${e.message}`); }
  }

  if (hitters.length === 0 && pitchers.length === 0) {
    console.error('\n✗ No data fetched. FanGraphs may be blocking. Try again later.');
    process.exit(1);
  }

  const output = { generated: new Date().toISOString(), season: YEAR, hitters, pitchers };
  fs.writeFileSync(OUT, JSON.stringify(output, null, 2));

  console.log(`\n✅ Wrote ${OUT}`);
  if (hitters[0]) console.log(`   #1 hitter: ${hitters[0].name} — ${hitters[0].war} fWAR`);
  if (pitchers[0]) console.log(`   #1 pitcher: ${pitchers[0].name} — ${pitchers[0].war} fWAR`);
  console.log(`\nRun: npm run build && vercel --prod`);
}

run().catch(e => { console.error('Error:', e.message); process.exit(1); });
