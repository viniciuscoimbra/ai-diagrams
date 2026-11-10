// Full-page captures of every page at 1440 px and 390 px, light and dark, into site/captures/ (not committed).
// Usage: PLAYWRIGHT_FROM=<folder with playwright installed> node site/src/capture.mjs   (after npm run build; needs Chrome)
import {createRequire} from 'node:module';
import {createServer} from 'node:http';
import {readFile, mkdir} from 'node:fs/promises';
import {dirname, extname, join, resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import assert from 'node:assert/strict';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const out = join(root, 'out');
assert(process.env.PLAYWRIGHT_FROM, 'Set PLAYWRIGHT_FROM to a folder where playwright is installed');
const {chromium} = createRequire(resolve(process.env.PLAYWRIGHT_FROM, 'package.json'))('playwright');
const types = {'.html': 'text/html', '.css': 'text/css', '.js': 'text/javascript', '.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2'};
const server = createServer(async (request, response) => {
  try {
    const path = join(out, decodeURIComponent(new URL(request.url, 'http://x').pathname));
    response.writeHead(200, {'content-type': types[extname(path)] || 'application/octet-stream'});
    response.end(await readFile(path));
  } catch { response.writeHead(404); response.end(); }
}).listen(0, '127.0.0.1');
await new Promise(r => server.once('listening', r));
const origin = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({executablePath: process.env.POSTER_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true});
await mkdir(join(root, 'captures'), {recursive: true});
const pages = ['01-home', '02-diagrams', '03-aws-architecture', '04-themes', '05-compatibility', '06-brand', '07-import'];
try {
  for (const page of pages) for (const width of [1440, 390]) for (const mode of ['light', 'dark']) {
    const context = await browser.newContext({viewport: {width, height: 900}, colorScheme: mode});
    await context.route(url => !url.href.startsWith(origin), route => route.abort());
    const tab = await context.newPage();
    const errors = [];
    tab.on('pageerror', error => errors.push(error.message));
    await tab.goto(`${origin}/${page}.html${mode === 'dark' ? '?theme=dark' : ''}`);
    await tab.evaluate(() => document.fonts.ready);
    await tab.waitForTimeout(1500);
    const overflow = await tab.evaluate(() => document.documentElement.scrollWidth - innerWidth);
    await tab.screenshot({path: join(root, 'captures', `${page}-${width}-${mode}.png`), fullPage: true});
    console.log(`${page} ${width} ${mode}: horizontal overflow ${overflow}px, page errors ${errors.length}`);
    await context.close();
  }
} finally {
  await browser.close();
  server.close();
}
