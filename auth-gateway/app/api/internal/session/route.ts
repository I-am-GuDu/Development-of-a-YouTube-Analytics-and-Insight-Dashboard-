import { readConfig } from "../../../../lib/config";
import { lookupSession } from "../../../../lib/session";
import { secretMatches, NO_STORE } from "../../../../lib/security";
import { sessionCookie } from "../../../../lib/security";
import { getAuth } from "../../../../lib/auth";

export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  try {
    const config = readConfig();
    if (!secretMatches(request.headers.get("authorization"), `Bearer ${config.internalSecret}`)) {
      return new Response(null, {status: 403, headers: NO_STORE});
    }
    const result = await lookupSession(request.headers.get("cookie"));
    return Response.json(result.session || {error: "Session unavailable"}, {status: result.status, headers: NO_STORE});
  } catch { return new Response(null, {status: 503, headers: NO_STORE}); }
}

export async function POST(request: Request) {
  try {
    const config = readConfig();
    if (!secretMatches(request.headers.get("authorization"), `Bearer ${config.internalSecret}`)) {
      return new Response(null, {status: 403, headers: NO_STORE});
    }
    const cookie = sessionCookie(request.headers.get("cookie"));
    if (!cookie) return new Response(null, {status: 401, headers: NO_STORE});
    const response = await getAuth().handler().POST(new Request(config.origin + "/api/auth/sign-out", {
      method: "POST", headers: {Cookie: cookie, Origin: config.origin, "Content-Type": "application/json"}, body: "{}"
    }), {params: Promise.resolve({path: ["sign-out"]})});
    return new Response(null, {status: response.ok ? 204 : 503, headers: NO_STORE});
  } catch { return new Response(null, {status: 503, headers: NO_STORE}); }
}
