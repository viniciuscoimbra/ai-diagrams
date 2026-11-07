import { readFile, writeFile, readdir, mkdir, mkdtemp, rm, copyFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import { dirname, resolve, join } from 'node:path';
import { tmpdir } from 'node:os';
import assert from 'node:assert/strict';

const here = dirname(fileURLToPath(import.meta.url));
const brand = resolve(here, '..');
const plyngo = resolve(brand, '../../plyngo');
const refy = join(plyngo, 'node_modules/@refy/ui');
const require = createRequire(join(plyngo, 'package.json'));
const { build } = require('esbuild');
assert.equal(JSON.parse(await readFile(join(refy, 'package.json'), 'utf8')).version, '0.4.0');
for (const name of ['react', 'react-dom']) {
  assert.equal(require(`${name}/package.json`).version, '19.2.4');
}
const palette = JSON.parse(await readFile(join(brand, 'paleta.json'), 'utf8'));
assert(Array.isArray(palette.colors) && Array.isArray(palette.pairs), 'Expected colors and pairs in paleta.json');
assert(palette.colors.length >= 4 && palette.colors.length <= 6, 'The brand palette needs 4 to 6 colors');
assert.equal(palette.pairs.length, palette.colors.length * (palette.colors.length - 1) / 2, 'Every multiply pair must be present');
const assets = {};
for (const file of (await readdir(join(brand, 'assets'))).filter(file => /\.(svg|png)$/.test(file))) {
  const mime = file.endsWith('.svg') ? 'image/svg+xml' : 'image/png';
  assets[file] = `data:${mime};base64,${(await readFile(join(brand, 'assets', file))).toString('base64')}`;
}
const brandData = { assets, palette };
const options = {
  bundle: true, write: false, minify: true, jsx: 'automatic',
  alias: { '@refy/ui': join(refy, 'dist/index.js'), react: join(plyngo, 'node_modules/react'), 'react-dom': join(plyngo, 'node_modules/react-dom') },
  define: { 'process.env.NODE_ENV': '"production"' },
  plugins: [{ name: 'brand-data', setup(build) {
    build.onResolve({ filter: /^brand-data$/ }, () => ({ path: 'brand-data', namespace: 'brand' }));
    build.onLoad({ filter: /.*/, namespace: 'brand' }, () => ({ contents: `export default ${JSON.stringify(brandData)}`, loader: 'js' }));
  } }],
};
const client = await build({ ...options, entryPoints: [join(here, 'client.jsx')], platform: 'browser', format: 'iife' });
const server = await build({ ...options, platform: 'node', format: 'cjs', stdin: {
  contents: "import React from 'react'; import {renderToString} from 'react-dom/server'; import {App} from './app.jsx'; export const markup = renderToString(React.createElement(App));",
  resolveDir: here,
} });
const temp = await mkdtemp(join(tmpdir(), 'ai-diagrams-brand-'));
let markup;
try {
  const output = join(temp, 'ssr.cjs');
  await writeFile(output, server.outputFiles[0].text);
  markup = require(output).markup;
} finally { await rm(temp, { recursive: true, force: true }); }

const fontSource = await readFile(join(plyngo, 'design-system/plyngo-tokens.css'), 'utf8');
const fonts = [];
for (const face of fontSource.matchAll(/@font-face\s*\{[^}]+\}/g)) {
  const url = face[0].match(/url\(([^)]+)\)/)[1];
  const file = url.replace(/^['"]|['"]$/g, '').replace('/plyngo-assets/', 'prototipo/assets/');
  const bytes = await readFile(join(plyngo, file));
  const mime = file.endsWith('.woff2') ? 'font/woff2' : 'font/ttf';
  fonts.push(face[0].replace(url, `"data:${mime};base64,${bytes.toString('base64')}"`));
}
const css = (await Promise.all(['src/tokens/tokens.css', 'src/styles/global.css', 'dist/style.css'].map(file => readFile(join(refy, file), 'utf8')))).join('\n').replace(/^@import[^\n]*\n/gm, '');
// Keep the same Plyngo token layers; only scope them to this offline guide.
const neutralBase = (await readFile(join(plyngo, 'prototipo/ui/tokens.css'), 'utf8')).replaceAll(':root', '.brandkit');
const neutralBridge = fontSource.replace(/@font-face\s*\{[^}]+\}/g, '').replaceAll('[data-plyngo-theme]', '.brandkit[data-theme]').replaceAll('[data-plyngo-theme=dark]', '.brandkit[data-theme=dark]');
const specimenTokens = '.brandkit{--brand-papel:#fff;--brand-tinta:#171717}';
const layout = await readFile(join(here, 'layout.css'), 'utf8');
const html = `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ai-diagrams · Brandkit</title><meta name="description" content="Assinatura, cor, tipografia, tom de voz e aplicações da marca ai-diagrams.">
<link rel="icon" href="${assets['favicon.svg']}">
<style>${fonts.join('\n')}\n${css}\n${neutralBase}\n${neutralBridge}\n${specimenTokens}\n${layout}</style>
</head><body><div id="root">${markup}</div>
<script>${client.outputFiles[0].text.replaceAll('</script', '<\\/script')}</script></body></html>`;
assert(!/<(?:script|link|img)[^>]+(?:src|href)="(?:https?:|\.\.?\/)/i.test(html), 'All rendered resources must be embedded');
assert(!/@import\s/.test(css), 'CSS must not fetch another stylesheet');
assert.equal(fonts.length, 3, 'Expected Plyngo Inter and two JetBrains Mono weights');
assert(!/url\(["']?\/(?!\/)/.test(neutralBridge), 'Theme assets must be embedded');
await writeFile(join(brand, 'brandkit.html'), html);

const licenses = join(brand, 'licenses');
await mkdir(licenses, { recursive: true });
const fontsDir = process.env.BRAND_FONTS;
assert(fontsDir, 'Set BRAND_FONTS to the local folder with the Inter and JetBrains Mono OFL files');
await writeFile(join(licenses, 'refy-NOTICE.txt'), '@refy/ui 0.4.0\nOrigin: plyngo/node_modules/@refy/ui.\nThe package declares license: UNLICENSED and supplies no LICENSE file.\nThis guide does not assign an open-source license to that private package.\n');
await copyFile(join(plyngo, 'node_modules/react/LICENSE'), join(licenses, 'react-MIT.txt'));
await copyFile(join(plyngo, 'node_modules/react-dom/LICENSE'), join(licenses, 'react-dom-MIT.txt'));
for (const name of ['inter', 'jetbrains-mono']) {
  await copyFile(join(fontsDir, `${name}-OFL.txt`), join(licenses, `${name}-OFL.txt`));
}
console.log(`brandkit.html: ${Math.round(Buffer.byteLength(html) / 1024)} KB, ${Object.keys(assets).length} assets, ${fonts.length} embedded font faces; @refy/ui 0.4.0 + Plyngo neutral tokens.`);
