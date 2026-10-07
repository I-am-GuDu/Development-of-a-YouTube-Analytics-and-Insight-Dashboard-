"use client";

import { useEffect, useState, type FormEvent } from "react";
import { authClient } from "../lib/client";
import { Scene } from "./scene";

export function AuthForm({view, googleEnabled}: {view: string; googleEnabled: boolean}) {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [light, setLight] = useState(false);
  const [resetToken, setResetToken] = useState("");
  const [email, setEmail] = useState("");
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (view === "reset-password") {
      setResetToken(params.get("token") || "");
      window.history.replaceState(null, "", window.location.pathname);
    }
    const error = params.get("error");
    if (view === "sign-in" && error) {
      setMessage(["google_canceled", "access_denied"].includes(error)
        ? "Google sign-in was canceled. You can try again."
        : "Google sign-in could not be completed. Please try again.");
      window.history.replaceState(null, "", window.location.pathname);
    }
  }, [view]);

  async function google() {
    setBusy(true); setMessage("");
    try {
      const {error} = await authClient.signIn.social({
        provider: "google",
        callbackURL: "/auth/callback"
      });
      if (error) {
        console.error("Social sign in error:", error);
        setMessage("Error: " + (error.message || "Could not start Google sign-in"));
      }
    } catch { setMessage("Google sign-in is temporarily unavailable."); }
    finally { setBusy(false); }
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setBusy(true); setMessage("");
    const form = new FormData(event.currentTarget);
    const formEmail = String(form.get("email") || "").trim();
    const password = String(form.get("password") || "");
    setEmail(formEmail);
    try {
      if (view === "sign-in") {
        const {error} = await authClient.signIn.email({email: formEmail, password});
        if (error) { setMessage(error.status === 429 ? "Too many attempts. Please wait a minute and try again." : error.status >= 500 ? "Sign-in is temporarily unavailable. Please try again." : "Check your email and password, or verify your email."); return; }
        const response = await fetch("/api/session", {cache: "no-store"});
        if (response.ok) { window.location.assign("/"); return; }
        setMessage(response.status === 401 ? "Verify your email before signing in." : "Sign-in is temporarily unavailable. Please try again.");
      } else if (view === "sign-up") {
        if (password !== form.get("confirm")) { setMessage("Passwords do not match."); return; }
        const {error} = await authClient.signUp.email({email: formEmail, password, name: String(form.get("name") || "")});
        if (error) { setMessage("Account creation is temporarily unavailable. Please try again."); return; }
        const sent = await authClient.emailOtp.sendVerificationOtp({email: formEmail, type: "email-verification"});
        if (sent.error) { setMessage("The verification email could not be requested. Try Send another code on the verification page."); return; }
        setMessage("If the address can be registered, a verification code will be sent. Enter it on the verification page.");
      } else if (view === "verify-email") {
        const {error} = await authClient.emailOtp.verifyEmail({email: formEmail, otp: String(form.get("otp") || "")});
        setMessage(error ? "Check your code and try again." : "Email verified. You can sign in now.");
      } else if (view === "forgot-password") {
        const {error} = await authClient.requestPasswordReset({email: formEmail, redirectTo: "/auth/reset-password"});
        setMessage(error ? "The reset email could not be requested. Please try again shortly." : "If this account is eligible, a reset email will be sent.");
      } else if (view === "reset-password") {
        if (password !== form.get("confirm")) { setMessage("Passwords do not match."); return; }
        if (!resetToken) { setMessage("Open the password reset link from your email again."); return; }
        const {error} = await authClient.resetPassword({newPassword: password, token: resetToken});
        setMessage(error ? "The link may have expired. Request a new reset email." : "Password updated. You can sign in now.");
      } else if (view === "sign-out") {
        const {error} = await authClient.signOut();
        if (error) setMessage("Sign-out could not complete. Please try again.");
        else window.location.replace("/auth/sign-in");
      }
    } catch { setMessage("Sign-in is temporarily unavailable. Please try again."); }
    finally { setBusy(false); }
  }

  async function resend() {
    setBusy(true);
    try { const {error} = await authClient.emailOtp.sendVerificationOtp({email, type: "email-verification"});
      setMessage(error ? "The code could not be requested. Please try again shortly." : "If the account is eligible, a new verification code will be sent.");
    } catch { setMessage("Please try again in a moment."); }
    finally { setBusy(false); }
  }

  const headings: Record<string, string> = {
    "sign-in": "Welcome", "sign-up": "Create your account", "verify-email": "Verify your email",
    "forgot-password": "Reset your password", "reset-password": "Choose a new password", "sign-out": "Sign out"
  };
  const labels: Record<string, string> = {
    "sign-in": "Sign in", "sign-up": "Create account", "verify-email": "Verify email",
    "forgot-password": "Send reset email", "reset-password": "Save password", "sign-out": "Sign out"
  };
  const needsEmail = ["sign-in", "sign-up", "verify-email", "forgot-password"].includes(view);
  const needsPassword = ["sign-in", "sign-up", "reset-password"].includes(view);
  return <main className={light ? "auth-page light" : "auth-page"}>
    <section className="auth-panel">
      <button className="theme-toggle" aria-label="Change color theme" onClick={() => setLight(!light)}>{light ? "☀" : "☾"}</button>
      <Scene/>
      <div className="form-side">
        <div className="sr-logo" aria-hidden="true">▶</div>
        <h2>{headings[view]}</h2>
        <p className="form-sub">{view === "sign-in" ? "Sign in to your analytics dashboard" : "YouTube Analytics"}</p>
        {message && <p className="form-message" role="status" aria-live="polite">{message}</p>}
        {view === "sign-in" && <>
          <button className="google-button" onClick={google} disabled={busy || !googleEnabled}>Continue with Google</button>
          {!googleEnabled && <p className="hint">Google sign-in is coming soon.</p>}
          <div className="divider"><span>or</span></div>
        </>}
        <form onSubmit={submit}>
          {view === "sign-up" && <label>Display name<input name="name" autoComplete="name" maxLength={100} required/></label>}
          {needsEmail && <label>Email<input name="email" type="email" autoComplete="email" maxLength={255} required onChange={e => setEmail(e.target.value)}/></label>}
          {needsPassword && <div className="field"><label htmlFor="auth-password">Password</label><div className="password-input">
            <input id="auth-password" name="password" type={showPassword ? "text" : "password"} autoComplete={view === "sign-in" ? "current-password" : "new-password"} minLength={view === "sign-in" ? 1 : 10} maxLength={128} required/>
            <button type="button" aria-label={showPassword ? "Hide password" : "Show password"} onClick={() => setShowPassword(!showPassword)}>◉</button>
          </div></div>}
          {["sign-up", "reset-password"].includes(view) && <label>Confirm password<input name="confirm" type="password" autoComplete="new-password" minLength={10} maxLength={128} required/></label>}
          {view === "verify-email" && <label>Verification code<input name="otp" inputMode="numeric" autoComplete="one-time-code" pattern="[0-9]{6,8}" maxLength={8} required/></label>}
          {view === "sign-out" && <p>Sign out of this browser?</p>}
          <button className="primary" type="submit" disabled={busy}>{busy ? "Please wait…" : labels[view]}</button>
        </form>
        {view === "verify-email" && <button className="text-button" onClick={resend} disabled={busy || !email}>Send another code</button>}
        {view === "sign-in" && <div className="secondary-links"><a href="/auth/forgot-password">Forgot password?</a><a href="/auth/verify-email">Verify email</a></div>}
        <div className="divider"><span>{view === "sign-in" ? "new here" : ""}</span></div>
        {view === "sign-in" ? <a className="switch-link" href="/auth/sign-up">Create a free account — Sign up</a> : <a className="switch-link" href="/auth/sign-in">Back to sign in</a>}
        {view === "sign-up" && <a className="switch-link" href="/auth/verify-email">Enter verification code</a>}
      </div>
    </section>
  </main>;
}
