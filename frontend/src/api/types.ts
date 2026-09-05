/**
 * AERIS API type definitions. Mirrors backend Pydantic models.
 */

export type UserRole = "admin" | "driver" | "citizen";

export interface UserOut {
  id: string;
  email: string;
  name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TokenBundle {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  csrf_token: string;
  user: UserOut;
}

export interface GeoPoint {
  type: "Point";
  coordinates: [number, number];
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

export interface ErrorResponse {
  detail: string;
  code?: string;
  request_id?: string;
}

export interface HealthStatus {
  status: string;
  version: string;
  services: Record<string, string>;
  timestamp: string;
}

// --- Trips ---------------------------------------------------------------
export type TripStatus = "pending" | "active" | "completed" | "cancelled";
export type TripPriority = "low" | "standard" | "high" | "critical";

export interface TripOut {
  id: string;
  vehicle_id: string;
  driver_id: string | null;
  status: TripStatus;
  priority: TripPriority;
  origin: GeoPoint;
  destination: GeoPoint;
  route_polyline: string | null;
  green_corridor: string[] | null;
  started_at: string;
  ended_at: string | null;
  eta_seconds: number | null;
  distance_metres: number | null;
}

// --- Vehicles ------------------------------------------------------------
export type VehicleType = "ambulance" | "fire" | "police" | "rescue";
export type VehicleStatus = "available" | "dispatched" | "en_route" | "on_scene" | "offline";

export interface VehicleOut {
  id: string;
  registration_number: string;
  type: VehicleType;
  status: VehicleStatus;
  driver_id: string | null;
  last_known_location: GeoPoint | null;
  current_trip_id: string | null;
  updated_at: string;
}

// --- Hazards -------------------------------------------------------------
export type HazardType =
  | "accident"
  | "pothole"
  | "flooding"
  | "obstruction"
  | "road_work"
  | "vehicle_breakdown";

export type HazardSeverity = "low" | "medium" | "high" | "critical";
export type HazardStatus = "active" | "verified" | "resolved" | "dismissed";

export interface HazardOut {
  id: string;
  type: HazardType;
  severity: HazardSeverity;
  status: HazardStatus;
  location: GeoPoint;
  description: string;
  reported_by: string;
  corroboration_score: number;
  image_urls: string[];
  created_at: string;
  updated_at: string;
}

// --- Signals -------------------------------------------------------------
export type SignalState = "green" | "red" | "flash" | "reverted";

export interface SignalPreemptionOut {
  id: string;
  trip_id: string;
  signal_id: string;
  state: SignalState;
  triggered_at: string;
  reverted_at: string | null;
  watchdog_active: boolean;
}

// --- ML ------------------------------------------------------------------
export interface RouteRiskAnalysis {
  overall: number;
  max_segment: number;
  segments: number[];
  version: string;
}

export interface SegmentScore {
  risk_score: number;
  version: string;
  features_received: string[];
}
