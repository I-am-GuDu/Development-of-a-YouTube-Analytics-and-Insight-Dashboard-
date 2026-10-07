import type { GatewayConfig } from "./config";

const GET_PATHS = new Set(["get-session", "verify-email"]);
const POST_PATHS = new Set([
  "sign-in/email", "sign-in/social", "sign-up/email", "sign-out",
  "send-verification-email", "request-password-reset", "reset-password",
  "email-otp/send-verification-otp", "email-otp/verify-email"
]);

export function allowedAuthPath(path: string, method: string): boolean {
  return method === "GET" ? GET_PATHS.has(path) : method === "POST" && POST_PATHS.has(path);
}

export function authPayload(path: string, body: Record<string, unknown>, config: GatewayConfig): Record<string, unknown> | null {
  const email = typeof body.email === "string" ? body.email.trim() : "";
  const password = typeof body.password === "string" ? body.password : "";
  const validEmail = email.length <= 255 && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  const callbackURL = config.origin + "/auth/sign-in";
  switch (path) {
    case "sign-in/social":
      return config.googleEnabled && body.provider === "google" ? {
        provider: "google", callbackURL: config.origin + "/auth/callback",
        newUserCallbackURL: config.origin + "/auth/callback"
      } : null;
    case "sign-in/email":
      return validEmail && password.length > 0 && password.length <= 128 ? {email, password, rememberMe: false} : null;
    case "sign-up/email":
      return validEmail && password.length >= 10 && password.length <= 128 &&
        typeof body.name === "string" && body.name.trim().length > 0 && body.name.length <= 100 ?
        {email, password, name: body.name.trim(), callbackURL} : null;
    case "send-verification-email":
      return validEmail ? {email, callbackURL} : null;
    case "request-password-reset":
      return validEmail ? {email, redirectTo: config.origin + "/auth/reset-password"} : null;
    case "reset-password":
      return typeof body.newPassword === "string" && body.newPassword.length >= 10 && body.newPassword.length <= 128 &&
        typeof body.token === "string" && body.token.length > 0 && body.token.length <= 2048 ?
        {newPassword: body.newPassword, token: body.token} : null;
    case "email-otp/send-verification-otp":
      return validEmail ? {email, type: "email-verification"} : null;
    case "email-otp/verify-email":
      return validEmail && typeof body.otp === "string" && /^\d{6,8}$/.test(body.otp) ? {email, otp: body.otp} : null;
    case "sign-out": return {};
    default: return null;
  }
}
