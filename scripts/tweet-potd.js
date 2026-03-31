const { TwitterApi } = require('twitter-api-v2');
const https = require('https');

function fetchJSON(url) {
  return new Promise((resolve, reject) => {
    https.get(url, { rejectUnauthorized: false }, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => { try { resolve(JSON.parse(data)); } catch(e) { reject(e); } });
    }).on('error', reject);
  });
}

function norm(s) { return (s||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase(); }

const POTD_POOL = [
  "Gunnar Henderson","Juan Soto","Bobby Witt Jr.","Shohei Ohtani","Paul Skenes",
  "Aaron Judge","Konnor Griffin","Elly De La Cruz","Corbin Carroll","Julio Rodriguez",
  "Fernando Tatis Jr.","Bryce Harper","Mookie Betts","Samuel Basallo","Kyle Tucker",
  "Ronald Acuna Jr.","Corey Seager","Freddie Freeman","Mike Trout","Roki Sasaki",
  "Jackson Chourio","Adley Rutschman","Yordan Alvarez","Tarik Skubal","Garrett Crochet",
  "Riley Greene","Jackson Merrill","James Wood","Cal Raleigh","Kevin McGonigle",
  "Vladimir Guerrero Jr.","Rafael Devers","Jose Ramirez","Francisco Lindor","Kyle Schwarber",
  "Trea Turner","Bo Bichette","Pete Alonso","Willy Adames","Max Clark",
  "Anthony Volpe","CJ Abrams","Jarren Duran","Roman Anthony","JJ Wetherholt",
  "Jackson Holliday","Dylan Crews","Evan Carter","Corbin Burnes","Zack Wheeler",
  "Matt McLain","Dansby Swanson","Marcus Semien","Alex Bregman","Manny Machado",
  "Pete Crow-Armstrong","Steven Kwan","Michael Harris II","Chris Sale","Cole Ragans",
  "Logan Webb","Dylan Cease","Colt Keith","Zach Neto","Matt Olson",
  "Kerry Carpenter","Bryson Stott","Cody Bellinger","Maikel Garcia","Aidan Miller",
  "Garrett Crochet",
];
const PITCHERS = new Set(["Paul Skenes","Tarik Skubal","Garrett Crochet","Roki Sasaki",
  "Corbin Burnes","Zack Wheeler","Chris Sale","Cole Ragans","Logan Webb","Dylan Cease"]);
const PEAKS = {C:27,'1B':29,'2B':28,'3B':28,SS:28,LF:28,CF:27,RF:28,DH:30};
const POS_ADJ = {C:-1,'1B':-12.5,'2B':2.5,'3B':2.5,SS:7.5,LF:-7.5,CF:2.5,RF:-5,DH:-17.5};

function getPlayerOfTheDay() {
  const now = new Date();
  const daysSinceEpoch = Math.floor(now.getTime() / 86400000);
  const launchDay = 20518;
  const idx = Math.abs(daysSinceEpoch - launchDay) % POTD_POOL.length;
  console.log('Day index: ' + idx);
  return POTD_POOL[idx];
}

function findPlayer(data, name, label) {
  const n = norm(name);
  const parts = n.replace(/jr|sr|iii|ii/g,'').trim().split(/\s+/).filter(p=>p.length>1);
  for (const d of data) {
    if (norm(d.PlayerName) === n) { console.log(label + ' exact: ' + d.PlayerName); return d; }
  }
  for (const d of data) {
    if (parts.every(p => norm(d.PlayerName).includes(p))) { console.log(label + ' parts: ' + d.PlayerName); return d; }
  }
  console.log(label + ': NO MATCH for "' + name + '"');
  return null;
}

function findInData(data, name) {
  const parts = norm(name).replace(/jr|sr|iii|ii/g,'').trim().split(/\s+/).filter(p=>p.length>1);
  // Check by value.name (savant data)
  for (const p of Object.values(data)) {
    if (p.name && parts.every(part => norm(p.name).includes(part))) return p;
  }
  // Check by key name (fg_pitcher_data uses name as key)
  for (const [k, v] of Object.entries(data)) {
    if (parts.every(part => norm(k).includes(part))) { v.name = v.name || k; return v; }
  }
  return null;
}

function projectHitter(player) {
  const S = player.seasons;
  const yrs = Object.keys(S).sort().reverse().slice(0, 3);
  const W = [0.55, 0.30, 0.15];
  let wxba=0,wxslg=0,wxwoba=0,wbb=0,wk=0,wbrl=0,wev=0,wspd=0,woaa=0,tw=0,tw2=0,twb=0,twe=0,tws=0,two=0;
  for (let i = 0; i < yrs.length; i++) {
    const s = S[yrs[i]], w = W[i] || 0.05;
    const pw = w * Math.min(1, (s.pa || 0) / 400);
    const pw2 = w * Math.min(1, (s.pa || 0) / 200);
    if (s.xba) { wxba += s.xba * pw; tw += pw; }
    if (s.xslg) wxslg += s.xslg * pw;
    if (s.xwoba) wxwoba += s.xwoba * pw;
    if (s.bb_pct) { wbb += s.bb_pct * pw2; tw2 += pw2; }
    if (s.k_pct) wk += s.k_pct * pw2;
    if (s.barrel_pct != null) { wbrl += s.barrel_pct * pw; twb += pw; }
    if (s.avg_ev) { wev += s.avg_ev * pw; twe += pw; }
  }
  // Sprint speed and OAA from player object
  if (player.sprint_speed) { wspd = player.sprint_speed; tws = 1; }
  if (player.oaa != null) { woaa = player.oaa; two = 1; }
  if (tw === 0) return null;
  let pXba = wxba/tw, pXslg = wxslg/tw;
  const pXwoba = tw > 0 ? wxwoba/tw : 0;
  const pBB = tw2 > 0 ? wbb/tw2 : 0.08;
  const pK = tw2 > 0 ? wk/tw2 : 0.22;
  const pBrl = twb > 0 ? wbrl/twb : 0;
  const pEV = twe > 0 ? wev/twe : 88;
  const age = player.age || 27, pos = player.pos || 'RF', pk = PEAKS[pos] || 28;
  const ytp = Math.max(0, pk - age);
  // Pre-peak development boost (matches engine)
  pXba *= (1 + Math.min(ytp * 0.012, 0.08));
  pXslg *= (1 + Math.min(ytp * 0.018, 0.12));
  // SLG compression (matches engine: 5% deflation + 20% regression to mean)
  pXslg = pXslg * 0.95 * 0.80 + 0.405 * 0.20;
  const avgAgeF = age > 32 ? Math.max(0.95, 1 - (age - 32) * 0.008) : 1.0;
  const slgAgeF = age > 30 ? Math.max(0.88, 1 - (age - 30) * 0.015) : 1.0;
  const avg = Math.max(0.18, Math.min(0.34, pXba * avgAgeF));
  const obp = Math.max(0.26, Math.min(0.45, avg + pBB * 0.65 + 0.015));
  const slg = Math.max(0.30, Math.min(0.70, pXslg * slgAgeF));
  const ops = obp + slg;
  // wRC+ using wOBA approximation (matches engine)
  const LG_WOBA = 0.305, WOBA_SCALE = 1.25, LG_R_PER_PA = 0.115;
  const estWoba = pXwoba > 0 ? pXwoba : (obp * 0.70 + slg * 0.30) * 0.72;
  const wrcRaw = Math.round(((estWoba - LG_WOBA) / WOBA_SCALE / LG_R_PER_PA + 1) * 100);
  // Amplifier calibrated to match ZiPS targets
  const wrc = Math.max(60, Math.min(195, Math.round(100 + (wrcRaw - 100) * 1.35)));
  const bestPA = Math.max(...yrs.map(yr => S[yr]?.pa || 0));
  const pa0 = S[yrs[0]]?.pa || 0;
  const ePA = Math.min(700, Math.max(200, Math.max(pa0, bestPA * 0.90) * 0.97));
  const hr = Math.round(Math.max(0, (pBrl*slgAgeF)/100*(ePA*0.75)*0.38 + ePA*0.010));
  // WAR: batting + defense + baserunning + positional + replacement (matches engine)
  const batRuns = ((wrc - 100) / 100) * ePA * LG_R_PER_PA;
  const oaa = two > 0 ? woaa : 0;
  const defRuns = oaa * 0.85 * 0.80 * (ePA / 600);
  const spd = tws > 0 ? wspd : 27;
  const bsr = (spd > 27 ? (spd - 27) * 1.5 : (spd - 27) * 1.0) * 0.75 * (ePA / 600);
  const posRuns = (POS_ADJ[pos] || 0) * (ePA / 600);
  const repRuns = 20 * (ePA / 600);
  const war = Math.round(((batRuns + defRuns + bsr + posRuns + repRuns) / 9.5) * 10) / 10;
  return { ops: ops.toFixed(3), wrc, hr, war: war.toFixed(1) };
}

function projectPitcher(savantP, fgP) {
  const fgS = fgP ? fgP.seasons : {};
  const savS = savantP ? savantP.seasons : {};
  const yrs = Object.keys({...fgS, ...savS}).sort().reverse().slice(0, 3);
  const W = [0.55, 0.30, 0.15];
  let wera=0, wk=0, wbb=0, tw=0, tw2=0, bestIP=0;

  for (let i = 0; i < yrs.length; i++) {
    const fg = fgS[yrs[i]] || {};
    const sav = savS[yrs[i]] || {};
    const w = W[i] || 0.05;
    const ip = fg.ip || 0;
    const pw = w * Math.min(1, ip / 120);

    // ERA anchor: SIERA first, then xFIP, then xERA, then FIP, then ERA
    const anchor = fg.siera || fg.xfip || sav.xera || fg.fip || fg.era || 4.50;
    if (pw > 0) { wera += anchor * pw; tw += pw; }

    const pw2 = w * Math.min(1, ip / 80);
    if (fg.k_pct) { wk += fg.k_pct * pw2; tw2 += pw2; }
    if (fg.bb_pct) wbb += fg.bb_pct * pw2;

    if (ip >= 100) bestIP = Math.max(bestIP, ip);
  }

  if (tw === 0) return null;
  const era = wera / tw;
  const kpct = tw2 > 0 ? wk / tw2 : 20;
  const bbpct = tw2 > 0 ? wbb / tw2 : 8;

  // IP: best full season, age-adjusted, cap 210
  const age = savantP?.age || 27;
  const ipFactor = age <= 27 ? 1.03 : age <= 30 ? 1.00 : age <= 33 ? 0.97 : 0.93;
  const ip = Math.min(210, Math.round((bestIP || 160) * ipFactor));

  // K count: K% * estimated BFP (IP * 4.1)
  const bfp = ip * 3.8;
  const k = Math.round(kpct / 100 * bfp);

  // WAR: (replacement_RA9 - projected_RA9) * IP/9 / runs_per_win
  const war = Math.round((5.34 - era) / 9.5 * ip / 9 * 10) / 10;

  return { era: era.toFixed(2), k, ip, war: war.toFixed(1) };
}

async function run() {
  const playerName = getPlayerOfTheDay();
  const isPitcher = PITCHERS.has(playerName);
  console.log('POTD: ' + playerName + ' (' + (isPitcher ? 'pitcher' : 'hitter') + ')');

  const stats = isPitcher ? 'pit' : 'bat';
  console.log('Fetching projections...');
  const [zips, steamer] = await Promise.all([
    fetchJSON('https://www.fangraphs.com/api/projections?type=zips&stats=' + stats + '&pos=all&team=0&players=0&lg=all&season=2026'),
    fetchJSON('https://www.fangraphs.com/api/projections?type=steamer&stats=' + stats + '&pos=all&team=0&players=0&lg=all&season=2026'),
  ]);
  const z = findPlayer(zips, playerName, 'ZiPS');
  const s = findPlayer(steamer, playerName, 'Steamer');

  // Read precomputed projections (generated by precompute-potd.mjs)
  let viaLine;
  try {
    const precomputed = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'src', 'potd-projections.json'), 'utf-8'));
    const v = precomputed[playerName];
    if (v && v.isPitcher) {
      viaLine = 'VIAcast: ' + v.era + ' ERA | ' + v.k + ' K | ' + v.ip + ' IP | ' + v.baseWAR + ' WAR';
    } else if (v) {
      viaLine = 'VIAcast: ' + v.ops + ' OPS | ' + v.wRCPlus + ' wRC+ | ' + v.hr + ' HR | ' + v.baseWAR + ' WAR';
    } else {
      viaLine = 'VIAcast: see full projection at viacastbaseball.com';
    }
  } catch (e) {
    console.log('Warning: Could not read potd-projections.json:', e.message);
    viaLine = 'VIAcast: see full projection at viacastbaseball.com';
  }

  let zLine, sLine;
  if (isPitcher) {
    zLine = z ? 'ZiPS: ' + z.ERA.toFixed(2) + ' ERA | ' + Math.round(z.SO) + ' K | ' + Math.round(z.IP) + ' IP | ' + z.WAR.toFixed(1) + ' WAR' : 'ZiPS: N/A';
    sLine = s ? 'Steamer: ' + s.ERA.toFixed(2) + ' ERA | ' + Math.round(s.SO) + ' K | ' + Math.round(s.IP) + ' IP | ' + s.WAR.toFixed(1) + ' WAR' : 'Steamer: N/A';
  } else {
    zLine = z ? 'ZiPS: ' + z.OPS.toFixed(3) + ' OPS | ' + Math.round(z['wRC+']) + ' wRC+ | ' + Math.round(z.HR) + ' HR | ' + z.WAR.toFixed(1) + ' WAR' : 'ZiPS: N/A';
    sLine = s ? 'Steamer: ' + s.OPS.toFixed(3) + ' OPS | ' + Math.round(s['wRC+']) + ' wRC+ | ' + Math.round(s.HR) + ' HR | ' + s.WAR.toFixed(1) + ' WAR' : 'Steamer: N/A';
  }

  const tweet = 'VIAcast Player of the Day: ' + playerName + '\n\n2026 Projections:\n' + viaLine + '\n' + zLine + '\n' + sLine + '\n\nviacastbaseball.com';
  console.log('\n' + tweet + '\n');

  const client = new TwitterApi({
    appKey: process.env.TWITTER_API_KEY,
    appSecret: process.env.TWITTER_API_SECRET,
    accessToken: process.env.TWITTER_ACCESS_TOKEN,
    accessSecret: process.env.TWITTER_ACCESS_TOKEN_SECRET,
  });
  const result = await client.v2.tweet(tweet);
  console.log('Posted: https://twitter.com/trevanvia/status/' + result.data.id);
}

run().catch(err => { console.error('Error:', err); process.exit(1); });
