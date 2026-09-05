/**
 * Typed API surface. Each function maps to a backend route.
 * Components MUST import from here. They MUST NOT call axios directly.
 */
import client from "./client";
import type {
  HazardOut,
  HealthStatus,
  PaginatedResponse,
  RouteRiskAnalysis,
  SegmentScore,
  SignalPreemptionOut,
  TokenBundle,
  TripOut,
  UserOut,
  VehicleOut,
} from "./types";

// --- Health ---------------------------------------------------------------
export async function getHealth(): Promise<HealthStatus> {
  const res = await client.get<HealthStatus>("/health");
  return res.data;
}

// --- Auth -----------------------------------------------------------------
export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  name: string;
  /** Admin accounts cannot self-register — restricted to citizen and driver. */
  role: "citizen" | "driver";
  password: string;
}

export async function login(payload: LoginPayload): Promise<TokenBundle> {
  const res = await client.post<TokenBundle>("/auth/login", payload);
  return res.data;
}

export async function register(payload: RegisterPayload): Promise<TokenBundle> {
  const res = await client.post<TokenBundle>("/auth/register", payload);
  return res.data;
}

export async function logout(): Promise<void> {
  await client.post("/auth/logout");
}

export async function refreshCsrf(): Promise<{ csrf_token: string }> {
  const res = await client.get<{ csrf_token: string }>("/security/csrf-token");
  return res.data;
}

// --- Trips ----------------------------------------------------------------
export async function listTrips(params: {
  status?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<TripOut>> {
  const res = await client.get<PaginatedResponse<TripOut>>("/dispatch/trips", { params });
  return res.data;
}

export async function getTrip(id: string): Promise<TripOut> {
  const res = await client.get<TripOut>(`/dispatch/trips/${id}`);
  return res.data;
}

export async function createTrip(payload: {
  vehicle_id: string;
  origin: { type: "Point"; coordinates: [number, number] };
  destination: { type: "Point"; coordinates: [number, number] };
  priority?: "low" | "standard" | "high" | "critical";
  caller_name?: string;
  caller_phone?: string;
  incident_type?: string;
}): Promise<TripOut> {
  const res = await client.post<TripOut>("/dispatch/trips", payload);
  return res.data;
}

export async function updateTripStatus(id: string, status: string): Promise<TripOut> {
  const res = await client.patch<TripOut>(`/dispatch/trips/${id}/status`, { status });
  return res.data;
}

export async function setGreenCorridor(
  id: string,
  signalSequence: string[],
  corridorPolyline?: string,
): Promise<TripOut> {
  const res = await client.put<TripOut>(`/dispatch/trips/${id}/green-corridor`, {
    signal_sequence: signalSequence,
    corridor_polyline: corridorPolyline,
  });
  return res.data;
}

// --- Vehicles -------------------------------------------------------------
export async function listVehicles(status?: string): Promise<VehicleOut[]> {
  const res = await client.get<VehicleOut[]>("/dispatch/vehicles", { params: { status } });
  return res.data;
}

// --- Hazards --------------------------------------------------------------
export async function listHazards(params: {
  type?: string;
  status?: string;
  bbox?: string;
  page?: number;
  page_size?: number;
}): Promise<PaginatedResponse<HazardOut>> {
  const res = await client.get<PaginatedResponse<HazardOut>>("/hazards", { params });
  return res.data;
}

export async function getHazard(id: string): Promise<HazardOut> {
  const res = await client.get<HazardOut>(`/hazards/${id}`);
  return res.data;
}

export async function createHazard(payload: {
  type: string;
  severity: string;
  location: { type: "Point"; coordinates: [number, number] };
  description?: string;
  nearest_landmark?: string;
  image_ids?: string[];
}): Promise<HazardOut> {
  const res = await client.post<HazardOut>("/hazards", payload);
  return res.data;
}

export async function corroborateHazard(
  id: string,
  payload: { same_location?: boolean; note?: string },
): Promise<HazardOut> {
  const res = await client.post<HazardOut>(`/hazards/${id}/corroborate`, payload);
  return res.data;
}

export async function updateHazardStatus(id: string, status: string): Promise<HazardOut> {
  const res = await client.patch<HazardOut>(`/hazards/${id}/status?new_status=${encodeURIComponent(status)}`);
  return res.data;
}

// --- Signals --------------------------------------------------------------
export async function preemptSignal(payload: {
  trip_id: string;
  signal_id: string;
  target_state?: string;
}): Promise<SignalPreemptionOut> {
  const res = await client.post<SignalPreemptionOut>("/signals/preempt", payload);
  return res.data;
}

export async function watchdogRevert(payload: {
  signal_id: string;
  reason: string;
  force_revert?: boolean;
}): Promise<SignalPreemptionOut> {
  const res = await client.post<SignalPreemptionOut>("/signals/watchdog", payload);
  return res.data;
}

export async function listActivePreemptions(): Promise<SignalPreemptionOut[]> {
  const res = await client.get<SignalPreemptionOut[]>("/signals/active");
  return res.data;
}

export async function listTripPreemptions(tripId: string): Promise<SignalPreemptionOut[]> {
  const res = await client.get<SignalPreemptionOut[]>(`/signals/history/${tripId}`);
  return res.data;
}

// --- ML -------------------------------------------------------------------
export async function scoreSegment(features: Record<string, number>): Promise<SegmentScore> {
  const res = await client.post<SegmentScore>("/ml/score-segment", features);
  return res.data;
}

export async function scoreRoute(segments: Record<string, number>[]): Promise<RouteRiskAnalysis> {
  const res = await client.post<RouteRiskAnalysis>("/ml/score-route", segments);
  return res.data;
}

// --- Citizens -------------------------------------------------------------
export async function uploadReportImage(file: File): Promise<{
  image_id: string;
  size_bytes: number;
  mime_type: string;
}> {
  const formData = new FormData();
  formData.append("file", file);
  const res = await client.post("/citizens/reports/uploads", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function myReports(): Promise<HazardOut[]> {
  const res = await client.get<HazardOut[]>("/citizens/me/reports");
  return res.data;
}

// --- Current user (server-confirmed) --------------------------------------
export async function getMe(): Promise<UserOut | null> {
  try {
    const res = await client.get<UserOut>("/auth/me");
    return res.data;
  } catch {
    return null;
  }
}
