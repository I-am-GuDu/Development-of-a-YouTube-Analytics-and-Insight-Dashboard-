import { getAuth } from "../../../../lib/auth";
import { readConfig, publicRequestAllowed } from "../../../../lib/config";
import { allowedAuthPath, authPayload } from "../../../../lib/auth-policy";
import { copyAuthCookies, NO_STORE, safeUser } from "../../../../lib/security";
import { lookupSession } from "../../../../lib/session";
import { readJsonBody } from "../../../../lib/request-body";

export const dynamic = "force-dynamic";
type Context = {params: Promise<{path: string[]}>};

async function handle(request: Request, context: Context) {
  try {
    const config = readConfig();
    const path = (await context.params).path.join("/");
    if (!allowedAuthPath(path, request.method)) return new Response(null, {status: 404, headers: NO_STORE});
    if (!publicRequestAllowed(request, config, request.method === "POST")) {
      return new Response(null, {status: 403, headers: NO_STORE});
    }
    if (path === "get-session") {
      const session = await lookupSession(request.headers.get("cookie"));
      const response = Response.json(session.session ? {
        user: {...session.session.user, name: session.session.user.display_name, emailVerified: true},
        session: {expiresAt: session.session.expires_at}
      } : null, {status: session.status === 401 ? 200 : session.status, headers: NO_STORE});
      copyAuthCookies(session.cookies, response.headers);
      return response;
    }
    const url = new URL(config.origin + "/api/auth/" + path);
    if (request.method === "GET") {
      const token = new URL(request.url).searchParams.get("token");
      if (!token || token.length > 2048) return new Response(null, {status: 400, headers: NO_STORE});
      url.searchParams.set("token", token);
      url.searchParams.set("callbackURL", config.origin + "/auth/sign-in");
    }
    const headers = new Headers({Host: new URL(config.origin).host, Origin: config.origin});
    const cookie = request.headers.get("cookie");
    if (cookie && cookie.length <= 16384 && !/[\r\n\0]/.test(cookie)) headers.set("Cookie", cookie);
    let body: string | undefined;
    if (request.method === "POST") {
      const parsed = await readJsonBody(request);
      if (!parsed.body) return new Response(null, {status: parsed.status || 400, headers: NO_STORE});
      const payload = authPayload(path, parsed.body, config);
      if (!payload) return Response.json({message: "Sign-in is unavailable or the form is incomplete."}, {status: 400, headers: NO_STORE});
      body = JSON.stringify(payload);
      headers.set("Content-Type", "application/json");
    }
    const handlers = getAuth().handler();
    const upstream = await handlers[request.method as "GET" | "POST"](
      new Request(url, {method: request.method, headers, body}), context
    );
    const data = await upstream.json().catch(() => null);
    let response: Response;
    if (path === "sign-up/email" || path === "request-password-reset" || path === "send-verification-email" || path === "email-otp/send-verification-otp") {
      // Keep success and account-existence errors indistinguishable.
      const accountExists = path === "sign-up/email" && ["USER_ALREADY_EXISTS", "USER_ALREADY_EXISTS_USE_ANOTHER_EMAIL"].includes(data?.code);
      const missingAccount = ["USER_NOT_FOUND", "EMAIL_NOT_FOUND"].includes(data?.code) && path !== "sign-up/email";
      const status = upstream.ok || accountExists || missingAccount ? 200 : upstream.status === 429 ? 429 : 503;
      response = Response.json(status === 200 ? {status: true} : {message: "Please try again shortly."}, {status, headers: NO_STORE});
    } else if (!upstream.ok) {
      response = Response.json({message: "Unable to complete sign-in. Check your details or verify your email."}, {
        status: upstream.status >= 500 ? 503 : upstream.status, headers: NO_STORE
      });
    } else if (path === "sign-in/social") {
      const target = typeof data?.url === "string" ? new URL(data.url) : null;
      const managedStart = new URL(config.neonUrl + "/sign-in/social/init");
      const expectedDestination = target && (target.hostname === "accounts.google.com" ||
        (target.origin === managedStart.origin && target.pathname === managedStart.pathname));
      if (!target || target.protocol !== "https:" || target.username || target.password || target.port || !expectedDestination) {
        return new Response(null, {status: 502, headers: NO_STORE});
      }
      response = Response.json({url: target.href, redirect: true}, {headers: NO_STORE});
    } else {
      response = Response.json({status: true, user: safeUser(data?.user)}, {headers: NO_STORE});
    }
    // Session and provider tokens remain in HttpOnly cookies, never in JSON or token headers.
    copyAuthCookies(upstream.headers, response.headers);
    return response;
  } catch { return Response.json({message: "Authentication is temporarily unavailable."}, {status: 503, headers: NO_STORE}); }
}
export const GET = handle;
export const POST = handle;
