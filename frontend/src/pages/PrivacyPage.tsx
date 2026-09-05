/**
 * Privacy Policy page.
 */
import { Seo } from "@/components/Seo";
import { Breadcrumbs } from "@/components/Breadcrumbs";

export default function PrivacyPage() {
  return (
    <>
      <Seo
        title="Privacy Policy"
        description="How AERIS collects, processes, and protects personal data."
        path="/privacy"
      />
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: "Privacy" }]} />

      <h1>Privacy Policy</h1>
      <p className="text-aeris-textSecondary mt-2 text-sm max-w-3xl">
        This policy describes how AERIS handles personal data collected through
        the dispatch, hazard reporting, and vehicle telemetry modules.
      </p>

      <article className="mt-6 max-w-3xl space-y-6 text-sm leading-relaxed">
        <section>
          <h2 className="text-base font-medium mb-2">1. Data we collect</h2>
          <p className="text-aeris-textSecondary">
            Account email, full name, role, hashed password, hazard report
            location, hazard photos, vehicle position, and signal preemption
            history. We do not collect device-level identifiers beyond what is
            required to deliver push alerts through Firebase Cloud Messaging.
          </p>
        </section>
        <section>
          <h2 className="text-base font-medium mb-2">2. Lawful basis</h2>
          <p className="text-aeris-textSecondary">
            Processing of personal data is necessary for the performance of a
            task carried out in the public interest in the area of emergency
            response. Vehicle telemetry and hazard locations are processed
            under explicit operational consent granted at sign-in.
          </p>
        </section>
        <section>
          <h2 className="text-base font-medium mb-2">3. Retention</h2>
          <p className="text-aeris-textSecondary">
            Trip records and signal preemption logs are retained for the
            duration required by the deploying jurisdiction's audit policy.
            Hazard reports are retained until their status is set to resolved
            or dismissed plus a 90-day grace period.
          </p>
        </section>
        <section>
          <h2 className="text-base font-medium mb-2">4. Sharing</h2>
          <p className="text-aeris-textSecondary">
            Data is shared with traffic control operators on a need-to-know
            basis. Routing requests are sent to Mappls. Push notifications are
            delivered through Firebase. Both providers process data under
            their respective privacy policies.
          </p>
        </section>
        <section>
          <h2 className="text-base font-medium mb-2">5. Your rights</h2>
          <p className="text-aeris-textSecondary">
            You may request a copy of your account data and the hazard reports
            you submitted by contacting the administrator who provisioned your
            account. Account deletion requires administrator approval because
            of the audit trail attached to trip and signal records.
          </p>
        </section>
        <section>
          <h2 className="text-base font-medium mb-2">6. Security</h2>
          <p className="text-aeris-textSecondary">
            The backend enforces HTTPS, Content-Security-Policy, strict CORS,
            rate-limited endpoints, JWT authentication, RBAC, and database
            schema validation. Cookies are set with HttpOnly, Secure, and
            SameSite=Strict flags. See the project documentation for the full
            list of 19 enforced security checks.
          </p>
        </section>
      </article>
    </>
  );
}
