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

// Same POTD pool and logic as the site
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

// Known pitchers in the pool
const PITCHERS = new Set(["Paul Skenes","Tarik Skubal","Garrett Crochet","Roki Sasaki",
  "Corbin Burnes","Zack Wheeler","Chris Sale","Cole Ragans","Logan Webb","Dylan Cease"]);

function getPlayerOfTheDay() {
  const now = new Date();
  const daysSinceEpoch = Math.floor(now.getTime() / 86400000);
  const launchDay = 20518;
  const idx = Math.abs(daysSinceEpoch - launchDay) % POTD_POOL.length;
  return POTD_POOL[idx];
}

async function getProjections(playerName, isPitcher) {
  const stats = isPitcher ? 'pit' : 'bat';
  const [zips, steamer] = await Promise.all([
    fetchJSON('https://www.fangraphs.com/api/projections?type=zips&stats=' + stats + '&pos=all&team=0&players=0&lg=all&season=2026'),
    fetchJSON('https://www.fangraphs.com/api/projections?type=steamer&stats=' + stats + '&pos=all&team=0&players=0&lg=all&season=2026'),
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

async function getVIAcastStats(playerName) {
  // Scrape the player card page directly
  const puppeteer = require('puppeteer');
  const browser = await puppeteer.launch({ headless: 'new', args: ['--no-sandbox','--disable-setuid-sandbox'] });
  const page = await browser.newPage();
  const slug = playerName.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  const url = 'https://viacastbaseball.com/player/' + slug;
  console.log('Fetching: ' + url);
  await page.goto(url, { waitUntil: 'networkidle2', timeout: 30000 });
  await new Promise(r => setTimeout(r, 4000));

  const stats = await page.evaluate(() => {
    const text = document.body.textContent;
    return {
      ops: (text.match(/([\d.]+)\s*OPS/) || [])[1],
      wrc: (text.match(/(\d+)\s*wRC\+/i) || [])[1],
      war: (text.match(/([\d.]+)\s*(?:Proj )?WAR/) || [])[1],
      hr: (text.match(/(\d+)\s*HR/) || [])[1],
      era: (text.match(/([\d.]+)\s*(?:Proj )?ERA/) || [])[1],
      ip: (text.match(/(\d+)\s*(?:Proj )?IP/) || [])[1],
      k: (text.match(/(\d+)\s*K\b/) || [])[1],
    };
  });
  await browser.close();
  return stats;
}

async function run() {
  const playerName = getPlayerOfTheDay();
  const isPitcher = PITCHERS.has(playerName);
  console.log('POTD: ' + playerName + ' (' + (isPitcher ? 'pitcher' : 'hitter') + ')');

  console.log('Fetching VIAcast stats...');
  const via = await getVIAcastStats(playerName);
  console.log('VIAcast:', via);

  console.log('Fetching ZiPS/Steamer...');
  const proj = await getProjections(playerName, isPitcher);

  let tweet;
  if (isPitcher) {
    const vLine = 'VIAcast: ' + (via.era||'-') + ' ERA | ' + (via.k||'-') + ' K | ' + (via.ip||'-') + ' IP | ' + (via.war||'-') + ' WAR';
    const zLine = proj.zips ? 'ZiPS: ' + proj.zips.era + ' ERA | ' + proj.zips.k + ' K | ' + proj.zips.ip + ' IP | ' + proj.zips.war + ' WAR' : 'ZiPS: N/A';
    const sLine = proj.steamer ? 'Steamer: ' + proj.steamer.era + ' ERA | ' + proj.steamer.k + ' K | ' + proj.steamer.ip + ' IP | ' + proj.steamer.war + ' WAR' : 'Steamer: N/A';
    tweet = 'VIAcast Player of the Day: ' + playerName + '\n\n2026 Projections:\n' + vLine + '\n' + zLine + '\n' + sLine + '\n\nviacastbaseball.com';
  } else {
    const vLine = 'VIAcast: ' + (via.ops||'-') + ' OPS | ' + (via.wrc||'-') + ' wRC+ | ' + (via.hr||'-') + ' HR | ' + (via.war||'-') + ' WAR';
    const zLine = proj.zips ? 'ZiPS: ' + proj.zips.ops + ' OPS | ' + proj.zips.wrc + ' wRC+ | ' + proj.zips.hr + ' HR | ' + proj.zips.war + ' WAR' : 'ZiPS: N/A';
    const sLine = proj.steamer ? 'Steamer: ' + proj.steamer.ops + ' OPS | ' + proj.steamer.wrc + ' wRC+ | ' + proj.steamer.hr + ' HR | ' + proj.steamer.war + ' WAR' : 'Steamer: N/A';
    tweet = 'VIAcast Player of the Day: ' + playerName + '\n\n2026 Projections:\n' + vLine + '\n' + zLine + '\n' + sLine + '\n\nviacastbaseball.com';
  }

  console.log('\nTweet:\n' + tweet + '\n');

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
