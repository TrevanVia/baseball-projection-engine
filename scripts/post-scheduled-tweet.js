/**
 * VIAcast Scheduled Tweet Poster
 * 
 * Uses date-based rotation to pick the next tweet — no state file needed.
 * Each calendar day picks a different tweet from the pool.
 * Multiple runs on the same day post the same tweet (cron dedup via Twitter API).
 * 
 * Usage:
 *   node scripts/post-scheduled-tweet.js          # Post today's tweet
 *   node scripts/post-scheduled-tweet.js --dry-run # Preview without posting
 *   node scripts/post-scheduled-tweet.js --list    # Show all tweets with schedule
 */

const { TwitterApi } = require('twitter-api-v2');
const TWEETS = require('./scheduled-tweets.js');
const args = process.argv.slice(2);

// ── DATE-BASED ROTATION ─────────────────────────────────────────────────────
function getTodaysTweet() {
  const now = new Date();
  // Days since a fixed epoch — rotates through tweets
  const daysSinceEpoch = Math.floor(now.getTime() / 86400000);
  const idx = daysSinceEpoch % TWEETS.length;
  return { tweet: TWEETS[idx], idx, total: TWEETS.length };
}

// ── LIST MODE ────────────────────────────────────────────────────────────────
if (args.includes('--list')) {
  const { idx } = getTodaysTweet();
  console.log(`\n📋 Scheduled Tweets (${TWEETS.length} total)\n`);
  TWEETS.forEach((t, i) => {
    const marker = i === idx ? '👉 TODAY' : `   day ${i}`;
    const preview = t.text.split('\n')[0].substring(0, 70);
    console.log(`${marker}  [${t.category}] ${t.id}`);
    console.log(`          ${preview}...`);
  });
  console.log(`\nToday's index: ${idx} — rotates daily`);
  process.exit(0);
}

// ── POST MODE ────────────────────────────────────────────────────────────────
async function main() {
  const { tweet, idx, total } = getTodaysTweet();
  const DRY_RUN = args.includes('--dry-run');

  console.log(`\n📅 Day index: ${idx} of ${total}`);
  console.log(`📝 Tweet: [${tweet.category}] ${tweet.id}`);
  console.log(`─────────────────────────────────────`);
  console.log(tweet.text);
  console.log(`─────────────────────────────────────`);
  console.log(`Characters: ${tweet.text.length}`);

  if (DRY_RUN) {
    console.log(`\n🔍 Dry run — not posting.`);
    return;
  }

  const {
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
  } = process.env;

  if (!TWITTER_API_KEY || !TWITTER_API_SECRET || !TWITTER_ACCESS_TOKEN || !TWITTER_ACCESS_TOKEN_SECRET) {
    console.error('❌ Missing Twitter API credentials.');
    process.exit(1);
  }

  const client = new TwitterApi({
    appKey: TWITTER_API_KEY,
    appSecret: TWITTER_API_SECRET,
    accessToken: TWITTER_ACCESS_TOKEN,
    accessSecret: TWITTER_ACCESS_TOKEN_SECRET,
  });

  try {
    const result = await client.v2.tweet(tweet.text);
    console.log(`\n✅ Posted! https://x.com/trevanvia/status/${result.data.id}`);
  } catch (err) {
    // Twitter returns 403 if duplicate tweet — that's fine, means it already posted today
    if (err.code === 403 || err.data?.detail?.includes('duplicate')) {
      console.log(`\n⏭️  Already posted today (duplicate detected). Skipping.`);
      return;
    }
    console.error(`❌ Failed: ${err.message}`);
    if (err.data) console.error(JSON.stringify(err.data, null, 2));
    process.exit(1);
  }
}

main();
