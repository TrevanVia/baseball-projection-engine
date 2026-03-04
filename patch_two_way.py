#!/usr/bin/env python3
"""Add two-way player support (Ohtani). Run from project root."""
APP = "src/App.jsx"
src = open(APP).read()
changes = 0

# 1. Fix PlayerCard career fetch: load BOTH for two-way players
old_fetch_logic = """    const isPitch = player.primaryPosition?.code === "1";
    if (isPitch) {
      getPlayerCareer(player.id, "pitching").then(s=>{setPitchCareer(s);setLoading(false);}).catch(()=>setLoading(false));
    } else {
      getPlayerCareer(player.id, "hitting").then(s=>{setCareer(s);setLoading(false);}).catch(()=>setLoading(false));
    }"""

new_fetch_logic = """    const isPitch = player.primaryPosition?.code === "1";
    const isTwoWay = player.primaryPosition?.code === "Y";
    if (isTwoWay) {
      // Two-way player: fetch BOTH hitting and pitching careers
      Promise.all([
        getPlayerCareer(player.id, "hitting").catch(() => []),
        getPlayerCareer(player.id, "pitching").catch(() => []),
      ]).then(([h, p]) => { setCareer(h); setPitchCareer(p); setLoading(false); });
    } else if (isPitch) {
      getPlayerCareer(player.id, "pitching").then(s=>{setPitchCareer(s);setLoading(false);}).catch(()=>setLoading(false));
    } else {
      getPlayerCareer(player.id, "hitting").then(s=>{setCareer(s);setLoading(false);}).catch(()=>setLoading(false));
    }"""

if old_fetch_logic in src:
    src = src.replace(old_fetch_logic, new_fetch_logic)
    changes += 1
    print("1. Fixed career fetch for two-way players (loads both)")

# 2. Add two-way detection and combined projection in base useMemo
old_base_memo = """  const isPitcher = player.primaryPosition?.code === "1";
  useEffect(()=>{if(isPitcher)setProjTab("war");},[isPitcher]);
  const base = useMemo(() => {
    if (isPitcher) {
      const pSav = getPitcherSavant(player.id, player.fullName);
      if (pSav && Object.keys(pSav.seasons || {}).length > 0) {
        const scP = projectPitcherFromStatcast(pSav, player.currentAge, player.fullName, player.id);
        if (scP) return scP;
      }
      return pitchCareer.length ? projectPitcherFromSeasons(pitchCareer, player.currentAge, player.fullName, player.id) : null;
    }
    const savP = getSavantPlayer(player.id, player.fullName);
    if (savP && Object.keys(savP.seasons || {}).length > 0) {
      const scProj = projectFromStatcast(savP, player.currentAge, player.primaryPosition?.code, player.fullName, player.id);
      if (scProj) return scProj;
    }
    return career.length ? projectFromSeasons(career, player.currentAge, player.primaryPosition?.code, player.fullName, player.id) : null;
  }, [career, pitchCareer, player, isPitcher]);"""

new_base_memo = """  const isPitcher = player.primaryPosition?.code === "1";
  const isTwoWay = player.primaryPosition?.code === "Y";
  useEffect(()=>{if(isPitcher)setProjTab("war");},[isPitcher]);
  const base = useMemo(() => {
    if (isPitcher) {
      const pSav = getPitcherSavant(player.id, player.fullName);
      if (pSav && Object.keys(pSav.seasons || {}).length > 0) {
        const scP = projectPitcherFromStatcast(pSav, player.currentAge, player.fullName, player.id);
        if (scP) return scP;
      }
      return pitchCareer.length ? projectPitcherFromSeasons(pitchCareer, player.currentAge, player.fullName, player.id) : null;
    }
    // Hitter projection (also base for two-way)
    let hitProj = null;
    const savP = getSavantPlayer(player.id, player.fullName);
    if (savP && Object.keys(savP.seasons || {}).length > 0) {
      hitProj = projectFromStatcast(savP, player.currentAge, player.primaryPosition?.code === "Y" ? "10" : player.primaryPosition?.code, player.fullName, player.id);
    }
    if (!hitProj && career.length) {
      hitProj = projectFromSeasons(career, player.currentAge, player.primaryPosition?.code === "Y" ? "10" : player.primaryPosition?.code, player.fullName, player.id);
    }
    if (!hitProj) return null;

    // Two-way: add pitching WAR
    if (isTwoWay) {
      let pitchWAR = 0;
      const pSav = getPitcherSavant(player.id, player.fullName);
      if (pSav && Object.keys(pSav.seasons || {}).length > 0) {
        const pProj = projectPitcherFromStatcast(pSav, player.currentAge, player.fullName, player.id);
        if (pProj) pitchWAR = pProj.baseWAR;
        hitProj._pitchProj = pProj;
      } else if (pitchCareer.length) {
        const pProj = projectPitcherFromSeasons(pitchCareer.filter(s => parseFloat(s.stat?.inningsPitched || 0) > 0), player.currentAge, player.fullName, player.id);
        if (pProj) pitchWAR = pProj.baseWAR;
        hitProj._pitchProj = pProj;
      }
      if (pitchWAR > 0) {
        hitProj._hitWAR = hitProj.baseWAR;
        hitProj._pitchWAR = pitchWAR;
        hitProj.baseWAR = Math.round((hitProj.baseWAR + pitchWAR) * 10) / 10;
        hitProj._isTwoWay = true;
      }
    }
    return hitProj;
  }, [career, pitchCareer, player, isPitcher, isTwoWay]);"""

