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
  return POTD_POOL[idx];
}

function findPlayer(data, name) {
  let p = data.find(d => d.PlayerName === name);
  if (p) return p;
  const parts = name.replace(/Jr\.|Sr\.|III|II/g, '').trim().split(/\s+/);
  p = data.find(d => d.PlayerName && parts.every(part => d.PlayerName.includes(part)));
  if (p) return p;
  const first = parts[0], last = parts[parts.length - 1];
  return data.find(d => d.PlayerName && d.PlayerName.includes(first) && d.PlayerName.includes(last));
}

function projectHitter(player) {
  const S = player.seasons;
  const yrs = Object.keys(S).sort().reverse().slice(0, 3);
  const W = [0.55, 0.30, 0.15];
  let wxba=0,wxslg=0,wbb=0,wk=0,wbrl=0,tw=0,tw2=0,twb=0;
  for (let i = 0; i < yrs.length; i++) {
    const s = S[yrs[i]], w = W[i] || 0.05;
    const pw = w * Math.min(1, (s.pa || 0) / 400);
    const pw2 = w * Math.min(1, (s.pa || 0) / 200);
    if (s.xba) { wxba += s.xba * pw; tw += pw; }
    if (s.xslg) wxslg += s.xslg * pw;
    if (s.bb_pct) { wbb += s.bb_pct * pw2; tw2 += pw2; }
    if (s.k_pct) wk += s.k_pct * pw2;
    if (s.barrel_pct != null) { wbrl += s.barrel_pct * pw; twb += pw; }
  }
  if (tw === 0) return null;
  let pXba = wxba/tw, pXslg = wxslg/tw;
  const pBB = tw2 > 0 ? wbb/tw2 : 0.08;
  const pK = tw2 > 0 ? wk/tw2 : 0.22;
  const pBrl = twb > 0 ? wbrl/twb : 0;
  const age = player.age || 27;
  const pos = player.pos || 'RF';
  const pk = PEAKS[pos] || 28;

  // Pre-peak dev boost
  const ytp = Math.max(0, pk - age);
  pXba *= (1 + Math.min(ytp * 0.012, 0.08));
  pXslg *= (1 + Math.min(ytp * 0.018, 0.12));

  // SLG compression: regress 20% toward league avg
  pXslg = pXslg * 0.80 + 0.405 * 0.20;

  // Post-peak aging
  const avgAgeF = age > 32 ? Math.max(0.95, 1 - (age - 32) * 0.008) : 1.0;
  const slgAgeF = age > 30 ? Math.max(0.88, 1 - (age - 30) * 0.015) : 1.0;

  const avg = Math.max(0.18, Math.min(0.34, pXba * avgAgeF));
  const obp = Math.max(0.26, Math.min(0.45, avg + pBB * 0.65 + 0.015));
  const slg = Math.max(0.30, Math.min(0.70, pXslg * slgAgeF));
  const ops = obp + slg;

  // wRC+ with amplifier
  let db = 0;
  if (pK < 0.15) db += 3; else if (pK > 0.30) db -= 2;
  if (pBB > 0.12) db += 2;
  const rawWrc = ((obp*0.70+slg*0.30)/0.342)*100;
  const wrc = Math.max(60, Math.min(195, Math.round(100 + (rawWrc - 100) * 2.0 + db)));

  // PA and HR
  const bestPA = Math.max(...yrs.map(yr => S[yr]?.pa || 0));
  const pa0 = S[yrs[0]]?.pa || 0;
  const ePA = Math.min(700, Math.max(200, Math.max(pa0, bestPA * 0.90) * 0.97));
  const hr = Math.round(Math.max(0, (pBrl*slgAgeF)/100*(ePA*0.75)*0.38 + ePA*0.010));

  // WAR
  const bat = ((wrc-100)/100)*ePA*0.115;
  const posAdj = (POS_ADJ[pos]||0)*(ePA/600);
  const rep = 20*(ePA/600);
  const war = Math.round(((bat + posAdj + rep) / 9.5) * 10) / 10;

  return { ops: ops.toFixed(3), wrc, hr, war: war.toFixed(1) };
}

async function run() {
  const playerName = getPlayerOfTheDay();
  const isPitcher = PITCHERS.has(playerName);
  console.log('POTD: ' + playerName);

  const stats = isPitcher ? 'pit' : 'bat';
  const [zips, steamer] = await Promise.all([
    fetchJSON('https://www.fangraphs.com/api/projections?type=zips&stats=' + stats + '&pos=all&team=0&players=0&lg=all&season=2026'),
    fetchJSON('https://www.fangraphs.com/api/projections?type=steamer&stats=' + stats + '&pos=all&team=0&players=0&lg=all&season=2026'),
  ]);
  const z = findPlayer(zips, playerName);
  const s = findPlayer(steamer, playerName);
  if (z) console.log('ZiPS: ' + z.PlayerName);
  if (s) console.log('Steamer: ' + s.PlayerName);

  // VIAcast projection
  let viaLine = 'VIAcast: see full projection below';
  if (!isPitcher) {
    const savant = await fetchJSON('https://raw.githubusercontent.com/TrevanVia/baseball-projection-engine/main/src/savant_data.json');
    let sp = null;
    for (const p of Object.values(savant)) {
      if (p.name === playerName || (p.name && playerName.replace(/Jr\.|Sr\./g,'').trim().split(/\s+/).every(part => p.name.includes(part)))) {
        sp = p; break;
      }
    }
    if (sp) {
      sp.age = z ? Math.round(z.Age || 27) : 27;
      // Get position from ZiPS data
      const posMap = {'C':'C','1B':'1B','2B':'2B','3B':'3B','SS':'SS','LF':'LF','CF':'CF','RF':'RF','DH':'DH','OF':'RF'};
      sp.pos = z ? (posMap[z.POS] || 'RF') : 'RF';
      const v = projectHitter(sp);
      if (v) viaLine = 'VIAcast: ' + v.ops + ' OPS | ' + v.wrc + ' wRC+ | ' + v.hr + ' HR | ' + v.war + ' WAR';
    }
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
