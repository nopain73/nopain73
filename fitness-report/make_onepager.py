import json,sys,datetime,statistics as st
d=json.load(open(sys.argv[1])); out=sys.argv[2]
Y,M=map(int,d["month"].split("-"))
C=dict(blue="#2a78d6",orange="#eb6834",aqua="#1baf7a",ink="#0b0b0b",ink2="#52514e",muted="#8a8984",grid="#e8e7e3",surf="#fcfcfb",card="#ffffff",crit="#e34948")
days=d["daily"]
def line_chart(idx,goal,unit,color,title,w=440,h=210):
    pts=[(i,r[idx]) for i,r in enumerate(days) if r[idx] is not None]
    vals=[v for _,v in pts]+[goal]; lo=min(vals)-0.5; hi=max(vals)+0.5
    L,R,T,B=40,14,30,26; pw=w-L-R; ph=h-T-B; n=len(days)
    X=lambda i:L+pw*i/(n-1); Yv=lambda v:T+ph*(hi-v)/(hi-lo)
    s=f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><text x="0" y="16" font-size="15" font-weight="700" fill="{C["ink"]}">{title}</text>'
    import math
    step=1 if hi-lo<6 else 2
    v=math.ceil(lo)
    while v<=hi:
        s+=f'<line x1="{L}" x2="{w-R}" y1="{Yv(v):.1f}" y2="{Yv(v):.1f}" stroke="{C["grid"]}"/><text x="{L-6}" y="{Yv(v)+4:.1f}" font-size="11" text-anchor="end" fill="{C["muted"]}">{v}</text>'; v+=step
    s+=f'<line x1="{L}" x2="{w-R}" y1="{Yv(goal):.1f}" y2="{Yv(goal):.1f}" stroke="{C["ink2"]}" stroke-dasharray="4 4"/><text x="{L+4}" y="{Yv(goal)+14:.1f}" font-size="11" fill="{C["ink2"]}">目标 {goal}{unit}</text>'
    # trend line
    xs=[i for i,_ in pts]; ys=[v for _,v in pts]; mx,my=st.mean(xs),st.mean(ys)
    b=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs); a=my-b*mx
    s+=f'<line x1="{X(0):.1f}" y1="{Yv(a):.1f}" x2="{X(n-1):.1f}" y2="{Yv(a+b*(n-1)):.1f}" stroke="{color}" stroke-width="2" stroke-opacity="0.35"/>'
    # segments break on gaps >3 days
    path=""; prev=None
    for i,v in pts:
        cmd="M" if prev is None or i-prev>4 else "L"; path+=f'{cmd}{X(i):.1f},{Yv(v):.1f} '; prev=i
    s+=f'<path d="{path}" fill="none" stroke="{color}" stroke-width="2" stroke-linejoin="round"/>'
    for i,v in pts: s+=f'<circle cx="{X(i):.1f}" cy="{Yv(v):.1f}" r="3.2" fill="{color}" stroke="{C["card"]}" stroke-width="1.5"/>'
    f0,fl=pts[0],pts[-1]; mn=min(pts,key=lambda t:t[1])
    for (i,v),anc in [(f0,"start"),(fl,"end")]:
        s+=f'<text x="{X(i):.1f}" y="{Yv(v)-9:.1f}" font-size="12" font-weight="700" text-anchor="{anc}" fill="{C["ink"]}">{v}</text>'
    for i in (0,9,19,n-1): s+=f'<text x="{X(i):.1f}" y="{h-6}" font-size="11" text-anchor="middle" fill="{C["muted"]}">{M}/{i+1}</text>'
    s+=f'<text x="{L+4}" y="{T+12}" font-size="11" fill="{C["ink2"]}">浅色线 = 线性趋势 {b*7:+.2f}{unit}/周</text>'
    return s+'</svg>'
