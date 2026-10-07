export type GatewayConfig = {
  origin: string;
  neonUrl: string;
  cookieSecret: string;
  internalSecret: string;
  googleEnabled: boolean;
};

export function readConfig(env: Record<string, string | undefined> = process.env): GatewayConfig {
  const origin = new URL(env.APP_ORIGIN || "");
  const neon = new URL(env.NEON_AUTH_URL || "");
  const local = env.APP_ENV === "development" && origin.protocol === "http:" &&
    origin.hostname === "localhost" && origin.port === "8509";
  if ((!local && (origin.protocol !== "https:" || origin.port)) || origin.username || origin.password ||
      origin.pathname !== "/" || origin.search || origin.hash) {
    throw new Error("APP_ORIGIN must be an HTTPS origin without a path or credentials.");
  }
  if (neon.protocol !== "https:" || !neon.hostname.endsWith(".neon.tech") ||
      !neon.hostname.includes(".neonauth.") || neon.username || neon.password ||
      neon.port || neon.search || neon.hash || !neon.pathname.replace(/\/$/, "").endsWith("/auth")) {
    throw new Error("NEON_AUTH_URL must be the managed Neon HTTPS Auth base URL.");
  }
  const cookieSecret = env.NEON_AUTH_COOKIE_SECRET || "";
  const internalSecret = env.AUTH_INTERNAL_SECRET || "";
  if (cookieSecret.length < 32 || internalSecret.length < 32 || cookieSecret === internalSecret ||
      /[\r\n\0]/.test(cookieSecret + internalSecret)) {
    throw new Error("Two separate auth secrets of at least 32 characters are required.");
  }
  const googleEnabled = env.AUTH_GOOGLE_ENABLED === "true";
  if (googleEnabled && env.AUTH_LINKING_REVIEWED !== "true" &&
      !(local && env.AUTH_LOCAL_TEST_ACCOUNTS_ONLY === "true")) {
    throw new Error("Review managed account linking before enabling Google sign-in.");
  }
  return {
    origin: origin.origin, neonUrl: neon.href.replace(/\/$/, ""),
    cookieSecret, internalSecret, googleEnabled
  };
}

export function publicRequestAllowed(request: Request, config: GatewayConfig, mutation = false): boolean {
  const host = request.headers.get("host");
  const expectedHost = new URL(config.origin).host;
  if (host !== expectedHost) return false;
  const origin = request.headers.get("origin");
  if (origin && origin !== config.origin) return false;
  if (mutation && origin !== config.origin) return false;
  return !["cross-site", "none"].includes(request.headers.get("sec-fetch-site") || "") || !mutation;
}
