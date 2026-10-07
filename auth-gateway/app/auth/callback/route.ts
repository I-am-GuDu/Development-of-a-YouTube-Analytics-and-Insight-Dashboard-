import { readConfig, publicRequestAllowed } from "../../../lib/config";
import { lookupSession } from "../../../lib/session";
import { copyAuthCookies, NO_STORE } from "../../../lib/security";

export async function GET(request: Request) {
  const config = readConfig();
  if (!publicRequestAllowed(request, config)) return new Response(null, {status: 403, headers: NO_STORE});
  const error = new URL(request.url).searchParams.get("error");
  if (error) {
    const code = ["access_denied", "google_canceled"].includes(error) ? "google_canceled" : "google_failed";
    return new Response(null, {status: 303, headers: {...NO_STORE,
      Location: config.origin + "/auth/sign-in?error=" + code}});
  }
  const result = await lookupSession(request.headers.get("cookie"));
  const destination = result.session ? "/" : "/auth/sign-in";
  const response = new Response(null, {status: 303, headers: {...NO_STORE, Location: config.origin + destination}});
  copyAuthCookies(result.cookies, response.headers);
  return response;
}
