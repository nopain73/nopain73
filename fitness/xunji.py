#!/usr/bin/env python3
"""拉取训记某一天的训练，输出「训练」列需要的摘要。

用法: python3 fitness/xunji.py 2026-11-15 [--json out.json]

鉴权: Key 存在云环境的网络密钥里，由代理自动注入 Authorization 头，
脚本里不放 Key。限频: 完整数据同一天 30 秒一次。

容量口径（2026-11-20 起）: 已打勾组的 重量×次数 之和，热身组也算；
未打勾组不算；没填重量的组（如腹肌轮）按 0。
"""
import gzip, json, sys, urllib.request
from datetime import datetime, timezone, timedelta

URL = "https://trains.xunjiapp.cn/api_trains_for_llm_v2"
JST = timezone(timedelta(hours=9))


def fetch(datestr):
    body = json.dumps({"schema_version": "train_open_api_v2", "datestr": datestr,
                       "include_full_data": True}).encode()
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "Content-Type": "application/json", "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return json.loads(raw)


def num(x):
    try:
        return float(x or 0)
    except (TypeError, ValueError):
        return 0.0


def fmt(x):
    v = num(x)
    return str(int(v)) if v == int(v) else str(v)


def summarize(data):
    trains = data.get("res", {}).get("trains", [])
    if not trains:
        print("当天训记没有记录")
        return
    for t in trains:
        mins = (t["end"] - t["start"]) / 60000
        st = datetime.fromtimestamp(t["start"] / 1000, JST).strftime("%H:%M")
        print(f"== {t.get('title') or '(无标题)'}  {st}起 {mins:.1f}min  note={t.get('note')!r}")
        if t.get("heartRate"):
            print("   心率:", {k: t["heartRate"].get(k) for k in ("avg", "max", "min")})
        vol = 0.0
        for m in t["movements"]:
            parts, warm, formal, undone = [], 0, 0, 0
            for s in m.get("sets", []):
                if s.get("metrics"):
                    parts.append(json.dumps(s["metrics"], ensure_ascii=False))
                    continue
                w, r = s.get("weight"), s.get("reps")
                tag = "热" if s.get("setType") == "热" else ""
                txt = f"{tag}{fmt(w)}×{fmt(r)}" if num(w) else f"{tag}×{fmt(r)}"
                if not s.get("done"):
                    txt += "(未)"
                    undone += 1
                else:
                    vol += num(w) * num(r)
                    if tag:
                        warm += 1
                    else:
                        formal += 1
                if s.get("note") or s.get("comment"):
                    txt += f"[{s.get('note','')}{s.get('comment','')}]"
                parts.append(txt)
            note = f"  备注:{m['note']}" if m.get("note") else ""
            print(f"- {m['name']}（{m.get('type') or '?'}）正式{formal} 热{warm} 未{undone}: {' '.join(parts)}{note}")
        print(f"   容量(已打勾含热身) ≈ {vol/1000:.2f} 吨")


if __name__ == "__main__":
    d = fetch(sys.argv[1])
    if "--json" in sys.argv:
        json.dump(d, open(sys.argv[sys.argv.index("--json") + 1], "w"), ensure_ascii=False, indent=1)
    summarize(d)