if old_base_memo in src:
    src = src.replace(old_base_memo, new_base_memo)
    changes += 1
    print("2. Added two-way combined projection (hitting + pitching WAR)")

# 3. Display two-way WAR breakdown on card
# Add after the existing pitcher/hitter stat rows
old_display = """          {base&&!isPitcher&&<>
              <Stat label="Proj WAR" value={base.baseWAR.toFixed(1)} color={base.baseWAR>=4?C.green:base.baseWAR>=2?C.blue:C.yellow}/>"""

new_display = """          {base&&!isPitcher&&<>
              <Stat label="Proj WAR" value={base.baseWAR.toFixed(1)} color={base.baseWAR>=4?C.green:base.baseWAR>=2?C.blue:C.yellow}/>
              {base._isTwoWay&&<>
                <Stat label="Hit WAR" value={base._hitWAR?.toFixed(1)} color={C.blue} sub="Batting"/>
                <Stat label="Pitch WAR" value={base._pitchWAR?.toFixed(1)} color={C.purple} sub="Pitching"/>
                {base._pitchProj&&<Stat label="Proj ERA" value={base._pitchProj.era?.toFixed(2)} color={base._pitchProj.era<=3.00?C.green:C.text}/>}
              </>}"""

if old_display in src:
    src = src.replace(old_display, new_display)
    changes += 1
    print("3. Added two-way WAR breakdown display on card")

# 4. Fix leaderboard: two-way players in hitter leaderboard need combined WAR
# Find where the leaderboard builds hitter entries
old_lb_war = """            projWAR: base.baseWAR,
            careerWAR: getCareerWAR(p.id, p.fullName),
            cumWAR: Math.round(cum * 10) / 10,
            projWRC: base.wRCPlus,"""

new_lb_war = """            projWAR: base.baseWAR + (() => {
              // Add pitching WAR for two-way players
              if (p.primaryPosition?.code === "Y") {
                const pSav = getPitcherSavant(p.id, p.fullName);
                if (pSav && Object.keys(pSav.seasons || {}).length > 0) {
                  const pp = projectPitcherFromStatcast(pSav, p.currentAge, p.fullName, p.id);
                  if (pp) return pp.baseWAR;
                }
              }
              return 0;
            })(),
            careerWAR: getCareerWAR(p.id, p.fullName),
            cumWAR: Math.round(cum * 10) / 10,
            projWRC: base.wRCPlus,"""

if old_lb_war in src:
    src = src.replace(old_lb_war, new_lb_war, 1)
    changes += 1
    print("4. Fixed leaderboard projWAR for two-way players")

# 5. Show TWP position label for two-way players
old_pos = 'const map = {C:"C","2":"C","3":"1B","4":"2B","5":"3B","6":"SS","7":"LF","8":"CF","9":"RF","10":"DH","D":"DH","Y":"TWP","O":"OF"};'
# This is already correct, just confirming
if '"Y":"TWP"' in src:
    print("5. Position label TWP already set (OK)")

# 6. Also handle the forward projection for two-way
# Forward projection should also include pitching WAR boost for each year
old_forward = """  const forward = useMemo(() => {
    if (!base) return [];
    if (isPitcher) return projectPitcherForward(base, player.currentAge);
    return projectForward(base, player.currentAge, player.primaryPosition?.code);
  }, [base, player, isPitcher]);"""

new_forward = """  const forward = useMemo(() => {
    if (!base) return [];
    if (isPitcher) return projectPitcherForward(base, player.currentAge);
    const hitFwd = projectForward(base, player.currentAge, player.primaryPosition?.code === "Y" ? "10" : player.primaryPosition?.code);
    // Two-way: add pitching trajectory to each year
    if (base._isTwoWay && base._pitchProj) {
      const pitchFwd = projectPitcherForward(base._pitchProj, player.currentAge);
      return hitFwd.map((h, i) => ({
        ...h,
        war: Math.round((h.war + (pitchFwd[i]?.war || 0)) * 10) / 10,
        _hitWar: h.war,
        _pitchWar: pitchFwd[i]?.war || 0,
      }));
    }
    return hitFwd;
  }, [base, player, isPitcher]);"""

if old_forward in src:
    src = src.replace(old_forward, new_forward)
    changes += 1
    print("6. Fixed forward projection to combine two-way trajectories")

open(APP, "w").write(src)
print("\nApplied %d changes" % changes)
