/**
 * VIAcast Scheduled Tweet Poster
 * 
 * Picks the next unposted tweet from scheduled-tweets.js and posts it.
 * Tracks which tweets have been posted via a simple JSON state file.
 * 
 * Usage:
 *   node scripts/post-scheduled-tweet.js          # Post next tweet
 *   node scripts/post-scheduled-tweet.js --dry-run # Preview without posting
 *   node scripts/post-scheduled-tweet.js --list    # Show all tweets and status
 *   node scripts/post-scheduled-tweet.js --reset   # Reset posted state
 * 
 * GitHub Actions runs this on a cron schedule (see .github/workflows/scheduled-tweets.yml)
 * 
 * Required env vars (GitHub Secrets):
 *   TWITTER_APP_KEY, TWITTER_APP_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
 */

const { TwitterApi } = require('twitter-api-v2');
const fs = require('fs');
const path = require('path');

const TWEETS = require('./scheduled-tweets.js');
const STATE_FILE = path.join(__dirname, '..', '.tweet-state.json');
const args = process.argv.slice(2);

// ── STATE MANAGEMENT ─────────────────────────────────────────────────────────
function loadState() {
  try {
    return JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
  } catch {
    return { posted: [], lastPostedAt: null };
  }
}

function saveState(state) {
  fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
}

// ── LIST MODE ────────────────────────────────────────────────────────────────
if (args.includes('--list')) {
  const state = loadState();
  console.log(`\n📋 Scheduled Tweets (${TWEETS.length} total, ${state.posted.length} posted)\n`);
  TWEETS.forEach((t, i) => {
    const posted = state.posted.includes(t.id);
    const status = posted ? '✅' : '⏳';
    const preview = t.text.split('\n')[0].substring(0, 80);
    console.log(`${status} ${String(i + 1).padStart(2)}. [${t.category}] ${t.id}`);
    console.log(`      ${preview}...`);
  });
  console.log(`\nNext up: ${TWEETS.find(t => !state.posted.includes(t.id))?.id || 'ALL POSTED'}`);
  process.exit(0);
}

// ── RESET MODE ───────────────────────────────────────────────────────────────
if (args.includes('--reset')) {
  saveState({ posted: [], lastPostedAt: null });
  console.log('🔄 Tweet state reset. All tweets will be re-queued.');
  process.exit(0);
}

// ── POST MODE ────────────────────────────────────────────────────────────────
async function main() {
  const state = loadState();
  const DRY_RUN = args.includes('--dry-run');

  // Find next unposted tweet
  const next = TWEETS.find(t => !state.posted.includes(t.id));
  if (!next) {
    console.log('✅ All scheduled tweets have been posted!');
    // Reset and loop — start over
    console.log('🔄 Resetting queue for next cycle...');
    saveState({ posted: [], lastPostedAt: state.lastPostedAt });
    return;
  }

  console.log(`\n📝 Next tweet: [${next.category}] ${next.id}`);
  console.log(`─────────────────────────────────────`);
  console.log(next.text);
  console.log(`─────────────────────────────────────`);
  console.log(`Characters: ${next.text.length}/280`);

  // X Premium allows up to 4,000 characters. Standard accounts: 280.
  // Set TWEET_CHAR_LIMIT env var to 280 if not on Premium.
  const charLimit = parseInt(process.env.TWEET_CHAR_LIMIT || '4000');
  
  if (next.text.length > charLimit) {
    console.log(`⚠️  Tweet exceeds ${charLimit} characters! Skipping.`);
    state.posted.push(next.id); // Skip it
    saveState(state);
    return;
  }

  if (DRY_RUN) {
    console.log(`\n🔍 Dry run — not posting.`);
    return;
  }

  // Post to Twitter
  const {
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
  } = process.env;

  if (!TWITTER_API_KEY || !TWITTER_API_SECRET || !TWITTER_ACCESS_TOKEN || !TWITTER_ACCESS_TOKEN_SECRET) {
    console.error('❌ Missing Twitter API credentials. Set TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET.');
    process.exit(1);
  }

  const client = new TwitterApi({
    appKey: TWITTER_API_KEY,
    appSecret: TWITTER_API_SECRET,
    accessToken: TWITTER_ACCESS_TOKEN,
    accessSecret: TWITTER_ACCESS_TOKEN_SECRET,
  });

  try {
    const result = await client.v2.tweet(next.text);
    console.log(`\n✅ Posted! Tweet ID: ${result.data.id}`);
    console.log(`   https://x.com/trevanvia/status/${result.data.id}`);

    state.posted.push(next.id);
    state.lastPostedAt = new Date().toISOString();
    saveState(state);
  } catch (err) {
    console.error(`❌ Failed to post: ${err.message}`);
    if (err.data) console.error(JSON.stringify(err.data, null, 2));
    process.exit(1);
  }
}

main();
