from __future__ import annotations

import json
import os
from collections import defaultdict
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import pydeck as pdk
import streamlit as st
import streamlit.components.v1 as components

from trustestate.config import (
    APP_NAME,
    APP_VERSION,
    CITY_COORDINATES,
    CITY_STATE,
    DEMO_PANORAMA,
    DISCLAIMER,
)
from trustestate.database import (
    authenticate,
    ensure_bootstrap_users,
    initialize_database,
    list_cases,
    platform_stats,
    save_case,
    update_case_status,
)
from trustestate.document_ai import inspect_upload
from trustestate.fraud_engine import analyze_listing, train_anomaly_model
from trustestate.geo import load_properties, nearest_comparables, polygon_area_sqft
from trustestate.official_portals import NATIONAL_PORTALS, portals_for_city
from trustestate.panorama import load_panorama, panorama_html
from trustestate.price_engine import predict_with_interval, train_price_model
from trustestate.reporting import build_due_diligence_pdf
from trustestate.risk_engine import CHECKS, evaluate_due_diligence, land_feature_score

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root { --navy:#061827; --blue:#176B87; --cyan:#64CCC5; --sand:#DAFFFB; }
        .stApp { background: linear-gradient(145deg,#04111d 0%,#071f31 50%,#082a3f 100%); color:#eef8fb; }
        [data-testid="stSidebar"] { background:#041421; border-right:1px solid rgba(100,204,197,.2); }
        [data-testid="stMetric"] { background:rgba(255,255,255,.04); border:1px solid rgba(100,204,197,.17); border-radius:14px; padding:14px; }
        .hero { padding:28px 30px; border-radius:22px; border:1px solid rgba(100,204,197,.25); background:linear-gradient(135deg,rgba(23,107,135,.28),rgba(5,28,44,.72)); margin-bottom:20px; }
        .hero h1 { margin:0 0 8px; color:#f5fdff; font-size:2.35rem; }
        .hero p { color:#a9c9d4; margin:0; font-size:1rem; }
        .risk-high { border-left:5px solid #ff5d73; background:rgba(255,93,115,.10); padding:16px; border-radius:10px; }
        .risk-medium { border-left:5px solid #f9c74f; background:rgba(249,199,79,.10); padding:16px; border-radius:10px; }
        .risk-low { border-left:5px solid #57cc99; background:rgba(87,204,153,.10); padding:16px; border-radius:10px; }
        .portal { padding:14px; border:1px solid rgba(100,204,197,.18); border-radius:12px; min-height:112px; background:rgba(255,255,255,.025); }
        .small-note { font-size:.82rem; color:#8fb0bc; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def get_secret(name: str, default: str = "") -> str:
    env_value = os.getenv(name)
    if env_value:
        return env_value
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


@st.cache_data(show_spinner=False)
def properties() -> pd.DataFrame:
    return load_properties()


@st.cache_resource(show_spinner="Training the explainable price model...")
def price_bundle():
    return train_price_model(properties())


@st.cache_resource(show_spinner="Preparing listing anomaly screening...")
def anomaly_bundle():
    return train_anomaly_model(properties())


def bootstrap() -> tuple[bool, str]:
    required = {
        "ADMIN_USERNAME": get_secret("ADMIN_USERNAME"),
        "ADMIN_PASSWORD": get_secret("ADMIN_PASSWORD"),
        "USER_USERNAME": get_secret("USER_USERNAME"),
        "USER_PASSWORD": get_secret("USER_PASSWORD"),
        "AUTH_PEPPER": get_secret("AUTH_PEPPER"),
    }
    missing = [key for key, value in required.items() if not value]
    if missing:
        return False, ", ".join(missing)
    initialize_database()
    ensure_bootstrap_users(
        required["ADMIN_USERNAME"],
        required["ADMIN_PASSWORD"],
        required["USER_USERNAME"],
        required["USER_PASSWORD"],
        required["AUTH_PEPPER"],
    )
    return True, required["AUTH_PEPPER"]


def login_page(pepper: str) -> None:
    st.markdown(
        """
        <div class="hero" style="max-width:760px;margin:8vh auto 24px;">
          <h1>🧭 Trustworthy Geo-AI</h1>
          <p>Evidence-led property and land due diligence before you commit money.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    left, middle, right = st.columns([1, 1.2, 1])
    with middle:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Secure login", use_container_width=True)
        if submitted:
            user = authenticate(username, password, pepper)
            if user:
                st.session_state.user = user
                st.rerun()
            st.error("Invalid username or password.")
        st.caption("Credentials are configured through private deployment secrets and are never displayed by the app.")


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def format_inr(value: float) -> str:
    if value >= 10_000_000:
        return f"₹{value / 10_000_000:,.2f} Cr"
    if value >= 100_000:
        return f"₹{value / 100_000:,.2f} L"
    return f"₹{value:,.0f}"


def overview_page(user: dict[str, Any]) -> None:
    hero("Trustworthy Geo-AI", "A buyer-first workspace combining official verification routes, geo intelligence, explainable AI and evidence tracking.")
    df = properties()
    stats = platform_stats()
    cols = st.columns(4)
    cols[0].metric("Reference listings", f"{len(df):,}")
    cols[1].metric("Cities covered", df["city"].nunique())
    cols[2].metric("Due-diligence cases", stats["cases"])
    cols[3].metric("Pending professional review", stats["pending_review"])

    st.warning(DISCLAIMER)
    st.subheader("What the system checks before a land purchase")
    c1, c2, c3, c4 = st.columns(4)
    c1.info("**Legal title**\n\nTitle chain, EC, seller identity, mutation, litigation and lender charge.")
    c2.info("**Planning**\n\nZoning, conversion, layout approval, prohibited land and RERA applicability.")
    c3.info("**Physical site**\n\nSurvey extent, boundaries, access, flood/water-body exposure, soil and utilities.")
    c4.info("**Financial decision**\n\nComparable prices, anomaly flags, guideline value and conditional risk report.")

    st.subheader("Approximate market coverage map")
    city_summary = (
        df.groupby("city", as_index=False)
        .agg(latitude=("latitude", "mean"), longitude=("longitude", "mean"), listings=("property_id", "count"), avg_price=("price", "mean"))
    )
    layer = pdk.Layer(
        "ScatterplotLayer",
        city_summary,
        get_position="[longitude, latitude]",
        get_radius="listings * 180",
        get_fill_color="[100, 204, 197, 150]",
        pickable=True,
    )
    st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=pdk.ViewState(latitude=21.0, longitude=78.0, zoom=3.5), tooltip={"text": "{city}\n{listings} demo listings"}))
    st.caption("Map points for the included academic dataset are approximate city-level demo coordinates, not cadastral locations.")


def device_location_component() -> None:
    components.html(
        """
        <button onclick="captureGPS()" style="width:100%;padding:10px 14px;border:0;border-radius:9px;background:#176B87;color:white;font-weight:700;cursor:pointer">📍 Capture device GPS</button>
        <div id="gps" style="font:13px sans-serif;color:#9cc4d1;margin-top:8px">Browser permission is required.</div>
        <script>
        function captureGPS(){
          const out=document.getElementById('gps');
          if(!navigator.geolocation){out.textContent='Geolocation is not supported.';return;}
          out.textContent='Requesting location...';
          navigator.geolocation.getCurrentPosition(function(pos){
            const url=new URL(window.parent.location.href);
            url.searchParams.set('lat',pos.coords.latitude.toFixed(7));
            url.searchParams.set('lon',pos.coords.longitude.toFixed(7));
            url.searchParams.set('gps_accuracy',Math.round(pos.coords.accuracy));
            window.parent.location.href=url.toString();
          },function(err){out.textContent='Location unavailable: '+err.message;},{enableHighAccuracy:true,timeout:15000});
        }
        </script>
        """,
        height=76,
    )


def collect_identity(prefix: str = "case") -> dict[str, Any]:
    df = properties()
    cities = sorted(df["city"].unique())
    query_lat = float(st.query_params.get("lat", CITY_COORDINATES[cities[0]][0]))
    query_lon = float(st.query_params.get("lon", CITY_COORDINATES[cities[0]][1]))
    left, right = st.columns([2, 1])
    with left:
        title = st.text_input("Property / land review title", "Residential plot review", key=f"{prefix}_title")
        c1, c2, c3 = st.columns(3)
        city = c1.selectbox("City", cities, key=f"{prefix}_city")
        state = CITY_STATE.get(city, "")
        survey = c2.text_input("Survey / plot number", key=f"{prefix}_survey")
        seller = c3.text_input("Seller / promoter name", key=f"{prefix}_seller")
        c4, c5 = st.columns(2)
        latitude = c4.number_input("Latitude", value=query_lat, format="%.7f", key=f"{prefix}_lat")
        longitude = c5.number_input("Longitude", value=query_lon, format="%.7f", key=f"{prefix}_lon")
    with right:
        device_location_component()
        accuracy = st.query_params.get("gps_accuracy")
        if accuracy:
            st.caption(f"Device-reported GPS accuracy: approximately {accuracy} m")
        st.info(f"State portal pack: **{state or 'Select a supported city'}**")
    return {
        "title": title,
        "city": city,
        "state": state,
        "survey_number": survey,
        "seller_name": seller,
        "latitude": latitude,
        "longitude": longitude,
    }


def due_diligence_page(user: dict[str, Any]) -> None:
    hero("Land Due-Diligence Command Center", "Record evidence, expose critical blockers and produce a lawyer-ready conditional report before paying a token.")
    identity = collect_identity()
    grouped: dict[str, list[Any]] = defaultdict(list)
    for check in CHECKS:
        grouped[check.category].append(check)

    st.subheader("1. Documentary and regulatory checks")
    statuses: dict[str, str] = {}
    options = ["Pending", "Verified", "Concern", "Failed", "Not applicable"]
    for category, checks in grouped.items():
        with st.expander(category, expanded=category in {"Ownership", "Survey", "Planning"}):
            for check in checks:
                left, right = st.columns([2, 1])
                left.markdown(f"**{check.label}**  \n<span class='small-note'>Evidence: {check.evidence}</span>", unsafe_allow_html=True)
                statuses[check.key] = right.selectbox("Status", options, key=f"status_{check.key}", label_visibility="collapsed")

    st.subheader("2. Land and access features")
    f1, f2, f3, f4 = st.columns(4)
    frontage = f1.number_input("Frontage (ft)", 0.0, 1000.0, 40.0, 1.0)
    road_width = f2.number_input("Access road width (ft)", 0.0, 300.0, 30.0, 1.0)
    slope = f3.number_input("Approx. slope (%)", 0.0, 100.0, 2.0, 0.5)
    intended_use = f4.selectbox("Intended use", ["Residential", "Commercial", "Agricultural", "Industrial", "Mixed use"])
    b1, b2, b3, b4 = st.columns(4)
    corner = b1.checkbox("Corner plot")
    water = b2.checkbox("Water available")
    electricity = b3.checkbox("Electricity available")
    flood_history = b4.checkbox("Flood/waterlogging reported")
    feature_payload = {
        "frontage_ft": frontage,
        "road_width_ft": road_width,
        "slope_pct": slope,
        "intended_use": intended_use,
        "corner_plot": corner,
        "water": water,
        "electricity": electricity,
        "flood_history": flood_history,
    }

    st.subheader("3. Evidence file inspection")
    uploads = st.file_uploader(
        "Upload PDFs or images of EC, title deed, revenue record, layout, tax receipt or survey sketch",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=True,
    )
    document_results = []
    for upload in uploads:
        result = inspect_upload(upload.name, upload.getvalue(), upload.type)
        document_results.append(result)
        with st.expander(f"{upload.name} - SHA-256 recorded"):
            st.json(result)

    if st.button("Run complete decision analysis", type="primary", use_container_width=True):
        due_result = evaluate_due_diligence(statuses)
        feature_result = land_feature_score(feature_payload)
        payload = {**identity, "statuses": statuses, "land_features": feature_payload, "document_results": document_results}
        st.session_state.current_analysis = {
            "payload": payload,
            "due_result": due_result,
            "feature_result": feature_result,
        }

    current = st.session_state.get("current_analysis")
    if current:
        result = current["due_result"]
        css = f"risk-{result['risk_band'].lower()}"
        st.markdown(f"<div class='{css}'><h3>{result['risk_band']} observed risk - {result['risk_score']}/100</h3><p>{result['decision']}</p></div>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("Evidence completion", f"{result['completion_pct']}%")
        m2.metric("Critical blockers", len(result["blockers"]))
        m3.metric("Physical usability", f"{current['feature_result']['score']}/100")
        if result["blockers"]:
            st.error("Critical blockers: " + "; ".join(result["blockers"]))
        st.caption("Physical usability is a transparent feature score and is not legal or planning approval.")

        report_bytes = build_due_diligence_pdf(current["payload"], current["payload"]["statuses"], result)
        c1, c2 = st.columns(2)
        if c1.button("Save case", use_container_width=True):
            case_id = save_case(user["id"], current["payload"], result["risk_score"], result["risk_band"])
            st.success(f"Case #{case_id} saved for review.")
        c2.download_button("Download due-diligence PDF", report_bytes, "property_due_diligence_report.pdf", "application/pdf", use_container_width=True)


def geo_page() -> None:
    hero("Geo Intelligence & Parcel Context", "Capture coordinates, compare nearby listings, measure uploaded parcel boundaries and open official spatial layers.")
    identity = collect_identity("geo")
    df = properties()
    latitude, longitude = identity["latitude"], identity["longitude"]
    comps = nearest_comparables(df, latitude, longitude, identity["city"], limit=20)
    selected = pd.DataFrame([{"latitude": latitude, "longitude": longitude, "label": "Selected site"}])
    layers = [
        pdk.Layer("ScatterplotLayer", comps, get_position="[longitude, latitude]", get_radius=220, get_fill_color="[100,204,197,145]", pickable=True),
        pdk.Layer("ScatterplotLayer", selected, get_position="[longitude, latitude]", get_radius=360, get_fill_color="[255,93,115,210]", pickable=True),
    ]
    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(latitude=latitude, longitude=longitude, zoom=10.5), tooltip={"text": "{locality}\n₹{price_per_sqft}/sqft"}))
    st.caption("Reference-listing points are approximate demo locations. The selected GPS coordinate should be cross-checked against an official survey/cadastral map.")

    st.subheader("Parcel boundary measurement")
    boundary_text = st.text_area("Paste boundary vertices, one latitude,longitude pair per line", placeholder="12.971600,77.594600\n12.971650,77.594900\n12.971350,77.594920\n12.971300,77.594620")
    points = []
    for line in boundary_text.splitlines():
        try:
            a, b = line.split(",", 1)
            points.append((float(a.strip()), float(b.strip())))
        except ValueError:
            pass
    if len(points) >= 3:
        area = polygon_area_sqft(points)
        st.metric("Approximate polygon area", f"{area:,.0f} sqft")
        st.warning("GPS polygon area is indicative only. Registered extent must be confirmed by a licensed surveyor and official records.")

    st.subheader("Nearby reference properties")
    st.dataframe(comps[["property_id", "locality", "property_type", "area_sqft", "price", "price_per_sqft", "distance_km"]].head(10), use_container_width=True, hide_index=True)
    _, state_portals = portals_for_city(identity["city"])
    cols = st.columns(3)
    for col, (label, url) in zip(cols, state_portals.items()):
        col.link_button(label.replace("_", " ").title(), url, use_container_width=True)


def price_page() -> None:
    hero("Explainable Price & Comparable AI", "Estimate a transparent price range and inspect nearby reference properties rather than relying on one unexplained number.")
    df = properties()
    cities = sorted(df["city"].unique())
    c1, c2, c3 = st.columns(3)
    city = c1.selectbox("City", cities, key="price_city")
    localities = sorted(df[df["city"].eq(city)]["locality"].unique())
    locality = c2.selectbox("Locality", localities)
    property_type = c3.selectbox("Property type", sorted(df["property_type"].unique()))
    c4, c5, c6, c7 = st.columns(4)
    bhk = c4.number_input("BHK", 0, 10, 2)
    area = c5.number_input("Area (sqft)", 100.0, 100000.0, 1200.0, 50.0)
    bathrooms = c6.number_input("Bathrooms", 0, 10, 2)
    floor = c7.number_input("Floor", 0, 100, 2)
    c8, c9, c10 = st.columns(3)
    age = c8.number_input("Age (years)", 0, 100, 5)
    amenity = c9.slider("Amenity score", 0, 14, 6)
    near_score = c10.slider("Nearby-service score", 0.0, 10.0, 6.0, 0.5)
    if st.button("Estimate price range", type="primary", use_container_width=True):
        payload = {
            "city": city,
            "locality": locality,
            "property_type": property_type,
            "bhk": bhk,
            "area_sqft": area,
            "bathrooms": bathrooms,
            "floor": floor,
            "age_years": age,
            "amenity_score": amenity,
            "school_nearby": near_score,
            "hospital_nearby": near_score,
            "metro_nearby": near_score,
            "mall_nearby": near_score,
        }
        result = predict_with_interval(price_bundle(), payload)
        st.session_state.price_result = result
    result = st.session_state.get("price_result")
    if result:
        p1, p2, p3 = st.columns(3)
        p1.metric("Estimated midpoint", format_inr(result["predicted_price"]))
        p2.metric("Observed model range", f"{format_inr(result['interval_low'])} - {format_inr(result['interval_high'])}")
        p3.metric("Estimated price/sqft", f"₹{result['price_per_sqft']:,.0f}")
        st.info(result["data_notice"])
        st.write("**Explanation factors:** " + " · ".join(result["explanations"]))
        st.json(result["model_metrics"], expanded=False)


def listing_risk_page() -> None:
    hero("Listing Anomaly & Fraud-Risk Screening", "Combine market deviation, structural plausibility and high-pressure language into an explainable screening result.")
    df = properties()
    c1, c2, c3 = st.columns(3)
    city = c1.selectbox("City", sorted(df["city"].unique()), key="risk_city")
    locality = c2.selectbox("Locality", sorted(df[df["city"].eq(city)]["locality"].unique()), key="risk_locality")
    property_type = c3.selectbox("Property type", sorted(df["property_type"].unique()), key="risk_type")
    c4, c5, c6, c7 = st.columns(4)
    area = c4.number_input("Area (sqft)", 100.0, 100000.0, 1200.0, 50.0, key="risk_area")
    bhk = c5.number_input("BHK", 0, 10, 2, key="risk_bhk")
    price_lakh = c6.number_input("Listed price (₹ lakh)", 1.0, 10000.0, 80.0, 1.0)
    age = c7.number_input("Age (years)", 0, 100, 5, key="risk_age")
    description = st.text_area("Listing description", "Ready to move property with clear documents.")
    if st.button("Screen listing", type="primary", use_container_width=True):
        result = analyze_listing(anomaly_bundle(), {
            "city": city, "locality": locality, "property_type": property_type,
            "area_sqft": area, "bhk": bhk, "price": price_lakh * 100000,
            "age_years": age, "amenity_score": 6, "description": description,
        })
        css = f"risk-{result['risk_band'].lower()}"
        st.markdown(f"<div class='{css}'><h3>{result['risk_band']} listing anomaly risk - {result['risk_score']}/100</h3></div>", unsafe_allow_html=True)
        for reason in result["reasons"]:
            st.write(f"- {reason}")
        st.caption(result["notice"])


def panorama_page() -> None:
    hero("360° FPP Property & Land View", "Walk the site virtually using an equirectangular panorama, then confirm the same features during a physical inspection.")
    upload = st.file_uploader("Upload a 2:1 equirectangular JPG/PNG panorama", type=["jpg", "jpeg", "png"])
    if upload:
        image_bytes = upload.getvalue()
        title = upload.name
        st.success("Displaying uploaded panorama. Do not treat imagery alone as proof of current site condition.")
    else:
        image_bytes = load_panorama(DEMO_PANORAMA)
        title = "AI-generated demonstration land panorama"
        st.info("Showing the built-in AI-generated demo panorama. Replace it with geotagged, dated site imagery for a real case.")
    components.html(panorama_html(image_bytes, title), height=560)
    st.subheader("Features to inspect in the first-person view")
    cols = st.columns(4)
    cols[0].write("**Boundaries**\n\nBoundary stones, fencing and encroachments")
    cols[1].write("**Access**\n\nRoad width, legal entry and approach condition")
    cols[2].write("**Utilities**\n\nDrainage, electricity, water and sewer connections")
    cols[3].write("**Surroundings**\n\nWater bodies, high-tension lines, waste, slopes and occupation")


def portals_page() -> None:
    hero("Official Verification Portals", "Open the issuing authority directly. The platform records your evidence but does not scrape CAPTCHA-protected or restricted government systems.")
    city = st.selectbox("Select property city", sorted(CITY_STATE))
    state, portals = portals_for_city(city)
    st.subheader(f"{state} official portal pack")
    cols = st.columns(3)
    for col, (purpose, url) in zip(cols, portals.items()):
        with col:
            st.markdown(f"<div class='portal'><b>{purpose.replace('_',' ').title()}</b><br><span class='small-note'>Open and verify using survey/project details.</span></div>", unsafe_allow_html=True)
            st.link_button("Open official portal", url, use_container_width=True)
    st.subheader("National verification routes")
    for portal in NATIONAL_PORTALS:
        c1, c2 = st.columns([4, 1])
        c1.markdown(f"**{portal['name']}**  \n{portal['purpose']}")
        c2.link_button("Open", portal["url"], use_container_width=True)


def cases_page(user: dict[str, Any]) -> None:
    hero("Saved Property Cases", "Review evidence status and risk decisions across your due-diligence workspace.")
    cases = list_cases(user["id"], user["role"])
    if not cases:
        st.info("No saved cases yet. Run a due-diligence analysis and save it first.")
        return
    display = pd.DataFrame(cases)
    st.dataframe(display[["id", "owner", "title", "city", "survey_number", "risk_score", "risk_band", "review_status", "updated_at"]], use_container_width=True, hide_index=True)
    selected_id = st.selectbox("Inspect case", [row["id"] for row in cases])
    selected = next(row for row in cases if row["id"] == selected_id)
    st.json(json.loads(selected["payload_json"]))


def admin_page(user: dict[str, Any]) -> None:
    hero("Admin Review Console", "Monitor cases, route professional review and preserve an auditable decision trail.")
    stats = platform_stats()
    cols = st.columns(4)
    for col, (label, value) in zip(cols, [("Users", stats["users"]), ("Cases", stats["cases"]), ("High risk", stats["high_risk"]), ("Pending review", stats["pending_review"])]):
        col.metric(label, value)
    cases = list_cases(user["id"], "admin")
    if not cases:
        st.info("No cases to review.")
        return
    df = pd.DataFrame(cases)
    st.dataframe(df[["id", "owner", "title", "city", "risk_score", "risk_band", "review_status", "updated_at"]], use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    case_id = c1.selectbox("Case ID", df["id"].tolist())
    status = c2.selectbox("Review status", ["Draft", "Needs evidence", "Lawyer review", "Verified externally", "Rejected"])
    if st.button("Update review status", type="primary"):
        update_case_status(int(case_id), status, user["id"])
        st.success("Status updated and audit event recorded.")
        st.rerun()


def main() -> None:
    apply_theme()
    ready, pepper_or_missing = bootstrap()
    if not ready:
        hero("Deployment setup required", "Secure bootstrap credentials are missing.")
        st.error("Configure these private secrets before starting the app: " + pepper_or_missing)
        st.code("ADMIN_USERNAME=...\nADMIN_PASSWORD=...\nUSER_USERNAME=...\nUSER_PASSWORD=...\nAUTH_PEPPER=...")
        st.stop()

    if "user" not in st.session_state:
        login_page(pepper_or_missing)
        st.stop()

    user = st.session_state.user
    with st.sidebar:
        st.markdown("## 🧭 Trustworthy Geo-AI")
        st.caption(f"v{APP_VERSION}")
        st.success(f"{user['username']} · {user['role']}")
        pages = [
            "Overview",
            "Land Due Diligence",
            "Geo Intelligence",
            "Price & Comparable AI",
            "Listing Risk",
            "360° FPP View",
            "Official Portals",
            "Saved Cases",
        ]
        if user["role"] == "admin":
            pages.append("Admin Console")
        page = st.radio("Navigation", pages)
        st.divider()
        if st.button("Log out", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    routes = {
        "Overview": lambda: overview_page(user),
        "Land Due Diligence": lambda: due_diligence_page(user),
        "Geo Intelligence": geo_page,
        "Price & Comparable AI": price_page,
        "Listing Risk": listing_risk_page,
        "360° FPP View": panorama_page,
        "Official Portals": portals_page,
        "Saved Cases": lambda: cases_page(user),
        "Admin Console": lambda: admin_page(user),
    }
    routes[page]()
    st.divider()
    st.caption(DISCLAIMER)


if __name__ == "__main__":
    main()
