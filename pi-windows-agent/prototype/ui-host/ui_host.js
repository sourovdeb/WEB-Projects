// PiWin UI host prototype — token minting, approval recording, hardened listener.
// No dependencies; Node >= 18. Deny-first inventory enforced with the helper's Guard.
const http = require("http");
const crypto = require("crypto");

const DENY_TOOLS = new Set(["powershell", "bash", "edit", "write", "mcp", "playwright", "codemode"]);
const ALLOW_TOOLS = new Set(["read", "list_windows", "list_controls", "screenshot"]);

function canonicalJson(name, args) {
  // Same encoding as helper/piwin_helper.py — both sides must match exactly.
  // Python: json.dumps({"name":n,"args":a}, sort_keys=True,
  //                     separators=(",",":"), ensure_ascii=False)
  // -> top-level keys sorted means "args" comes BEFORE "name".
  const canon = (o) => {
    if (o === null || typeof o !== "object") return JSON.stringify(o);
    if (Array.isArray(o)) return "[" + o.map(canon).join(",") + "]";
    return "{" + Object.keys(o).sort().map(k => JSON.stringify(k) + ":" + canon(o[k])).join(",") + "}";
  };
  return canon({ args, name });
}

function callHash(name, args) {
  return crypto.createHash("sha256").update(canonicalJson(name, args), "utf8").digest("hex");
}

class UiHost {
  constructor() {
    this.launchToken = crypto.randomBytes(32).toString("hex");
    this.approvals = new Map(); // hash -> {target}
  }

  approve(name, args, target) {
    if (DENY_TOOLS.has(name) || name.startsWith("mcp__")) {
      throw new Error(`tool ${name} is DENIED outright in v0.1`);
    }
    if (!name.startsWith("ui.") && !ALLOW_TOOLS.has(name)) {
      throw new Error(`tool ${name} is not in the v0.1 inventory`);
    }
    const h = callHash(name, args);
    this.approvals.set(h, { target });
    return h;
  }

  has(h) { return this.approvals.has(h); }
}

function startServer(uiHost, port = 7431) {
  const server = http.createServer((req, res) => {
    res.setHeader("Content-Type", "application/json");
    // Cross-origin rejection: no Origin header allowed except same-origin.
    const origin = req.headers["origin"];
    if (origin) { res.writeHead(403); res.end('{"error":"cross-origin rejected"}'); return; }
    // Host header pinning (DNS-rebinding defense).
    const host = req.headers["host"] || "";
    if (!host.startsWith("127.0.0.1:") && host !== "localhost:7431") {
      res.writeHead(403); res.end('{"error":"bad host"}'); return;
    }
    let body = "";
    req.on("data", (c) => { body += c; if (body.length > 1e6) req.destroy(); });
    req.on("end", () => {
      try {
        const msg = body ? JSON.parse(body) : {};
        if (msg.token !== uiHost.launchToken) {
          res.writeHead(401); res.end('{"error":"bad launch token"}'); return;
        }
        if (req.url === "/approve" && msg.name && msg.args) {
          const h = uiHost.approve(msg.name, msg.args, msg.target || null);
          res.writeHead(200); res.end(JSON.stringify({ hash: h }));
        } else if (req.url === "/status") {
          res.writeHead(200); res.end('{"status":"ok"}');
        } else {
          res.writeHead(404); res.end('{"error":"not found"}');
        }
      } catch (e) {
        res.writeHead(400); res.end(JSON.stringify({ error: String(e.message || e) }));
      }
    });
  });
  server.listen(port, "127.0.0.1"); // 127.0.0.1 only — never 0.0.0.0
  return server;
}

module.exports = { UiHost, startServer, callHash, canonicalJson, DENY_TOOLS, ALLOW_TOOLS };

if (require.main === module) {
  const uiHost = new UiHost();
  console.log("Launch token (per-launch, printed once to console):", uiHost.launchToken);
  startServer(uiHost);
  console.log("PiWin UI host prototype on http://127.0.0.1:7431 (localhost only)");
}
