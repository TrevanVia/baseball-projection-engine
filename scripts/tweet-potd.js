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

function getPlayerOfTheDay() {
  const now = new Date();
  const daysSinceEpoch = Math.floor(now.getTime() / 86400000);
  const launchDay = 20518;
  const idx = Math.abs(daysSinceEpoch - launchDay) % POTD_POOL.length;
  return POTD_POOL[idx];
}

function findPlayer(data, name) {
  // Exact match first
  let p = data.find(d => d.PlayerName === name);
  if (p) return p;
  // Match all name parts (handles accents, suffixes like Jr.)
  const parts = name.replace(/Jr\.|Sr\.|III|II/g, '').trim().split(/\s+/);
  p = data.find(d => d.PlayerName && parts.every(part => d.PlayerName.includes(part)));
  if (p) return p;
  // Last resort: first + last name contains
  const first = parts[0], last = parts[parts.length - 1];
  return data.find(d => d.PlayerName && d.PlayerName.includes(first) && d.PlayerName.includes(last));
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

  const z = findPlayer(zips, playerName);
  const s = findPlayer(steamer, playerName);

  if (z) console.log('ZiPS match: ' + z.PlayerName);
  if (s) console.log('Steamer match: ' + s.PlayerName);

  let zLine, sLine;
  if (isPitcher) {
    zLine = z ? 'ZiPS: ' + z.ERA.toFixed(2) + ' ERA | ' + Math.round(z.SO) + ' K | ' + Math.round(z.IP) + ' IP | ' + z.WAR.toFixed(1) + ' WAR' : 'ZiPS: N/A';
    sLine = s ? 'Steamer: ' + s.ERA.toFixed(2) + ' ERA | ' + Math.round(s.SO) + ' K | ' + Math.round(s.IP) + ' IP | ' + s.WAR.toFixed(1) + ' WAR' : 'Steamer: N/A';
  } else {
    zLine = z ? 'ZiPS: ' + z.OPS.toFixed(3) + ' OPS | ' + Math.round(z['wRC+']) + ' wRC+ | ' + Math.round(z.HR) + ' HR | ' + z.WAR.toFixed(1) + ' WAR' : 'ZiPS: N/A';
    sLine = s ? 'Steamer: ' + s.OPS.toFixed(3) + ' OPS | ' + Math.round(s['wRC+']) + ' wRC+ | ' + Math.round(s.HR) + ' HR | ' + s.WAR.toFixed(1) + ' WAR' : 'Steamer: N/A';
  }

  const tweet = 'VIAcast Player of the Day: ' + playerName + '\n\n2026 Projections:\n' + zLine + '\n' + sLine + '\n\nFull VIAcast projection at viacastbaseball.com';

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
