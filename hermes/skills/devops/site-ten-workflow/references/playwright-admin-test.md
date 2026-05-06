# SiteTen Admin — Playwright Test Scripts

## Testar admin via Playwright (autenticado)

O login do admin usa upload de ficheiro `.pem` que o Playwright headless não consegue fazer nativamente. Usa esta abordagem:

### Teste rápido de verificação (E-books)
```javascript
import { chromium } from '/home/alvarobiano/.hermes/hermes-agent/node_modules/playwright/index.mjs';

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();

const errors = [];
page.on('pageerror', err => errors.push(err.message));
page.on('console', msg => { if (msg.type() === 'error') errors.push(msg.text()); });

try {
  await page.goto('https://alvarobiano-linuxmint.taile2fd75.ts.net/admin/index.html',
    { timeout: 20000, waitUntil: 'networkidle' });

  await page.fill('#admin_password', 'AeSm1979@#');
  await page.setInputFiles('#admin_key', '/home/alvarobiano/repos/SiteTen/api/security/private_key.pem');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(5000);

  await page.screenshot({ path: '/tmp/screen_admin.png', fullPage: false });

  const states = await page.evaluate(() => {
    const ids = ['crud-main', 'dashboard-content', 'dynamic-table-body'];
    return ids.map(id => {
      const el = document.getElementById(id);
      if (!el) return { id, found: false };
      const style = window.getComputedStyle(el);
      return {
        id, display: style.display,
        hidden: el.classList.contains('hidden'),
        width: Math.round(el.getBoundingClientRect().width),
        height: Math.round(el.getBoundingClientRect().height)
      };
    });
  });
  console.log('States:', JSON.stringify(states));

  const rowCount = await page.$$eval('#dynamic-table-body tr', r => r.length);
  console.log('Row count:', rowCount);

  const firstTitle = await page.$eval('#dynamic-table-body tr:first-child', tr =>
    tr.textContent.trim().substring(0, 200)
  ).catch(() => 'NONE');
  console.log('First row:', firstTitle);

  console.log('Errors:', errors.length ? errors : 'NONE');

} catch(err) {
  console.error('Error:', err.message);
} finally {
  await browser.close();
}
```

Guardar em `/tmp/test_admin.mjs` e correr com `node /tmp/test_admin.mjs`.

### Verificação rápida de elementos (sem screenshot)
```javascript
const all = await page.evaluate(() => {
  const ids = ['login-view','dashboard-view','dashboard-content','crud-main',
                'dynamic-table-body','tab-ebooks','tab-dashboard'];
  return ids.map(id => {
    const el = document.getElementById(id);
    if (!el) return { id, found: false };
    const s = window.getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return { id, display: s.display, hidden: el.classList.contains('hidden'),
             w: Math.round(r.width), h: Math.round(r.height) };
  });
});
console.log(JSON.stringify(all, null, 2));
```

### Notas
- **404s das capas**: os ficheiros não existem no servidor — não afecta funcionalidade
- Caminho local das capas: `~/repos/SiteTen/images/ebooks/`
- Apenas existe 1 ficheiro local: `ebooks_4934251855658700469.png`
