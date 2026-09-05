/**
 * Accessible breadcrumb navigation. Each page must declare its trail.
 * Renders a nav with aria-label and a JSON-LD BreadcrumbList entry.
 */
import { Link } from "react-router-dom";
import { Helmet } from "react-helmet-async";

export interface BreadcrumbItem {
  label: string;
  to?: string;
}

const SITE_ORIGIN = "https://aeris.example.com";

export function Breadcrumbs({ items }: { items: BreadcrumbItem[] }) {
  const jsonLd = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.label,
      item: item.to ? `${SITE_ORIGIN}${item.to}` : undefined,
    })),
  };
  return (
    <nav aria-label="Breadcrumb" className="aeris-breadcrumbs mb-4">
      <Helmet>
        <script type="application/ld+json">
          {JSON.stringify(jsonLd)}
        </script>
      </Helmet>
      <ol className="flex items-center gap-2">
        {items.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            {item.to && index < items.length - 1 ? (
              <Link to={item.to} className="hover:text-aeris-textPrimary">
                {item.label}
              </Link>
            ) : (
              <span aria-current={index === items.length - 1 ? "page" : undefined}>
                {item.label}
              </span>
            )}
            {index < items.length - 1 && <span aria-hidden="true">/</span>}
          </li>
        ))}
      </ol>
    </nav>
  );
}
