// Development only: one loopback origin for auth and Streamlit WebSockets.
import http from "node:http";
import {pathToFileURL} from "node:url";

const origin = "http://localhost:3001";
const views = new Set(["sign-in", "sign-up", "sign-out", "verify-email", "forgot-password", "reset-password", "callback"]);

export function createLocalProxy({internalSecret, gatewayPort = 3000, streamlitPort = 8501}) {
  if (!internalSecret || internalSecret.length < 32) throw new Error("Local auth secret missing");
  const attempts = new Map();
  function route(req) {
    if (req.headers.host !== "localhost:3001" || !req.url?.startsWith("/") || req.url.startsWith("//")) return null;
    const path = new URL(req.url, origin).pathname;
    if (/%|\\|\/\//.test(path) || path.startsWith("/api/internal")) return null;
    const auth = path.startsWith("/api/auth/") || path === "/api/session" ||
      path.startsWith("/_next/") || views.has(path.replace(/^\/auth\//, "")) && path.startsWith("/auth/");
    return {path, port: auth ? gatewayPort : streamlitPort, auth};
  }
  function headers(req, websocket = false) {
    const result = {...req.headers};
    for (const key of Object.keys(result)) {
      if (key.startsWith("x-forwarded-") || key.startsWith("x-auth-") ||
          ["authorization", "forwarded", "proxy-authorization"].includes(key)) delete result[key];
    }
    if (!websocket) {delete result.connection; delete result.upgrade;}
    result.host = "localhost:3001";
    result["x-forwarded-host"] = "localhost:3001";
    result["x-forwarded-proto"] = "http";
    return result;
  }
  function validate(req) {
    return new Promise(resolve => {
      const request = http.request({hostname: "127.0.0.1", port: gatewayPort, path: "/api/internal/session",
        headers: {Authorization: `Bearer ${internalSecret}`, Cookie: req.headers.cookie || "", Origin: origin},
        timeout: 10000}, response => {response.resume(); resolve(response.statusCode === 200 ? 200 : response.statusCode === 401 ? 401 : 503);});
      request.on("timeout", () => request.destroy());
      request.on("error", () => resolve(503));
      request.end();
    });
  }
  const server = http.createServer(async (req, res) => {
    const target = route(req);
    const finish = (status, message) => {res.writeHead(status, {"Cache-Control": "no-store", "Content-Type": "text/plain"}); res.end(message);};
    if (!target) return finish(403, "Request rejected");
    if (req.headers.origin && req.headers.origin !== origin) return finish(403, "Request rejected");
    if (!["GET", "HEAD", "OPTIONS"].includes(req.method) && req.headers.origin !== origin) return finish(403, "Request rejected");
    if (target.auth && req.method === "POST") {
      if (Number(req.headers["content-length"] || 0) > 8192) return finish(413, "Request too large");
      const now = Date.now();
      const bucket = attempts.get("local") || {until: now + 60000, count: 0};
      if (bucket.until <= now) {bucket.until = now + 60000; bucket.count = 0;}
      attempts.set("local", bucket);
      if (++bucket.count > 30) return finish(429, "Please wait a minute before trying again");
    }
    // Streamlit's bundled static assets contain no user data. Every data route
    // and WebSocket still requires an authoritative session check.
    if (!target.auth && !target.path.startsWith("/static/")) {
      const status = await validate(req);
      if (status === 401) {res.writeHead(303, {Location: "/auth/sign-in", "Cache-Control": "no-store"}); res.end(); return;}
      if (status !== 200) return finish(503, "Sign-in service unavailable. Please try again.");
    }
    const upstream = http.request({hostname: "127.0.0.1", port: target.port, path: req.url,
      method: req.method, headers: headers(req), timeout: 30000}, response => {
        res.writeHead(response.statusCode, {...response.headers, "cache-control": "no-store"}); response.pipe(res);
      });
    upstream.on("timeout", () => upstream.destroy());
    upstream.on("error", () => {if (!res.headersSent) finish(503, "Local service is starting. Try again shortly."); else res.destroy();});
    req.on("aborted", () => upstream.destroy());
    req.pipe(upstream);
  });
  server.on("upgrade", async (req, socket, head) => {
    socket.on("error", () => {});
    const target = route(req);
    if (!target || target.auth || target.path !== "/_stcore/stream" || req.headers.origin !== origin || await validate(req) !== 200) {
      socket.end("HTTP/1.1 403 Forbidden\r\nConnection: close\r\n\r\n"); return;
    }
    const upstream = http.request({hostname: "127.0.0.1", port: streamlitPort, path: req.url, headers: headers(req, true)});
    upstream.on("upgrade", (response, stream, upstreamHead) => {
      socket.write(`HTTP/1.1 101 Switching Protocols\r\n${Object.entries(response.headers).map(([k,v]) => `${k}: ${v}`).join("\r\n")}\r\n\r\n`);
      if (upstreamHead.length) socket.write(upstreamHead);
      if (head.length) stream.write(head);
      socket.pipe(stream); stream.pipe(socket);
      stream.on("error", () => socket.destroy());
      socket.on("close", () => stream.destroy());
      stream.on("close", () => socket.destroy());
    });
    upstream.on("response", response => {response.resume(); socket.end("HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\n\r\n");});
    upstream.on("error", () => socket.destroy());
    upstream.end();
  });
  return server;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  if (process.env.APP_ENV !== "development" || process.env.APP_ORIGIN !== origin) throw new Error("Local proxy requires development settings");
  const server = createLocalProxy({internalSecret: process.env.AUTH_INTERNAL_SECRET});
  server.on("error", () => {process.stderr.write("Local proxy could not start. Check port 3001.\n"); process.exit(1);});
  server.listen(3001, "127.0.0.1");
}
