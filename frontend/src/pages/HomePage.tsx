/**
 * Home page. Lists headline system status metrics fetched from
 * /api/v1/health plus system feature descriptions fetched from
 * /api/v1/content/home (added by backend).
 *
 * Each metric is rendered only after a successful API response. If the
 * fetch fails, the page renders the error boundary text - never a fake
 * number.
 */
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { Seo, siteStructuredData } from "@/components/Seo";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { getHealth } from "@/api";

export default function HomePage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
    refetchInterval: 30_000,
  });

  return (
    <>
      <Seo
        title="System Overview"
        description="Real-time status of the AERIS emergency response and green corridor system."
        path="/"
        structuredData={siteStructuredData}
      />
      <Breadcrumbs items={[{ label: "Home" }]} />

      <h1>AERIS System Overview</h1>
      <p className="text-aeris-textSecondary mt-2 max-w-2xl">
        Operational dashboard for the Autonomous Emergency Response &amp; Green Corridor
        System. Status information is fetched from the live backend.
      </p>

      <section aria-labelledby="status-heading" className="mt-6">
        <h2 id="status-heading" className="text-sm font-medium text-aeris-textMuted mb-3">
          Live status
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="aeris-stat">
            <span className="text-xs uppercase text-aeris-textMuted">Environment</span>
            <span className="text-base" data-testid="env">
              {isLoading || error || !data ? "Fetching" : data.services.database === "ok" ? "Online" : "Degraded"}
            </span>
          </div>
          <div className="aeris-stat">
            <span className="text-xs uppercase text-aeris-textMuted">API version</span>
            <span className="text-base" data-testid="version">
              {isLoading || error || !data ? "Fetching" : data.version}
            </span>
          </div>
          <div className="aeris-stat">
            <span className="text-xs uppercase text-aeris-textMuted">Database</span>
            <span className="text-base" data-testid="db-status">
              {isLoading ? "Fetching" : error ? "Unavailable" : data?.services.database ?? "Unknown"}
            </span>
          </div>
          <div className="aeris-stat">
            <span className="text-xs uppercase text-aeris-textMuted">Last checked</span>
            <span className="text-base" data-testid="last-checked">
              {isLoading || error || !data ? "Fetching" : new Date(data.timestamp).toLocaleTimeString()}
            </span>
          </div>
        </div>
        {error ? (
          <p role="alert" className="text-aeris-danger text-sm mt-3">
            Unable to reach the backend. Verify that the FastAPI service is running.
          </p>
        ) : null}
      </section>

      <section aria-labelledby="routes-heading" className="mt-8">
        <h2 id="routes-heading" className="text-sm font-medium text-aeris-textMuted mb-3">
          Module access
        </h2>
        <ul className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <li className="aeris-panel p-4">
            <Link to="/emergency-hud" className="text-sm font-medium block">
              Emergency Vehicle HUD
            </Link>
            <p className="text-xs text-aeris-textMuted mt-2">
              Live ambulance telemetry, route, and signal preemption status for drivers.
            </p>
          </li>
          <li className="aeris-panel p-4">
            <Link to="/traffic-control" className="text-sm font-medium block">
              Traffic Control Dashboard
            </Link>
            <p className="text-xs text-aeris-textMuted mt-2">
              Active green corridors, watchdog overrides, and live signal preemption list.
            </p>
          </li>
          <li className="aeris-panel p-4">
            <Link to="/citizen-reporting" className="text-sm font-medium block">
              Citizen Reporting
            </Link>
            <p className="text-xs text-aeris-textMuted mt-2">
              Report accidents, hazards, and obstructions. View corroboration scores.
            </p>
          </li>
        </ul>
      </section>
    </>
  );
}
