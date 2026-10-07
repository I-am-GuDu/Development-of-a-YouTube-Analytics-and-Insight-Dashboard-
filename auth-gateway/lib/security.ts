import { timingSafeEqual } from "node:crypto";

export const SESSION_COOKIE = "__Secure-neon-auth.session_token";
export const NO_STORE = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"};

export function secretMatches(supplied: string | null, expected: string): boolean {
  if (!supplied || !expected) return false;
  const actual = Buffer.from(supplied);
  const desired = Buffer.from(expected);
  return actual.length === desired.length && timingSafeEqual(actual, desired);
}

export function sessionCookie(header: string | null): string | null {
  if (!header || header.length > 16384 || /[\r\n\0]/.test(header)) return null;
  const matching = header.split(";").map(v => v.trim()).filter(v => v.startsWith(`${SESSION_COOKIE}=`));
  if (matching.length !== 1) return null;
  const value = matching[0].slice(SESSION_COOKIE.length + 1);
  return value && value.length <= 4096 && !/\s/.test(value) ? matching[0] : null;
}

export type VerifiedSession = {
  user: {id: string; email: string; display_name: string};
  expires_at: string;
};

export function verifiedSession(data: unknown, now = Date.now()): VerifiedSession | null {
  if (!data || typeof data !== "object") return null;
  const {user, session} = data as Record<string, any>;
  if (!user || !session || typeof user.id !== "string" || !user.id ||
      user.id.length > 255 || session.userId !== user.id ||
      typeof user.email !== "string" || !user.email.includes("@") || user.email.length > 255 ||
      user.emailVerified !== true || user.banned === true || user.isActive === false) return null;
  const expiry = new Date(session.expiresAt).getTime();
  if (!Number.isFinite(expiry) || expiry <= now) return null;
  return {user: {
    id: user.id, email: user.email,
    display_name: typeof user.name === "string" ? user.name.slice(0, 255) : ""
  }, expires_at: new Date(expiry).toISOString()};
}

export function copyAuthCookies(source: Headers, target: Headers): void {
  for (const raw of source.getSetCookie()) {
    if (!raw.startsWith("__Secure-neon-auth.")) continue;
    // Host-only cookies; the SDK keeps signing and OAuth challenge handling.
    const parts = raw.split(";").map(v => v.trim());
    const value = parts.shift()!;
    const attributes = parts.filter(v => !/^(domain|path|secure|httponly|samesite)(=|$)/i.test(v));
    target.append("Set-Cookie", [value, ...attributes, "Path=/", "Secure", "HttpOnly", "SameSite=Lax"].join("; "));
  }
}

export function safeUser(data: unknown) {
  if (!data || typeof data !== "object") return undefined;
  const u = data as Record<string, unknown>;
  return {
    id: typeof u.id === "string" ? u.id.slice(0, 255) : undefined,
    email: typeof u.email === "string" ? u.email.slice(0, 255) : undefined,
    name: typeof u.name === "string" ? u.name.slice(0, 255) : undefined,
    emailVerified: u.emailVerified === true
  };
}
