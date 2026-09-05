/**
 * Citizen Reporting page.
 *
 * Lists recent hazard reports, supports creating a new report, and
 * allows corroboration. All data is fetched from the backend. Form
 * submission also routes through the backend - no client-side
 * validation of backend logic.
 */
import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Seo } from "@/components/Seo";
import { Breadcrumbs } from "@/components/Breadcrumbs";
import { Loading } from "@/components/Loading";
import {
  corroborateHazard,
  createHazard,
  listHazards,
  uploadReportImage,
} from "@/api";

const HAZARD_TYPES = ["accident", "pothole", "flooding", "obstruction", "road_work", "vehicle_breakdown"];
const SEVERITIES = ["low", "medium", "high", "critical"];

export default function CitizenReportingPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    type: "pothole",
    severity: "medium",
    longitude: "",
    latitude: "",
    description: "",
    nearest_landmark: "",
  });
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [formSuccess, setFormSuccess] = useState<string | null>(null);

  const hazards = useQuery({
    queryKey: ["hazards", "active"],
    queryFn: () => listHazards({ status: "active", page: 1, page_size: 30 }),
    refetchInterval: 20_000,
  });

  const create = useMutation({
    mutationFn: async () => {
      let image_ids: string[] = [];
      if (imageFile) {
        const upload = await uploadReportImage(imageFile);
        image_ids = [upload.image_id];
      }
      const lon = parseFloat(form.longitude);
      const lat = parseFloat(form.latitude);
      if (!Number.isFinite(lon) || !Number.isFinite(lat)) {
        throw new Error("Coordinates are not valid numbers.");
      }
      return createHazard({
        type: form.type,
        severity: form.severity,
        location: { type: "Point", coordinates: [lon, lat] },
        description: form.description,
        nearest_landmark: form.nearest_landmark,
        image_ids,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hazards"] });
      setFormSuccess("Report submitted. Operators have been notified.");
      setFormError(null);
      setShowForm(false);
      setImageFile(null);
    },
    onError: (err: any) => {
      setFormError(err?.response?.data?.detail || err?.message || "Submission failed.");
      setFormSuccess(null);
    },
  });

  const corroborate = useMutation({
    mutationFn: (id: string) => corroborateHazard(id, { same_location: true }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["hazards"] });
    },
  });

  return (
    <>
      <Seo
        title="Citizen Reporting"
        description="Report accidents, hazards, and obstructions on the road network."
        path="/citizen-reporting"
      />
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: "Citizen Reporting" }]} />

      <h1>Citizen Reporting</h1>
      <p className="text-aeris-textSecondary mt-2 max-w-2xl text-sm">
        File a hazard report or corroborate an existing one. Operators use the
        corroboration score to decide which hazards to prioritise.
      </p>

      <div className="mt-4">
        <button
          type="button"
          onClick={() => setShowForm((s) => !s)}
          className="aeris-btn aeris-btn-primary"
          aria-expanded={showForm}
          aria-controls="new-report-form"
        >
          {showForm ? "Hide form" : "File a new report"}
        </button>
      </div>

      {showForm ? (
        <form
          id="new-report-form"
          onSubmit={(event) => {
            event.preventDefault();
            create.mutate();
          }}
          className="mt-4 max-w-xl space-y-4"
        >
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="hazard-type" className="block text-xs text-aeris-textMuted mb-1">Type</label>
              <select
                id="hazard-type"
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value })}
                className="aeris-select"
              >
                {HAZARD_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="hazard-severity" className="block text-xs text-aeris-textMuted mb-1">Severity</label>
              <select
                id="hazard-severity"
                value={form.severity}
                onChange={(e) => setForm({ ...form, severity: e.target.value })}
                className="aeris-select"
              >
                {SEVERITIES.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="hazard-lon" className="block text-xs text-aeris-textMuted mb-1">Longitude</label>
              <input
                id="hazard-lon"
                type="number"
                step="any"
                required
                min={-180}
                max={180}
                value={form.longitude}
                onChange={(e) => setForm({ ...form, longitude: e.target.value })}
                className="aeris-input"
              />
            </div>
            <div>
              <label htmlFor="hazard-lat" className="block text-xs text-aeris-textMuted mb-1">Latitude</label>
              <input
                id="hazard-lat"
                type="number"
                step="any"
                required
                min={-90}
                max={90}
                value={form.latitude}
                onChange={(e) => setForm({ ...form, latitude: e.target.value })}
                className="aeris-input"
              />
            </div>
          </div>
          <div>
            <label htmlFor="hazard-desc" className="block text-xs text-aeris-textMuted mb-1">Description</label>
            <textarea
              id="hazard-desc"
              maxLength={1000}
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              className="aeris-textarea"
              rows={3}
            />
          </div>
          <div>
            <label htmlFor="hazard-landmark" className="block text-xs text-aeris-textMuted mb-1">Nearest landmark (optional)</label>
            <input
              id="hazard-landmark"
              type="text"
              maxLength={200}
              value={form.nearest_landmark}
              onChange={(e) => setForm({ ...form, nearest_landmark: e.target.value })}
              className="aeris-input"
            />
          </div>
          <div>
            <label htmlFor="hazard-image" className="block text-xs text-aeris-textMuted mb-1">Photo (optional)</label>
            <input
              id="hazard-image"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              onChange={(e) => setImageFile(e.target.files?.[0] ?? null)}
              className="aeris-input"
            />
            <p className="text-xs text-aeris-textMuted mt-1">JPG, PNG, or WebP. Maximum 5 MB.</p>
          </div>
          <button type="submit" className="aeris-btn aeris-btn-primary" disabled={create.isPending}>
            {create.isPending ? "Submitting" : "Submit report"}
          </button>
          {formError ? (
            <p role="alert" className="text-aeris-danger text-xs">{formError}</p>
          ) : null}
        </form>
      ) : null}

      {formSuccess ? (
        <p role="status" className="aeris-badge aeris-badge-resolved mt-4">
          {formSuccess}
        </p>
      ) : null}

      <section className="mt-8">
        <h2 className="text-sm font-medium text-aeris-textMuted mb-3">Active hazard reports</h2>
        {hazards.isLoading ? <Loading /> : null}
        {hazards.error ? (
          <p role="alert" className="text-aeris-danger text-sm">Unable to load hazard reports.</p>
        ) : null}
        {hazards.data && hazards.data.items.length === 0 ? (
          <p className="text-aeris-textMuted text-sm">No active hazard reports.</p>
        ) : null}
        {hazards.data && hazards.data.items.length > 0 ? (
          <table className="aeris-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Severity</th>
                <th>Location</th>
                <th>Corroboration</th>
                <th>Reported</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {hazards.data.items.map((h) => (
                <tr key={h.id}>
                  <td>{h.type}</td>
                  <td>
                    <span className={`aeris-badge ${h.severity === "critical" ? "aeris-badge-critical" : h.severity === "high" ? "aeris-badge-warning" : "aeris-badge-muted"}`}>
                      {h.severity}
                    </span>
                  </td>
                  <td className="font-mono text-xs">{h.location.coordinates.join(", ")}</td>
                  <td>{(h.corroboration_score * 100).toFixed(0)}%</td>
                  <td>{new Date(h.created_at).toLocaleString()}</td>
                  <td>
                    <button
                      type="button"
                      onClick={() => corroborate.mutate(h.id)}
                      className="aeris-btn"
                      disabled={corroborate.isPending}
                    >
                      Confirm
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
      </section>
    </>
  );
}
