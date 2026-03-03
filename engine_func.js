// VIAcast Statcast Projection Engine
function projectFromStatcast(sP, age, posCode, playerName, playerId) {
  const S = sP.seasons || {}, yrs = Object.keys(S).sort().reverse();
  if (!yrs.length) return null;
  const W=[.55,.30,.15], lat=S[yrs[0]]||{}, pa0=lat.pa||0;
  let wxw=0,wev=0,wbr=0,tw1=0;
  yrs.forEach((yr,i)=>{const s=S[yr],w=W[i]||.05,pw=w*Math.min(1,(s.pa||0)/400);
    if(s.xwoba!=null){wxw+=s.xwoba*pw;tw1+=pw}if(s.avg_ev!=null)wev+=s.avg_ev*pw;
    if(s.barrel_pct!=null)wbr+=s.barrel_pct*pw});
  const pXw=tw1>0?wxw/tw1:.310, pEV=tw1>0?wev/tw1:87, pBrl=tw1>0?wbr/tw1:6;
  const ev5T=yrs.length>=2&&S[yrs[0]]?.ev50&&S[yrs[1]]?.ev50?S[yrs[0]].ev50-S[yrs[1]].ev50:0;
  let wbb=0,wk=0,wos=0,wzs=0,tw2=0;
  yrs.forEach((yr,i)=>{const s=S[yr],w=W[i]||.05,pw=w*Math.min(1,(s.pa||0)/200);
    if(s.bb_pct!=null){wbb+=s.bb_pct*pw;tw2+=pw}if(s.k_pct!=null)wk+=s.k_pct*pw;
    if(s.o_swing_pct!=null)wos+=s.o_swing_pct*pw;if(s.z_swing_pct!=null)wzs+=s.z_swing_pct*pw});
  const pBB=tw2>0?wbb/tw2:.08, pK=tw2>0?wk/tw2:.22;
  const pOs=tw2>0?wos/tw2:null, pZs=tw2>0?wzs/tw2:null;
  const selI=(pOs&&pZs&&pOs>0)?pZs/pOs:null;
  const chT=yrs.length>=2&&S[yrs[0]]?.o_swing_pct!=null&&S[yrs[1]]?.o_swing_pct!=null?S[yrs[1]].o_swing_pct-S[yrs[0]].o_swing_pct:0;
  const bsT=yrs.length>=2&&S[yrs[0]]?.bat_speed&&S[yrs[1]]?.bat_speed?S[yrs[0]].bat_speed-S[yrs[1]].bat_speed:0;
  const spd=sP.sprint_speed||null; let bsr=0;
  if(spd){let a2=spd;if(age>28)a2-=(age-28)*.15;bsr=a2>=30?5:a2>=29?3.5:a2>=28?2:a2>=27?0:a2>=25.5?-2:-4}
  const oaa=sP.oaa!=null?sP.oaa:null;
  const dPk=(posCode==="6"||posCode==="8")?26:(posCode==="4"||posCode==="5")?27:28;
  const dAg=Math.max(.3,1-Math.max(0,age-dPk)*.06);
  let dR=0; if(oaa!==null)dR=oaa*.6*1.5*dAg;
  const ap=getAP(posCode), pk=ap.peak; let af=1;
  if(age<pk)af=Math.pow(1.02,pk-age);
  else if(age<=32)af=Math.pow(.985,age-pk);
  else af=Math.pow(.985,32-pk)*Math.pow(.97,age-32);
  let tb=0;
  if(yrs.length>=2){const x0=S[yrs[0]]?.xwoba,x1=S[yrs[1]]?.xwoba;
    const x2=yrs.length>=3?S[yrs[2]]?.xwoba:null;
    if(x0!=null&&x1!=null){const d1=x0-x1,d2=x2!=null?x1-x2:null;
      if(d2!=null&&Math.sign(d1)===Math.sign(d2)&&d1>0)tb+=d1*.3;else tb+=d1*.15}}
  if(chT>.02)tb+=chT*.15; if(ev5T>1.5)tb+=.005; if(bsT<-1.5)tb-=.008;
  const axw=Math.max(.2,Math.min(.5,pXw+tb))*af;
  let db=0;
  if(selI!=null){if(selI>3.5)db=Math.min(5,(selI-3.5)*3);else if(selI<2)db=Math.max(-4,(selI-2)*3)}
  if(pK<.15)db+=3;else if(pK>.30)db-=2; if(pBB>.12)db+=2;
  const wrc=Math.max(60,Math.min(190,Math.round(((axw-.315)/.01)*3.2+100+db)));
  const ops=Math.max(.52,Math.min(1.15,wrc*.0072+.002));
  const avg=lat.xba!=null?Math.max(.18,Math.min(.34,lat.xba*af)):Math.max(.2,Math.min(.32,(ops-.1)/2.5));
  const obp=Math.max(.26,Math.min(.45,avg+pBB*.85+.02));
  const slg=Math.max(.3,Math.min(.7,ops-obp+avg));
  const ePA=Math.min(700,Math.max(200,pa0*.97));
  const hr=Math.round(Math.max(0,pBrl/100*(ePA*.75)*.24*af));
  const bat=((wrc-100)/100)*ePA*.115, pos=ap.pa*(ePA/600), rep=20*(ePA/600);
  const rW=(bat+dR*(ePA/600)+bsr*(ePA/600)+pos+rep)/9.5;
  const fv=getPlayerFV(playerId,playerName);let fW=rW;
  if(fv){const b=FV_BENCHMARKS[Math.min(70,Math.max(40,fv))]||FV_BENCHMARKS[50];
    fW=Math.max(b.war*.3,Math.min(b.war*1.8,rW))}
  fW=Math.round(fW*10)/10;
  const tPA=yrs.reduce((s,yr)=>s+(S[yr]?.pa||0),0);
  return{ops:Math.round(ops*1e3)/1e3,obp:Math.round(obp*1e3)/1e3,
    slg:Math.round(slg*1e3)/1e3,avg:Math.round(avg*1e3)/1e3,
    wRCPlus:wrc,baseWAR:fW,estPA:Math.round(ePA),hr:hr,
    paReliability:Math.min(95,Math.round((tPA/1200)*95)),
    highestLevel:"MLB",peakAge:pk,ageForLevel:0,translationNote:null,
    _statcast:{xwoba:Math.round(axw*1e3)/1e3,projEV:Math.round(pEV*10)/10,
      projBarrel:Math.round(pBrl*10)/10,
      projK:pK!=null?Math.round(pK*1e3)/10:null,
      projBB:pBB!=null?Math.round(pBB*1e3)/10:null,
      sprintSpeed:spd,oaa:oaa,
      trendBoost:Math.round(tb*1e3)/1e3,
      selectivityIndex:selI?Math.round(selI*100)/100:null}};
}

function projectPlayer(splits, age, posCode, name, id) {
  const savP = getSavantPlayer(id, name);
  if (savP && Object.keys(savP.seasons || {}).length > 0) {
    const sc = projectFromStatcast(savP, age, posCode, name, id);
    if (sc) return sc;
  }
  return splits && splits.length
    ? projectFromSeasons(splits, age, posCode, name, id)
    : null;
}
