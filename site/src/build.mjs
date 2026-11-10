// Builds the static site in out/: one HTML per page and language, shared CSS, scripts and fonts in out/assets/,
// and one HTML per diagram in out/diagrams/<lang>/, loaded by the pages in an iframe.
// Every dependency comes from this folder's package.json (npm install); nothing is read from other repositories.
import {readFile, writeFile, readdir, mkdir, mkdtemp, rm, copyFile} from 'node:fs/promises';
import {existsSync} from 'node:fs';
import {createRequire} from 'node:module';
import {fileURLToPath} from 'node:url';
import {dirname, resolve, join, extname, basename} from 'node:path';
import assert from 'node:assert/strict';
import {execFileSync} from 'node:child_process';
import {themeTokens, tokenList, validate, ROOT} from './preview.mjs';
import {languages, translator, importGateMessage} from './i18n.mjs';
import {brandPreview} from './brand-preview.mjs';
import {compatibility} from './compatibility.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const project = resolve(here, '..');
const repo = resolve(project, '..');
const brand = join(repo, 'brand');
const skill = join(repo, 'skills/ai-diagrams');
const out = join(project, 'out');
const require = createRequire(join(project, 'package.json'));
const {build} = require('esbuild');
const ui = join(project, 'node_modules/@refy-design/web');
assert.equal(JSON.parse(await readFile(join(ui, 'package.json'), 'utf8')).version, '1.0.1');
for (const name of ['react', 'react-dom']) assert.equal(require(`${name}/package.json`).version, '19.2.4');
await rm(out, {recursive: true, force: true});
await mkdir(join(out, 'assets/fonts'), {recursive: true});
await mkdir(join(out, 'assets/brand'), {recursive: true});

const mime = {'.svg': 'image/svg+xml', '.png': 'image/png', '.woff2': 'font/woff2', '.ttf': 'font/ttf'};
const dataUrl = async path => `data:${mime[extname(path)]};base64,${(await readFile(path)).toString('base64')}`;
const write = async (path, text) => { await mkdir(dirname(path), {recursive: true}); await writeFile(path, text); return Buffer.byteLength(text); };

// Brand files are copied once; pages refer to them by path.
const brandFiles = (await readdir(join(brand, 'assets'))).filter(file => /\.(svg|png)$/.test(file));
for (const file of brandFiles) await copyFile(join(brand, 'assets', file), join(out, 'assets/brand', file));
const palette = JSON.parse(await readFile(join(brand, 'paleta.json'), 'utf8'));
const themes = {};
for (const name of ['ai-diagrams', 'paper']) themes[name] = validate(JSON.parse(await readFile(join(skill, `themes/${name}.json`), 'utf8')));

