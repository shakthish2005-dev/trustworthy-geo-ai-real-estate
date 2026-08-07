# Real Estate Scout AI

## Geo-AI Land Assessment and Buyer Decision Support System

**Explore locations, assess land, detect risks and make informed buying decisions.**

A deployable, buyer-first third-year project for evaluating land and property before purchase. It combines an auditable due-diligence checklist, geolocation, comparable-property analysis, explainable price and listing-risk models, official verification routes, document triage, admin review, PDF reporting, and a 360-degree first-person property view.

## What is genuinely real-time

- Device-location capture is requested at the moment the user clicks the GPS control.
- Maps, parcel-area estimates, comparable selection, risk scoring, document triage, and model predictions update per request.
- Saved review cases and admin status changes are written immediately to the app database.

Official land, court, registration, RERA, lender-charge, and environmental findings are not silently claimed as verified. The app routes a buyer to the responsible government portals and records the evidence status. This separation is deliberate and legally safer than presenting synthetic data as a live government result.

## Buyer workflow

1. Sign in as a buyer or administrator.
2. Record the city, survey number, location, seller, intended use, and quoted price.
3. Complete 24 weighted checks across ownership, survey, planning, legal, finance, environmental, engineering, infrastructure, and physical possession.
4. Upload available PDF evidence for text/hash triage.
5. Review critical blockers, risk score, feature score, official portal routes, and nearby synthetic demonstration comparables.
6. Inspect a 360-degree equirectangular site panorama or upload one captured on site.
7. Save the case and download a professional due-diligence report.
8. Let the admin change the external-review status with an audit trail.

## Trust and safety design

- PBKDF2-SHA256 password hashing with per-password salt and a private deployment pepper.
- Role-based buyer/admin pages; secrets are excluded from Git.
- Critical failed/concern checks force a high-risk stop recommendation.
- Model intervals, validation metrics, rules, data quality, and limitations are visible.
- Listing screening is labelled anomaly detection—not proof of fraud.
- Synthetic demo coordinates are labelled and never represented as cadastral data.
- Uploaded documents are processed in memory; only derived metadata enters a saved case.

## Local setup

Use Python 3.12.

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-dev.txt
Copy-Item .streamlit\secrets.toml.example .streamlit\secrets.toml
# Replace all placeholder secrets.
.venv\Scripts\python -m streamlit run streamlit_app.py
```

Run tests:

```powershell
.venv\Scripts\python -m pytest
```

## Deployment

The quickest public route is Streamlit Community Cloud: push this folder to a GitHub repository, choose `streamlit_app.py` as the entrypoint, paste the five values from the private secrets file into Advanced settings, and deploy. A Dockerfile and `render.yaml` are included as an alternative. See [DEPLOYMENT.md](DEPLOYMENT.md).

## Production upgrades after the academic demonstration

- Replace the included synthetic CSV with licensed listings/registered-sale feeds and record lineage.
- Use PostgreSQL/PostGIS and object storage instead of local SQLite for multi-instance hosting.
- Connect authorised state APIs or permitted datasets; do not scrape portals that disallow it.
- Add OTP/OIDC, secure cookies, rate limiting, password reset, encryption at rest, malware scanning, backups, consent/retention controls, and structured monitoring.
- Commission city-specific legal templates and validate model fairness, calibration, drift, and error by property segment.
- Use a survey-grade GNSS/cadastral overlay for parcel boundaries; phone GPS is contextual only.

## Academic demonstration notice

The application is decision support, not legal, surveying, engineering, environmental, lending, or valuation certification. A buyer must obtain certified records and independent professional advice before paying money or signing.
