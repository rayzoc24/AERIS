/**
 * Custom 404 page. Required: must not use default placeholders.
 */
import { Link } from "react-router-dom";

import { Seo } from "@/components/Seo";
import { Breadcrumbs } from "@/components/Breadcrumbs";

export default function NotFoundPage() {
  return (
    <>
      <Seo
        title="Page not found"
        description="The page you requested does not exist on the AERIS platform."
        path="/404"
        noIndex
      />
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: "Not found" }]} />

      <h1>Page not found</h1>
      <p className="text-aeris-textSecondary mt-2 max-w-md text-sm">
        The URL you requested does not match any route on this site. Return to
        the dashboard or use the navigation bar to reach an available module.
      </p>
      <div className="mt-4 flex gap-3">
        <Link to="/" className="aeris-btn aeris-btn-primary">
          Back to dashboard
        </Link>
        <Link to="/citizen-reporting" className="aeris-btn">
          File a hazard report
        </Link>
      </div>
    </>
  );
}
