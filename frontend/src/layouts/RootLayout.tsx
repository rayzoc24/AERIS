/**
 * Top-level site layout: header, footer, and skip link.
 *
 * Hard rule: every visual element is data-less. No metrics, no fake
 * counts, no taglines. Only navigation and authentication status.
 */
import { Link, NavLink, Outlet } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

const NAV_ITEMS: Array<{ label: string; to: string; roles: Array<"admin" | "driver" | "citizen"> }> = [
  { label: "Dashboard", to: "/", roles: ["admin", "driver", "citizen"] },
  { label: "Emergency Vehicle HUD", to: "/emergency-hud", roles: ["admin", "driver"] },
  { label: "Traffic Control", to: "/traffic-control", roles: ["admin"] },
  { label: "Citizen Reporting", to: "/citizen-reporting", roles: ["admin", "citizen", "driver"] },
];

function Header() {
  const { user, isAuthenticated, logout, hasRole } = useAuth();
  const visibleItems = NAV_ITEMS.filter((item) => !user || hasRole(...item.roles));
  return (
    <header className="aeris-header">
      <div className="max-w-content mx-auto px-4 flex items-center justify-between h-14">
        <div className="flex items-center gap-6">
          <Link to="/" className="text-base font-semibold tracking-wide" aria-label="AERIS home">
            AERIS
          </Link>
          <nav aria-label="Primary" className="hidden md:flex items-center gap-1">
            {visibleItems.map((item) => (
              <NavLink key={item.to} to={item.to} end className="aeris-nav-link">
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-3 text-sm">
          {isAuthenticated && user ? (
            <>
              <span className="text-aeris-textMuted" data-testid="user-name">
                {user.name}
              </span>
              <span className="aeris-badge aeris-badge-muted" data-testid="user-role">
                {user.role}
              </span>
              <button onClick={logout} className="aeris-btn" type="button">
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link to="/login" className="aeris-btn">
                Sign in
              </Link>
              <Link to="/register" className="aeris-btn aeris-btn-primary">
                Create account
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-aeris-border bg-aeris-surface mt-12">
      <div className="max-w-content mx-auto px-4 py-6 text-xs text-aeris-textMuted flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        <div>
          <p>AERIS - Autonomous Emergency Response &amp; Green Corridor System.</p>
          <p>SIH-26205. Team Port2Code.</p>
        </div>
        <nav aria-label="Legal" className="flex items-center gap-3">
          <Link to="/terms" className="hover:text-aeris-textPrimary">
            Terms
          </Link>
          <Link to="/privacy" className="hover:text-aeris-textPrimary">
            Privacy
          </Link>
        </nav>
      </div>
    </footer>
  );
}

export function RootLayout() {
  return (
    <div className="min-h-full flex flex-col">
      <a href="#main" className="skip-link">
        Skip to main content
      </a>
      <Header />
      <main id="main" className="flex-1 max-w-content mx-auto w-full px-4 py-6">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}
