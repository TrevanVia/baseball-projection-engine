#!/usr/bin/env node
/**
 * Builds src/prospects.json for the Prospects tab from the FV grades in
 * src/engine.js (FV_BY_NAME / FV_LOOKUP).
 *
 *   node scripts/build-prospects.mjs
 *
 * For each graded player: MLB id, organization, position, age in PROJ_SEASON,
 * highest level reached last season, and whether they've exceeded rookie
 * limits (130 MLB AB or 50 MLB IP) — graduated players drop off the list.
 * Re-run after updating FV grades each winter.
 */
import fs from "fs";
import path from "path";
import os from "os";
import { fileURLToPath, pathToFileURL } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.join(__dirname, "..");
const API = "https://statsapi.mlb.com/api/v1";
const args = Object.fromEntries(process.argv.slice(2).map(a => { const [k, v] = a.replace(/^--/, "").split("="); return [k, v ?? true]; }));

async function getJSON(url) {
  for (let i = 0; i < 3; i++) {
    try { const r = await fetch(url, { signal: AbortSignal.timeout(30000) }); if (r.ok) return r.json(); } catch {}
    await new Promise(r => setTimeout(r, 800 * (i + 1)));
  }
  return null;
}
// Name collisions the youngest-match rule gets wrong (name -> MLBAM id).
const ID_OVERRIDES = { "Jared Jones": 683003 };
const norm = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().trim();
const LEVELS = { 1: "MLB", 11: "AAA", 12: "AA", 13: "A+", 14: "A", 16: "ROK" };
const ORDER = ["ROK", "A", "A+", "AA", "AAA", "MLB"];

async function main() {
  let bundle = args["engine-bundle"];
  if (!bundle) {
    const { build } = await import("esbuild");
    bundle = path.join(os.tmpdir(), `viacast-engine-${process.pid}.mjs`);
    await build({ entryPoints: [path.join(ROOT, "src/engine.js")], bundle: true, platform: "node", format: "esm", outfile: bundle, logLevel: "error" });
  }
  const E = await import(pathToFileURL(path.resolve(bundle)).href);
  const season = E.PROJ_SEASON, last = season - 1;

  // One entry per player: FV_LOOKUP (by id) wins over FV_BY_NAME; names deduped ignoring accents.
  const byName = new Map();
  for (const [name, fv] of Object.entries(E.FV_BY_NAME)) if (!byName.has(norm(name))) byName.set(norm(name), { name, fv });

  const teams = {};
  const tl = await getJSON(`${API}/teams?sportId=1&season=${last}`);
  for (const t of tl?.teams || []) teams[t.id] = t.abbreviation;

  const out = [];
  for (const { name, fv } of byName.values()) {
    const s = await getJSON(`${API}/people/search?names=${encodeURIComponent(name)}&hydrate=currentTeam`);
    const cands = (s?.people || []).filter(p => norm(p.fullName) === norm(name));
    // Prefer the id that FV_LOOKUP knows about, else the youngest match (prospects).
    const p = cands.find(c => c.id === ID_OVERRIDES[name]) || cands.find(c => E.FV_LOOKUP[c.id]) || cands.sort((a, b) => (b.birthDate || "").localeCompare(a.birthDate || ""))[0];
    if (!p) { console.log(`  ? not found: ${name}`); continue; }
    const fvFinal = E.FV_LOOKUP[p.id] || fv;
    const isPitcher = p.primaryPosition?.code === "1";
    // Career MLB totals for rookie status; last season's levels for "highest level".
    const car = await getJSON(`${API}/people/${p.id}/stats?stats=career&group=hitting,pitching&sportId=1`);
    let ab = 0, ip = 0;
    for (const g of car?.stats || []) {
      const st = g.splits?.[0]?.stat || {};
      if (g.group?.displayName === "hitting") ab = st.atBats || 0;
      if (g.group?.displayName === "pitching") { const x = parseFloat(st.inningsPitched || 0); ip = Math.floor(x) + Math.round((x % 1) * 10) / 3; }
    }
    const grp = isPitcher ? "pitching" : "hitting";
    const [yrMil, yrMlb] = await Promise.all([
      getJSON(`${API}/people/${p.id}/stats?stats=yearByYear&group=${grp}&leagueListId=milb_all`),
      getJSON(`${API}/people/${p.id}/stats?stats=yearByYear&group=${grp}&sportId=1`),
    ]);
    let level = null;
    for (const sp of [...(yrMil?.stats?.[0]?.splits || []), ...(yrMlb?.stats?.[0]?.splits || [])].map(sp => ({ ...sp, sport: sp.sport || { id: 1 } }))) {
      if (sp.season !== String(last)) continue;
      const lv = LEVELS[sp.sport?.id]; if (lv && (!level || ORDER.indexOf(lv) > ORDER.indexOf(level))) level = lv;
    }
    const orgId = p.currentTeam?.parentOrgId || p.currentTeam?.id;
    out.push({
      id: p.id, name: p.fullName, fv: fvFinal, pos: E.posLabel(p.primaryPosition?.code), isPitcher,
      org: teams[orgId] || null, age: E.projAge(p), level,
      graduated: isPitcher ? ip > 50 : ab > 130, mlbAB: ab, mlbIP: Math.round(ip * 10) / 10,
    });
    await new Promise(r => setTimeout(r, 60));
  }
  out.sort((a, b) => b.fv - a.fv || a.age - b.age);
  const file = path.join(ROOT, "src", "prospects.json");
  fs.writeFileSync(file, JSON.stringify({ generated: new Date().toISOString(), season, fvSource: "FanGraphs/ESPN consensus, Feb 2026", players: out }, null, 1));
  const live = out.filter(p => !p.graduated);
  console.log(`Wrote ${file}: ${out.length} graded, ${live.length} still prospects, ${out.length - live.length} graduated`);
}
main().catch(e => { console.error(e); process.exit(1); });
