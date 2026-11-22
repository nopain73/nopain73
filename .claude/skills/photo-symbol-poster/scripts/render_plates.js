#!/usr/bin/env node
// Render every [data-plate] group of a symbol SVG to its own transparent PNG,
// so compose.py can print them one ink at a time (that is what makes the
// overprint and mis-registration look like real print instead of a filter).
// Usage: node render_plates.js symbol.svg outdir [width height]
const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

(async () => {
  const [svgPath, outDir, w = '2400', h = '1600'] = process.argv.slice(2);
  if (!svgPath || !outDir) { console.error('usage: render_plates.js symbol.svg outdir [w h]'); process.exit(2); }
  const W = parseInt(w), H = parseInt(h);
  fs.mkdirSync(outDir, { recursive: true });
  const svg = fs.readFileSync(svgPath, 'utf8');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
  await page.setContent(`<!doctype html><html><body style="margin:0;background:transparent">${svg}</body></html>`);
  await page.evaluate(([W, H]) => {
    const s = document.querySelector('svg');
    s.setAttribute('width', W); s.setAttribute('height', H); s.style.display = 'block';
  }, [W, H]);
  await page.evaluate(() => document.fonts.ready);
  const plates = await page.evaluate(() => {
    const s = document.querySelector('svg');
    return {
      paper: s.getAttribute('data-paper'),
      viewBox: s.getAttribute('viewBox'),
      plates: [...document.querySelectorAll('[data-plate]')].map(e => ({
        name: e.getAttribute('data-plate'), register: e.getAttribute('data-register') || '' })),
    };
  });
  if (!plates.plates.length) { console.error('no [data-plate] groups found in the SVG'); process.exit(1); }
  for (let i = 0; i < plates.plates.length; i++) {
    await page.evaluate(i => {
      document.querySelectorAll('[data-plate]').forEach((e, j) => { e.style.display = j === i ? '' : 'none'; });
    }, i);
    const file = `${String(i).padStart(2, '0')}_${plates.plates[i].name}.png`;
    await page.screenshot({ path: path.join(outDir, file), omitBackground: true });
    plates.plates[i].file = file;
  }
  fs.writeFileSync(path.join(outDir, 'plates.json'), JSON.stringify(plates, null, 2));
  await browser.close();
  console.log(`rendered ${plates.plates.length} plates -> ${outDir}`);
})().catch(e => { console.error(e); process.exit(1); });
