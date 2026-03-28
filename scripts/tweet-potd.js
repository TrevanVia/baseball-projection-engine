const puppeteer = require('puppeteer');
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

async function getProjections(playerName, isPitcher) {
  const stats = isPitcher ? 'pit' : 'bat';
  const [zips, steamer] = await Promise.all([
    fetchJSON(`https://www.fangraphs.com/api/projections?type=zips&stats=${stats}&pos=all&team=0&players=0&lg=all&season=2026`),
    fetchJSON(`https://www.fangraphs.com/api/projections?type=steamer&stats=${stats}&pos=all&team=0&players=0&lg=all&season=2026`),
  ]);
  const find = (data) => data.find(p => p.PlayerName === playerName) ||
    data.find(p => p.PlayerName && p.PlayerName.includes(playerName.split(' ').pop()));
  const z = find(zips), s = find(steamer);
  if (isPitcher) {
    return {
      zips: z ? { era: z.ERA?.toFixed(2), war: z.WAR?.toFixed(1), k: Math.round(z.SO||0), ip: Math.round(z.IP||0) } : null,
      steamer: s ? { era: s.ERA?.toFixed(2), war: s.WAR?.toFixed(1), k: Math.round(s.SO||0), ip: Math.round(s.IP||0) } : null,
    };
  }
  return {
    zips: z ? { ops: z.OPS?.toFixed(3), war: z.WAR?.toFixed(1), hr: Math.round(z.HR||0), wrc: Math.round(z['wRC+']||0) } : null,
    steamer: s ? { ops: s.OPS?.toFixed(3), war: s.WAR?.toFixed(1), hr: Math.round(s.HR||0), wrc: Math.round(s['wRC+']||0) } : null,
  };
}

async function run() {
  console.log('Launching browser...');
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox','--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 900 });
  await page.goto('https://viacastbaseball.com', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForSelector('text/PLAYER OF THE DAY', { timeout: 10000 });
  await new Promise(r => setTimeout(r, 3000));
  const potdEl = await page.evaluateHandle(() => {
    const els = document.querySelectorAll('.via-panel');
    for (const el of els) { if (el.textContent.includes('PLAYER OF THE DAY')) return el; }
    return null;
  });
  if (!potdEl) { console.error('POTD panel not found'); await browser.close(); process.exit(1); }
  const info = await page.evaluate(el => {
    const text = el.textContent;
    const h2 = el.querySelector('h2') || el.querySelector('[style*="fontSize"]');
    const name = h2 ? h2.textContent.trim() : '';
    const isPitcher = text.includes('ERA') && text.includes('IP') && !text.includes('OPS');
    return {
      name, isPitcher,
      ops: (text.match(/([\d.]+)\s*OPS/) || [])[1],
      wrc: (text.match(/(\d+)\s*wRC\+/i) || [])[1],
      war: (text.match(/([\d.]+)\s*WAR/) || [])[1],
      hr: (text.match(/(\d+)\s*HR/) || [])[1],
      era: (text.match(/([\d.]+)\s*(?:PROJ )?ERA/) || [])[1],
      ip: (text.match(/(\d+)\s*(?:PROJ )?IP/) || [])[1],
      k: (text.match(/(\d+)\s*K\b/) || [])[1],
    };
  }, potdEl);
  console.log('POTD: ' + info.name);
  await browser.close();
  console.log('Fetching ZiPS/Steamer...');
  const proj = await getProjections(info.name, info.isPitcher);
  let tweet;
  if (info.isPitcher) {
    const via = 'VIAcast: ' + info.era + ' ERA | ' + (info.k||'-') + ' K | ' + info.ip + ' IP | ' + info.war + ' WAR';
    const z = proj.zips ? 'ZiPS: ' + proj.zips.era + ' ERA | ' + proj.zips.k + ' K | ' + proj.zips.ip + ' IP | ' + proj.zips.war + ' WAR' : 'ZiPS: N/A';
    const s = proj.steamer ? 'Steamer: ' + proj.steamer.era + ' ERA | ' + proj.steamer.k + ' K | ' + proj.steamer.ip + ' IP | ' + proj.steamer.war + ' WAR' : 'Steamer: N/A';
    tweet = 'VIAcast Player of the Day: ' + info.name + '\n\n2026 Projections:\n' + via + '\n' + z + '\n' + s + '\n\nviacastbaseball.com';
  } else {
    const via = 'VIAcast: ' + info.ops + ' OPS | ' + info.wrc + ' wRC+ | ' + info.hr + ' HR | ' + info.war + ' WAR';
    const z = proj.zips ? 'ZiPS: ' + proj.zips.ops + ' OPS | ' + proj.zips.wrc + ' wRC+ | ' + proj.zips.hr + ' HR | ' + proj.zips.war + ' WAR' : 'ZiPS: N/A';
    const s = proj.steamer ? 'Steamer: ' + proj.steamer.ops + ' OPS | ' + proj.steamer.wrc + ' wRC+ | ' + proj.steamer.hr + ' HR | ' + proj.steamer.war + ' WAR' : 'Steamer: N/A';
    tweet = 'VIAcast Player of the Day: ' + info.name + '\n\n2026 Projections:\n' + via + '\n' + z + '\n' + s + '\n\nviacastbaseball.com';
  }
  console.log('Tweet:\n' + tweet);
  const client = new TwitterApi({
    appKey: process.env.TWITTER_API_KEY,
    appSecret: process.env.TWITTER_API_SECRET,
    accessToken: process.env.TWITTER_ACCESS_TOKEN,
    accessSecret: process.env.TWITTER_ACCESS_TOKEN_SECRET,
  });
  const result = await client.v2.tweet(tweet);
  console.log('Posted:', 'https://twitter.com/trevanvia/status/' + result.data.id);
}

run().catch(err => { console.error('Error:', err); process.exit(1); });
