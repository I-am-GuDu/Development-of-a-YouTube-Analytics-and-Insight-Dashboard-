import { createNeonAuth } from "@neondatabase/auth/next/server";
import { readConfig } from "./config";

// Lazy initialization lets builds run without access to production secrets.
export function getAuth() {
  const config = readConfig();
  return createNeonAuth({
    baseUrl: config.neonUrl,
    cookies: {secret: config.cookieSecret, sessionDataTtl: 1, sameSite: "lax"},
    logLevel: "silent"
  });
}
