/**
 * VIAcast Scheduled Tweet Content
 * 
 * Each tweet follows the formula:
 * 1. Lead with the wildest data point
 * 2. Explain why it matters in plain english
 * 3. Close with viacastbaseball.com
 * 
 * Style: casual, data-first, no fluff, let the numbers speak.
 * Capitalize first letter of each sentence.
 */

const TWEETS = [
  {
    id: "miller-slider",
    category: "arsenal",
    text: "Mason Miller's slider has a 54.6% whiff rate and .163 xwOBA against. A+ grade.\n\nHitters swing and miss more than half the time. When they do connect it's basically a guaranteed out.\n\nOh and he throws it 45.6% of the time. Just daring you to hit it.\n\nThe scariest part? His fastball sits 102. So you're guessing between triple digits and the best slider in baseball.\n\nPitcher arsenal grades on viacastbaseball.com",
  },
  {
    id: "skubal-changeup",
    category: "arsenal",
    text: "Tarik Skubal's changeup graded out A+ on VIAcast\n\n46.8% whiff rate. .188 xwOBA against. 2.8 run value per 100 pitches.\n\nHe throws it 31.4% of the time \u2014 that's not a secondary pitch, that's his identity. A changeup-first ace.\n\nThe league average changeup xwOBA is around .310. Skubal's is 40% better than that.\n\nFull arsenal grades for every pitcher at viacastbaseball.com",
  },
  {
    id: "wheeler-curveball",
    category: "arsenal",
    text: "Zack Wheeler's curveball before his injury: 55.3% whiff rate. .121 xwOBA against. A+ grade.\n\nThat's the lowest xwOBA against of any pitch in baseball with 200+ thrown. Hitters literally couldn't do anything with it.\n\nHe also had an A+ sweeper (.219 xwOBA) and a B+ fastball that missed 30% of bats at 97 mph.\n\nWheeler healthy is a top 3 arsenal in the sport.\n\nviacastbaseball.com",
  },
  {
    id: "sale-slider",
    category: "arsenal",
    text: "Chris Sale threw his slider 47.3% of the time in 2025. It graded A+.\n\n39.8% whiff. .196 xwOBA against. He's 37 years old and it's still one of the 5 best pitches in baseball.\n\nThe problem: his fastball graded C (.348 xwOBA against). The slider carries the entire arsenal.\n\nWhen one pitch is that dominant you can get away with it. But it's a thin margin.\n\nEvery pitcher's arsenal graded at viacastbaseball.com",
  },
  {
    id: "crochet-sweeper",
    category: "arsenal",
    text: "Garrett Crochet's sweeper: 40.5% whiff, .152 xwOBA, A+ grade\n\nHe only throws it 16% of the time. That's criminal. It's his best pitch by a mile and he barely uses it.\n\nHis fastball is a C+ and his sinker sits at C. The sweeper and changeup (also A+) are carrying the whole operation.\n\nIf Crochet ever ups that sweeper usage to 25%+ the league is in trouble.\n\nviacastbaseball.com",
  },
  {
    id: "judge-contact",
    category: "hitter",
    text: "Aaron Judge's 2025 Statcast line:\n\n.460 xwOBA (1st in MLB)\n95.4 avg exit velo\n24.7% barrel rate\n\nFor context, the league average barrel rate is 7.5%. Judge barrels the ball more than 3x the average hitter.\n\nThat's why VIAcast projects him at 7.9 fWAR for 2026. The contact quality is generational.\n\nviacastbaseball.com",
  },
  {
    id: "soto-discipline",
    category: "hitter",
    text: "Juan Soto posted a .429 xwOBA in 2025. 2nd in MLB behind only Judge.\n\nBut here's what separates Soto: his walk rate and chase rate are elite. He doesn't just hit the ball hard \u2014 he only swings at pitches he can destroy.\n\nVIAcast projects him at 6.6 fWAR. He's 27. The next 5 years are going to be absurd.\n\nFull projections at viacastbaseball.com",
  },
  {
    id: "basallo-power",
    category: "prospect",
    text: "Samuel Basallo's Prospect Savant data is terrifying\n\n.424 xwOBA\n21% barrel rate\n115.9 max exit velo\n57.4% hard hit rate\n\nHe's a 21 year old catcher producing Judge-level batted ball data in the minors.\n\nThe 32.77% chase rate needs work. But the raw power is as loud as any prospect in baseball.\n\nMiLB Statcast profiles now on viacastbaseball.com",
  },
  {
    id: "anthony-elite",
    category: "prospect",
    text: "Roman Anthony's Prospect Savant profile is the best in the minors. 100th percentile PS Score.\n\n.443 xwOBA. 20.3% barrel rate. 19.2% walk rate. 116 mph max exit velo.\n\nThe walk rate is the key. Most power prospects chase. Anthony has elite discipline AND elite power. That combination at 21 is extremely rare.\n\nVIAcast has his MiLB Statcast profile live at viacastbaseball.com",
  },
  {
    id: "wetherholt-plate-discipline",
    category: "prospect",
    text: "JJ Wetherholt's chase rate at AAA: 18.55%\n\nFor reference, the MLB average is around 28%. He's chasing 10 percentage points less than the average big leaguer while still posting a .366 xwOBA.\n\n12.7% walk rate. 14.9% K rate. 12.4% barrel rate. That's an above average hit tool with plus power and elite plate discipline.\n\nProspect Savant data on viacastbaseball.com",
  },
  {
    id: "mcgonigle-small-sample",
    category: "prospect",
    text: "Kevin McGonigle has 50 PA of Prospect Savant data and the numbers are stupid\n\n.443 xwOBA. .351 xBA. .591 xSLG.\n5% K rate. 15% walk rate.\n56.2% hard hit rate.\n\nYes it's a tiny sample. But a 5% K rate with that kind of exit velo data is almost unheard of at any level. The bat-to-ball skill is special.\n\nviacastbaseball.com",
  },
  {
    id: "griffin-tools",
    category: "prospect",
    text: "Konnor Griffin is the #1 prospect in baseball and his Statcast data shows why\n\n28.6 ft/s sprint speed (97th percentile)\n90.7 avg exit velo at A-ball\n48.7% hard hit rate\n\nHe's 19 playing A-ball with plus-plus speed and above average power. The 22.9% K rate and 6.5% walk rate need development but the physical tools are off the charts.\n\nProspect profiles at viacastbaseball.com",
  },
  {
    id: "engine-update",
    category: "meta",
    text: "Just shipped a major VIAcast update:\n\n- Pitch arsenal grades (A+ to F) for every MLB pitcher\n- Per-pitch run values, whiff rates, and xwOBA from Savant\n- Refreshed 2023-2025 Statcast data pipeline\n- MiLB Prospect Savant profiles for 18 top prospects\n\nAll free. All open source.\n\nviacastbaseball.com",
  },
  {
    id: "milb-statcast",
    category: "meta",
    text: "Added MiLB Statcast profiles to VIAcast for top prospects\n\nYou can now see Prospect Savant data \u2014 exit velo, barrel rate, chase rate, sprint speed \u2014 with percentile bars benchmarked against MLB averages.\n\n18 prospects live including Griffin, Basallo, Anthony, Wetherholt, McGonigle, Miller, Stewart, Clark, and more.\n\nviacastbaseball.com",
  },
];

module.exports = TWEETS;
