#!/usr/bin/env python3
"""Add new VIAcast research articles. Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()

new_articles = '''  {
    id: "baserunning-gap",
    date: "March 2026",
    title: "The Baserunning Gap: Why BsR Changes Everything",
    tags: ["methodology", "baserunning", "statcast"],
    summary: "Replacing sprint speed tiers with Statcast Baserunning Run Value reshuffled our WAR leaderboard. Here's who won and who lost.",
    content: `For most of VIAcast's development, baserunning value was estimated using sprint speed tiers. If you ran 29+ ft/s, you got +3.5 runs. Under 26 ft/s, you got -2 runs. Simple, fast, and wrong.

The problem with sprint speed tiers is that they measure capacity, not production. A guy who runs 30 ft/s but never attempts a stolen base and makes poor baserunning decisions isn't actually creating value on the bases. Meanwhile, a 28 ft/s runner with elite instincts and aggressive coaching might be worth more.

Statcast's Baserunning Run Value (BsR) solves this. It measures actual runs created — or lost — via two channels: stolen base value and extra-bases-taken value. Each steal attempt is contextualized against the specific pitcher-catcher battery. Each baserunning opportunity is evaluated against the outfielder's arm strength and the runner's position.

When we integrated BsR data for 252 MLB players, the WAR leaderboard shifted meaningfully.

THE WINNERS

Bobby Witt Jr. jumped the most. His +7.4 BsR translates to roughly 0.8 WAR from baserunning alone. Under the old sprint speed system, he was getting about 0.4 WAR — the BsR integration nearly doubled his baserunning contribution. Witt doesn't just run fast; he runs smart, takes extra bases aggressively, and rarely gets thrown out.

Elly De La Cruz (+8.9 BsR, ~0.9 WAR) and Corbin Carroll (+10.1 BsR, ~1.1 WAR) also saw significant boosts. Carroll leads all of baseball in BsR, and it's not just stolen bases — his extra-bases-taken value is elite, meaning he consistently turns singles into scoring position.

Gunnar Henderson (+6.8 BsR, ~0.7 WAR) was a surprise gainer. He's not typically thought of as a speed threat, but his baserunning decisions are consistently positive.

THE LOSERS

Aaron Judge dropped. His -3.6 BsR costs him roughly 0.4 WAR. Under the old sprint speed system, his 27.5 ft/s speed put him in a neutral tier. In reality, he's a below-average baserunner who occasionally gets thrown out trying to take extra bases, and his size makes him a poor stolen base threat.

The broader pattern: speed doesn't equal value. BsR captures the difference between players who convert their athleticism into runs and those who don't. For a projection engine trying to estimate total player value, that distinction matters.

THE FALLBACK

For MiLB players without BsR data, VIAcast still uses sprint speed tiers as a proxy. It's imperfect, but until Statcast tracking expands to all minor league parks, it's the best available option. As more BsR data becomes available, the fallback will apply to fewer players.

The takeaway: baserunning is a meaningful component of player value, and measuring it correctly can swing a projection by nearly a full win. That's the difference between a 5 WAR player and a 6 WAR player — which is the difference between an All-Star and an MVP candidate.`
  },
  {
    id: "prospect-fv-blend",
    date: "March 2026",
    title: "Projecting Prospects: How VIAcast Blends Stats and Scouting Grades",
    tags: ["prospects", "methodology", "FV"],
    summary: "A 70 FV prospect with 118 MLB plate appearances shouldn't project like a league-average player. Here's how VIAcast solves the small-sample problem.",
    content: `The hardest problem in baseball projection is the prospect problem.

Take Samuel Basallo. He's a 65 FV prospect — FanGraphs' scouting department says he profiles as a perennial All-Star. He hit 23 HR with a .966 OPS in AAA at age 20. Then he got called up to Baltimore and posted a .286 xwOBA in 118 plate appearances.

If you only look at the MLB stats, Basallo projects as a below-average hitter. If you only look at the scouting grade, he projects as a star. The truth is somewhere in between, but figuring out exactly where requires a framework.

VIAcast uses what we call the FV Blend — a weighted combination of translated statistical performance and FanGraphs Future Value benchmarks.

HOW THE BLEND WORKS

For any player with an FV grade and fewer than 400 MLB plate appearances, VIAcast computes two OPS estimates:

1. Stats OPS: Career MiLB stats translated to MLB equivalents using level-specific factors (AAA 0.82x, AA 0.68x, etc.), regressed toward league average based on sample size.

2. FV Benchmark OPS: The historical MLB outcome for that FV tier. A 65 FV projects to .880 OPS at peak. A 60 FV projects to .830. A 70 FV projects to .960.

The final OPS is a weighted blend: finalOPS = statsOPS × statWeight + benchOPS × fvWeight.

The key innovation: higher FV grades get more FV weight. A 70 FV prospect like Konnor Griffin gets 20% additional FV weight because scouting consensus at that tier is extremely predictive. A 55 FV gets no additional boost — the grade carries less certainty.

WHY THE SLASH LINE HAS TO MATCH

Early versions of VIAcast had a bug where wRC+ was boosted by the FV blend but the displayed OBP/SLG weren't. You'd see a prospect with 120 wRC+ but .712 OPS — numbers that can't coexist. A 120 wRC+ implies roughly .790-.800 OPS.

The fix: when the FV blend boosts OPS, the slash line now scales proportionally. The boost splits 40/60 between OBP and SLG, reflecting that prospect upside is more power-driven than patience-driven. HR also scales with the SLG increase.

THE WAR FLOOR

The other piece of the FV puzzle is the WAR clamp. Without it, a 70 FV prospect with a terrible 50-PA MLB sample could project for 1.0 WAR — which contradicts what the scouting grade means.

VIAcast sets the WAR floor at 50% of the FV benchmark:
- 70 FV: 4.0 WAR minimum (benchmark: 8.0)
- 65 FV: 2.8 WAR minimum (benchmark: 5.5)
- 60 FV: 2.0 WAR minimum (benchmark: 4.0)
- 55 FV: 1.4 WAR minimum (benchmark: 2.8)

These floors are conservative — they represent the low end of what a player at that tier should produce. But they prevent the embarrassing outcome of projecting the best prospect in baseball for 1.2 WAR because he had a rough 30-game audition.

WHAT THIS MEANS FOR SPECIFIC PLAYERS

Basallo (65 FV): His translated MiLB stats are strong, and the 65 FV benchmark pulls his projection to ~120 wRC+ with a .790 OPS. The WAR floor of 2.8 provides a safety net, but his stats-based projection actually exceeds it.

Konnor Griffin (70 FV): With no MLB data at all, his projection is almost entirely FV-driven. The .960 benchmark OPS and 4.0 WAR floor reflect the scouting consensus that he's the best prospect in baseball.

Jackson Holliday (60 FV, ~850 MLB PA): With more MLB data, the blend trusts his stats more and the FV less. He's transitioning from prospect to established player in the engine's eyes.

The FV blend isn't perfect. Scouting grades are subjective, and FanGraphs occasionally misses. But for small-sample prospects, it's far better than pure statistical regression, which would project every 100-PA callup as a league-average hitter.`
  },
  {
    id: "xera-vs-fip",
    date: "March 2026",
    title: "Why VIAcast Uses xERA Instead of FIP for Pitcher WAR",
    tags: ["pitching", "methodology", "statcast"],
    summary: "Most projection systems anchor pitcher WAR on FIP. VIAcast uses xERA instead. Here's the case for expected ERA as a better projection anchor.",
    content: `FIP (Fielding Independent Pitching) has been the gold standard for pitcher evaluation for over a decade. It strips out the things a pitcher can't control — defense, sequencing, luck on balls in play — and focuses on strikeouts, walks, and home runs.

For historical evaluation, FIP is excellent. But for projection, it has a blind spot that matters: it ignores contact quality.

Two pitchers can have identical K%, BB%, and HR rates but be vastly different pitchers. One might induce weak grounders and lazy fly balls. The other might get hit hard but have the ball land in gloves. FIP treats them the same. The market shouldn't.

This is where xERA (Expected ERA) comes in.

WHAT xERA CAPTURES THAT FIP DOESN'T

xERA is built on Statcast's expected stats framework. It takes every batted ball a pitcher allows and assigns an expected outcome based on exit velocity and launch angle. A 110 mph line drive is expected to be a hit. A 75 mph grounder is expected to be an out. The pitcher gets credit or blame for the quality of contact they allow, regardless of what actually happened.

This means xERA captures:
- Contact management (barrel% allowed, hard-hit%, avg EV against)
- Ground ball tendency (which suppresses HR independent of HR/FB rate)
- Quality of weak contact (not all outs are created equal)

FIP captures none of this. A pitcher who allows a .250 xBA on contact and a .350 xBA on contact look identical in FIP if their K/BB/HR rates match.

THE PRACTICAL DIFFERENCE

In VIAcast's pitcher projections, the choice of anchor matters most for pitchers with elite contact management. Adrian Morejon is the poster child: his 2025 xERA was 1.71 (1st in baseball), driven by a 2.7% barrel rate and 25.4% hard-hit rate — both best in MLB. His FIP was good but not historic, because his strikeout rate was merely above-average.

A FIP-based system would project Morejon as a solid mid-rotation arm. An xERA-based system sees one of the most effective run preventers in the sport.

The reverse also applies. A pitcher with a great K rate but who gets barreled frequently will have a better FIP than xERA. VIAcast would project them for regression — which is usually correct.

THE K%/BB% DATA GAP

There's a practical reason too. VIAcast's Statcast data pipeline doesn't always have clean K% and BB% data from FanGraphs (the primary source for plate discipline metrics). For many pitchers, K% has to be estimated from whiff rate (K% ≈ whiff% × 0.80). Since FIP requires precise K and BB counts, an estimated FIP is less reliable than xERA, which comes directly from Statcast's batted ball data.

WHERE FIP STILL SHOWS UP

VIAcast does compute FIP for every pitcher — it's displayed on the player card alongside xERA-based WAR. This gives users the full picture: the xERA projection tells you what VIAcast thinks will happen, and the FIP provides a cross-reference from the traditional framework.

For the Marcel engine (which handles pitchers without Statcast data), FIP is actually the WAR anchor, since translated MiLB data doesn't include batted ball quality metrics. This is a known limitation — as Statcast expands to more minor league parks, the xERA advantage will extend to prospect pitchers too.

The bottom line: for MLB pitchers with Statcast data, contact quality is too important to ignore. xERA captures it. FIP doesn't. That's why VIAcast builds pitcher WAR on expected ERA.`
  },
  {
    id: "defense-tax",
    date: "March 2026",
    title: "The Defense Tax: How OAA Reshuffles the WAR Leaderboard",
    tags: ["defense", "methodology", "statcast"],
    summary: "At 0.5 runs per OAA, defense can swing a player's WAR by 1-2 wins. Here's how VIAcast handles the most volatile component of player value.",
    content: `Defense is the noisiest component of WAR. A hitter's wRC+ is relatively stable year-to-year. A pitcher's xERA regresses predictably. But a fielder's OAA can swing wildly — and even one season of elite or terrible defense can dramatically change a projection.

VIAcast converts Outs Above Average at 0.5 runs per OAA. This is deliberately conservative. Some models use higher conversion rates (0.7-0.9 runs per OAA), but we found those rates inflate defensive contributions beyond what the data supports when backtested against full-season WAR.

THE CALIBRATION PROBLEM

Our original defense formula used OAA × 0.6 × 1.5, which works out to 0.9 runs per OAA. For Bobby Witt Jr. (21.9 OAA), that produced 19.7 defensive runs — over 2 full WAR from defense alone. His total projection hit 8.6 WAR, which would make him the best position player in baseball by a wide margin.

That didn't pass the smell test. Witt is an elite defender, but 2.1 dWAR from a single season's OAA is historically rare. Andrelton Simmons at his peak managed about 3.0-3.5 dWAR, and he's considered one of the best defensive shortstops ever measured.

Dropping to 0.5 runs per OAA brought Witt's defensive contribution to 11.0 runs (1.2 dWAR). His total projection landed at 7.8 WAR — still the top position player in our system, but driven by a realistic combination of offense, baserunning, and defense rather than defense alone.

DEFENSIVE AGING

Defense ages faster than offense. VIAcast tracks defensive peaks separately from offensive peaks:
- SS and CF peak defensively at 26
- Corner infielders at 27
- Corner outfielders at 28

After the defensive peak, fielding value decays at 6% per year. A shortstop who was +15 OAA at age 26 would be projected at roughly +12 OAA by age 28 and +9 by age 30 — even if their offensive peak hasn't arrived yet.

This creates interesting projection dynamics. A 24-year-old shortstop like Gunnar Henderson is still improving offensively (peak at 28) but will start declining defensively soon (peak at 26). His total WAR trajectory reflects both curves, which is why his projected WAR peaks around age 27 — the sweet spot where both offense and defense are near their best.

WHO BENEFITS, WHO DOESN'T

The biggest defensive beneficiaries in VIAcast's system are premium-position players with plus OAA: Witt (+1.2 dWAR), Henderson, Francisco Lindor, and Elly De La Cruz all get meaningful WAR boosts from their glove work.

The biggest losers are bat-first players at premium positions with negative OAA. CJ Abrams (-13.4 OAA) loses about 0.7 WAR from defense. Juan Soto (-9.2 OAA) takes a similar hit — partly offset by playing a less demanding position.

DH-only players like Yordan Alvarez and designated hitters receive no defensive value but also no defensive penalty. However, the DH positional adjustment (-17.5 runs per 600 PA) is the harshest in the system, reflecting the opportunity cost of a roster spot that contributes nothing in the field.

Defense remains the component of WAR that we're least confident in projecting forward. OAA can be volatile, and a single season's data is noisier than three years of Statcast batting data. But ignoring it entirely — as some simpler projection models do — systematically undervalues elite defenders and overvalues poor ones. The 0.5 conversion rate is our current best estimate of the signal-to-noise ratio.`
  },
  {
    id: "counting-stats-approach",
    date: "March 2026",
    title: "Counting Stats for Prospects: A Games-First Approach",
    tags: ["prospects", "methodology", "HR"],
    summary: "Why VIAcast projects games played first and derives plate appearances and home runs from there — and how MiLB HR translation prevents power inflation.",
    content: `Early versions of VIAcast had a counting-stat problem. Samuel Basallo — a 65 FV catcher with 23 HR in AAA — was projecting for 15 HR in his first full MLB season. Jackson Merrill and Jackson Chourio, despite very different barrel rates, both projected for exactly 28 HR.

These numbers didn't pass scrutiny. Basallo's HR total was too low for his power profile. Merrill and Chourio converging to the same number suggested a formula artifact, not a real projection. Both problems had different root causes, but the fix for each started with the same principle: project playing time first, then derive counting stats from rate stats.

THE GAMES-FIRST APPROACH

Instead of projecting PA from career averages and then scaling HR to match, VIAcast now projects games played based on position and level:
- Catchers: 120 games (catchers need rest days)
- Position players: 140 games (typical for a projected starter)
- Established MLB players: based on actual recent game history

Plate appearances are then derived: PA = projected games × 4.0 PA/G (the MLB average). This ensures PA and games are always internally consistent — you won't see a player with 140 games but 170 PA.

THE MiLB HR TRANSLATION

The second piece was translating minor league home runs. A player who hits 23 HR in AA doesn't project for 23 HR in MLB. AA ball has different pitch quality, park factors, and competitive level. VIAcast now applies the same translation factors to HR that it applies to other stats:
- AAA HR × 0.82
- AA HR × 0.68
- High-A HR × 0.58
- Single-A HR × 0.50

So Basallo's 23 AA/AAA HR become roughly 17 translated HR. At a rate of 17 HR per 125 MiLB games, that's 0.136 HR/game. Multiply by 120 projected games (catcher) and you get about 16 base HR. Add the FV SLG boost (his 65 FV grade pushes projected SLG above the baseline) and you land around 22-24 HR — right in line with ZiPS and Steamer.

THE CONVERGENCE FIX

The Chourio/Merrill/Holliday convergence to 28 HR had a different cause. The Statcast HR formula for MLB players uses barrel rate and a non-barrel baseline:

HR = barrel% × BBE × 0.45 + PA × baseline

The original baseline was 0.018 HR per PA — about 11 non-barrel HR per full season. This was too aggressive. It made plate appearances the dominant driver of HR totals, overwhelming the barrel-rate differences between players. A low-barrel guy with lots of PA could match a high-barrel guy with fewer PA.

Reducing the baseline to 0.010 restored barrel rate as the primary differentiator. The non-barrel contribution dropped to about 6-7 HR per season, which is more empirically grounded — most home runs come from barreled balls, and the non-barrel HR rate should be modest.

WHAT THE NUMBERS LOOK LIKE NOW

The games-first approach produces internally consistent projections:
- Basallo: 120G, 480 PA, ~22 HR (was 100G, 170 PA, 15 HR)
- Chourio: 140G, 560 PA, ~23 HR (was 28, same as everyone else)
- Merrill: 140G, 560 PA, ~24 HR (differentiated by higher barrel rate)
- Holliday: 140G, 560 PA, ~23 HR (appropriately lower barrel rate)

These aren't perfect — no preseason projection is. But they're internally consistent, position-appropriate, and differentiated by the underlying skills that drive power production.`
  },
'''

# Insert before the TrevKnowsBall archive
old_marker = """  // ── TrevKnowsBall Archive (July-September 2025) ──"""

if old_marker in src:
    src = src.replace(old_marker, new_articles + "\n  // ── TrevKnowsBall Archive (July-September 2025) ──")
    open(APP, "w").write(src)
    print("Added 5 new VIAcast research articles:")
    print("  1. The Baserunning Gap: Why BsR Changes Everything")
    print("  2. Projecting Prospects: How VIAcast Blends Stats and Scouting Grades")
    print("  3. Why VIAcast Uses xERA Instead of FIP for Pitcher WAR")
    print("  4. The Defense Tax: How OAA Reshuffles the WAR Leaderboard")
    print("  5. Counting Stats for Prospects: A Games-First Approach")
else:
    print("ERROR: TrevKnowsBall marker not found")
