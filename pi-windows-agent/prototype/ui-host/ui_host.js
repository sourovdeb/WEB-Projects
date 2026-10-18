// PiWin UI host prototype — token minting, approval recording, hardened listener.
// v0.1.1 audit fixes: exact Host pinning (bound port only), float normalization,
// __-key stripping, confirm_second endpoint, target required for ui.* approvals.
const http = require("http");
const crypto = require("crypto");

const DENY_TOOLS = new Set(["powershell", "bash", "edit", "write", "mcp", "playwright", "codemode"]);
const ALLOW_TOOLS = new Set(["read", "list_windows", "list_controls", "screenshot"]);
const IRREVERSIBLE_ACTION_CLASSES = new Set([
  "delete-file", "recycle", "publish", "send", "share", "grant-token",
  "save-over", "install", "format", "pay", "export",
]);

// Hash-side normalization — must match helper/piwin_helper.py byte for byte.
function normalize(v) {
  if (typeof v === "number" && Number.isInteger(v)) return v;       // 1 stays 1
  if (typeof v === "number" && Number.isFinite(v) && v % 1 === 0) return v | 0 || Math.trunc(v); // 1.0 -> 1
  if (v === null || typeof v !== "object") return v;
  if (Array.isArray(v)) return v.map(normalize);
  const o = {};
  for (const k of Object.keys(v)) if (!k.startsWith("__")) o[k] = normalize(v[k]);
  return o;
}

function canonicalJson(name, args) {
  const canon = (o) => {
    if (o === null || typeof o !== "object") return JSON.stringify(o);
    if (Array.isArray(o)) return "[" + o.map(canon).join(",") + "]";
    return "{" + Object.keys(o).sort().map(k => JSON.stringify(k) + ":" + canon(o[k])).join(",") + "}";
  };
  return canon({ args: normalize(args), name });
}

function callHash(name, args) {
  return crypto.createHash("sha256").update(canonicalJson(name, args), "utf8").digest("hex");
}

function inventoryCheck(name) {
  if (DENY_TOOLS.has(name) || name.startsWith("mcp__")) {
    throw new Error(`tool ${name} is DENIED outright in v0.1`);
  }
  if (name.startsWith("ui.") || ALLOW_TOOLS.has(name)) return;
  throw new Error(`tool ${name} is not in the v0.1 inventory`);
}

class UiHost {
  constructor() {
    this.launchToken = crypto.randomBytes(32).toString("hex");
    this.approvals = new Map(); // hash -> {target, actionClass, requiresSecond, secondConfirmed}
  }

  approve(name, args, target, actionClass = "ui", extraConfirm = false) {
    inventoryCheck(name); // fix 3 mirrored: mint refuses DENY/unknown
    if (name.startsWith("ui.")) {
      if (!target || target.pid == null || !target.window || !target.control) {
        throw new Error("ui.* approval requires pid/window/control target");
      }
    }
    const h = callHash(name, args);
    this.approvals.set(h, {
      target,
      actionClass,
      requiresSecond: IRREVERSIBLE_ACTION_CLASSES.has(actionClass) || !!extraConfirm,
      secondConfirmed: false,
    });
    return h;
  }

  confirmSecond(h, target) {
    const ap = this.approvals.get(h);
    if (!ap) throw new Error("no such approval");
    if (!target || !ap.target ||
        target.pid !== ap.target.pid || target.window !== ap.target.window ||
        target.control !== ap.target.control) {
      throw new Error("second confirmation target mismatch");
    }
    ap.secondConfirmed = true;
  }

  has(h) { return this.approvals.has(h); }
}

function startServer(uiHost, port = 7431) {
  const server = http.createServer((req, res) => {
    res.setHeader("Content-Type", "application/json");
    const origin = req.headers["origin"];
    if (origin) { res.writeHead(403); res.end('{"error":"cross-origin rejected"}'); return; }
    // fix 4: exact pinning — only 127.0.0.1:<port> or localhost:<port>.
    const host = req.headers["host"] || "";
    const okHost = host === `127.0.0.1:${port}` || host === `localhost:${port}`;
    if (!okHost) { res.writeHead(403); res.end('{"error":"bad host"}'); return; }
    let body = "";
    req.on("data", (c) => { body += c; if (body.length > 1e6) req.destroy(); });
    req.on("end", () => {
      try {
        const msg = body ? JSON.parse(body) : {};
        if (msg.token !== uiHost.launchToken) {
          res.writeHead(401); res.end('{"error":"bad launch token"}'); return;
        }
        if (req.url === "/approve" && msg.name && msg.args) {
          const h = uiHost.approve(msg.name, msg.args, msg.target || null,
                                   msg.action_class || "ui", !!msg.extra_confirm);
          res.writeHead(200); res.end(JSON.stringify({ hash: h }));
        } else if (req.url === "/confirm-second" && msg.hash) {
          uiHost.confirmSecond(msg.hash, msg.target || null);
          res.writeHead(200); res.end('{"status":"confirmed"}');
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

module.exports = { UiHost, startServer, callHash, canonicalJson, normalize,
                   inventoryCheck, DENY_TOOLS, ALLOW_TOOLS, IRREVERSIBLE_ACTION_CLASSES };

if (require.main === module) {
  const uiHost = new UiHost();
  console.log("Launch token (per-launch, printed once to console):", uiHost.launchToken);
  startServer(uiHost);
  console.log("PiWin UI host prototype on http://127.0.0.1:7431 (localhost only)");
}