// Fonts: the OFL files shipped in the component package, plus Public Sans kept in src/fonts.
const fontFamilies = ['IBM Plex Sans', 'IBM Plex Mono', 'Public Sans', 'Source Code Pro', 'Inter', 'JetBrains Mono'];
const uiFonts = join(ui, 'src/styles');
const availableFaces = await readFile(join(uiFonts, 'fonts.css'), 'utf8');
const faces = family => [...availableFaces.matchAll(/@font-face\s*\{[^}]+\}/g)].map(match => match[0]).filter(face => face.includes(`'${family}'`));
const fontUrl = face => face.match(/url\(([^)]+)\)/)[1].replace(/^['"]|['"]$/g, '');
async function embedFaces(list) {
  return Promise.all(list.map(async face => face.replace(fontUrl(face), `"${await dataUrl(resolve(uiFonts, fontUrl(face)))}"`)));
}
const publicSans = `@font-face{font-family:'Public Sans';font-style:normal;font-weight:100 900;font-display:swap;src:url("${await dataUrl(join(here, 'fonts/public-sans.ttf'))}") format('truetype')}`;
// The site shell links its two families from files; diagrams get every family as data in one shared stylesheet, so a diagram file also works on its own.
const shellFaces = [];
for (const face of ['Inter', 'JetBrains Mono'].flatMap(faces)) {
  const file = basename(fontUrl(face));
  await copyFile(resolve(uiFonts, fontUrl(face)), join(out, 'assets/fonts', file));
  shellFaces.push(face.replace(fontUrl(face), `fonts/${file}`));
}
assert.equal(shellFaces.length, 2);
const diagramFonts = [...await embedFaces(fontFamilies.flatMap(faces)), publicSans].join('\n');
await write(join(out, 'assets/diagram-fonts.css'), diagramFonts);
const specimenFonts = await embedFaces(['Inter', 'JetBrains Mono'].flatMap(faces));

const translationsByLanguage = Object.fromEntries(languages.map(language => [language, {}]));
for (const file of ['ui.tsv', 'content.tsv']) {
  for (const line of (await readFile(join(here, 'locales', file), 'utf8')).trim().split('\n')) {
    const [key, pt, es, extra] = line.split('\t');
    assert(key && pt && es && !extra, `Incomplete translation: ${file}: ${key}`);
    for (const [language, value] of [['pt-BR', pt], ['es', es]]) {
      const previous = translationsByLanguage[language][key];
      assert(!previous || previous === value, `Conflicting translation: ${key}`);
      translationsByLanguage[language][key] = value;
    }
  }
}

const iconbase = execFileSync('python3', ['-c', 'import sys; sys.path.insert(0, sys.argv[1]); import build; print(build.find_iconbase())', join(skill, 'scripts')], {encoding: 'utf8'}).trim();
const posterCss = await readFile(join(skill, 'assets/style.css'), 'utf8');
const conceptCss = await readFile(join(skill, 'assets/style-conceptual.css'), 'utf8');
const runtime = await readFile(join(here, 'diagram-runtime.js'), 'utf8');
const conceptual = new Set(['swimlanes', 'sequence', 'state-machine', 'card-catalog', 'states', 'catalog']);
const STYLE = /\/\*(?:STYLE|ESTILO)\*\//;
const widthOf = html => Number(html.match(/<meta name="(?:width|largura)" content="(\d+)"/)?.[1])
  || [...html.matchAll(/body\s*\{[^}]*?width\s*:\s*(\d+)px/g)].map(match => Number(match[1])).at(-1)
  || Number(html.match(/\.page\s*\{[^}]*?width\s*:\s*(\d+)px/)?.[1]);

// BPMN: bpmn-js paints the colors written in the XML, so the page maps each color back to its token, repaints on a theme
// change, and answers element picks from the same map (sentinel colors cannot reach an already drawn SVG).
const bpmnTokens = {};
for (const group of ['er_palette', 'derived', 'colors']) {
  for (const [key, value] of Object.entries(themes['ai-diagrams'][group])) bpmnTokens[value.toUpperCase()] = key.replaceAll('_', '-');
}
const bpmnAdapter = `const colorTokens=${JSON.stringify(bpmnTokens)};const tokenOf={};
function themedXml(){const rootStyle=getComputedStyle(document.documentElement);return xml.replace(/bioc:(fill|stroke)="(#[\\da-f]{6})"/gi,(all,property,color)=>{const token=colorTokens[color.toUpperCase()];return token?'bioc:'+property+'="'+rootStyle.getPropertyValue('--'+token).trim()+'"':all})}
const shapes=new DOMParser().parseFromString(xml,'text/xml').querySelectorAll('[bpmnElement]');shapes.forEach(s=>{const u=[];const f=s.getAttribute('bioc:fill'),k=s.getAttribute('bioc:stroke');if(f&&colorTokens[f.toUpperCase()])u.push({token:colorTokens[f.toUpperCase()],role:'fill'});if(k&&colorTokens[k.toUpperCase()])u.push({token:colorTokens[k.toUpperCase()],role:'line'});tokenOf[s.getAttribute('bpmnElement')]=u});
window.__aiDiagramsBpmnPick=target=>{const el=target.closest('[data-element-id]');if(!el)return null;return {uses:tokenOf[el.getAttribute('data-element-id')]||[],element:el}};
window.__aiDiagramsBpmnScan=()=>[...document.querySelectorAll('[data-element-id]')].map(el=>({element:el,uses:tokenOf[el.getAttribute('data-element-id')]||[]})).filter(item=>item.uses.length);
window.__aiDiagramsFont=()=>getComputedStyle(document.documentElement).getPropertyValue('--font-text').replace(/'/g,'').trim();
window.__aiDiagramsRetheme=()=>{const old=window.__aiDiagramsViewer;if(!old)return;old.destroy();const font=window.__aiDiagramsFont();
// a new viewer, so bpmn-js measures labels with the theme font, as the engine's viewer does
const v=window.__aiDiagramsViewer=new BpmnJS({container:'#canvas',textRenderer:{defaultStyle:{fontFamily:font,fontSize:13},externalStyle:{fontFamily:font,fontSize:12}}});
document.fonts.load('13px '+font).then(()=>document.fonts.ready).then(()=>v.importXML(themedXml())).then(()=>{v.get('canvas').zoom('fit-viewport');document.body.dataset.repainted=String(Number(document.body.dataset.repainted||0)+1)})};`;

function diagramPage(html, {id, language, width}) {
  html = html.replace(/<link\b[^>]*>/g, '').replace(/@import\s+[^;]+;/g, '');
  assert(ROOT.test(html), `Missing diagram token root: ${language}/${id}`);
  const defaultTokens = tokenList(themes['ai-diagrams']);
  // the token :root moves to its own <style>, which the runtime replaces on a theme change
  html = html.replace(ROOT, '');
  const head = `<link rel="stylesheet" href="../../assets/diagram-fonts.css"><style id="ai-diagrams-theme">${themeTokens(themes['ai-diagrams'])}</style>`
    + `<style>.hdr,.foot{visibility:var(--frame-visibility,visible)}</style>`
    + `<script>window.__aiDiagramsTokens=${JSON.stringify(defaultTokens)};</script><script>${runtime}</script>`;
  html = html.replace(/<head>/i, `<head>\n${head}`);
  if (id === 'bpmn' || /new BpmnJS/.test(html)) {
    html = html.replace('const viewer = new BpmnJS', `${bpmnAdapter}\nconst viewer = window.__aiDiagramsViewer = new BpmnJS`)
      .replaceAll('fontFamily:"IBM Plex Sans,Arial,sans-serif"', 'fontFamily:window.__aiDiagramsFont()')
      .replace('viewer.importXML(xml)', 'document.fonts.ready.then(()=>viewer.importXML(themedXml()))');
    assert(html.includes('viewer.importXML(themedXml())'), `BPMN theme adapter was not installed: ${language}/${id}`);
  }
  assert(!/<(?:img|script|link)\b[^>]*(?:src|href)=["'](?!data:|#|\.\.\/\.\.\/assets\/)[^"']+/i.test(html), `Diagram fetches an outside asset: ${language}/${id}`);
  assert(!html.includes('—'), `Diagram includes an em dash: ${language}/${id}`);
  assert(width > 0, `Native width missing: ${language}/${id}`);
  return html;
}

const typeIds = ['aws-architecture', 'step-flow', 'c4', 'bpmn', 'swimlanes', 'sequence', 'state-machine', 'er-schema', 'dependency-matrix', 'card-catalog', 'comparison-table'];
const importFormats = [
  ['flowchart', 'Mermaid flowchart', 'mermaid'], ['sequence', 'Mermaid sequence', 'mermaid'],
  ['state', 'Mermaid state', 'mermaid'], ['er', 'Mermaid ER', 'mermaid'],
  ['process', 'BPMN XML', 'xml'], ['schema', 'DDL SQL', 'sql'],
  ['catalog', 'CSV catalog', 'csv'], ['comparison', 'YAML comparison', 'yaml'],
  ['workspace', 'Structurizr DSL', 'text'],
];
const importRoot = join(repo, 'examples/import');
const importManifest = JSON.parse(await readFile(join(importRoot, 'manifest.json'), 'utf8'));
const compat = await compatibility(repo, importManifest);

const sizes = {};
for (const language of languages) {
  const prefix = language === 'en' ? '' : '../';
  const languageOut = language === 'en' ? out : join(out, language);
  const translations = translationsByLanguage[language];
  const t = translator(language, translations);
  const assets = Object.fromEntries(brandFiles.map(file => [file, `${prefix}assets/brand/${file}`]));
  const specimen = brandPreview(await readFile(join(brand, 'assets/exemplo-diagrama.svg'), 'utf8'), language, specimenFonts);
  await write(join(out, `assets/brand/example-diagram-${language}.svg`), specimen);
  assets['exemplo-diagrama.svg'] = `${prefix}assets/brand/example-diagram-${language}.svg`;
  const awsFolder = language === 'pt-BR' ? join(repo, 'examples/aws-architecture') : join(project, 'examples-i18n', language, 'aws-architecture');
  const aws = {prompt: await readFile(join(awsFolder, 'prompt.md'), 'utf8'), exampleData: await readFile(join(awsFolder, 'antifraud-decision.md'), 'utf8')};

  const diagrams = [];
  for (const id of typeIds) {
    const folder = join(repo, 'examples', id, 'output');
    // the main view has the shortest name; C4 writes one page per view, <name>-<key>.html next to it
    const pages = (await readdir(folder)).filter(file => file.endsWith('.html')).sort((a, b) => a.length - b.length || a.localeCompare(b));
    const filename = pages[0];
    assert(filename, `Example HTML missing: ${id}`);
    // every language uses the HTML the engine built (examples/build-all.sh, site/examples-i18n/build-all.sh), so the site shows what the engine draws
    const sourceFolder = language === 'pt-BR' ? folder : join(project, 'examples-i18n', language, id, 'output');
    const sourcePath = join(sourceFolder, filename);
    const source = sourcePath.slice(repo.length + 1);
    assert(existsSync(sourcePath), `Built example missing: ${source}; run site/examples-i18n/build-all.sh`);
    const original = await readFile(sourcePath, 'utf8');
    assert.match(original, new RegExp(`<html[^>]*lang=["']${language}["']`), `Wrong example language: ${source}`);
    assert(!STYLE.test(original), `Example was not built by the engine: ${source}`);
    const width = widthOf(original);
    const png = await readFile(join(folder, filename.replace(/\.html$/, '.png')));
    const height = Math.ceil(png.readUInt32BE(20) / (png.readUInt32BE(16) / width));
    const url = `diagrams/${language}/${id}.html`;
    // links between views keep working on the site: <name>.html -> <id>.html, <name>-<key>.html -> <id>-<key>.html
    const base = filename.replace(/\.html$/, '');
    const relink = html => html.replaceAll(`href="${filename}"`, `href="${id}.html"`).replaceAll(`href="${base}-`, `href="${id}-`);
    sizes[url] = await write(join(out, url), diagramPage(relink(original), {id, language, width}));
    for (const page of pages.filter(file => file.startsWith(base + '-'))) {
      const html = await readFile(join(sourceFolder, page), 'utf8');
      assert(!STYLE.test(html), `Example view was not built by the engine: ${page}`);
      const viewUrl = `diagrams/${language}/${id}-${page.slice(base.length + 1)}`;
      sizes[viewUrl] = await write(join(out, viewUrl), diagramPage(relink(html), {id, language, width: widthOf(html)}));
    }
    diagrams.push({id, language, url: prefix + url, width, height, source, kind: id === 'bpmn' ? 'html+bpmn-js' : 'html'});
  }
  assert.equal(diagrams.length, 11);

  const imports = [];
  for (const [id, name, syntax] of importFormats) {
    const record = importManifest.find(item => item.id === id && item.language === language);
    assert(record?.tested === true, `Import sample has no passing source test: ${language}/${id}`);
    importGateMessage(record.gate);
    // the HTML built by the import gate sits next to _src/; the source is used only while the gate is pending
    const built = resolve(importRoot, record.output.replace('/_src/', '/'));
    const sourcePath = record.gate === 'passed' && existsSync(built) ? built : resolve(importRoot, record.output);
    const inputPath = resolve(importRoot, record.input);
    for (const path of [sourcePath, inputPath]) assert(path.startsWith(`${importRoot}/`), 'Import sample escapes its directory');
    let html = await readFile(sourcePath, 'utf8');
    assert.match(html, new RegExp(`<html[^>]*lang=["']${language}["']`), `Wrong import language: ${id}`);
    if (STYLE.test(html)) html = html.replace(STYLE, () => conceptual.has(record.type) ? conceptCss : posterCss);
    const width = widthOf(html);
    const url = `diagrams/${language}/import-${id}.html`;
    sizes[url] = await write(join(out, url), diagramPage(html, {id: `import-${id}`, language, width}));
    const input = inputPath.slice(repo.length + 1), output = sourcePath.slice(repo.length + 1);
    const command = `npx ai-diagrams import ${input} --out diagrams/${id} --lang ${language}`;
    imports.push({...record, id, name, syntax, input, output, command, inputText: await readFile(inputPath, 'utf8'), url: prefix + url, width, height: 1200});
  }

  const siteData = {language, prefix, translations, aws, assets, palette, themes, diagrams, imports, fontFamilies, compat};
  const options = {
    bundle: true, write: false, minify: true, jsx: 'automatic', nodePaths: [join(project, 'node_modules')],
    // the package's CSS goes in once, through dist/style.css in assets/site.css
    loader: {'.css': 'empty'},
    define: {'process.env.NODE_ENV': '"production"'},
    plugins: [{name: 'site-data', setup(b) {
      b.onResolve({filter: /^virtual:site-data$/}, () => ({path: 'site-data', namespace: 'site'}));
      b.onLoad({filter: /.*/, namespace: 'site'}, () => ({contents: `export const siteData = ${JSON.stringify(siteData)};`, loader: 'js'}));
    }}],
  };
  const client = await build({...options, entryPoints: [join(here, 'client.jsx')], platform: 'browser', format: 'iife'});
  sizes[`assets/app-${language}.js`] = await write(join(out, `assets/app-${language}.js`), client.outputFiles[0].text);
  const server = await build({...options, platform: 'node', format: 'cjs', stdin: {
    contents: "import React from 'react';import{renderToString}from'react-dom/server';import{App}from'./app.jsx';export const render=page=>renderToString(React.createElement(App,{page}));", resolveDir: here,
  }});
  const temp = await mkdtemp(join(project, '.ssr-'));
  let render;
  try {
    const path = join(temp, 'ssr.cjs');
    await writeFile(path, server.outputFiles[0].text);
    render = require(path).render;
  } finally { await rm(temp, {recursive: true, force: true}); }

  const pages = [
    ['01-home.html', 'home', 'Diagrams from a description'], ['02-diagrams.html', 'catalog', 'Diagrams'],
    ['03-aws-architecture.html', 'aws', 'AWS architecture'], ['04-themes.html', 'themes', 'Themes'],
    ['05-compatibility.html', 'compatibility', 'Compatibility and installation'], ['06-brand.html', 'brand', 'Brand'],
    ['07-import.html', 'import', 'Import'], ['index.html', 'index', 'Page mockups'],
  ];
  for (const [filename, page, title] of pages) {
    const markup = render(page);
    const html = `<!doctype html>\n<html lang="${language}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ai-diagrams · ${t(title)}</title><meta name="description" content="${t('Static page mockup for ai-diagrams design review.')}"><link rel="icon" href="${assets['favicon.svg']}"><link rel="stylesheet" href="${prefix}assets/site.css"></head><body><div id="root">${markup}</div><script>window.__PAGE__=${JSON.stringify(page)};</script><script src="${prefix}assets/app-${language}.js"></script></body></html>`;
    assert(!html.includes('—'), `Em dash in ${filename}`);
    sizes[`${language === 'en' ? '' : `${language}/`}${filename}`] = await write(join(languageOut, filename), html);
  }
  console.log(`Built ${language}: ${pages.length} pages, ${diagrams.length} examples, ${imports.length} imports.`);
}

const componentCss = (await Promise.all(['src/tokens/tokens.css', 'src/styles/global.css', 'dist/style.css'].map(file => readFile(join(ui, file), 'utf8')))).join('\n').replace(/^@import[^\n]*\n/gm, '');
const layout = await readFile(join(here, 'layout.css'), 'utf8');
const css = `${shellFaces.join('\n')}\n${componentCss}\n${layout}`.replaceAll('—', '-');
assert(!/@import\s/.test(css), 'CSS must not fetch another stylesheet');
sizes['assets/site.css'] = await write(join(out, 'assets/site.css'), css);

const licenses = join(out, 'licenses');
await mkdir(licenses, {recursive: true});
await copyFile(join(ui, 'LICENSE'), join(licenses, 'refy-design-web-MIT.txt'));
for (const name of ['react', 'react-dom']) await copyFile(join(dirname(require.resolve(`${name}/package.json`)), 'LICENSE'), join(licenses, `${name}-MIT.txt`));
for (const name of ['inter', 'jetbrains-mono', 'ibmplexsans', 'ibmplexmono', 'sourcecodepro']) await copyFile(join(ui, `src/assets/fonts/${name}-OFL.txt`), join(licenses, `${name}-OFL.txt`));
await copyFile(join(here, 'fonts/public-sans-OFL.txt'), join(licenses, 'public-sans-OFL.txt'));
await writeFile(join(licenses, 'public-sans-SOURCE.txt'), 'Public Sans variable font, official Google Fonts repository\nhttps://github.com/google/fonts/blob/main/ofl/publicsans/PublicSans%5Bwght%5D.ttf\nGit blob: c747e1de8c8deadb6ba852eb9a0a7d893b8bd36f\n');
const total = Object.values(sizes).reduce((a, b) => a + b, 0);
console.log(`Built ${Object.keys(sizes).length} files, ${(total / 1048576).toFixed(1)} MB in all; largest: ${Object.entries(sizes).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([f, s]) => `${f} ${(s / 1048576).toFixed(1)} MB`).join(', ')}. No browser launched.`);
