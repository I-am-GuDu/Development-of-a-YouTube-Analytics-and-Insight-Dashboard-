import test from "node:test";
import assert from "node:assert/strict";
import { readConfig, publicRequestAllowed } from "../lib/config";
import { authPayload, allowedAuthPath } from "../lib/auth-policy";
import { SESSION_COOKIE, sessionCookie, verifiedSession, secretMatches, copyAuthCookies } from "../lib/security";
import { lookupSession } from "../lib/session";
import { createNeonAuth } from "@neondatabase/auth/next/server";

const env = {
  APP_ORIGIN: "https://ytvideoanalysis.studio",
  NEON_AUTH_URL: "https://unit-test.neonauth.ap-southeast-1.aws.neon.tech/neondb/auth",
  NEON_AUTH_COOKIE_SECRET: "c".repeat(48), AUTH_INTERNAL_SECRET: "i".repeat(48),
  AUTH_GOOGLE_ENABLED: "false", AUTH_LINKING_REVIEWED: "false"
};
const config = readConfig(env);
const identity = () => ({user: {id: "user-a", email: "a@example.com", name: "A", emailVerified: true},
  session: {userId: "user-a", expiresAt: new Date(Date.now() + 3600000).toISOString(), token: "private-token"}});

test("unsafe configuration and unreviewed linking fail closed", () => {
  for (const APP_ORIGIN of ["http://ytvideoanalysis.studio", "https://ytvideoanalysis.studio/path", "https://a:b@ytvideoanalysis.studio"]) {
    assert.throws(() => readConfig({...env, APP_ORIGIN}));
  }
  assert.throws(() => readConfig({...env, AUTH_INTERNAL_SECRET: env.NEON_AUTH_COOKIE_SECRET}));
  assert.throws(() => readConfig({...env, NEON_AUTH_URL: "https://attacker.example/auth"}));
  assert.throws(() => readConfig({...env, AUTH_GOOGLE_ENABLED: "true"}));
});

test("local HTTP and test-account Google access are restricted to the explicit development origin", () => {
  const local = {...env, APP_ENV: "development", APP_ORIGIN: "http://localhost:3001",
    AUTH_GOOGLE_ENABLED: "true", AUTH_LOCAL_TEST_ACCOUNTS_ONLY: "true"};
  assert.equal(readConfig(local).googleEnabled, true);
  for (const APP_ORIGIN of ["http://localhost:3000", "http://127.0.0.1:3001", "http://localhost.evil.example:3001", "http://ytvideoanalysis.studio:3001"]) {
    assert.throws(() => readConfig({...local, APP_ORIGIN}));
  }
  assert.throws(() => readConfig({...local, APP_ENV: "production"}));
  assert.throws(() => readConfig({...local, APP_ORIGIN: env.APP_ORIGIN}));
});

test("mutations reject absent or foreign Origin and forged Host", () => {
  const request = (headers: Record<string, string>) => new Request(config.origin, {headers});
  assert.equal(publicRequestAllowed(request({Host: "attacker.example", Origin: config.origin}), config, true), false);
  assert.equal(publicRequestAllowed(request({Host: "ytvideoanalysis.studio"}), config, true), false);
  assert.equal(publicRequestAllowed(request({Host: "ytvideoanalysis.studio", Origin: "https://attacker.example"}), config, true), false);
  assert.equal(publicRequestAllowed(request({Host: "ytvideoanalysis.studio", Origin: config.origin, "Sec-Fetch-Site": "cross-site"}), config, true), false);
  assert.equal(publicRequestAllowed(request({Host: "ytvideoanalysis.studio", Origin: config.origin}), config, true), true);
});

test("Google is gated; user-supplied destinations and scopes are discarded", () => {
  assert.equal(authPayload("sign-in/social", {provider: "google"}, config), null);
  const payload = authPayload("sign-in/social", {provider: "google", callbackURL: "https://attacker.example", scopes: ["youtube"], idToken: "forged"}, {...config, googleEnabled: true});
  assert.deepEqual(payload, {provider: "google", callbackURL: config.origin + "/auth/callback",
    newUserCallbackURL: config.origin + "/auth/callback"});
  assert.equal(authPayload("sign-in/social", {provider: "github"}, {...config, googleEnabled: true}), null);
  assert.equal(allowedAuthPath("admin/ban-user", "POST"), false);
  assert.equal(allowedAuthPath("link-social", "POST"), false);
  assert.equal(allowedAuthPath("sign-out", "GET"), false);
});

