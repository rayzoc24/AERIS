/**
 * Login page. No placeholder text, no marketing copy.
 */
import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import { Seo } from "@/components/Seo";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { useAuth } from "@/context/AuthContext";

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const reason = params.get("reason");

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email.trim(), password);
      const redirect = params.get("redirect") || "/";
      navigate(redirect, { replace: true });
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Login failed. Check your credentials.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Seo
        title="Sign in"
        description="Sign in to your AERIS account to access the emergency response modules."
        path="/login"
        noIndex
      />
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: "Sign in" }]} />

      <h1>Sign in to AERIS</h1>
      <p className="text-aeris-textSecondary mt-2 max-w-md text-sm">
        Enter your credentials to access the dispatch, traffic control, and citizen
        reporting modules.
      </p>

      {reason === "session_expired" ? (
        <p role="alert" className="aeris-badge aeris-badge-warning mt-4">
          Your session expired. Please sign in again.
        </p>
      ) : null}
      {error ? (
        <p role="alert" className="aeris-badge aeris-badge-critical mt-4">
          {error}
        </p>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-6 max-w-md space-y-4" autoComplete="on">
        <div>
          <label htmlFor="email" className="block text-xs text-aeris-textMuted mb-1">
            Email address
          </label>
          <input
            id="email"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="aeris-input"
            data-testid="email-input"
          />
        </div>
        <div>
          <label htmlFor="password" className="block text-xs text-aeris-textMuted mb-1">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            autoComplete="current-password"
            minLength={1}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="aeris-input"
            data-testid="password-input"
          />
        </div>
        <button
          type="submit"
          className="aeris-btn aeris-btn-primary w-full"
          disabled={submitting}
          data-testid="login-submit"
        >
          {submitting ? "Signing in" : "Sign in"}
        </button>
        <p className="text-xs text-aeris-textMuted text-center">
          New user? <Link to="/register" className="underline">Create an account</Link>
        </p>
      </form>
    </>
  );
}