def intake_chart(w=980,h=230):
    L,R,T,B=46,14,34,26; pw=w-L-R; ph=h-T-B; n=len(days); hi=5000
    Yv=lambda v:T+ph*(hi-v)/hi; bw=pw/n
    s=f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}"><text x="0" y="16" font-size="15" font-weight="700" fill="{C["ink"]}">每日摄入（kcal）</text>'
    s+=f'<rect x="{w-330}" y="5" width="10" height="10" rx="2" fill="{C["blue"]}"/><text x="{w-315}" y="14" font-size="12" fill="{C["ink2"]}">普通日</text><rect x="{w-262}" y="5" width="10" height="10" rx="2" fill="{C["orange"]}"/><text x="{w-247}" y="14" font-size="12" fill="{C["ink2"]}">≥4000</text><rect x="{w-196}" y="5" width="10" height="10" rx="2" fill="none" stroke="{C["muted"]}" stroke-dasharray="2 2"/><text x="{w-181}" y="14" font-size="12" fill="{C["ink2"]}">无记录</text>'
    for v in (0,1000,2000,3000,4000,5000):
        s+=f'<line x1="{L}" x2="{w-R}" y1="{Yv(v):.1f}" y2="{Yv(v):.1f}" stroke="{C["grid"]}"/><text x="{L-6}" y="{Yv(v)+4:.1f}" font-size="11" text-anchor="end" fill="{C["muted"]}">{v}</text>'
    for i,r in enumerate(days):
        x=L+i*bw+2; bwid=bw-4
        if r[3] is None:
            s+=f'<rect x="{x:.1f}" y="{Yv(1200):.1f}" width="{bwid:.1f}" height="{Yv(0)-Yv(1200):.1f}" rx="3" fill="none" stroke="{C["muted"]}" stroke-dasharray="2 2"/>'
        else:
            col=C["orange"] if r[3]>=4000 else C["blue"]
            s+=f'<path d="M{x:.1f},{Yv(0):.1f} V{Yv(r[3])+4:.1f} q0,-4 4,-4 h{bwid-8:.1f} q4,0 4,4 V{Yv(0):.1f}Z" fill="{col}"/>'
            if r[3]>=4000: s+=f'<text x="{x+bwid/2:.1f}" y="{Yv(r[3])-4:.1f}" font-size="10" text-anchor="middle" fill="{C["ink"]}">{r[3]}</text>'
        if (i+1)%5==0 or i==0: s+=f'<text x="{x+bwid/2:.1f}" y="{h-6}" font-size="11" text-anchor="middle" fill="{C["muted"]}">{M}/{i+1}</text>'
    t=d["trueTDEE"]
    gaps=[i for i,r in enumerate(days) if r[3] is None]
    lx=L+bw*(st.mean(gaps)+0.5) if gaps else L+pw/2
    for v,lab in ((t,f"推算真实 TDEE ≈{t}"),(1900,"下限 1900")):
        s+=f'<line x1="{L}" x2="{w-R}" y1="{Yv(v):.1f}" y2="{Yv(v):.1f}" stroke="{C["ink"]}" stroke-dasharray="5 4" stroke-width="1.2"/><text x="{lx:.1f}" y="{Yv(v)-5:.1f}" font-size="11" font-weight="700" text-anchor="middle" fill="{C["ink"]}" style="paint-order:stroke" stroke="{C["card"]}" stroke-width="3">{lab}</text>'
    return s+'</svg>'
def calendar():
    col={"S":C["blue"],"B":C["orange"],"H":C["aqua"],"SB":C["blue"],"W":"#c9c8c3","R":"#ffffff","N":"#f1f0ec"}
    first=datetime.date(Y,M,1); nd=(datetime.date(Y+(M==12),M%12+1,1)-first).days
    s='<div class="cal">'+''.join(f'<div class="wd">{w}</div>' for w in "一二三四五六日")
    s+='<div></div>'*first.weekday()
    for k in range(1,nd+1):
        t,lab=d["activity"].get(f"{k:02d}",["N","—"])
        dark=t in("S","B","H","SB"); fg="#fff" if dark else C["ink2"]
        extra=f'border-bottom:6px solid {C["orange"]};' if t=="SB" else ""
        bd=f'border:1.5px solid {C["grid"]};' if t in("R","N","W") else ""
        hatch="background-image:repeating-linear-gradient(45deg,#e2e1dc 0 2px,transparent 2px 7px);" if t=="N" else ""
        s+=f'<div class="day" style="background-color:{col[t]};color:{fg};{bd}{extra}{hatch}"><span class="dn">{k}</span><span class="dl">{lab}</span></div>'
    s+='</div><div class="leg">'+''.join(f'<span><i style="background:{c};{b}"></i>{n}</span>' for c,b,n in [(C["blue"],"","力量"),(C["orange"],"","篮球"),(C["aqua"],"","徒步/爬山"),("#c9c8c3","","仅步行"),("#fff",f"border:1.5px solid {C['grid']}","休息"),("#f1f0ec","background-image:repeating-linear-gradient(45deg,#d6d5d0 0 2px,transparent 2px 6px)","无记录")])+'</div>'
    return s
