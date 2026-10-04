// Headless Chrome playthroughs of the real page. Reports console errors and dead ends; exits 1 on either.
// Usage: node tools/smoke.mjs [url] [--runs N]     (a server must be running: uv run python -m http.server 8000 -d site)
// Chrome: set CHROME=/path/to/chrome, or it tries the usual macOS and Linux locations. No npm packages needed.
import { spawn } from 'node:child_process';
import { existsSync, mkdirSync, rmSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const args = process.argv.slice(2);
const url = args.find((a) => a.startsWith('http')) || 'http://127.0.0.1:8000/';
const runs = Number(args[args.indexOf('--runs') + 1]) || 6;
const port = 9300 + Math.floor(Math.random() * 500);
const profile = join(dirname(fileURLToPath(import.meta.url)), '.smoke', 'profile');
const chromePath = [
  process.env.CHROME,
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
].find((p) => p && existsSync(p));
if (!chromePath) { console.error('No Chrome found: set CHROME=/path/to/chrome'); process.exit(2); }

rmSync(profile, { recursive: true, force: true });
mkdirSync(profile, { recursive: true });
const chrome = spawn(chromePath, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${profile}`, '--no-first-run', 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const watchdog = setTimeout(() => { console.error('timed out'); chrome.kill(); process.exit(2); }, 60000 + runs * 30000);

let ws = null;
for (let i = 0; i < 50 && !ws; i++) {
  try {
    const target = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
    if (target.webSocketDebuggerUrl) ws = new WebSocket(target.webSocketDebuggerUrl);
  } catch { /* Chrome still starting */ }
  if (!ws) await sleep(200);
}
if (!ws) { console.error('Could not reach Chrome DevTools'); chrome.kill(); process.exit(2); }
if (ws.readyState !== WebSocket.OPEN) await new Promise((r) => ws.addEventListener('open', r));

let id = 0;
const pending = new Map();
const errors = [];
ws.addEventListener('message', (event) => {
  const m = JSON.parse(event.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text);
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') errors.push(m.params.args.map((a) => a.value ?? a.description).join(' '));
});
const send = (method, params = {}) => new Promise((r) => { const n = ++id; pending.set(n, r); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (expression) => (await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true })).result?.result?.value;
const waitFor = async (sel) => { for (let t = 0; t < 8000; t += 100) { if (await ev(`!!document.querySelector(${JSON.stringify(sel)})`)) return true; await sleep(100); } return false; };

await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
await send('Network.setCacheDisabled', { cacheDisabled: true });
await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 900, deviceScaleFactor: 1, mobile: false });

const results = [];
for (let run = 0; run < runs; run++) {
  await send('Page.navigate', { url });
  if (!(await waitFor('.gb-cover'))) { errors.push(`cover did not render: ${await ev(`document.getElementById('gb-app')?.innerText`)}`); break; }
  await ev('localStorage.clear()');
  await send('Page.reload');
  await waitFor('.gb-cover');
  // Cycle through every adventure on the cover, then through its investigators.
  const covers = Math.max(await ev(`document.querySelectorAll('[data-act="begin"]').length`), 1);
  const story = await ev(`document.querySelectorAll('.gb-cover-title')[${run % covers}]?.textContent`);
  await ev(`document.querySelectorAll('[data-act="begin"]')[${run % covers}].click()`);
  await waitFor('.gb-inv');
  const investigators = await ev(`document.querySelectorAll('.gb-inv button').length`);
  await ev(`document.querySelectorAll('.gb-inv button')[${Math.floor(run / covers) % Math.max(investigators, 1)}].click()`);
  await waitFor('.gb-page');
  const path = [];
  for (let step = 0; step < 150; step++) {
    const sec = await ev(`document.querySelector('.gb-sec-num')?.textContent`);
    if (path.at(-1) !== sec) path.push(sec);
    if (await ev(`!!document.querySelector('.gb-ending')`)) break;
    if (await ev(`!!document.querySelector('.gb-roll')`)) {
      await sleep(700);
      await ev(`[...document.querySelectorAll('.gb-roll .gb-btn')].pop().click()`);
    } else {
      const n = await ev(`document.querySelectorAll('.gb-choice').length`);
      if (!n) { errors.push(`dead end at section ${sec}`); break; }
      await ev(`document.querySelectorAll('.gb-choice')[${Math.floor(Math.random() * 1000)} % ${n}].click()`);
    }
    await sleep(60);
  }
  results.push({ run, story, sections: path.length, ending: await ev(`document.querySelector('.gb-ending') ? document.querySelector('.gb-sec-title').textContent : null`) });
}

clearTimeout(watchdog);
ws.close();
chrome.kill();
for (const r of results) console.log(`run ${r.run + 1} (${r.story}): ${r.sections} sections -> ${r.ending ?? 'NO ENDING'}`);
for (const e of errors) console.log(`ERROR ${e}`);
const failed = errors.length > 0 || results.some((r) => !r.ending);
console.log(failed ? 'SMOKE FAILED' : 'smoke ok');
process.exit(failed ? 1 : 0);
