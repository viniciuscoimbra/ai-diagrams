import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const brand = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const output = resolve(brand, 'capturas');
const html = resolve(brand, 'brandkit.html');
const report = {
  version: 2,
  date: new Date().toISOString(),
  html_sha256: createHash('sha256').update(await readFile(html)).digest('hex'),
  captured: [], checks: [], status: 'pending', html_visual_review: 'pending',
};
let browser;

await mkdir(output, { recursive: true });
try {
  const { chromium } = createRequire(resolve(process.env.PLAYWRIGHT_FROM || process.cwd(), 'package.json'))('playwright');
  const sharp = createRequire(resolve(brand, '../../plyngo/package.json'))('sharp');
  browser = await chromium.launch({
    executablePath: process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: true,
  });
  for (const [device, width, height] of [['desktop', 1440, 1000], ['mobile', 390, 844]]) {
    for (const theme of ['light', 'dark']) {
      const context = await browser.newContext({ viewport: { width, height }, deviceScaleFactor: 1 });
      const network = [];
      await context.route(/^https?:\/\//, route => { network.push(route.request().url()); return route.abort(); });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const url = pathToFileURL(html);
      url.searchParams.set('theme', theme);
      await page.goto(url.href);
      await page.evaluate(async () => {
        await document.fonts.ready;
        await Promise.all([...document.images].map(image => image.decode()));
      });
      const scope = page.locator('.brandkit');
      const mode = async expected => {
        await page.waitForFunction(value => document.querySelector('.brandkit')?.dataset.theme === value, expected);
        assert.equal(await scope.getAttribute('data-theme'), expected);
      };
      await mode(theme);
      const dark = page.getByRole('radio', { name: 'Escuro', exact: true });
      await dark.click();
      await mode('dark');
      await dark.press('ArrowLeft');
      await mode('light');
      await page.getByRole('radio', { name: 'Claro', exact: true }).press('ArrowRight');
      await mode('dark');
      await page.getByRole('radio', { name: theme === 'light' ? 'Claro' : 'Escuro', exact: true }).click();
      await mode(theme);
      const button = page.locator('.asset-actions button').first();
      const buttonStates = [];
      for (const state of ['hover', 'focus']) {
        if (state === 'hover') await button.hover();
        else { await page.mouse.move(0, 0); await button.focus(); }
        buttonStates.push(await button.evaluate((element, state) => {
          const css = getComputedStyle(element);
          return { state, color: css.color, backgroundColor: css.backgroundColor, borderColor: css.borderColor, outlineColor: css.outlineColor };
        }, state));
      }
      await button.evaluate(element => element.blur());
      await page.evaluate(() => scrollTo(0, 0));
      const layout = await page.evaluate(() => {
        const failures = [];
        const visible = element => {
          const rect = element.getBoundingClientRect();
          const css = getComputedStyle(element);
          return rect.width > 1 && rect.height > 1 && css.visibility !== 'hidden' && css.display !== 'none'
            && css.opacity !== '0' && css.clip === 'auto' && css.clipPath === 'none';
        };
        const label = element => element.id || element.className?.baseVal || element.className || element.tagName;
        const rect = element => element.getBoundingClientRect();
        if (document.documentElement.scrollWidth > innerWidth + 1) failures.push('Horizontal page overflow');
        for (const element of document.querySelectorAll('.brandkit *')) {
          if (!visible(element) || element.closest('svg, [hidden], [aria-hidden="true"]')) continue;
          const bounds = rect(element);
          if (bounds.left < -1 || bounds.right > innerWidth + 1) failures.push(`Offscreen: ${label(element)}`);
        }
        const sections = [...document.querySelectorAll('main .brand-section')];
        const ids = sections.map(section => section.id);
        const expected = ['assinatura', 'cor-tipografia', 'tom-de-voz', 'aplicacoes'];
        if (JSON.stringify(ids) !== JSON.stringify(expected)) failures.push(`Unexpected section order: ${ids.join(', ')}`);
        sections.forEach((section, index) => {
          const box = rect(section);
          for (const previous of sections.slice(0, index)) {
            const other = rect(previous);
            if (Math.min(box.right, other.right) - Math.max(box.left, other.left) > 1 && Math.min(box.bottom, other.bottom) - Math.max(box.top, other.top) > 1) failures.push(`Overlapping sections: ${previous.id}, ${section.id}`);
          }
        });
        for (const figure of document.querySelectorAll('.signature-symbol, .specimen, .application-figure')) {
          const children = [...figure.children].filter(child => visible(child) && !['absolute', 'fixed'].includes(getComputedStyle(child).position));
          children.forEach((child, index) => {
            const box = rect(child), frame = rect(figure);
            if (box.left < frame.left - 1 || box.right > frame.right + 1 || box.top < frame.top - 1 || box.bottom > frame.bottom + 1) failures.push(`Figure overflow: ${label(child)}`);
            for (const previous of children.slice(0, index)) {
              const other = rect(previous);
              if (Math.min(box.right, other.right) - Math.max(box.left, other.left) > 1 && Math.min(box.bottom, other.bottom) - Math.max(box.top, other.top) > 1) failures.push(`Overlapping figure children: ${label(child)}`);
            }
          });
        }
        const symbols = [...document.querySelectorAll('#assinatura .signature-symbol')];
        if (JSON.stringify(symbols.map(element => element.dataset.symbol)) !== JSON.stringify(['encontro'])) failures.push('Expected only the Encontro symbol');
        const symbolSizes = [...document.querySelectorAll('#assinatura .symbol-sizes img')].map(element => ({ width: rect(element).width, height: rect(element).height }));
        if (JSON.stringify(symbolSizes) !== JSON.stringify([16, 32, 64].map(size => ({ width: size, height: size })))) failures.push('Incorrect symbol display sizes');
        const colors = document.querySelectorAll('.swatches > figure').length;
        const pairs = document.querySelectorAll('.multiply-grid > *').length;
        if (colors < 4 || colors > 6) failures.push(`Expected 4–6 palette colors, got ${colors}`);
        if (pairs !== colors * (colors - 1) / 2) failures.push(`Missing multiply pairs: ${pairs}`);
        const favicons = [...document.querySelectorAll('.favicon-sizes img')].map(element => ({ width: rect(element).width, height: rect(element).height }));
        if (JSON.stringify(favicons) !== JSON.stringify([16, 32, 64].map(size => ({ width: size, height: size })))) failures.push('Incorrect favicon display sizes');
        const ui = [...document.querySelectorAll('.brandkit, .masthead, .brand-board, .brand-section, .sample-site-header, .page-footer, button, [role="radio"]')].filter(visible).map(element => {
          const css = getComputedStyle(element);
          return { element: label(element), color: css.color, backgroundColor: css.backgroundColor, borderColor: css.borderColor };
        });
        return { failures, sections: ids, colors, pairs, favicons, ui, width: innerWidth, height: document.documentElement.scrollHeight };
      });
      for (const item of [...layout.ui, ...buttonStates]) {
        for (const property of ['color', 'backgroundColor', 'borderColor', 'outlineColor']) {
          if (!item[property]) continue;
          const channels = item[property].match(/[\d.]+/g)?.map(Number);
          if (!channels || (channels[3] !== 0 && Math.max(...channels.slice(0, 3)) - Math.min(...channels.slice(0, 3)) > 1)) layout.failures.push(`Non-neutral UI ${item.element || item.state} ${property}: ${item[property]}`);
        }
      }
      report.checks.push({ device, theme, errors, network, buttonStates, ...layout });
      assert.deepEqual(errors, [], 'Browser errors');
      assert.deepEqual(network, [], 'The HTML requested external resources');
      assert.deepEqual(layout.failures, [], 'Layout checks failed');
      const name = `brandkit-v2-${device}-${theme}.jpg`;
      const screenshot = await page.screenshot({ type: 'png', fullPage: true, animations: 'disabled' });
      let captureWidth = Math.min(width, 1280), jpeg;
      do {
        jpeg = await sharp(screenshot).resize({ width: captureWidth, withoutEnlargement: true }).jpeg({ quality: 70, mozjpeg: true }).toBuffer();
        if (jpeg.length <= 300 * 1024) break;
        captureWidth = Math.floor(captureWidth * 0.85);
      } while (captureWidth >= 320);
      assert.ok(jpeg.length <= 300 * 1024, 'QA image exceeds 300 KB');
      const metadata = await sharp(jpeg).metadata();
      assert.ok(metadata.width <= 1280, 'QA image exceeds 1280 px');
      await writeFile(resolve(output, name), jpeg);
      report.checks.at(-1).capture = { file: name, width: metadata.width, height: metadata.height, bytes: jpeg.length };
      report.captured.push(name);
      await context.close();
    }
  }
  report.status = 'captured_pending_visual_review';
} catch (error) {
  report.status = 'failed';
  report.reason = String(error.stack || error);
  process.exitCode = 1;
} finally {
  await browser?.close();
  await writeFile(resolve(output, 'checks-v2.json'), `${JSON.stringify(report, null, 2)}\n`);
  await writeFile(resolve(output, 'status.json'), `${JSON.stringify({
    version: report.version, date: report.date, status: report.status,
    html_sha256: report.html_sha256, captured: report.captured,
    html_visual_review: 'pending', checks: 'checks-v2.json',
    previous_version: 'The four v1 PNGs and checks.json are preserved; they do not validate v2.',
    ...(report.reason ? { reason: report.reason } : {}),
  }, null, 2)}\n`);
  console.log(JSON.stringify(report));
}
