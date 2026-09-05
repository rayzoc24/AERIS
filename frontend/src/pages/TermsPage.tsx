/**
 * Terms & Conditions page.
 */
import { Seo } from "@/components/Seo";
import { Breadcrumbs } from "@/components/Breadcrumbs";

export default function TermsPage() {
  return (
    <>
      <Seo
        title="Terms & Conditions"
        description="Terms of use for the AERIS emergency response system."
        path="/terms"
      />
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: "Terms" }]} />

      <h1>Terms &amp; Conditions</h1>
      <p className="text-aeris-textSecondary mt-2 text-sm max-w-3xl">
        These terms govern access to and use of the AERIS platform. By signing
        in you accept them in full.
      </p>

      <article className="mt-6 max-w-3xl space-y-6 text-sm leading-relaxed">
        <section>
          <h2 className="text-base font-medium mb-2">1. Purpose of use</h2>
          <p className="text-aeris-textSecondary">
            AERIS is intended for use by emergency services, traffic control
            operators, and registered citizens. Use of the dispatch, signal
            preemption, and hazard reporting features for non-emergency
            purposes is prohibited.
          </p>
        </section>
        <section>
          <h2 className="text-base font-medium mb-2">2. Account responsibilities</h2>
          <p className="text-aeris-textSecondary">
            You are responsible for keeping your credentials confidential and
            for all activity under your account. Report any unauthorised use to
            your administrator promptly.
          </p>
        </section>
        <section>
          <h2 className="text-base font-medium mb-2">3. Acceptable use</h2>
          <p className="text-aeris-textSecondary">
            You agree not to submit false hazard reports, attempt to access
            endpoints outside your assigned role, or interfere with signal
            preemption controls. Violations will result in account suspension.
          </p>
        </section>
        <section>
          <h2 className="text-base font-medium mb-2">4. Data handling</h2>
          <p className="text-aeris-textSecondary">
            Hazard reports, vehicle telemetry, and signal preemption records
            are stored in MongoDB and retained per the retention policy
            defined by the deploying jurisdiction. See the Privacy Policy for
            details.
          </p>
        </section>
        <section>
          <h2 className="text-base font-medium mb-2">5. Service availability</h2>
          <p className="text-aeris-textSecondary">
            AERIS is provided on a best-effort basis. Signal preemption and
            routing depend on third-party providers including Mappls and
            Firebase. Service degradation in upstream providers may affect
            AERIS response times.
          </p>
        </section>
      </article>
    </>
  );
}