arrow={"up2":("↑↑",C["aqua"]),"up":("↑",C["aqua"]),"eq":("＝",C["ink2"]),"new":("新",C["blue"])}
kpi=''.join(f'<div class="kpi"><div class="kl">{a}</div><div class="kv">{b}<small>{u}</small></div><div class="ks">{c}</div></div>' for a,b,u,c in d["kpi"])
strength=''.join(f'<tr><td>{n}</td><td class="m">{b}</td><td class="v">{v}</td><td style="color:{arrow[j][1]};font-weight:700">{arrow[j][0]}</td></tr>' for n,b,v,j in d["strength"])
stats=''.join(f'<div class="st"><div class="kl">{a}</div><div class="sv">{b}</div><div class="ks">{c}</div></div>' for a,b,c in d["stats"])
issues=''.join(f'<li><b class="ic">!</b>{x}</li>' for x in d["issues"])
nxt=''.join(f'<li><b class="num">{i+1}</b>{x}</li>' for i,x in enumerate(d["next"]))
html=f'''<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:"WenQuanYi Zen Hei","IPAGothic",sans-serif;background:{C["surf"]};color:{C["ink"]};width:1080px;padding:36px 40px 30px}}
h1{{font-size:34px;letter-spacing:1px}}.sub{{color:{C["ink2"]};font-size:14px;margin-top:6px}}
.card{{background:{C["card"]};border:1px solid {C["grid"]};border-radius:14px;padding:18px 20px;margin-top:16px}}
.kpis{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:20px}}.kpi{{background:{C["card"]};border:1px solid {C["grid"]};border-radius:14px;padding:16px}}
.kl{{font-size:13px;color:{C["ink2"]}}}.kv{{font-size:38px;font-weight:700;margin:4px 0}}.kv small{{font-size:15px;color:{C["ink2"]};margin-left:4px}}.ks{{font-size:12px;color:{C["ink2"]};line-height:1.5}}
.row{{display:flex;gap:16px}}.row>.card{{flex:1}}
h2{{font-size:15px;margin-bottom:10px}}
.cal{{display:grid;grid-template-columns:repeat(7,1fr);gap:5px}}.wd{{font-size:11px;color:{C["muted"]};text-align:center}}
.day{{height:50px;border-radius:7px;padding:4px 6px;display:flex;flex-direction:column;justify-content:space-between}}.dn{{font-size:11px;opacity:.85}}.dl{{font-size:13px;font-weight:700;text-align:right}}
.leg{{display:flex;flex-wrap:wrap;gap:6px 12px;margin-top:10px;font-size:12px;color:{C["ink2"]}}}.leg i{{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:4px;vertical-align:-1px}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}td{{padding:7px 4px;border-bottom:1px solid {C["grid"]}}}td.m{{color:{C["muted"]}}}td.v{{font-weight:700}}th{{font-size:11px;color:{C["muted"]};text-align:left;padding:0 4px 4px;font-weight:400}}
.sts{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:14px}}.st{{border-top:1px solid {C["grid"]};padding-top:8px}}.sv{{font-size:22px;font-weight:700;margin:2px 0}}
ul{{list-style:none}}li{{font-size:14px;line-height:1.5;padding:6px 0;display:flex;gap:10px;align-items:flex-start}}
.ic{{flex:none;width:20px;height:20px;border-radius:50%;background:{C["crit"]};color:#fff;font-size:13px;text-align:center;line-height:20px}}
.num{{flex:none;width:20px;height:20px;border-radius:6px;background:{C["ink"]};color:#fff;font-size:12px;text-align:center;line-height:20px}}
.foot{{font-size:11px;color:{C["muted"]};margin-top:14px;line-height:1.6}}
</style></head><body>
<h1>{d["title"]}</h1><div class="sub">数据：Notion 减肥日记 + Strava · 东京时间 · 斜率/TDEE 为根据日记推算</div>
<div class="kpis">{kpi}</div>
<div class="row"><div class="card">{line_chart(1,d["goal"]["weight"],"kg",C["blue"],"晨重（kg）")}</div><div class="card">{line_chart(2,d["goal"]["waist"],"cm",C["aqua"],"腰围（cm）")}</div></div>
<div class="card">{intake_chart()}</div>
<div class="row"><div class="card" style="flex:1.15"><h2>训练日历</h2>{calendar()}</div>
<div class="card"><h2>力量基准</h2><table><tr><th>动作</th><th>基准</th><th>本月最好</th><th></th></tr>{strength}</table><div class="sts">{stats}</div></div></div>
<div class="row"><div class="card"><h2>本月问题</h2><ul>{issues}</ul></div><div class="card"><h2>下月只盯这几件</h2><ul>{nxt}</ul></div></div>
<div class="foot">详细版见 Notion「健身 / 月报 · {d["month"]}」。无记录日不补记、不外推；日记与 Strava 冲突时取消耗较大的一份。</div>
</body></html>'''
open(out,"w").write(html)
