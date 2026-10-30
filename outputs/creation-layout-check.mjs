import assert from 'node:assert/strict';
import { mkdir, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { createServer } from '../前端/node_modules/vite/dist/node/index.js';

const root = fileURLToPath(new URL('../前端/', import.meta.url));
const output = fileURLToPath(new URL('./creation-layout-check/', import.meta.url));
const url = 'http://127.0.0.1:3010/creation';

if (process.argv.includes('--serve')) {
  const server = await createServer({
    root,
    server: { host: '127.0.0.1', port: 3010, strictPort: true, open: false },
  });
  await server.listen();
  server.printUrls();
} else {
  await mkdir(output, { recursive: true });
  const browser = await chromium.launch({ channel: 'chrome', headless: true });
  const results = [];
  try {
    for (const width of [1920, 1440, 1280, 1024, 820, 768, 390, 320]) {
      const page = await browser.newPage({ viewport: { width, height: 1000 } });
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      // Fixtures isolate layout checks from external APIs and paid model calls.
      await page.route('**/*', route => {
        const requestUrl = route.request().url();
        if (requestUrl.includes('/api/')) {
          let body = {};
          if (requestUrl.includes('/history')) body = { history: [] };
          if (requestUrl.includes('/templates')) body = { templates: [] };
          if (requestUrl.includes('/profile')) body = { products: [] };
          if (requestUrl.endsWith('/api/ai/generate')) {
            body = { content: '界面回归测试文案，不属于真实模型输出。', product_name: '界面测试', recommended_tags: [] };
          }
          return route.fulfill({ contentType: 'application/json', body: JSON.stringify(body) });
        }
        if (!requestUrl.startsWith('http://127.0.0.1:3010')) return route.abort();
        return route.continue();
      });
      await page.addInitScript(() => {
        localStorage.setItem('auth_token', 'layout-test-only');
        localStorage.setItem('user_info', JSON.stringify({ id: 'layout-test', username: '界面检查' }));
      });
      await page.goto(url, { waitUntil: 'networkidle' });
      await page.locator('#creation-request').fill('突出产地与产品口感，不添加未经证实的功效。'.repeat(8));
      const geometry = await page.evaluate(() => {
        const rect = selector => {
          const element = document.querySelector(selector);
          const r = element.getBoundingClientRect();
          return { left: r.left, top: r.top, right: r.right, bottom: r.bottom, width: r.width, height: r.height };
        };
        return {
          viewport: innerWidth,
          scrollWidth: document.documentElement.scrollWidth,
          panel: rect('.view-16'),
          textarea: rect('.custom-textarea'),
          tools: rect('.input-tools'),
          submit: rect('.arrow-up-left-wrapper'),
          sidebar: rect('aside.view'),
          position: getComputedStyle(document.querySelector('.custom-textarea')).position,
          titleSize: getComputedStyle(document.querySelector('.welcome-title')).fontSize,
        };
      });
      assert(geometry.scrollWidth <= width + 1, `Horizontal overflow at ${width}: ${geometry.scrollWidth}`);
      assert.equal(geometry.position, 'static');
      assert(geometry.textarea.left >= geometry.panel.left, `Textarea left overflow at ${width}`);
      assert(geometry.textarea.right <= geometry.panel.right, `Textarea right overflow at ${width}`);
      assert(geometry.textarea.bottom <= geometry.submit.top, `Textarea overlaps submit at ${width}`);
      assert(geometry.tools.bottom <= geometry.submit.top, `Tools overlap submit at ${width}`);
      assert(geometry.submit.bottom <= geometry.panel.bottom, `Submit outside form at ${width}`);
      if (width > 768) assert(geometry.panel.left >= geometry.sidebar.right, `Sidebar overlap at ${width}`);
      await page.locator('.fill-btn').first().click();
      await page.locator('.tag-dropdown-popup.active').waitFor({ state: 'visible' });
      const menu = await page.locator('.tag-dropdown-popup.active').boundingBox();
      assert(menu.x >= 0 && menu.x + menu.width <= width, `Menu outside viewport at ${width}`);
      await page.locator('.tag-dropdown-popup.active .tag-dropdown-option').first().click();
      await page.locator('.welcome-title').click();
      await page.locator('.script-btn').click();
      await page.locator('.script-btn').click();
      await page.screenshot({ path: `${output}/creation-${width}.png`, fullPage: true });
      await page.locator('.arrow-up-left-wrapper').click();
      await page.locator('.ai-text').filter({ hasText: '界面回归测试文案' }).waitFor({ state: 'visible' });
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1), true, `Result overflow at ${width}`);
      assert.deepEqual(errors, [], `Runtime errors at ${width}`);
      results.push({ width, geometry, dropdown: 'passed', scriptToggle: 'passed', fixtureSubmit: 'passed', runtimeErrors: errors });
      await page.close();
    }
    await writeFile(`${output}/report.json`, JSON.stringify({ scope: 'Frontend only, API fixtures; not model performance measurements', results }, null, 2));
    console.log(JSON.stringify({ checkedViewports: results.map(result => result.width), status: 'passed', output }, null, 2));
  } finally {
    await browser.close();
  }
}
