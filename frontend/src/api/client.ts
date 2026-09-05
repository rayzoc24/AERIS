/**
 * AERIS API client.
 *
 * Rules enforced here:
 * - No hardcoded data. Every component fetches through this client.
 * - CSRF token is read from the csrf_token cookie and echoed in X-CSRF-Token.
 * - Access token is read from the HttpOnly access_token cookie automatically
 *   by the browser. We do NOT store tokens in localStorage or in JS.
 * - On 401, the client attempts a single refresh, then redirects to login.
 * - All responses are validated at the boundary by the calling hook.
 */
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from "axios";

const API_PREFIX = "/api/v1";

function readCookie(name: string): string | null {
  const match = document.cookie.match(
    new RegExp("(?:^|; )" + name.replace(/([.$?*|{}()[\]\\/+^])/g, "\\$1") + "=([^;]*)"),
  );
  return match ? decodeURIComponent(match[1]) : null;
}

const client: AxiosInstance = axios.create({
  baseURL: API_PREFIX,
  withCredentials: true,
  timeout: 15_000,
  headers: {
    "Content-Type": "application/json",
    "X-Requested-With": "XMLHttpRequest",
  },
});

client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  // Methods that mutate state must include a CSRF token.
  if (["post", "put", "patch", "delete"].includes(config.method?.toLowerCase() ?? "")) {
    const csrf = readCookie("csrf_token");
    if (csrf) {
      config.headers["X-CSRF-Token"] = csrf;
    }
  }
  return config;

  // The above return is the happy path. If no csrf token cookie exists, the
  // request will still go out; the backend will reject it with 403. The
  // calling hook will then surface the error to the user.
});

let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

async function refreshToken(): Promise<void> {
  try {
    await client.post("/auth/refresh");
  } catch (err) {
    // Refresh failed - clear local auth state by redirecting to login.
    if (!window.location.pathname.startsWith("/login")) {
      window.location.assign("/login?reason=session_expired");
    }
    throw err;
  }
}

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry && !original.url?.includes("/auth/")) {
      original._retry = true;
      if (!isRefreshing) {
        isRefreshing = true;
        refreshPromise = refreshToken().finally(() => {
          isRefreshing = false;
          refreshPromise = null;
        });
      }
      try {
        await refreshPromise;
        return client.request(original);
      } catch {
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  },
);

export { client };
export default client;
