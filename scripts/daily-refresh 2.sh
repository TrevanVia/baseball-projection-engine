#!/bin/bash
# scripts/daily-refresh.sh
# Runs on your Mac via cron at 2am ET
# Fetches live fWAR from FanGraphs, rebuilds, and deploys

DIR="$HOME/Desktop/baseball-projection-engine"
cd "$DIR" || exit 1

# Pull latest from GitHub first
git pull --rebase 2>/dev/null

# Fetch FanGraphs leaderboard using curl (your Mac isn't blocked)
YEAR=$(date +%Y)
BAT=$(curl -s -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" \
  "https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=bat&lg=all&qual=0&season=${YEAR}&month=0&hand=&team=0&pageItems=8&sortCol=WAR&sortDir=desc")
PIT=$(curl -s -H "User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" \
  "https://www.fangraphs.com/api/leaders/major-league/data?pos=all&stats=pit&lg=all&qual=0&season=${YEAR}&month=0&hand=&team=0&pageItems=8&sortCol=WAR&sortDir=desc")

# Check if we got valid JSON (not Cloudflare HTML)
if echo "$BAT" | node -e "JSON.parse(require('fs').readFileSync('/dev/stdin','utf8')).data[0]" 2>/dev/null; then
  # Build the live_leaderboard.json using node
  node -e "
    const b = JSON.parse(\`$(echo "$BAT" | sed 's/`/\\`/g')\`);
    const p = JSON.parse(\`$(echo "$PIT" | sed 's/`/\\`/g')\`);
    const t = s => (s||'').replace(/<[^>]+>/g,'').trim();
    const o = {
      generated: new Date().toISOString(),
      season: ${YEAR},
      hitters: (b.data||[]).slice(0,8).map(x=>({name:x.PlayerName,tm:t(x.Team),war:+x.WAR.toFixed(1),hr:Math.round(x.HR||0),wrc:Math.round(x['wRC+']||0)})),
      pitchers: (p.data||[]).slice(0,8).map(x=>({name:x.PlayerName,tm:t(x.Team),war:+x.WAR.toFixed(1),era:+x.ERA.toFixed(2),k9:+(x['K/9']||0).toFixed(1),ip:+x.IP.toFixed(1)}))
    };
    require('fs').writeFileSync('src/live_leaderboard.json', JSON.stringify(o, null, 2));
    console.log('✅ Live leaderboard updated: ' + o.hitters.length + ' hitters, ' + o.pitchers.length + ' pitchers');
  "
else
  echo "⚠ FanGraphs blocked, keeping existing leaderboard"
fi

# Rebuild and deploy
npm run build
npx vercel --prod --yes

# Commit and push
git add src/live_leaderboard.json
git diff --cached --quiet || {
  git commit -m "Daily leaderboard refresh $(date +%Y-%m-%d)"
  git push
}

echo "✅ Daily refresh complete $(date)"
