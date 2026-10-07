import { readConfig, publicRequestAllowed } from "../../../lib/config";
import { lookupSession } from "../../../lib/session";
import { copyAuthCookies, NO_STORE } from "../../../lib/security";

export const dynamic = "force-dynamic";
export async function GET(request: Request) {
  try {
    if (!publicRequestAllowed(request, readConfig())) return new Response(null, {status: 403, headers: NO_STORE});
    const result = await lookupSession(request.headers.get("cookie"));
    const response = Response.json(result.session || {error: "Session unavailable"}, {status: result.status, headers: NO_STORE});
    copyAuthCookies(result.cookies, response.headers);
    return response;
  } catch { return new Response(null, {status: 503, headers: NO_STORE}); }
}
