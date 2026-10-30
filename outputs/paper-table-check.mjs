import assert from 'node:assert/strict';
import { chromium } from 'playwright';
import { fileURLToPath } from 'node:url';
import { readFile } from 'node:fs/promises';

const results = JSON.parse(await readFile(new URL('./paper_eval_30_20261019/verified_summary.json', import.meta.url), 'utf8'));

const browser = await chromium.launch({ channel: 'chrome', headless: true });
try {
  for (const width of [1440, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 1100 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(new URL('./论文表3表4_替换稿.html', import.meta.url).href);
    assert.equal(await page.locator('table').count(), 2);
    assert.equal(await page.locator('#table3-content tbody tr').count(), 5);
    assert.equal(await page.locator('#table4-content tbody tr').count(), 3);
    const rows = page.locator('#table4-content tbody tr');
    for (const [index, key] of ['writer_only', 'writer_rag', 'writer_rag_qa'].entries()) {
      const result = results[key];
      const cells = rows.nth(index).locator('td');
      assert.equal(await cells.nth(1).textContent(), '30');
      assert.equal(await cells.nth(2).textContent(), `${result.covered_fields}/${result.total_fields}（${(result.covered_fields / result.total_fields * 100).toFixed(1)}%）`);
      assert.equal(await cells.nth(3).textContent(), `${result.risk_tasks}/30（${(result.risk_tasks / 30 * 100).toFixed(1)}%）`);
      assert.equal(await cells.nth(4).textContent(), `${result.p50.toFixed(3)} / ${result.p95.toFixed(3)}`);
      assert.equal(await cells.nth(5).textContent(), String(result.calls));
      assert.equal(await cells.nth(6).textContent(), result.mean_tokens.toFixed(2));
    }
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
    // Inspect rich clipboard payload without modifying the user's clipboard.
    await page.evaluate(() => {
      window.capturedCopy = [];
      Object.defineProperty(navigator, 'clipboard', { value: { write: async items => {
        const item = items[0];
        window.capturedCopy.push(await (await item.getType('text/html')).text());
      } }, configurable: true });
    });
    for (const id of ['table3-content', 'table4-content']) {
      await page.locator(`[data-copy="${id}"]`).click();
      await page.waitForFunction(() => document.querySelector('#copy-status').textContent.includes('已复制'));
    }
    const copies = await page.evaluate(() => window.capturedCopy);
    assert.equal(copies.length, 2);
    assert(copies.every(html => html.includes('<table') && !html.includes('复制表')));
    await page.locator('h1').scrollIntoViewIfNeeded();
    await page.screenshot({ path: fileURLToPath(new URL(`./paper-tables-${width}.png`, import.meta.url)), fullPage: true });
    assert.deepEqual(errors, []);
    console.log(`Tables and rich-copy checks passed: ${width}px`);
    await page.close();
  }
} finally {
  await browser.close();
}