test("reset and verification destinations are fixed; weak signup is rejected", () => {
  assert.deepEqual(authPayload("request-password-reset", {email: "a@example.com", redirectTo: "https://attacker.example"}, config),
    {email: "a@example.com", redirectTo: config.origin + "/auth/reset-password"});
  assert.equal(authPayload("sign-up/email", {email: "a@example.com", password: "short", name: "A"}, config), null);
  assert.equal(authPayload("email-otp/verify-email", {email: "a@example.com", otp: "<script>"}, config), null);
});

test("expired, unverified, disabled and mismatched identities are denied", () => {
  assert.equal(verifiedSession({...identity(), user: {...identity().user, emailVerified: false}}), null);
  assert.equal(verifiedSession({...identity(), user: {...identity().user, banned: true}}), null);
  assert.equal(verifiedSession({...identity(), session: {...identity().session, userId: "user-b"}}), null);
  assert.equal(verifiedSession({...identity(), session: {...identity().session, expiresAt: "2000-01-01"}}), null);
  const verified = verifiedSession(identity());
  assert.equal(verified?.user.id, "user-a");
  assert.equal(JSON.stringify(verified).includes("private-token"), false);
});

test("ambiguous cookies are denied and internal credentials are compared exactly", () => {
  assert.equal(sessionCookie(`${SESSION_COOKIE}=a; ${SESSION_COOKIE}=b`), null);
  assert.equal(sessionCookie(`${SESSION_COOKIE}=bad value`), null);
  assert.equal(sessionCookie(`${SESSION_COOKIE}=ok; untrusted=email`), `${SESSION_COOKIE}=ok`);
  assert.equal(secretMatches("Bearer wrong", "Bearer correct"), false);
  assert.equal(secretMatches("Bearer correct", "Bearer correct"), true);
});

test("only secure host-only Neon cookies reach the browser", () => {
  const source = new Headers();
  source.append("Set-Cookie", `${SESSION_COOKIE}=x; Domain=.neon.tech; Path=/auth; SameSite=None`);
  source.append("Set-Cookie", "unrelated=value");
  const target = new Headers();
  copyAuthCookies(source, target);
  const cookies = target.getSetCookie();
  assert.equal(cookies.length, 1);
  assert.match(cookies[0], /Path=\/; Secure; HttpOnly; SameSite=Lax$/);
  assert.doesNotMatch(cookies[0], /Domain=/);
});

test("every validation bypasses local caches and rejects revocation on the next call", async () => {
  let calls = 0;
  const handler = async (request: Request) => {
    calls++;
    assert.equal(new URL(request.url).searchParams.get("disableCookieCache"), "true");
    assert.equal(request.headers.get("cookie"), `${SESSION_COOKIE}=synthetic`);
    return Response.json(calls === 1 ? identity() : null);
  };
  const cookie = `${SESSION_COOKIE}=synthetic; __Secure-neon-auth.local.session_data=stale`;
  assert.equal((await lookupSession(cookie, handler, config.origin)).status, 200);
  assert.equal((await lookupSession(cookie, handler, config.origin)).status, 401);
  assert.equal(calls, 2);
  assert.equal((await lookupSession(cookie, async () => {throw new Error("private detail");}, config.origin)).status, 503);
});

test("pinned official SDK forwards cache bypass to Neon", async () => {
  const original = globalThis.fetch;
  const seen: string[] = [];
  globalThis.fetch = async (input, init) => {
    const url = String(input);
    seen.push(url);
    assert.equal(new URL(url).searchParams.get("disableCookieCache"), "true");
    assert.equal(new Headers(init?.headers).get("cookie"), `${SESSION_COOKIE}=synthetic`);
    return Response.json(seen.length === 1 ? identity() : null);
  };
  try {
    const auth = createNeonAuth({baseUrl: config.neonUrl, cookies: {secret: config.cookieSecret, sessionDataTtl: 1}, logLevel: "silent"});
    assert.equal((await lookupSession(`${SESSION_COOKIE}=synthetic`, auth.handler().GET, config.origin)).status, 200);
    assert.equal((await lookupSession(`${SESSION_COOKIE}=synthetic`, auth.handler().GET, config.origin)).status, 401);
    assert.equal(seen.length, 2);
  } finally { globalThis.fetch = original; }
});
