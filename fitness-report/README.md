# 健身月报一图流

每月 1 号由定时任务生成：从 Notion「减肥日记」统计上个月数据 → 写 `data-YYYY-MM.json` → 渲染 PNG。

```
python3 make_onepager.py data-YYYY-MM.json onepager-YYYY-MM.html
node shot.js "$PWD/onepager-YYYY-MM.html" "$PWD/月报-YYYY-MM.png"
```

`data-2026-10.json` 是字段格式样例（daily: [日期, 晨重, 腰围, 摄入, 蛋白]；activity 类型 S=力量 B=篮球 H=徒步 SB=力量+篮球 W=仅步行 R=休息 N=无记录）。
