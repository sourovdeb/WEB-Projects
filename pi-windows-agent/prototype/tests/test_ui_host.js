// UI host guard tests — run: node tests/test_ui_host.js  (exit 0 = pass)
const assert = require("assert");
const http = require("http");
const { UiHost, startServer, callHash } = require("../ui-host/ui_host.js");

let failures = 0;
function check(name, fn) {
  return new Promise((resolve) => {
    Promise.resolve(fn(() => resolve())) // fn receives a `done` if it needs async
      .then(() => { if (fn.length === 0) resolve(); })
      .catch((e) => { console.error("FAIL -", name, "\n ", e.message); failures++; resolve(); });
  });
}

async function request(port, path, headers, body) {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: "127.0.0.1", port, path, method: "POST", headers }, (res) => {
      let b = "";
      res.on("data", (c) => (b += c));
      res.on("end", () => resolve({ status: res.statusCode, body: b }));
    });
    req.on("error", reject);
    req.end(body || "");
  });
}

(async () => {
  const ui = new UiHost();

  // sync guard tests
  let n = 0;
  const sync = [
    ["deny tool cannot be approved", () => { assert.throws(() => ui.approve("powershell", { cmd: "x" }, null), /DENIED/); }],
    ["mcp-prefixed denied", () => { assert.throws(() => ui.approve("mcp__gmail__send", {}, null), /DENIED/); }],
    ["ui.* approval yields 64-hex hash", () => {
      const h = ui.approve("ui.click", { pid: 5, window: "w", control: "c" }, { pid: 5 });
      assert.ok(/^[0-9a-f]{64}$/.test(h)); assert.ok(ui.has(h));
    }],
    ["hash is canonical-JSON stable across key order", () => {
      const h1 = ui.approve("ui.type", { b: 2, a: 1 }, null);
      const h2 = callHash("ui.type", { a: 1, b: 2 });
      assert.strictEqual(h1, h2);
    }],
  ];
  for (const [name, fn] of sync) {
    try { fn(); n++; console.log("ok -", name); }
    catch (e) { failures++; console.error("FAIL -", name, "\n ", e.message); }
  }

  // network hardening tests
  const u2 = new UiHost();
  const server = startServer(u2, 7439);
  await new Promise((r) => setTimeout(r, 100));

  let res = await request(7439, "/status", { Origin: "https://evil.example" }, "{}");
  if (res.status === 403) { n++; console.log("ok - cross-origin rejected 403"); } else { failures++; console.error("FAIL - cross-origin", res.status); }

  res = await request(7439, "/status", { "Host": "evil.com:7439", "content-type": "application/json" }, JSON.stringify({ token: u2.launchToken }));
  if (res.status === 403) { n++; console.log("ok - bad Host header rejected 403"); } else { failures++; console.error("FAIL - bad host", res.status); }

  res = await request(7439, "/status", { "content-type": "application/json" }, JSON.stringify({ token: "wrong" }));
  if (res.status === 401) { n++; console.log("ok - bad token rejected 401"); } else { failures++; console.error("FAIL - bad token", res.status); }

  res = await request(7439, "/status", { "content-type": "application/json" }, JSON.stringify({ token: u2.launchToken }));
  if (res.status === 200) { n++; console.log("ok - correct token gets 200"); } else { failures++; console.error("FAIL - good token", res.status, res.body); }

  res = await request(7439, "/approve", { "content-type": "application/json" }, JSON.stringify({ token: u2.launchToken, name: "bash", args: { cmd: "x" } }));
  if (res.status === 400 && /DENIED/.test(res.body)) { n++; console.log("ok - /approve refuses deny-class tool over HTTP"); } else { failures++; console.error("FAIL - deny over http", res.status, res.body); }

  server.close();
  console.log(`\n${n} passed, ${failures} failed`);
  process.exit(failures ? 1 : 0);
})();
