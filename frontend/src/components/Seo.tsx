/**
 * Per-page SEO wrapper. Components must supply a unique title, meta
 * description, canonical URL, and an EmergencyService structured data
 * block when relevant.
 *
 * The AERIS site name is appended automatically so individual pages only
 * declare the page-specific title.
 */
import { Helmet } from "react-helmet-async";

interface SeoProps {
  title: string;
  description: string;
  path: string;
  structuredData?: Record<string, unknown>;
  noIndex?: boolean;
}

const SITE_ORIGIN = "https://aeris.example.com";
const SITE_NAME = "AERIS";

export function Seo({ title, description, path, structuredData, noIndex }: SeoProps) {
  const fullTitle = `${title} | ${SITE_NAME}`;
  const canonical = `${SITE_ORIGIN}${path}`;
  return (
    <Helmet>
      <title>{fullTitle}</title>
      <meta name="description" content={description} />
      <link rel="canonical" href={canonical} />
      {noIndex && <meta name="robots" content="noindex, nofollow" />}
      {structuredData && (
        <script type="application/ld+json">
          {JSON.stringify(structuredData)}
        </script>
      )}
    </Helmet>
  );
}

export const siteStructuredData = {
  "@context": "https://schema.org",
  "@type": "EmergencyService",
  name: "AERIS",
  description: "Autonomous Emergency Response & Green Corridor System",
  areaServed: "IN",
  serviceType: "Emergency vehicle dispatch and signal preemption",
  provider: {
    "@type": "Organization",
    name: "Port2Code",
    url: SITE_ORIGIN,
  },
};
