// The theme editor shows what the engine draws: exports a theme from the editor page, builds the C4 example with it
// through skills/ai-diagrams/scripts/build.py, and compares both renderings pixel by pixel.
// Usage: PLAYWRIGHT_FROM=<folder with playwright installed> node site/src/parity.mjs   (after npm run build; needs Chrome)
import {createRequire} from 'node:module';
import {mkdtemp, readFile, writeFile, mkdir} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {dirname, join, resolve} from 'node:path';
import {fileURLToPath, pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createServer} from 'node:http';
import {extname} from 'node:path';
import assert from 'node:assert/strict';
import {GROUPS} from './preview.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const repo = resolve(here, '../..');
const out = resolve(here, '../out');
assert(process.env.PLAYWRIGHT_FROM, 'Set PLAYWRIGHT_FROM to a folder where playwright is installed');
const {chromium} = createRequire(resolve(process.env.PLAYWRIGHT_FROM, 'package.json'))('playwright');
const chrome = process.env.POSTER_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const tmp = await mkdtemp(join(tmpdir(), 'ai-diagrams-parity-'));
const fontsCss = await readFile(join(out, 'assets/diagram-fonts.css'), 'utf8');

// 1. A theme unlike both presets: every color drawn from a fixed seed, other font families.
const theme = JSON.parse(await readFile(join(repo, 'skills/ai-diagrams/themes/ai-diagrams.json'), 'utf8'));
let seed = 20261107;
const random = () => (seed = (seed * 48271) % 2147483647) / 2147483647;
for (const group of Object.keys(GROUPS)) for (const key of GROUPS[group]) theme[group][key] = '#' + Math.floor(random() * 0xffffff).toString(16).padStart(6, '0').toUpperCase();
theme.name = 'parity';
theme.fonts = {text: 'Inter', mono: 'JetBrains Mono'};
const input = join(tmp, 'input.json');
await writeFile(input, JSON.stringify(theme, null, 2));

