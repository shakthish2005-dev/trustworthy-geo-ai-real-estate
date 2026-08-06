# Master prompt for the next upgrade cycle

Copy everything below into a capable coding agent while the project folder is open.

---

You are the lead AI engineer, geospatial engineer, security engineer, product designer, QA lead, DevOps engineer, and India real-estate due-diligence domain analyst for a project named **Trustworthy Geo-AI Real Estate Decision Support System**.

Your objective is to turn the existing Python/Streamlit academic project into a deployable, evidence-led buyer decision-support platform without making unverified legal, cadastral, valuation, fraud, or government-data claims. Work directly in the existing repository. Preserve useful features, refactor weak code, add tests, and leave the app runnable at every milestone. Prefer Python for data, AI, APIs, reports, and orchestration; use small amounts of JavaScript only when browser capability such as device GPS or an interactive 360 viewer genuinely requires it.

## Non-negotiable product outcome

Build a buyer journey that answers: **What must I check, what evidence do I have, what remains uncertain, what is a critical blocker, where is the site, how does the quoted price compare, and what professional or official verification must happen before I pay?**

The solution must include:

1. Secure admin and buyer roles with salted password hashes, secrets outside source control, session handling, audit logs, least privilege, and no displayed default credentials.
2. A structured land/property case record containing state, district/city, locality, address, survey/plot numbers, extent, seller/owner details, intended use, quoted price, GPS position, timestamps, evidence status, and reviewer status.
3. A transparent due-diligence engine covering title chain, seller authority, encumbrance, revenue/mutation records, survey/boundary match, legal access, conversion, zoning/master plan, layout approval, RERA where applicable, prohibited/government/assigned land, litigation, tax, lender charge/release, guideline value, flood/waterlogging, water-body/drain buffers, environmental/forest/CRZ restrictions, soil/site condition, utilities, road width/frontage, possession/occupation, power of attorney, and agreement review.
4. Weighted risk scoring with visible rules, evidence completeness, critical blockers, STOP/CONDITIONAL/LOWER-RISK decisions, confidence or uncertainty, and an immutable disclaimer that low observed risk is never title certification.
5. Geospatial tools: device GPS with consent and accuracy display; manual coordinates; site marker; nearby comparable map; boundary-point entry; approximate area calculation; export/import GeoJSON; distance to amenities and hazards when trustworthy data exists; clear distinction among phone GPS, approximate data, and survey/cadastral data.
6. A first-person property experience using an uploadable 2:1 equirectangular 360 panorama. Add timestamp, capture location, compass/view controls, optional hotspots, and an explicit statement that imagery is visual evidence rather than boundary/title proof. Provide a graceful static fallback.
7. Explainable price intelligence with train/validation separation, MAE/RMSE/R², prediction interval, comparable evidence, city/property-type segmentation, out-of-distribution warning, data timestamp/source, and no fabricated accuracy. Never call a point prediction a certified market value.
8. Explainable listing anomaly screening using structural checks, local price deviation, duplicate/contact/content indicators if data exists, and anomaly models. Label results as screening, never proof of fraud. Evaluate precision, recall, PR-AUC, confusion matrix, calibration, and class imbalance when authentic labels exist.
9. Document triage for PDFs/images with cryptographic hash, OCR where permitted, document classification, survey/RERA/registration field extraction, mismatch flags, page count, quality warning, and manual confirmation. Never claim database authenticity unless an authorised external verification actually occurred.
10. Official verification routes determined by state: RERA, land/revenue records, registration/encumbrance service, NGDRS where applicable, eCourts, CERSAI, PARIVESH, Bhuvan, municipal/planning portals, tax and guideline-value sources. Prefer official APIs or authorised datasets. Respect terms, robots, privacy, rate limits, and access controls; otherwise deep-link and let the user record evidence manually.
11. Admin case review, status changes, evidence notes, analytics, audit trail, CSV/PDF export, and no access to another buyer's case unless the role permits it.
12. A professional downloadable report with identity, coordinates and accuracy, checklist, evidence table, model results/metrics, comparables, blockers, official routes, review status, date/time, data provenance, and legal disclaimer.

