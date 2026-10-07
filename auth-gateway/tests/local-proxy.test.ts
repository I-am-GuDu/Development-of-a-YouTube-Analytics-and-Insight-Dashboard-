import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
// The dev proxy also runs directly in Node without a TypeScript runtime.
// @ts-expect-error JavaScript executable shared with integration tests
import {createLocalProxy} from "../scripts/local-proxy.mjs";

test("local proxy blocks forged hosts, internal routes, unauthenticated dashboard and cross-origin requests", async () => {
  let authenticated = false;
  let protectedHits = 0;
  const gateway = http.createServer((req, res) => {
    if (req.url === "/api/internal/session") {
      assert.equal(req.headers.authorization, "Bearer " + "i".repeat(48));
      res.writeHead(authenticated ? 200 : 401); res.end();
    } else {res.end("auth page");}
  });
  const dashboard = http.createServer((_req, res) => {protectedHits++; res.end("protected dashboard");});
  const listen = (server: http.Server) => new Promise<number>(resolve => server.listen(0, "127.0.0.1", () => resolve((server.address() as import("node:net").AddressInfo).port)));
  const gatewayPort = await listen(gateway), streamlitPort = await listen(dashboard);
  const proxy = createLocalProxy({internalSecret: "i".repeat(48), gatewayPort, streamlitPort});
  const port = await listen(proxy);
  const request = (path: string, headers = {}, method = "GET") => new Promise<{status: number; body: string}>(resolve => {
    const req = http.request({hostname: "127.0.0.1", port, path, method, headers: {Host: "localhost:3001", ...headers}}, res => {
      let body = ""; res.on("data", chunk => body += chunk); res.on("end", () => resolve({status: res.statusCode!, body}));
    }); req.end();
  });
  try {
    assert.equal((await request("/auth/sign-in")).status, 200);
    assert.equal((await request("/", {Host: "evil.example"})).status, 403);
    assert.equal((await request("/api/internal/session")).status, 403);
    assert.equal((await request("/api/auth/sign-out", {Origin: "https://evil.example"}, "POST")).status, 403);
    assert.equal((await request("/")).status, 303);
    assert.equal(protectedHits, 0);
    authenticated = true;
    assert.equal((await request("/")).body, "protected dashboard");
    authenticated = false;
    assert.equal((await request("/_stcore/upload_file/test")).status, 303);
    assert.equal(protectedHits, 1);
  } finally {
    await Promise.all([proxy, gateway, dashboard].map(server => new Promise<void>(resolve => server.close(() => resolve()))));
  }
});
