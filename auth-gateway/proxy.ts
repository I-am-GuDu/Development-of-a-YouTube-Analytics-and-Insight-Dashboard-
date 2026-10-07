import { NextRequest, NextResponse } from "next/server";
import { getAuth } from "./lib/auth";
import { readConfig, publicRequestAllowed } from "./lib/config";
import { randomBytes } from "node:crypto";

export async function proxy(request: NextRequest) {
  try {
    const config = readConfig();
    if (!publicRequestAllowed(request, config)) return new NextResponse(null, {status: 403});
    // The official middleware exchanges Neon's one-use OAuth verifier and
    // redirects to a clean URL. Never implement a token-in-URL handoff here.
    const nonce = randomBytes(16).toString("base64");
    const csp = `default-src 'self'; script-src 'self' 'nonce-${nonce}' 'strict-dynamic'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'; object-src 'none'`;
    const headers = new Headers(request.headers);
    headers.set("Content-Security-Policy", csp);
    headers.set("x-nonce", nonce);
    const response = request.nextUrl.pathname === "/auth/callback"
      ? await getAuth().middleware({loginUrl: "/auth/sign-in"})(request)
      : NextResponse.next({request: {headers}});
    response.headers.set("Content-Security-Policy", csp);
    response.headers.set("Cache-Control", "no-store");
    response.headers.set("Referrer-Policy", "no-referrer");
    return response;
  } catch { return new NextResponse(null, {status: 503}); }
}
export const config = {matcher: ["/auth/:path*"]};
