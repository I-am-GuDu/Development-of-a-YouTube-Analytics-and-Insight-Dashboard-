import { getAuth } from "./auth";
import { readConfig } from "./config";
import { sessionCookie, verifiedSession, type VerifiedSession } from "./security";

export type SessionResult = {status: number; session: VerifiedSession | null; cookies: Headers};
type Handler = (request: Request, context: {params: Promise<{path: string[]}>}) => Promise<Response>;

export async function lookupSession(
  cookieHeader: string | null,
  handler?: Handler,
  origin?: string
): Promise<SessionResult> {
  const cookie = sessionCookie(cookieHeader);
  const empty = (status: number): SessionResult => ({status, session: null, cookies: new Headers()});
  if (!cookie) return empty(401);
  try {
    const appOrigin = origin || readConfig().origin;
    const request = new Request(`${appOrigin}/api/auth/get-session?disableCookieCache=true`, {
      headers: {Cookie: cookie, Origin: appOrigin, Host: new URL(appOrigin).host}
    });
    // Only the primary session cookie is passed. Both the SDK cache and the
    // upstream Better Auth cookie cache are bypassed on every validation.
    let timer: ReturnType<typeof setTimeout> | undefined;
    const timeout = new Promise<never>((_, reject) => {
      timer = setTimeout(() => reject(new Error("Auth timeout")), 8000);
    });
    try {
      return await Promise.race([
        (async () => {
          const response = await (handler || getAuth().handler().GET)(request, {params: Promise.resolve({path: ["get-session"]})});
          if (!response.ok) return empty(response.status >= 500 ? 503 : 401);
          const session = verifiedSession(await response.json());
          if (!session) return empty(401);
          return {status: 200, session, cookies: response.headers};
        })(), timeout]);
    } finally { clearTimeout(timer); }
  } catch { return empty(503); }
}
