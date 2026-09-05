/**
 * AERIS route tree.
 *
 * - Routes are lazy-loaded (security check: code-splitting for performance).
 * - Role-protected routes use the RequireRole guard.
 * - Exactly one H1 per page is enforced by each page component.
 * - Each page sets its own title/meta/canonical via the Seo component.
 */
import React, { Suspense } from "react";
import { Route, Routes, Navigate, useLocation, Outlet } from "react-router-dom";
import { RootLayout } from "@/layouts/RootLayout";
import { useAuth } from "@/context/AuthContext";
import type { UserRole } from "@/api/types";
import { Loading } from "@/components/Loading";

const HomePage = React.lazy(() => import("@/pages/HomePage"));
const LoginPage = React.lazy(() => import("@/pages/LoginPage"));
const RegisterPage = React.lazy(() => import("@/pages/RegisterPage"));
const EmergencyHudPage = React.lazy(() => import("@/pages/EmergencyHudPage"));
const TrafficControlPage = React.lazy(() => import("@/pages/TrafficControlPage"));
const CitizenReportingPage = React.lazy(() => import("@/pages/CitizenReportingPage"));
const TermsPage = React.lazy(() => import("@/pages/TermsPage"));
const PrivacyPage = React.lazy(() => import("@/pages/PrivacyPage"));
const NotFoundPage = React.lazy(() => import("@/pages/NotFoundPage"));

function RequireRole({ roles, children }: { roles: UserRole[]; children: React.ReactNode }) {
  const { isAuthenticated, hasRole, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) return <Loading />;
  if (!isAuthenticated) {
    const redirect = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?redirect=${redirect}`} replace />;
  }
  if (roles.length > 0 && !hasRole(...roles)) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

function PublicOnly({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <Loading />;
  if (isAuthenticated) return <Navigate to="/" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      <Route element={<RootLayout />}>
        <Route
          index
          element={
            <Suspense fallback={<Loading />}>
              <HomePage />
            </Suspense>
          }
        />
        <Route
          path="login"
          element={
            <PublicOnly>
              <Suspense fallback={<Loading />}>
                <LoginPage />
              </Suspense>
            </PublicOnly>
          }
        />
        <Route
          path="register"
          element={
            <PublicOnly>
              <Suspense fallback={<Loading />}>
                <RegisterPage />
              </Suspense>
            </PublicOnly>
          }
        />
        <Route
          path="emergency-hud"
          element={
            <RequireRole roles={["admin", "driver"]}>
              <Suspense fallback={<Loading />}>
                <EmergencyHudPage />
              </Suspense>
            </RequireRole>
          }
        />
        <Route
          path="traffic-control"
          element={
            <RequireRole roles={["admin"]}>
              <Suspense fallback={<Loading />}>
                <TrafficControlPage />
              </Suspense>
            </RequireRole>
          }
        />
        <Route
          path="citizen-reporting"
          element={
            <RequireRole roles={["admin", "citizen", "driver"]}>
              <Suspense fallback={<Loading />}>
                <CitizenReportingPage />
              </Suspense>
            </RequireRole>
          }
        />
        <Route
          path="terms"
          element={
            <Suspense fallback={<Loading />}>
              <TermsPage />
            </Suspense>
          }
        />
        <Route
          path="privacy"
          element={
            <Suspense fallback={<Loading />}>
              <PrivacyPage />
            </Suspense>
          }
        />
        <Route
          path="*"
          element={
            <Suspense fallback={<Loading />}>
              <NotFoundPage />
            </Suspense>
          }
        />
      </Route>
    </Routes>
  );
}

export default function App() {
  return <AppRoutes />;
}

export { Outlet };
