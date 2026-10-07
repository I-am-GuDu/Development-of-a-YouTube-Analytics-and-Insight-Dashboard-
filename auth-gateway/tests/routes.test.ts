import test from "node:test";
import assert from "node:assert/strict";
import { POST } from "../app/api/auth/[...path]/route";
import { GET as internalSession } from "../app/api/internal/session/route";
import { GET as oauthCallback } from "../app/auth/callback/route";
import { SESSION_COOKIE } from "../lib/security";

const origin = "https://ytvideoanalysis.studio";
Object.assign(process.env, {
  APP_ORIGIN: origin, NEON_AUTH_URL: "https://unit-test.neonauth.ap-southeast-1.aws.neon.tech/neondb/auth",
  NEON_AUTH_COOKIE_SECRET: "c".repeat(48), AUTH_INTERNAL_SECRET: "i".repeat(48),
  AUTH_GOOGLE_ENABLED: "false", AUTH_LINKING_REVIEWED: "false"
});
const context = (path: string) => ({params: Promise.resolve({path: path.split("/")})});
test("OAuth callback errors return safely to sign-in without a session lookup", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error("Unexpected session lookup"); };
  try {
    for (const [error, expected] of [["access_denied", "google_canceled"], ["google_canceled", "google_canceled"],
      ["https://attacker.example", "google_failed"]]) {
      const response = await oauthCallback(new Request(origin + "/auth/callback?error=" + encodeURIComponent(error),
        {headers: {Host: "ytvideoanalysis.studio"}}));
      assert.equal(response.status, 303);
      assert.equal(response.headers.get("Location"), origin + "/auth/sign-in?error=" + expected);
      assert.equal(response.headers.get("Cache-Control"), "no-store");
    }
  } finally { globalThis.fetch = original; }
});
function request(path: string, body: object, requestOrigin = origin) {
  return new Request(origin + "/api/auth/" + path, {
    method: "POST", headers: {Host: "ytvideoanalysis.studio", Origin: requestOrigin, "Content-Type": "application/json"},
    body: JSON.stringify(body)
  });
}

test("browser response removes SDK token bodies and headers", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => Response.json({token: "DO-NOT-EXPOSE", user: {id: "a", email: "a@example.com", name: "A", emailVerified: true}}, {
    headers: {"set-auth-token": "DO-NOT-EXPOSE", "Set-Cookie": `${SESSION_COOKIE}=synthetic; HttpOnly; Secure; Path=/`}
  });
  try {
    const response = await POST(request("sign-in/email", {email: "a@example.com", password: "synthetic-password"}), context("sign-in/email"));
    assert.equal(response.status, 200);
    assert.equal((await response.text()).includes("DO-NOT-EXPOSE"), false);
    assert.equal(response.headers.get("set-auth-token"), null);
    assert.match(response.headers.get("Set-Cookie") || "", /HttpOnly/);
    assert.equal(response.headers.get("Cache-Control"), "no-store");
  } finally { globalThis.fetch = original; }
});

test("cross-origin mutations and admin endpoints never reach Neon", async () => {
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {calls++; throw new Error("Unexpected call");};
  try {
    assert.equal((await POST(request("sign-in/email", {email: "a@example.com", password: "synthetic"}, "https://attacker.example"), context("sign-in/email"))).status, 403);
    assert.equal((await POST(request("admin/list-users", {}), context("admin/list-users"))).status, 404);
    assert.equal((await POST(request("sign-in/social", {provider: "google"}), context("sign-in/social"))).status, 400);
    assert.equal(calls, 0);
  } finally { globalThis.fetch = original; }
});

test("internal session endpoint rejects cookie-only access", async () => {
  assert.equal((await internalSession(new Request(origin + "/api/internal/session", {headers: {Cookie: `${SESSION_COOKIE}=synthetic`}}))).status, 403);
});

test("Google allows the exact managed Neon initiation route and rejects other destinations", async () => {
  const original = globalThis.fetch;
  process.env.AUTH_GOOGLE_ENABLED = "true";
  process.env.AUTH_LINKING_REVIEWED = "true";
  try {
    for (const [url, expected] of [
      [process.env.NEON_AUTH_URL + "/sign-in/social/init?opaque=synthetic", 200],
      ["https://accounts.google.com/o/oauth2/v2/auth?opaque=synthetic", 200],
      [process.env.NEON_AUTH_URL + "/arbitrary-redirect", 502],
      ["https://attacker.neonauth.aws.neon.tech/neondb/auth/sign-in/social/init", 502],
      ["https://accounts.google.com.evil.example/oauth", 502],
    ] as const) {
      globalThis.fetch = async () => Response.json({url, redirect: true});
      const response = await POST(request("sign-in/social", {provider: "google"}), context("sign-in/social"));
      assert.equal(response.status, expected);
    }
  } finally {
    globalThis.fetch = original;
    process.env.AUTH_GOOGLE_ENABLED = "false";
    process.env.AUTH_LINKING_REVIEWED = "false";
  }
});

test("account-existence responses stay generic but provider configuration failures are not reported as success", async () => {
  const original = globalThis.fetch;
  try {
    for (const [code, status, expected] of [
      ["USER_ALREADY_EXISTS", 400, 200], ["USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL", 422, 200],
      ["INVALID_ORIGIN", 403, 503], ["SERVICE_UNAVAILABLE", 503, 503], ["TOO_MANY_REQUESTS", 429, 429]
    ] as const) {
      globalThis.fetch = async () => Response.json({code, message: "private upstream detail"}, {status});
      const response = await POST(request("sign-up/email", {name: "Test", email: "test@example.com", password: "test-password-long"}), context("sign-up/email"));
      assert.equal(response.status, expected);
      assert.equal((await response.text()).includes("private upstream detail"), false);
    }
  } finally {globalThis.fetch = original;}
});

test("malformed JSON and oversized streamed bodies are rejected before contacting Neon", async () => {
  const original = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async () => {calls++; throw new Error("Unexpected call");};
  try {
    for (const [body, status] of [["{invalid", 400], ["[1,2]", 400], ["x".repeat(8193), 413]] as const) {
      const input = new Request(origin + "/api/auth/sign-in/email", {method: "POST",
        headers: {Host: "ytvideoanalysis.studio", Origin: origin, "Content-Type": "application/json"}, body});
      assert.equal((await POST(input, context("sign-in/email"))).status, status);
    }
    assert.equal(calls, 0);
  } finally {globalThis.fetch = original;}
});
