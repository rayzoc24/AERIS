/**
 * Registration page. The role selector is restricted to citizen and driver.
 * Admin accounts are created server-side only.
 */
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { Seo } from "@/components/Seo";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { useAuth } from "@/context/AuthContext";
import type { RegisterPayload } from "@/api";

/** Mirror the backend UserCreate validator so we surface errors before a round-trip. */
function validatePassword(pw: string): string | null {
  if (pw.length < 10) return "Password must be at least 10 characters.";
  if (pw.length > 128) return "Password must be at most 128 characters.";
  if (!/[A-Z]/.test(pw)) return "Password must contain at least one uppercase letter.";
  if (!/[a-z]/.test(pw)) return "Password must contain at least one lowercase letter.";
  if (!/[0-9]/.test(pw)) return "Password must contain at least one digit.";
  if (!/[!@#$%^&*()\-_=+[\]{};:,.?]/.test(pw))
    return "Password must contain at least one special character (!@#$%^&*…).";
  return null;
}

export default function RegisterPage() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState<RegisterPayload>({
    email: "",
    name: "",
    role: "citizen",
    password: "",
  });
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);

    const pwError = validatePassword(form.password);
    if (pwError) {
      setError(pwError);
      return;
    }

    setSubmitting(true);
    try {
      await register(form);
      navigate("/", { replace: true });
    } catch (err: any) {
      // Show the first validation message from a 422 array, or the plain detail string.
      const detail = err?.response?.data?.detail;
      if (Array.isArray(detail) && detail.length > 0) {
        setError(detail[0]?.msg ?? "Registration failed.");
      } else {
        setError(typeof detail === "string" ? detail : "Registration failed.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <Seo
        title="Create account"
        description="Create a new AERIS account as a citizen or driver."
        path="/register"
        noIndex
      />
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: "Create account" }]} />

      <h1>Create an AERIS account</h1>
      <p className="text-aeris-textSecondary mt-2 max-w-md text-sm">
        Citizen accounts can file hazard reports. Driver accounts can be assigned
        to emergency vehicles. Admin accounts are provisioned by the system
        administrator and cannot self-register.
      </p>

      {error ? (
        <p role="alert" className="aeris-badge aeris-badge-critical mt-4">
          {error}
        </p>
      ) : null}

      <form onSubmit={handleSubmit} className="mt-6 max-w-md space-y-4" autoComplete="on">
        <div>
          <label htmlFor="name" className="block text-xs text-aeris-textMuted mb-1">
            Full name
          </label>
          <input
            id="name"
            type="text"
            required
            minLength={1}
            maxLength={120}
            autoComplete="name"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="aeris-input"
          />
        </div>
        <div>
          <label htmlFor="email-register" className="block text-xs text-aeris-textMuted mb-1">
            Email address
          </label>
          <input
            id="email-register"
            type="email"
            required
            autoComplete="email"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="aeris-input"
          />
        </div>
        <div>
          <label htmlFor="role" className="block text-xs text-aeris-textMuted mb-1">
            Account type
          </label>
          <select
            id="role"
            value={form.role}
            onChange={(e) => setForm({ ...form, role: e.target.value as RegisterPayload["role"] })}
            className="aeris-select"
          >
            <option value="citizen">Citizen (file hazard reports)</option>
            <option value="driver">Driver (assigned to emergency vehicles)</option>
          </select>
        </div>
        <div>
          <label htmlFor="password-register" className="block text-xs text-aeris-textMuted mb-1">
            Password
          </label>
          <input
            id="password-register"
            type="password"
            required
            minLength={10}
            maxLength={128}
            autoComplete="new-password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            className="aeris-input"
          />
          <p className="text-xs text-aeris-textMuted mt-1">
            At least 10 characters with one uppercase, one lowercase, one digit, and one special character.
          </p>
        </div>
        <button
          type="submit"
          className="aeris-btn aeris-btn-primary w-full"
          disabled={submitting}
        >
          {submitting ? "Creating account…" : "Create account"}
        </button>
        <p className="text-xs text-aeris-textMuted text-center">
          Already have an account?{" "}
          <Link to="/login" className="underline">
            Sign in
          </Link>
        </p>
      </form>
    </>
  );
}
