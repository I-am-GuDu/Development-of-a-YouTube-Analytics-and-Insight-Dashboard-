// Offline UI preview only. Production must use the HTTPS gateway behind Nginx.
import http from "node:http";
import {spawn} from "node:child_process";
import {fileURLToPath} from "node:url";

const appDirectory = fileURLToPath(new URL("../", import.meta.url));
const excluded = new Set(["DATABASE_URL", "DB_PASSWORD", "YOUTUBE_API_KEY", "CLOUDFLARE_API_TOKEN", "CLOUDFLARE_ACCOUNT_ID"]);
const env = {...Object.fromEntries(Object.entries(process.env).filter(([key]) => !excluded.has(key))),
  APP_ORIGIN: "https://ytvideoanalysis.studio",
  NEON_AUTH_URL: "https://unit-test.neonauth.ap-southeast-1.aws.neon.tech/neondb/auth",
  NEON_AUTH_COOKIE_SECRET: "c".repeat(48), AUTH_INTERNAL_SECRET: "i".repeat(48),
  AUTH_GOOGLE_ENABLED: "false", AUTH_LINKING_REVIEWED: "false", NEXT_TELEMETRY_DISABLED: "1"};
const child = spawn(process.execPath, ["node_modules/next/dist/bin/next", "start", "--hostname", "127.0.0.1", "--port", "3000"],
  {cwd: appDirectory, env, stdio: ["ignore", "pipe", "pipe"], windowsHide: true});
child.stdout.pipe(process.stdout); child.stderr.pipe(process.stderr);
const views = new Set(["sign-in", "sign-up", "sign-out", "verify-email", "forgot-password", "reset-password"]);
const server = http.createServer((req, res) => {
  try {
    const path = new URL(req.url, "http://localhost").pathname;
    if (req.method !== "GET" || (!path.startsWith("/_next/") && !views.has(path.replace(/^\/auth\//, "")))) {
      res.writeHead(503, {"Content-Type": "application/json", "Cache-Control": "no-store"});
      res.end(JSON.stringify({message: "Sign-in is unavailable in this offline preview."}));
      return;
    }
    const headers = {Host: "ytvideoanalysis.studio", "X-Forwarded-Host": "ytvideoanalysis.studio", "X-Forwarded-Proto": "https"};
    for (const [key, value] of Object.entries(req.headers)) {
      if (value && !["host", "connection", "cookie", "authorization", "x-forwarded-host", "x-forwarded-proto"].includes(key)) headers[key] = value;
    }
    const upstream = http.request({hostname: "127.0.0.1", port: 3000, path: req.url, headers}, response => {
      res.writeHead(response.statusCode, response.headers); response.pipe(res);
    });
    upstream.on("error", () => {res.writeHead(503); res.end("Starting preview");});
    upstream.end();
  } catch {res.writeHead(503); res.end("Preview unavailable");}
});
let stopping = false;
function stop() {stopping = true; server.close(); child.kill(); process.exit(0);}
child.on("error", () => {server.close(); process.exit(1);});
child.on("exit", code => {if (!stopping) {server.close(); process.exit(code || 1);}});
server.on("error", () => {child.kill(); process.exit(1);});
server.listen(3001, "127.0.0.1", () => process.stdout.write("Offline preview: http://localhost:3001/auth/sign-in\n"));
process.on("SIGINT", stop); process.on("SIGTERM", stop); process.on("exit", () => child.kill());
// Private parent-process pipe lets the combined local launcher stop this helper.
process.stdin.on("data", value => {if (value.toString().trim() === "stop") stop();});
