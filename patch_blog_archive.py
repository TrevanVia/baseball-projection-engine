#!/usr/bin/env python3
"""Add TrevKnowsBall blog posts to Research section. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

# Add the TrevKnowsBall posts to BLOG_POSTS array (after the existing 2 methodology articles)
# These link out to the original blog instead of embedding full content

old_end = """];

function ResearchPanel() {"""

tkb_posts = """  // ── TrevKnowsBall Archive (July-September 2025) ──
  {
    id: "trent-grisham-rise",
    date: "September 3, 2025",
    title: "The Rise of Trent Grisham",
    tags: ["player analysis", "breakout"],
    summary: "From role player to game-changer. How Grisham's retooled approach turned him into a legitimate contributor.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/09/role-player-to-game-changer-rise-of.html",
  },
  {
    id: "jhoan-duran-closer",
    date: "August 11, 2025",
    title: "Jhoan Duran is The Game's Most Untouchable Closer",
    tags: ["pitching", "statcast", "reliever"],
    summary: "Breaking down Duran's arsenal and why his pitch mix makes him virtually unhittable. Statcast data tells the story.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/jhoan-duran-is-games-most-untouchable.html",
  },
  {
    id: "tatis-just-fine",
    date: "August 9, 2025",
    title: "Fernando Tatis Jr. is Just Fine, Guys",
    tags: ["player analysis", "statcast"],
    summary: "Despite the noise, Tatis's underlying metrics show a player who's still elite. The expected stats back it up.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/fernando-tatis-jr-is-just-fine-guys.html",
  },
  {
    id: "schwarber-nl-mvp",
    date: "August 7, 2025",
    title: "Kyle Schwarber is Your NL MVP",
    tags: ["player analysis", "MVP"],
    summary: "The case for Schwarber as the National League's most valuable player, backed by production and advanced metrics.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/kyle-schwarber-is-your-nl-mvp.html",
  },
  {
    id: "bo-bichette-back",
    date: "August 5, 2025",
    title: "Bo Bichette is Back in Business",
    tags: ["player analysis", "statcast", "breakout"],
    summary: "After a disastrous 2024, Bichette has re-emerged with a 125 wRC+ and career-high 48.7% hard-hit rate. The rebound is real.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/bo-bichette-hasnt-just-bounced-back-hes.html",
  },
  {
    id: "hunter-brown-peaks-valleys",
    date: "August 4, 2025",
    title: "Hunter Brown's Season of Peaks & Valleys",
    tags: ["pitching", "statcast", "breakout"],
    summary: "From 28 consecutive scoreless innings to a July slump and back again. Tracking Brown's 2025 through Statcast.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/hunter-browns-season-of-peaks-valleys.html",
  },
  {
    id: "max-clark-prospect",
    date: "August 2, 2025",
    title: "Max Clark Punches Way Above His Age",
    tags: ["prospects", "scouting"],
    summary: "At age 20, Clark is slashing .323/.386/.581 in Double-A with elite plate discipline. Breaking down why his FV 60 grade might be conservative.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/max-clark-punches-way-above-his-age.html",
  },
  {
    id: "adrian-morejon-dream",
    date: "August 1, 2025",
    title: "Adrian Morej\\u00f3n, A Front Office's Dream Player",
    tags: ["pitching", "statcast", "value"],
    summary: "Ranked 1st in xERA, avg EV, xSLG, xwOBA, barrel%, and hard-hit% among pitchers with 80+ IP. At $2M salary, he's the most cost-efficient pitcher in baseball.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/08/adrian-morejon-is-on-absolute-tear.html",
  },
  {
    id: "will-smith-best-hitter",
    date: "July 31, 2025",
    title: "Will Smith Is The Best Hitter We Don't Talk About",
    tags: ["player analysis", "statcast", "catcher"],
    summary: "Six straight years of 120+ wRC+ from the catcher position. 92nd percentile xwOBA, 83rd percentile chase rate. Smith is quietly elite.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/07/will-smith-is-best-hitter-we-dont-talk.html",
  },
  {
    id: "matthew-boyd-shoving",
    date: "July 30, 2025",
    title: "Matthew Boyd is Shoving, What's Changed?",
    tags: ["pitching", "breakout"],
    summary: "A 34-year-old lefty has become the ace of a first-place Cubs team. The Statcast page confirms this isn't smoke and mirrors.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/07/you-know-i-had-to-squeeze-some-alonso.html",
  },
  {
    id: "langeliers-breakout",
    date: "July 29, 2025",
    title: "Shea Langeliers is Quietly Having His Best Season Yet",
    tags: ["player analysis", "statcast", "catcher"],
    summary: "Career-high power numbers backed by a 11.1% barrel rate and xwOBA matching his actual production. Oakland's cornerstone is arriving.",
    externalUrl: "https://trevknowsball.blogspot.com/2025/07/langeliers-quietly-having-his-best.html",
  },
"""

new_end = tkb_posts + """];

function ResearchPanel() {"""

if old_end in src:
    src = src.replace(old_end, new_end)
    print("1. Added 11 TrevKnowsBall articles to BLOG_POSTS")
else:
    print("ERROR: Could not find BLOG_POSTS end")

# Now update the ResearchPanel to handle externalUrl (open in new tab instead of inline)
old_click = """            onClick={() => setSelectedPost(post.id)}"""
new_click = """            onClick={() => post.externalUrl ? window.open(post.externalUrl, '_blank') : setSelectedPost(post.id)}"""

if old_click in src:
    src = src.replace(old_click, new_click)
    print("2. External posts open in new tab, VIAcast posts open inline")

# Add a small "Originally published on TrevKnowsBall" indicator for external posts
old_arrow = """              <span style={{fontSize:18,color:C.border,fontFamily:F,paddingTop:4}}>&rarr;</span>"""
new_arrow = """              <div style={{display:"flex",flexDirection:"column",alignItems:"center",gap:4,paddingTop:4}}>
                <span style={{fontSize:18,color:C.border,fontFamily:F}}>{post.externalUrl ? "↗" : "→"}</span>
                {post.externalUrl && <span style={{fontSize:7,color:C.muted,fontFamily:F,whiteSpace:"nowrap"}}>TrevKnowsBall</span>}
              </div>"""

if old_arrow in src:
    src = src.replace(old_arrow, new_arrow)
    print("3. Added TrevKnowsBall label on external posts")

open(APP, "w").write(src)
print("\nDone! Research section now has 13 articles (2 VIAcast + 11 TrevKnowsBall)")
