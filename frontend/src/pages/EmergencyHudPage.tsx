/**
 * Emergency Vehicle HUD.
 *
 * Live ambulance telemetry, route, and signal preemption status. All
 * data is fetched via the dispatch and signals APIs. No hardcoded
 * positions or ETA values.
 *
 * Vehicle selection is the only piece of UI state. Selecting a vehicle
 * triggers trip + preemption queries.
 */
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { Seo } from "@/components/Seo";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Loading } from "@/components/Loading";
import { getTrip, listTripPreemptions, listTrips, listVehicles } from "@/api";

const STATUSES_WITH_BADGE: Record<string, string> = {
  active: "aeris-badge-active",
  completed: "aeris-badge-resolved",
  pending: "aeris-badge-muted",
  cancelled: "aeris-badge-critical",
};

export default function EmergencyHudPage() {
  const [selectedTripId, setSelectedTripId] = useState<string | null>(null);

  const trips = useQuery({
    queryKey: ["trips", "active"],
    queryFn: () => listTrips({ status: "active" }),
    refetchInterval: 10_000,
  });

  const vehicles = useQuery({
    queryKey: ["vehicles", "all"],
    queryFn: () => listVehicles(),
    refetchInterval: 15_000,
  });

  const trip = useQuery({
    queryKey: ["trip", selectedTripId],
    queryFn: () => getTrip(selectedTripId as string),
    enabled: !!selectedTripId,
  });

  const preemptions = useQuery({
    queryKey: ["preemptions", selectedTripId],
    queryFn: () => listTripPreemptions(selectedTripId as string),
    enabled: !!selectedTripId,
  });

  return (
    <>
      <Seo
        title="Emergency Vehicle HUD"
        description="Live ambulance telemetry, route, and signal preemption status for drivers."
        path="/emergency-hud"
      />
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: "Emergency Vehicle HUD" }]} />

      <h1>Emergency Vehicle HUD</h1>
      <p className="text-aeris-textSecondary mt-2 max-w-2xl text-sm">
        Select an active trip to view vehicle telemetry, route details, and the
        green corridor preemption sequence.
      </p>

      <section className="mt-6">
        <h2 className="text-sm font-medium text-aeris-textMuted mb-3">Active trips</h2>
        {trips.isLoading ? <Loading /> : null}
        {trips.error ? (
          <p role="alert" className="text-aeris-danger text-sm">
            Unable to load active trips.
          </p>
        ) : null}
        {trips.data && trips.data.items.length === 0 ? (
          <p className="text-aeris-textMuted text-sm">No active trips at this moment.</p>
        ) : null}
        {trips.data && trips.data.items.length > 0 ? (
          <table className="aeris-table">
            <thead>
              <tr>
                <th>Trip</th>
                <th>Vehicle</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Started</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {trips.data.items.map((t) => (
                <tr key={t.id}>
                  <td className="font-mono text-xs">{t.id.slice(-8)}</td>
                  <td className="font-mono text-xs">{t.vehicle_id.slice(-8)}</td>
                  <td>{t.priority}</td>
                  <td>
                    <span className={`aeris-badge ${STATUSES_WITH_BADGE[t.status] ?? "aeris-badge-muted"}`}>
                      {t.status}
                    </span>
                  </td>
                  <td>{new Date(t.started_at).toLocaleString()}</td>
                  <td>
                    <button
                      type="button"
                      className="aeris-btn"
                      onClick={() => setSelectedTripId(t.id)}
                      data-testid={`select-trip-${t.id}`}
                    >
                      View
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </section>

      {selectedTripId ? (
        <section aria-labelledby="trip-detail-heading" className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-4">
          <h2 id="trip-detail-heading" className="sr-only">Trip detail</h2>
          <div className="aeris-panel p-4">
            <h3 className="text-sm font-medium mb-3">Trip summary</h3>
            {trip.isLoading ? <Loading /> : trip.data ? (
              <dl className="grid grid-cols-2 gap-2 text-sm">
                <dt className="text-aeris-textMuted">Trip ID</dt>
                <dd className="font-mono text-xs break-all">{trip.data.id}</dd>
                <dt className="text-aeris-textMuted">Vehicle</dt>
                <dd className="font-mono text-xs break-all">{trip.data.vehicle_id}</dd>
                <dt className="text-aeris-textMuted">Origin (lon, lat)</dt>
                <dd className="font-mono text-xs">{trip.data.origin.coordinates.join(", ")}</dd>
                <dt className="text-aeris-textMuted">Destination (lon, lat)</dt>
                <dd className="font-mono text-xs">{trip.data.destination.coordinates.join(", ")}</dd>
                <dt className="text-aeris-textMuted">Priority</dt>
                <dd>{trip.data.priority}</dd>
                <dt className="text-aeris-textMuted">ETA</dt>
                <dd>{trip.data.eta_seconds ? `${Math.round(trip.data.eta_seconds / 60)} min` : "Pending"}</dd>
                <dt className="text-aeris-textMuted">Distance</dt>
                <dd>{trip.data.distance_metres ? `${(trip.data.distance_metres / 1000).toFixed(2)} km` : "Pending"}</dd>
              </dl>
            ) : (
              <p className="text-aeris-danger text-sm">Trip not found.</p>
            )}
          </div>

          <div className="aeris-panel p-4">
            <h3 className="text-sm font-medium mb-3">Signal preemption sequence</h3>
            {preemptions.isLoading ? <Loading /> : preemptions.data && preemptions.data.length > 0 ? (
              <ol className="space-y-2 text-sm">
                {preemptions.data.map((p) => (
                  <li key={p.id} className="border border-aeris-border p-2 flex items-center justify-between">
                    <span className="font-mono text-xs">{p.signal_id}</span>
                    <span className={`aeris-badge ${p.state === "reverted" ? "aeris-badge-critical" : "aeris-badge-active"}`}>
                      {p.state}
                    </span>
                    <span className="text-xs text-aeris-textMuted">
                      {new Date(p.triggered_at).toLocaleTimeString()}
                    </span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="text-aeris-textMuted text-sm">No preemptions issued for this trip.</p>
            )}
          </div>
        </section>
      ) : null}

      <section className="mt-8">
        <h2 className="text-sm font-medium text-aeris-textMuted mb-3">Vehicles</h2>
        {vehicles.isLoading ? <Loading /> : null}
        {vehicles.data && vehicles.data.length > 0 ? (
          <table className="aeris-table">
            <thead>
              <tr>
                <th>Registration</th>
                <th>Type</th>
                <th>Status</th>
                <th>Last update</th>
              </tr>
            </thead>
            <tbody>
              {vehicles.data.map((v) => (
                <tr key={v.id}>
                  <td className="font-mono">{v.registration_number}</td>
                  <td>{v.type}</td>
                  <td>{v.status}</td>
                  <td>{new Date(v.updated_at).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : vehicles.data && vehicles.data.length === 0 ? (
          <p className="text-aeris-textMuted text-sm">No vehicles registered.</p>
        ) : null}
      </section>
    </>
  );
}