// the pages need an http origin: under file:// every file is an opaque origin to Chrome
const types = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2', '.json': 'application/json'};
const server = createServer(async (request, response) => {
  try {
    const path = join(out, decodeURIComponent(new URL(request.url, 'http://x').pathname));
    response.writeHead(200, {'content-type': types[extname(path)] || 'application/octet-stream'});
    response.end(await readFile(path));
  } catch { response.writeHead(404); response.end(); }
}).listen(0, '127.0.0.1');
await new Promise(r => server.once('listening', r));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({executablePath: chrome, headless: true});
try {
  // Each case: the tab in the editor, the example source, and how the engine builds it.
  const scripts = join(repo, 'skills/ai-diagrams');
  const CASES = [
    {id: 'c4', tab: /C4/, src: 'billing-c4.html', out: 'billing-c4.html', build: f => ['python3', join(scripts, 'scripts/build.py'), f]},
    {id: 'bpmn', tab: /BPMN/, src: 'access-recovery.json', out: 'access-recovery.html', build: f => ['python3', join(scripts, 'bpmn/build_bpmn.py'), f]},
    {id: 'swimlanes', tab: /Swimlanes|Raias|Carriles/, src: 'limit-increase.html', out: 'limit-increase.html', build: f => ['python3', join(scripts, 'scripts/conceptual.py'), f]},
    {id: 'er-schema', tab: /ER diagram|DER|Diagrama ER/, src: 'er-billing.html', out: 'er-billing.html', build: f => ['python3', join(scripts, 'scripts/build.py'), f]},
  ];
  const sourceOf = (lang, c) => lang === 'pt-BR' ? join(repo, 'examples', c.id, 'output/_src', c.src) : join(here, '..', 'examples-i18n', lang, c.id, 'output/_src', c.src);
  const compare = (a, b) => execFileSync('python3', ['-c', `
import sys
from PIL import Image, ImageChops
a, b = (Image.open(p).convert('RGB') for p in sys.argv[1:3])
if a.size != b.size:
    print('size', a.size, b.size)
else:
    d = ImageChops.difference(a, b)
    n = sum(1 for p in d.get_flattened_data() if p != (0, 0, 0)) if d.getbbox() else 0
    print('different pixels', n, 'of', a.size[0] * a.size[1])
`, a, b], {encoding: 'utf8'}).trim();
  async function shot(name, html) {
    const ctx = await browser.newContext({viewport: {width: 1760, height: 1000}, deviceScaleFactor: 1});
    await ctx.route(/fonts\.googleapis\.com/, route => route.fulfill({contentType: 'text/css', body: fontsCss}));
    await ctx.route(/fonts\.gstatic\.com/, route => route.abort());
    const p = await ctx.newPage();
    const file = join(tmp, `${name}.html`);
    // the editor copy refers to the shared fonts by a relative path; point it at the built file
    await writeFile(file, html.replace('../../assets/diagram-fonts.css', pathToFileURL(join(out, 'assets/diagram-fonts.css')).href));
    await p.goto(pathToFileURL(file).href);
    await p.evaluate(() => document.fonts.ready);
    await p.waitForTimeout(1500);
    const path = join(tmp, `${name}.png`);
    await p.screenshot({path, fullPage: true});
    await ctx.close();
    return path;
  }

  async function editorShot(name, url, css) {
    const ctx = await browser.newContext({viewport: {width: 1760, height: 1000}, deviceScaleFactor: 1});
    await ctx.route(u => !u.href.startsWith(origin), route => route.abort());
    const p = await ctx.newPage();
    await p.goto(url);
    await p.evaluate(() => document.fonts.ready);
    await p.evaluate(value => window.postMessage({type: 'ai-diagrams:theme', css: value}, '*'), css);
    // BPMN repaints by importing the XML again; wait until it says so
    if (url.endsWith('/bpmn.html')) await p.waitForFunction(() => document.body.dataset.repainted, null, {timeout: 20000});
    await p.waitForTimeout(1500);
    await p.evaluate(() => document.fonts.ready);
    const path = join(tmp, `${name}.png`);
    await p.screenshot({path, fullPage: true});
    await ctx.close();
    return path;
  }

  const results = [];
  for (const lang of ['en', 'es', 'pt-BR']) {
    // 2. The editor: open the theme file, export it, and read every case as the canvas shows it.
    const context = await browser.newContext({viewport: {width: 1440, height: 1000}, acceptDownloads: true});
    await context.route(url => !url.href.startsWith(origin), route => route.abort());
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(`${origin}/${lang === 'en' ? '' : `${lang}/`}04-themes.html`);
    await page.locator('input[type=file]').setInputFiles(input);
    const download = page.waitForEvent('download');
    await page.locator('.studio-actions button').last().click();
    const exported = join(tmp, `exported-${lang}.json`);
    await (await download).saveAs(exported);
    const exportedTheme = JSON.parse(await readFile(exported, 'utf8'));
    assert.equal(exportedTheme.schema_version, 2);
    assert.deepEqual(exportedTheme.colors, theme.colors);
    for (const c of CASES) {
      await page.getByRole('tab', {name: c.tab}).click();
      await page.waitForTimeout(2500);
      const frame = page.frames().find(f => f.url().endsWith(`/diagrams/${lang}/${c.id}.html`));
      assert(frame, `${lang}/${c.id}: iframe not found`);
      const rootCss = await frame.evaluate(() => document.getElementById('ai-diagrams-theme').textContent);
      assert(rootCss.includes(theme.colors.ink), `${lang}/${c.id}: the editor did not apply the theme`);

      // 3. The engine: the same source built with the exported file, through its own gate.
      const src = join(tmp, `engine-${lang}-${c.id}/_src`);
      await mkdir(src, {recursive: true});
      await writeFile(join(src, c.src), await readFile(sourceOf(lang, c), 'utf8'));
      execFileSync(c.build(join(src, c.src))[0], [...c.build(join(src, c.src)).slice(1), '--theme', exported], {stdio: 'ignore'});
      const engineHtml = await readFile(join(src, '..', c.out), 'utf8');

      // 4. Both rendered at native width with the same font files.
      // the editor's diagram page at native size, painted with exactly the :root the editor sent to its canvas
      const result = compare(await editorShot(`editor-${lang}-${c.id}`, `${origin}/diagrams/${lang}/${c.id}.html`, rootCss), await shot(`engine-${lang}-${c.id}`, engineHtml));
      console.log(`${lang}/${c.id}: ${result}`);
      results.push([`${lang}/${c.id}`, result]);
    }
    assert.deepEqual(errors, [], `${lang}: page errors`);
    await context.close();
  }
  console.log(`screenshots in ${tmp}`);
  // anti-aliasing of glyph edges varies by a few pixels between two renders of the same page; anything above 0.002% is a real difference
  const failed = results.filter(([, r]) => { const m = r.match(/different pixels (\d+) of (\d+)/); return !m || Number(m[1]) / Number(m[2]) > 0.00002; });
  assert.deepEqual(failed, [], 'the editor and the engine render differently');
  console.log(`parity: ${results.length} diagrams in 3 languages; the exported theme, built by the engine, renders as the editor shows it (largest difference ${Math.max(...results.map(([, r]) => Number(r.match(/different pixels (\d+)/)[1])))} px)`);
} finally {
  await browser.close();
  server.close();
}
