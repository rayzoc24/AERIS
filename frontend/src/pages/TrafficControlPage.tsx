/**
 * Traffic Control Dashboard.
 *
 * Shows active green corridors, current signal preemptions, and
 * watchdog controls. Admin-only. All data is fetched from the signals
 * and dispatch APIs.
 */
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { Seo } from "@/components/Seo";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Loading } from "@/components/Loading";
import { listActivePreemptions, watchdogRevert, listTrips } from "@/api";

export default function TrafficControlPage() {
  const [watchdogSignalId, setWatchdogSignalId] = useState("");
  const [watchdogReason, setWatchdogReason] = useState("");
  const queryClient = useQueryClient();

  const preemptions = useQuery({
    queryKey: ["preemptions", "active"],
    queryFn: listActivePreemptions,
    refetchInterval: 5_000,
  });

  const activeTrips = useQuery({
    queryKey: ["trips", "active"],
    queryFn: () => listTrips({ status: "active" }),
    refetchInterval: 10_000,
  });

  const revert = useMutation({
    mutationFn: (payload: { signal_id: string; reason: string }) =>
      watchdogRevert(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preemptions"] });
      queryClient.invalidateQueries({ queryKey: ["trips"] });
      setWatchdogSignalId("");
      setWatchdogReason("");
    },
  });

  return (
    <>
      <Seo
        title="Traffic Control Dashboard"
        description="Active green corridors, live signal preemptions, and watchdog controls for traffic operators."
        path="/traffic-control"
      />
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: "Traffic Control Dashboard" }]} />

      <h1>Traffic Control Dashboard</h1>
      <p className="text-aeris-textSecondary mt-2 max-w-2xl text-sm">
        Live view of active signal preemptions and green corridors. Use the
        watchdog control to revert a preemption when the upstream GPS feed is
        interrupted.
      </p>

      <section className="mt-6">
        <h2 className="text-sm font-medium text-aeris-textMuted mb-3">Active preemptions</h2>
        {preemptions.isLoading ? <Loading /> : null}
        {preemptions.error ? (
          <p role="alert" className="text-aeris-danger text-sm">
            Unable to load preemption list.
          </p>
        ) : null}
        {preemptions.data && preemptions.data.length === 0 ? (
          <p className="text-aeris-textMuted text-sm">No active preemptions.</p>
        ) : null}
        {preemptions.data && preemptions.data.length > 0 ? (
          <table className="aeris-table">
            <thead>
              <tr>
                <th>Signal</th>
                <th>State</th>
                <th>Trip</th>
                <th>Triggered</th>
                <th>Watchdog</th>
              </tr>
            </thead>
            <tbody>
              {preemptions.data.map((p) => (
                <tr key={p.id}>
                  <td className="font-mono text-xs">{p.signal_id}</td>
                  <td>
                    <span className={`aeris-badge ${p.state === "green" ? "aeris-badge-active" : "aeris-badge-critical"}`}>
                      {p.state}
                    </span>
                  </td>
                  <td className="font-mono text-xs">{p.trip_id.slice(-8)}</td>
                  <td>{new Date(p.triggered_at).toLocaleTimeString()}</td>
                  <td>{p.watchdog_active ? "Reverted" : "Armed"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </section>

      <section className="mt-8">
        <h2 className="text-sm font-medium text-aeris-textMuted mb-3">Active trips</h2>
        {activeTrips.isLoading ? <Loading /> : null}
        {activeTrips.data && activeTrips.data.items.length > 0 ? (
          <table className="aeris-table">
            <thead>
              <tr>
                <th>Trip</th>
                <th>Vehicle</th>
                <th>Priority</th>
                <th>Green corridor</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {activeTrips.data.items.map((t) => (
                <tr key={t.id}>
                  <td className="font-mono text-xs">{t.id.slice(-8)}</td>
                  <td className="font-mono text-xs">{t.vehicle_id.slice(-8)}</td>
                  <td>{t.priority}</td>
                  <td>{t.green_corridor ? `${t.green_corridor.length} signals` : "Not configured"}</td>
                  <td>{new Date(t.started_at).toLocaleTimeString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-aeris-textMuted text-sm">No active trips.</p>
        )}
      </section>

      <section className="mt-8">
        <h2 className="text-sm font-medium text-aeris-textMuted mb-3">Watchdog override</h2>
        <p className="text-xs text-aeris-textMuted mb-3">
          Use this control when the upstream GPS feed for a signal is lost. The
          preemption is reverted to normal traffic signalling.
        </p>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (!watchdogSignalId || !watchdogReason) return;
            revert.mutate({ signal_id: watchdogSignalId, reason: watchdogReason });
          }}
          className="max-w-md space-y-3"
        >
          <div>
            <label htmlFor="watchdog-signal" className="block text-xs text-aeris-textMuted mb-1">
              Signal ID
            </label>
            <input
              id="watchdog-signal"
              type="text"
              required
              minLength={1}
              maxLength={64}
              value={watchdogSignalId}
              onChange={(e) => setWatchdogSignalId(e.target.value)}
              className="aeris-input"
            />
          </div>
          <div>
            <label htmlFor="watchdog-reason" className="block text-xs text-aeris-textMuted mb-1">
              Reason
            </label>
            <input
              id="watchdog-reason"
              type="text"
              required
              minLength={1}
              maxLength={200}
              value={watchdogReason}
              onChange={(e) => setWatchdogReason(e.target.value)}
              className="aeris-input"
            />
          </div>
          <button
            type="submit"
            className="aeris-btn aeris-btn-danger"
            disabled={revert.isPending}
          >
            {revert.isPending ? "Reverting" : "Trigger watchdog revert"}
          </button>
          {revert.isError ? (
            <p role="alert" className="text-aeris-danger text-xs">
              Revert failed. The backend reported an error.
            </p>
          ) : null}
          {revert.isSuccess ? (
            <p role="status" className="text-aeris-success text-xs">
              Reverted. The signal has returned to normal operation.
            </p>
          ) : null}
        </form>
      </section>
    </>
  );
}