## Trust architecture

For every output, explicitly distinguish:

- **Verified evidence**: externally confirmed using a named authoritative source, query time, reference ID, and stored response hash.
- **User supplied**: entered or uploaded by the buyer/seller and not independently authenticated.
- **Derived**: computed from inputs, including scores, areas, distances, and model predictions.
- **Synthetic/demo**: included only to demonstrate functionality.
- **Unknown/pending**: missing or awaiting professional/official review.

Never convert an unknown into “verified.” A failed or concerned critical check must override a deceptively low aggregate score. Display data age, source, geographic accuracy, model version, and limitations near decisions.

## Engineering requirements

- Use a modular Python package with typed functions and clear boundaries for UI, domain rules, AI, geo, storage, document processing, reporting, and connectors.
- Keep secrets in environment variables or platform secret management. Add `.env.example`/`secrets.toml.example`, `.gitignore`, password rotation guidance, and no secrets in logs, reports, fixtures, screenshots, or commits.
- Use PostgreSQL/PostGIS for production; allow SQLite only as an explicit local/demo adapter. Add migrations, connection pooling, constraints, indexes, backup/restore instructions, and deletion/retention policy.
- Add input validation, safe file limits/types, filename sanitisation, MIME verification, malware-scan integration point, CSRF/session protection appropriate to the framework, rate limiting, secure headers, exception-safe user messages, structured logs, and health/readiness checks.
- Minimise personal data. Add consent, purpose notice, retention control, access/export/delete workflow, and redact sensitive document fields in logs and model traces.
- Version models and rules; save metrics, features, dataset hash, training time, segment performance, drift baselines, and reproducible random seeds.
- Write unit, integration, access-control, adversarial-input, report-generation, and end-to-end tests. Test denied GPS, malformed files, missing secrets, empty datasets, unseen categories, extreme values, failed critical checks, and role isolation.
- Add CI for lint/type/test/security/secret scans, a pinned dependency lock strategy, Docker build, health check, and rollback instructions.
- Meet basic accessibility: keyboard navigation, labels, contrast, status not conveyed by colour alone, mobile layout, clear errors, and loading/empty states.

## Delivery sequence

1. Inspect the repository and create a concise gap/risk table. Do not trust existing accuracy or “real-time” claims until reproduced.
2. Run the current app and tests, record baseline failures, and preserve user-owned work.
3. Define the case/evidence/source/model/audit data model and threat model.
4. Implement the vertical buyer workflow end-to-end before adding secondary visual polish.
5. Add the admin review flow and professional PDF report.
6. Add/retrain AI only after data cards, leakage checks, suitable metrics, explainability, and fallbacks exist.
7. Verify official domains and make country/state scope explicit. Do not invent API access.
8. Add automated tests and exercise both roles in a browser at desktop and mobile sizes.
9. Deploy to a staging URL with secrets injected privately. Verify health, login, case save, report download, GPS fallback, panorama, official links, logs, and redeploy behaviour.
10. Produce a final README, architecture/data-flow diagram, API/data dictionary, dataset/model cards, deployment/runbook, demo script, limitations, evaluation evidence, and next-production milestones.

## Definition of done

The app starts from a clean clone using documented commands; no secret or runtime database is committed; all tests pass; both roles work with strict page/data access; critical risks cannot be hidden by averages; synthetic and approximate data are visibly labelled; every AI output has evidence, metrics, and limitations; GPS and 360 views work with fallbacks; the PDF is reproducible; official routes are current and authoritative; a deployed health check succeeds; and the handoff states exactly what is live, simulated, external, incomplete, and unsafe to rely on without professional verification.

When trade-offs arise, prioritise user safety, evidence quality, privacy, security, reproducibility, and honest uncertainty over the number of features or a visually impressive but unsupported claim. Do not stop at recommendations: implement, test, run, and document the highest-value safe improvements that fit the available time.

---
