import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from urllib.parse import urlparse
from database.db import *
from scraper.sources import COMPANY_NEWS_FEEDS
from scraper import case_studies as cs_scraper

st.set_page_config(page_title="Robotics Industry Comparison", layout="wide", page_icon="🤖")

# --- Simple password gate ---
import os

def _check_password():
    if st.session_state.get("authenticated", False):
        return True
    password = st.secrets.get("APP_PASSWORD") or os.environ.get("APP_PASSWORD", "robotics2026")
    with st.container():
        st.markdown("## 🔒 Access Restricted")
        st.markdown("Enter the password to view this dashboard.")
        col1, col2 = st.columns([1, 2])
        with col1:
            user_input = st.text_input("Password", type="password", label_visibility="collapsed",
                                       placeholder="Enter password")
            if st.button("Unlock"):
                if user_input == password:
                    st.session_state["authenticated"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password")
    return False

if not _check_password():
    st.stop()

# --- End password gate ---

def _is_valid_image_url(url):
    return bool(url) and url not in (None, "None", "") and (url.startswith("http://") or url.startswith("https://"))

conn = get_db()
init_db(conn)
seed_database(conn)

SPEC_CATEGORIES = {
    "Physical": ["payload_capacity", "payload_capacity_metric", "dimensions", "weight",
                  "max_shelf_size", "rotation_diameter", "robot_weight", "max_package_size"],
    "Performance": ["max_speed", "max_speed_with_load", "max_speed_no_load", "throughput",
                     "lift_time", "stop_accuracy", "acceleration", "lift_speed",
                     "max_operating_height", "max_lift_height", "storage_density"],
    "Power": ["battery_life", "charge_time", "power_consumption", "battery_type",
               "voltage_nominal", "charge_current_max"],
    "Operational": ["deployment_time", "navigation_type", "operating_temp_range",
                     "operating_humidity", "uptime", "gripper_type"],
    "Business": ["business_model", "typical_cost", "fleet_size_supported",
                  "wms_integration", "certification"],
}
NUMERIC_SPECS = ["payload_capacity_metric", "max_speed", "max_speed_with_load",
                  "throughput", "battery_life", "charge_time", "max_operating_height",
                  "max_lift_height", "lift_time", "storage_density", "uptime"]

def favicon_html(domain, size=16):
    return f'<img src="https://www.google.com/s2/favicons?domain={domain}&sz={size}" width="{size}" height="{size}" style="vertical-align:middle;margin-right:4px">'

def product_img_html(url, alt="", max_width=120):
    if url and url.strip() and url != "None":
        return f'<img src="{url}" alt="{alt}" style="max-width:{max_width}px;max-height:90px;border-radius:6px;object-fit:contain;margin-right:14px" onerror="this.style.display=\'none\'">'
    return f'<div style="width:{max_width}px;height:80px;border-radius:6px;background:rgba(128,128,128,0.08);display:flex;align-items:center;justify-content:center;margin-right:14px;font-size:2.5em">🤖</div>'

def spec_value_to_float(spec_value, spec_name):
    import re
    val = str(spec_value).replace(",", "").strip()
    ranges = re.findall(r'[\d.]+', val)
    if ranges:
        nums = [float(v) for v in ranges]
        return sum(nums) / len(nums)
    return None

def product_card_html(product, specs, capabilities):
    html = f"""
    <div style="border:1px solid rgba(128,128,128,0.2);border-radius:8px;padding:16px;margin-bottom:12px;
                box-shadow:0 1px 3px rgba(0,0,0,0.08)">
    <div style="display:flex;gap:14px;align-items:flex-start">
    {product_img_html(product.get("image_url", ""), product.get("name", ""))}
    <div style="flex:1;min-width:0">
    """
    domain = urlparse(product.get("product_url", "")).netloc or "example.com"
    html += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">'
    html += favicon_html(domain, 20)
    html += f'<strong style="font-size:1.1em">{product["company_name"]}</strong>'
    html += f'<span> — </span>'
    html += f'<span style="font-size:1.1em">{product["name"]}</span>'
    html += status_badge_html(product.get("status", "current"))
    html += f'</div>'
    html += f'<div style="font-size:0.9em;margin-bottom:8px;opacity:0.85">{product.get("description", "")[:200]}...</div>'
    html += '<div style="display:flex;flex-wrap:wrap;gap:8px">'
    for s in specs[:6]:
        html += f'<span style="background:rgba(128,128,128,0.1);border-radius:4px;padding:2px 8px;font-size:0.85em">'
        html += f'<strong>{s["spec_name"]}:</strong> {s["spec_value"]}</span>'
    html += '</div>'
    if capabilities:
        html += '<div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:4px">'
        for cap in capabilities:
            html += f'<span style="background:rgba(0,100,150,0.12);border-radius:4px;padding:1px 6px;font-size:0.8em;color:var(--text-color)">{cap["name"]}</span>'
        html += '</div>'
    html += '</div></div></div>'
    return html

def company_card_html(company):
    domain = urlparse(company["website"]).netloc if company["website"] else ""
    html = f"""
    <div style="border:1px solid rgba(128,128,128,0.2);border-radius:8px;padding:16px;margin-bottom:12px;
                box-shadow:0 1px 3px rgba(0,0,0,0.08)">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
    """
    if domain:
        html += favicon_html(domain, 20)
    html += f'<strong style="font-size:1.15em">{company["name"]}</strong>'
    html += status_badge_html(company.get("status", "active"))
    html += '</div>'
    html += f'<div style="font-size:0.9em;margin-bottom:6px;opacity:0.85">{company.get("short_description", "")}</div>'
    html += f'<div style="font-size:0.85em;opacity:0.7">'
    if company.get("headquarters"):
        html += f'📍 {company["headquarters"]}'
    elif company.get("country"):
        html += f'📍 {company["country"]}'
    if company.get("country"):
        html += f' · {company["country"]}'
    if company.get("founded_year"):
        html += f' · Founded {company["founded_year"]}'
    if company.get("founded_year"):
        html += f' · Founded {company["founded_year"]}'
    if company.get("business_model"):
        html += f' · {company["business_model"]}'
    html += '</div>'
    html += '</div>'
    return html

def status_badge_html(status):
    if not status or status in (None, "None", "active", "current"):
        return ""
    colors = {"acquired": "rgba(180,120,0,0.15)", "division": "rgba(0,100,180,0.15)",
              "defunct": "rgba(180,0,0,0.12)", "rebranded": "rgba(100,100,180,0.15)",
              "discontinued": "rgba(180,80,0,0.15)", "legacy": "rgba(120,120,120,0.15)",
              "acquired_product": "rgba(180,120,0,0.15)"}
    bg = colors.get(status, "rgba(128,128,128,0.1)")
    label = status.replace("_", " ").title()
    return f'<span style="background:{bg};border-radius:4px;padding:1px 7px;font-size:0.75em;margin-left:6px;vertical-align:middle">{label}</span>'

tabs = st.tabs(["Insights", "Compare", "Companies", "Products", "Case Studies", "Network", "Manage"])

with tabs[0]:
    st.subheader("Industry Insights")
    st.markdown("Synthesized metrics across all companies, products, and relationships in the robotics landscape.")

    # --- 1. Summary KPIs ---
    kpis = get_insight_summary_kpis(conn)
    kpi_cols = st.columns(len(kpis))
    for i, (label, val) in enumerate(kpis):
        with kpi_cols[i]:
            st.metric(label, val)

    # --- 2. Companies Overview ---
    with st.expander("🌍 Companies Overview", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            by_country = get_insight_company_counts(conn, "country")
            if by_country:
                df_c = pd.DataFrame(by_country, columns=["country", "count"])
                fig = px.pie(df_c, names="country", values="count", title="Companies by Country")
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            by_bmodel = get_insight_business_model_counts(conn)
            if by_bmodel:
                df_bm = pd.DataFrame(by_bmodel, columns=["model", "count"])
                fig = px.bar(df_bm, x="count", y="model", orientation="h", title="Business Model")
                st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            founding_hist = get_insight_founding_year_histogram(conn)
            if founding_hist:
                df_f = pd.DataFrame(founding_hist, columns=["year", "count"])
                fig = px.bar(df_f, x="year", y="count", title="Founding Year Distribution")
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            by_status = get_insight_status_counts(conn)
            if by_status:
                df_s = pd.DataFrame(by_status, columns=["status", "count"])
                fig = px.pie(df_s, names="status", values="count", title="Company Status")
                st.plotly_chart(fig, use_container_width=True)

    # --- 3. Products & Capabilities ---
    with st.expander("📦 Products & Capabilities", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            by_cat = get_insight_products_by_category(conn)
            if by_cat:
                df_pc = pd.DataFrame(by_cat, columns=["category", "count"])
                fig = px.bar(df_pc, x="category", y="count", title="Products by Category")
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            release_hist = get_insight_release_year_histogram(conn)
            if release_hist:
                df_r = pd.DataFrame(release_hist, columns=["year", "count"])
                fig = px.bar(df_r, x="year", y="count", title="Product Release Year Distribution")
                st.plotly_chart(fig, use_container_width=True)

        cov = get_insight_capability_coverage(conn)
        if cov:
            df_cap = pd.DataFrame(cov, columns=["capability", "count"])
            fig = px.bar(df_cap, x="count", y="capability", orientation="h",
                         title="Top Capabilities by Product Count")
            st.plotly_chart(fig, use_container_width=True)

        spec_keys = ["payload_capacity_metric", "max_speed", "throughput", "max_operating_height"]
        spec_avgs = get_insight_spec_averages_by_category(conn, spec_keys)
        if spec_avgs:
            df_sa = pd.DataFrame(spec_avgs)
            fig = px.bar(df_sa, x="category", y="avg_val", color="spec_key",
                         barmode="group", title="Avg Spec Values by Category")
            st.plotly_chart(fig, use_container_width=True)

    # --- 4. Engineering & Talent ---
    with st.expander("👥 Engineering & Talent", expanded=False):
        eng = get_insight_engineering_percent(conn)
        if eng:
            df_eng = pd.DataFrame(eng)
            fig = px.bar(df_eng.head(20), x="engineering_pct", y="name", orientation="h",
                         title="Engineering % of Workforce (Top 20)")
            st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                fig = px.scatter(df_eng, x="emp_numeric", y="eng_numeric",
                                 hover_name="name", title="Engineering Headcount vs Total Employees")
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                eng_by_cat = get_insight_engineering_by_category(conn)
                if eng_by_cat:
                    df_ec = pd.DataFrame(eng_by_cat)
                    fig = px.bar(df_ec, x="category", y="avg_eng_pct",
                                 title="Avg Engineering % by Product Category")
                    st.plotly_chart(fig, use_container_width=True)

    # --- 5. Storage & Bin Types ---
    with st.expander("🗄️ Storage & Bin Types", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            bin_types = get_insight_bin_type_counts(conn)
            if bin_types:
                df_bt = pd.DataFrame(bin_types, columns=["bin_type", "count"])
                fig = px.bar(df_bt, x="bin_type", y="count", title="Bin Types by Count")
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            payload_hist = get_insight_payload_histogram(conn)
            if payload_hist:
                df_ph = pd.DataFrame(payload_hist)
                fig = px.bar(df_ph, x="max_payload_kg", y="product_name", color="bin_type",
                             orientation="h", title="Max Payload by Product",
                             hover_data=["label"])
                st.plotly_chart(fig, use_container_width=True)

        grid = get_insight_grid_heights(conn)
        if grid:
            df_g = pd.DataFrame(grid)
            fig = px.bar(df_g, x="grid_height_m", y="product_name", color="label",
                         orientation="h", title="Grid Height by Product")
            st.plotly_chart(fig, use_container_width=True)

        bins_detail = get_insight_bins_detail(conn)
        if bins_detail:
            df_bd = pd.DataFrame(bins_detail)
            cols = ["product_name", "category", "bin_type", "label",
                    "outer_length_mm", "outer_width_mm", "outer_height_mm",
                    "max_payload_kg", "grid_height_m"]
            df_bd = df_bd[[c for c in cols if c in df_bd.columns]]
            st.dataframe(df_bd, use_container_width=True)

    # --- 6. Case Study Insights ---
    with st.expander("📋 Case Study Insights", expanded=False):
        # --- KPIs for metrics ---
        metric_names = get_metric_names(conn)
        if metric_names:
            kpi_map = {}
            for r in metric_names:
                kpi_map[r["metric_name"]] = r
            m1, m2, m3, m4, m5 = st.columns(5)
            if "picks_per_hour" in kpi_map:
                r = kpi_map["picks_per_hour"]
                m1.metric("Picks/hr (peak)", f"{r['max_val']:.0f}", f"{r['count']} case(s)")
            if "throughput_multiplier" in kpi_map:
                r = kpi_map["throughput_multiplier"]
                m2.metric("Throughput (peak)", f"{r['max_val']:.0f}x", f"{r['count']} case(s)")
            if "storage_density_multiplier" in kpi_map:
                r = kpi_map["storage_density_multiplier"]
                m3.metric("Density Gain (peak)", f"{r['max_val']:.0f}x", f"{r['count']} case(s)")
            if "roi_months" in kpi_map:
                r = kpi_map["roi_months"]
                sm = get_case_study_metric_summary(conn, "roi_months")
                avg_roi = sm[0]["avg_val"] if sm else r["max_val"]
                m4.metric("Avg ROI", f"{avg_roi:.0f}m", f"{r['count']} case(s)")
            if "robots_deployed" in kpi_map:
                r = kpi_map["robots_deployed"]
                m5.metric("Max Fleet", f"{r['max_val']:,.0f}", f"{r['count']} case(s)")

        # --- Existing charts ---
        col1, col2 = st.columns(2)
        with col1:
            cs_by_industry = get_insight_case_studies_by_industry(conn)
            if cs_by_industry:
                df_csi = pd.DataFrame(cs_by_industry, columns=["industry", "count"])
                fig = px.bar(df_csi, x="count", y="industry", orientation="h",
                             title="Case Studies by Industry")
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            top_cust = get_insight_top_customers(conn)
            if top_cust:
                df_tc = pd.DataFrame(top_cust, columns=["customer", "count"])
                fig = px.bar(df_tc, x="count", y="customer", orientation="h",
                             title="Top Customers")
                st.plotly_chart(fig, use_container_width=True)

        cs_by_comp = get_insight_case_studies_by_company(conn)
        if cs_by_comp:
            df_csc = pd.DataFrame(cs_by_comp)
            fig = px.bar(df_csc, x="cs_count", y="company", orientation="h",
                         title="Case Studies by Company")
            st.plotly_chart(fig, use_container_width=True)

        st.divider()
        st.markdown("##### 📊 Extracted Metrics")

        # --- Throughput chart ---
        throughput_metrics = ["picks_per_hour", "cases_per_hour", "bins_per_hour", "items_per_hour"]
        tp_data = []
        for m in throughput_metrics:
            rows = get_case_study_metrics(conn, metric_name=m)
            for r in rows:
                if r.get("metric_value_num"):
                    tp_data.append({
                        "company": r["company_name"],
                        "metric": m.replace("_per_hour", "/hr").replace("_", " ").title(),
                        "value": r["metric_value_num"],
                        "unit": r["unit"],
                    })
        if tp_data:
            df_tp = pd.DataFrame(tp_data)
            fig = px.bar(df_tp, x="value", y="company", color="metric",
                         barmode="group", orientation="h",
                         title="Throughput Metrics (picks/cases/bins per hour)")
            st.plotly_chart(fig, use_container_width=True)

        # --- Multipliers chart ---
        mult_metrics = ["picking_efficiency_multiplier", "throughput_multiplier",
                        "storage_density_multiplier", "productivity_multiplier"]
        mult_data = []
        for m in mult_metrics:
            rows = get_case_study_metrics(conn, metric_name=m)
            for r in rows:
                if r.get("metric_value_num"):
                    mult_data.append({
                        "company": r["company_name"],
                        "metric": m.replace("_multiplier", "").replace("_", " ").title(),
                        "value": r["metric_value_num"],
                        "unit": "x",
                    })
        if mult_data:
            df_md = pd.DataFrame(mult_data)
            fig = px.bar(df_md, x="value", y="company", color="metric",
                         barmode="group", orientation="h",
                         title="Productivity & Density Multipliers (x improvement)")
            fig.update_layout(xaxis_title="Multiplier (x)")
            st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            # --- Accuracy / Uptime ---
            acc_data = []
            for m in ["uptime_pct", "inventory_accuracy_pct", "delivery_reliability_pct", "pick_rate_pct"]:
                rows = get_case_study_metrics(conn, metric_name=m)
                for r in rows:
                    if r.get("metric_value_num"):
                        acc_data.append({
                            "company": r["company_name"],
                            "metric": m.replace("_pct", "").replace("_", " ").title(),
                            "value": r["metric_value_num"],
                        })
            if acc_data:
                df_acc = pd.DataFrame(acc_data)
                fig = px.bar(df_acc, x="value", y="company", color="metric",
                             barmode="group", orientation="h",
                             title="Accuracy, Uptime & Reliability (%)")
                fig.update_layout(xaxis_title="%", xaxis_range=[90, 100])
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # --- ROI / Payback ---
            roi_data = get_case_study_metrics(conn, metric_name="roi_months")
            if roi_data:
                df_roi = pd.DataFrame(roi_data)
                fig = px.bar(df_roi, x="metric_value_num", y="company_name",
                             orientation="h", title="ROI / Payback Period (months)",
                             hover_data=["metric_value_text"])
                fig.update_layout(xaxis_title="Months")
                st.plotly_chart(fig, use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            # --- Scale: Robots Deployed vs SKUs ---
            robots_data = get_case_study_metrics(conn, metric_name="robots_deployed")
            skus_data = get_case_study_metrics(conn, metric_name="sku_count")
            scale_data = []
            for r in robots_data:
                if r.get("metric_value_num"):
                    scale_data.append({
                        "company": r["company_name"],
                        "metric": "Robots Deployed",
                        "value": r["metric_value_num"],
                    })
            for r in skus_data:
                if r.get("metric_value_num"):
                    scale_data.append({
                        "company": r["company_name"],
                        "metric": "SKU Count",
                        "value": r["metric_value_num"],
                    })
            if scale_data:
                df_scale = pd.DataFrame(scale_data)
                fig = px.bar(df_scale, x="value", y="company", color="metric",
                             barmode="group", orientation="h",
                             title="Operational Scale (Robots & SKUs)")
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            # --- Floor Space Savings ---
            floor_data = get_case_study_metrics(conn, metric_name="floor_space_reduction_pct")
            if floor_data:
                df_floor = pd.DataFrame(floor_data)
                fig = px.bar(df_floor, x="metric_value_num", y="company_name",
                             orientation="h", title="Floor Space Reduction (%)",
                             hover_data=["metric_value_text"])
                fig.update_layout(xaxis_title="% Reduction")
                st.plotly_chart(fig, use_container_width=True)

        # --- Retrieval / Process Time ---
        time_data = []
        for m in ["retrieval_time_seconds", "process_time_minutes"]:
            rows = get_case_study_metrics(conn, metric_name=m)
            for r in rows:
                if r.get("metric_value_num"):
                    time_data.append({
                        "company": r["company_name"],
                        "metric": "Retrieval (s)" if "second" in str(r.get("unit", "")) else "Process (min)",
                        "value": r["metric_value_num"],
                    })
        if time_data:
            df_time = pd.DataFrame(time_data)
            fig = px.bar(df_time, x="value", y="company", color="metric",
                         barmode="group", orientation="h",
                         title="Retrieval & Process Times")
            st.plotly_chart(fig, use_container_width=True)

        # --- Inferred metrics ---
        inferred_metrics = ["items_per_case", "units_per_sqft", "bins_per_hour_per_robot",
                           "storage_per_throughput_ratio", "skus_per_robot"]
        inf_labels = {
            "items_per_case": "Items per Case",
            "units_per_sqft": "Units per Sq Ft",
            "bins_per_hour_per_robot": "Bins/hr/Robot",
            "storage_per_throughput_ratio": "Storage:Throughput Ratio",
            "skus_per_robot": "SKUs per Robot",
        }
        inf_data = []
        for m in inferred_metrics:
            rows = get_case_study_metrics(conn, metric_name=m)
            for r in rows:
                if r.get("metric_value_num"):
                    inf_data.append({
                        "company": r["company_name"],
                        "metric": inf_labels.get(m, m),
                        "value": r["metric_value_num"],
                        "unit": r.get("unit", ""),
                        "source": r.get("source", ""),
                    })
        if inf_data:
            st.markdown("##### 🔍 Inferred / Calculated Metrics")
            df_inf = pd.DataFrame(inf_data)
            fig = px.bar(df_inf, x="value", y="company", color="metric",
                         barmode="group", orientation="h",
                         title="Inferred Metrics (calculated from available data)",
                         hover_data=["source"])
            st.plotly_chart(fig, use_container_width=True)

        # --- Metric Coverage ---
        coverage = get_metric_coverage(conn)
        if coverage:
            st.markdown("##### 📋 Metric Coverage by Company")
            df_cov = pd.DataFrame(coverage)
            pivot = df_cov.pivot_table(
                index="company", columns="metric_name",
                values="source", aggfunc=lambda x: "✓" if "parsed" in list(x) or "inferred" in list(x) else " "
            ).fillna("")
            # Reorder columns: parsed first, then inferred
            col_order = [c for c in pivot.columns if any(
                m in c for m in ["per_hour", "per_day", "multiplier", "_pct", "deployed", "count", "months", "seconds", "minutes", "mps"]
            )]
            col_order += [c for c in pivot.columns if c not in col_order]
            pivot = pivot[[c for c in col_order if c in pivot.columns]]
            # Color-code
            def _style_val(v):
                if v == "✓":
                    return "background-color: #d4edda; color: #155724"
                return ""
            st.dataframe(pivot.style.applymap(_style_val), use_container_width=True)

    # --- 7. Network & Relationships ---
    with st.expander("🔗 Network & Relationships", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            assoc_types = get_insight_association_type_counts(conn)
            if assoc_types:
                df_at = pd.DataFrame(assoc_types, columns=["type", "count"])
                fig = px.bar(df_at, x="count", y="type", orientation="h",
                             title="Associations by Type")
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            most_conn = get_insight_most_connected(conn)
            if most_conn:
                df_mc = pd.DataFrame(most_conn)
                fig = px.bar(df_mc, x="connection_count", y="name", orientation="h",
                             title="Most Connected Companies")
                st.plotly_chart(fig, use_container_width=True)

        academic = get_insight_academic_origins(conn)
        if academic:
            df_ac = pd.DataFrame(academic)
            univ_counts = df_ac.groupby("university").size().reset_index(name="count").sort_values("count", ascending=False)
            fig = px.bar(univ_counts, x="count", y="university",
                         orientation="h", title="Academic Origins")
            st.plotly_chart(fig, use_container_width=True)

    # --- 8. People & Leadership ---
    with st.expander("👤 People & Leadership", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            by_company = get_insight_people_by_company(conn)
            if by_company:
                df_pc = pd.DataFrame(by_company)
                fig = px.bar(df_pc, x="people_count", y="company", orientation="h",
                             title="People by Company")
                st.plotly_chart(fig, use_container_width=True)
        with col2:
            roles = get_insight_role_distribution(conn)
            if roles:
                df_rd = pd.DataFrame(roles, columns=["role", "count"])
                fig = px.pie(df_rd, names="role", values="count", title="Role Distribution")
                st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.subheader("Product Comparison")

    all_products_for_compare = get_all_products(conn)
    if not all_products_for_compare:
        st.info("No products in database yet. Use the Manage tab to add some.")
    else:
        categories = sorted(set(p["category"] for p in all_products_for_compare if p.get("category")))
        col_cat, col_ps, _ = st.columns([1, 1, 2])
        with col_cat:
            selected_cat = st.selectbox("Filter by category", ["All"] + categories, key="compare_cat")
        with col_ps:
            prod_statuses = get_product_statuses(conn)
            ps_opts_comp = {"All Statuses": None}
            ps_opts_comp.update({s.replace("_", " ").title(): s for s in prod_statuses})
            selected_ps = st.selectbox("Product Status", list(ps_opts_comp.keys()), key="compare_ps")

        filtered_products = all_products_for_compare
        if selected_cat != "All":
            filtered_products = [p for p in filtered_products if p["category"] == selected_cat]
        if selected_ps != "All Statuses":
            filtered_products = [p for p in filtered_products if p.get("status", "current") == ps_opts_comp[selected_ps]]

        product_options = {f"{p['company_name']} — {p['name']}": p["id"] for p in filtered_products}
        selected_names = st.multiselect(
            "Select products to compare",
            options=list(product_options.keys()),
            max_selections=8,
            placeholder="Choose 2-8 products...",
        )

        if len(selected_names) >= 2:
            selected_ids = [product_options[n] for n in selected_names]
            compare_products_list, all_spec_keys = compare_products(conn, selected_ids)

            st.markdown("### Side-by-Side Spec Comparison")
            spec_data = {s: {} for s in all_spec_keys}
            spec_units = {}

            for item in compare_products_list:
                p = item["product"]
                label = f"{p['company_name']} {p['name']}"
                for s in item["specs"]:
                    if s["spec_name"] in spec_data:
                        val = s["spec_value"]
                        if s["unit"]:
                            val += f" {s['unit']}"
                        spec_data[s["spec_name"]][label] = val
                        if s["unit"]:
                            spec_units[s["spec_name"]] = s["unit"]

            df_specs = pd.DataFrame(spec_data).T
            df_specs.index.name = "Specification"
            st.dataframe(df_specs, use_container_width=True)

            chart_specs = []
            for sk in all_spec_keys:
                vals = []
                for item in compare_products_list:
                    for s in item["specs"]:
                        if s["spec_name"] == sk:
                            fv = spec_value_to_float(s["spec_value"], sk)
                            if fv is not None:
                                vals.append(fv)
                            break
                if len(vals) == len(selected_ids) and all(v > 0 for v in vals):
                    chart_specs.append(sk)

            if len(chart_specs) >= 3:
                st.markdown("### Radar Chart")
                radar_labels = []
                for sk in chart_specs:
                    label = sk.replace("_", " ").title()
                    if sk in spec_units:
                        label += f" ({spec_units[sk]})"
                    radar_labels.append(label)

                radar_df = pd.DataFrame()
                for item in compare_products_list:
                    p = item["product"]
                    label = f"{p['company_name']} {p['name']}"
                    row = {}
                    for sk in chart_specs:
                        for s in item["specs"]:
                            if s["spec_name"] == sk:
                                fv = spec_value_to_float(s["spec_value"], sk)
                                row[sk] = fv
                                break
                    radar_df[label] = pd.Series(row)

                radar_df.index = radar_labels
                radar_df_t = radar_df.T

                fig = go.Figure()
                for idx, row in radar_df_t.iterrows():
                    fig.add_trace(go.Scatterpolar(
                        r=row.values.tolist() + [row.values[0]],
                        theta=radar_labels + [radar_labels[0]],
                        name=idx,
                        fill='toself',
                        opacity=0.6,
                    ))
                fig.update_layout(
                    polar=dict(radialaxis=dict(visible=True)),
                    height=500,
                    margin=dict(l=80, r=80, t=20, b=20),
                )
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Capabilities Comparison")
            cap_data = {}
            for item in compare_products_list:
                p = item["product"]
                label = f"{p['company_name']} {p['name']}"
                caps = get_product_capabilities(conn, p["id"])
                cap_data[label] = {c["name"]: True for c in caps}

            all_caps = set()
            for v in cap_data.values():
                all_caps.update(v.keys())
            all_caps = sorted(all_caps)

            cap_rows = []
            for cap in all_caps:
                row = {"Capability": cap}
                for label in cap_data:
                    row[label] = "✅" if cap in cap_data[label] else "—"
                cap_rows.append(row)
            if cap_rows:
                st.dataframe(pd.DataFrame(cap_rows), use_container_width=True)
        else:
            st.info("Select at least 2 products to see a comparison.")

with tabs[2]:
    st.subheader("Companies")

    company_statuses = get_company_statuses(conn)
    status_opts = {"All Statuses": None}
    status_opts.update({s.replace("_", " ").title(): s for s in company_statuses})

    company_types = get_company_types(conn)
    type_opts = {"All Types": None}
    for t in company_types:
        type_opts[t.replace("_", " ").title()] = t

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        sel_cs = st.selectbox("Company Status", list(status_opts.keys()), key="cs_filter_company_status")
    with col_f2:
        sel_ct = st.selectbox("Company Type", list(type_opts.keys()), key="cs_filter_company_type")
    with col_f3:
        countries = get_company_countries(conn)
        country_opts = {"All Countries": None}
        for c in countries:
            if c:
                country_opts[c] = c
        sel_country = st.selectbox("Country", list(country_opts.keys()), key="cs_filter_country")

    companies = get_all_companies(conn, status=status_opts[sel_cs])
    sel_ct_val = type_opts[sel_ct]
    if sel_ct_val:
        companies = [c for c in companies if c.get("company_type") == sel_ct_val]
    sel_country_val = country_opts[sel_country]
    if sel_country_val:
        companies = [c for c in companies if c.get("country") == sel_country_val]

    for comp in companies:
        domain = urlparse(comp["website"]).netloc if comp["website"] else ""
        comp_status = comp.get("status", "active")
        status_label = "" if comp_status in (None, "None", "active") else f" [{comp_status.replace('_', ' ').title()}]"
        with st.expander(f"**{comp['name']}**{status_label}  ", expanded=False):
            col1, col2 = st.columns([2, 1])
            with col1:
                if domain:
                    st.markdown(f"{favicon_html(domain, 20)} [{comp['website']}]({comp['website']})",
                                unsafe_allow_html=True)
                st.markdown(comp.get("description", ""))
                products = get_company_products(conn, comp["id"])
                if products:
                    st.markdown("#### Products")
                    for prod in products:
                        p_domain = urlparse(prod["product_url"]).netloc if prod.get("product_url") else domain
                        st.markdown(f"{favicon_html(p_domain, 14)} **{prod['name']}** — {prod.get('description', '')[:150]}",
                                    unsafe_allow_html=True)
            with col2:
                details = []
                if comp.get("country"):
                    details.append(f"**Country:** {comp['country']}")
                if comp.get("headquarters"):
                    details.append(f"**HQ:** {comp['headquarters']}")
                if comp.get("founded_year"):
                    details.append(f"**Founded:** {comp['founded_year']}")
                if comp.get("business_model"):
                    details.append(f"**Model:** {comp['business_model']}")
                if comp.get("funding_total_usd"):
                    details.append(f"**Funding:** {comp['funding_total_usd']}")
                if comp.get("employees"):
                    details.append(f"**Employees:** {comp['employees']}")
                if comp.get("engineering_pct"):
                    details.append(f"**Engineering:** {comp['engineering_pct']} of workforce")
                for d in details:
                    st.markdown(d)

with tabs[3]:
    st.subheader("Products")

    all_products = get_all_products(conn)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        companies_list = get_all_companies(conn)
        comp_names = ["All Companies"] + [c["name"] for c in companies_list]
        filter_company = st.selectbox("Company", comp_names, key="filter_company")
    with col_f2:
        categories = sorted(set(p["category"] for p in all_products if p.get("category")))
        cat_names = ["All Categories"] + categories
        filter_category = st.selectbox("Category", cat_names, key="filter_category")
    with col_f3:
        prod_statuses = get_product_statuses(conn)
        ps_opts = {"All Statuses": None}
        ps_opts.update({s.replace("_", " ").title(): s for s in prod_statuses})
        filter_status = st.selectbox("Product Status", list(ps_opts.keys()), key="filter_product_status")

    search_text = st.text_input("Search products", placeholder="Search by name or description...")

    filtered = all_products
    if filter_company != "All Companies":
        filtered = [p for p in filtered if p["company_name"] == filter_company]
    if filter_category != "All Categories":
        filtered = [p for p in filtered if p["category"] == filter_category]
    if filter_status != "All Statuses":
        filtered = [p for p in filtered if p.get("status", "current") == ps_opts[filter_status]]
    if search_text:
        stext = search_text.lower()
        filtered = [p for p in filtered if stext in p["name"].lower() or stext in (p.get("description") or "").lower()]

    if not filtered:
        st.info("No products match your filters.")
    else:
        st.markdown(f"**{len(filtered)}** product{'s' if len(filtered)!=1 else ''} found")
        for p in filtered:
            specs = get_product_display_specs(conn, p["id"], include_common=False)
            caps = get_product_capabilities(conn, p["id"])
            html = product_card_html(p, specs, caps)
            st.markdown(html, unsafe_allow_html=True)

with tabs[4]:
    st.subheader("Case Studies")
    st.markdown("Real-world deployment case studies across the robotics industry.")

    cs_stats = get_case_studies_stats(conn)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Case Studies", cs_stats.get("total", 0))
    col2.metric("Industries", cs_stats.get("industries", 0))
    col3.metric("Companies", cs_stats.get("companies", 0))
    col4.metric("Products Featured", cs_stats.get("products_featured", 0))

    cs_tabs = st.tabs(["Browse", "Search", "By Industry"])

    with cs_tabs[0]:
        companies_list = get_all_companies(conn)
        co_opts = {"All Companies": None}
        co_opts.update({c["name"]: c["id"] for c in companies_list})
        filter_company = st.selectbox("Filter by company", list(co_opts.keys()), key="cs_company_filter")
        company_id = co_opts[filter_company]

        cs_list = get_all_case_studies(conn, company_id=company_id)
        if not cs_list:
            st.info("No case studies found.")
        for cs in cs_list:
            with st.expander(f"{cs['title']}"):
                st.markdown(f"""
                <div style="margin-bottom:8px">
                    <span style="background:rgba(0,100,150,0.12);border-radius:4px;padding:2px 8px;font-size:0.85em">{cs['company_name']}</span>
                    <span style="background:rgba(100,100,100,0.1);border-radius:4px;padding:2px 8px;font-size:0.85em">{cs['industry'] or 'N/A'}</span>
                    <span style="background:rgba(100,180,100,0.12);border-radius:4px;padding:2px 8px;font-size:0.85em">{cs['customer'] or 'N/A'}</span>
                </div>
                """, unsafe_allow_html=True)
                if cs.get("product_name"):
                    st.markdown(f"**Product:** {cs['product_name']}")
                if cs.get("challenge"):
                    st.markdown("**Challenge**")
                    st.markdown(cs["challenge"])
                if cs.get("solution"):
                    st.markdown("**Solution**")
                    st.markdown(cs["solution"])
                if cs.get("results"):
                    st.markdown("**Results**")
                    st.markdown(cs["results"])
                if cs.get("metrics"):
                    st.markdown("**Key Metrics**")
                    for m in cs["metrics"].split("|"):
                        st.markdown(f"- {m.strip()}")
                if cs.get("url"):
                    st.markdown(f"[View full case study →]({cs['url']})")
                st.markdown("---")

    with cs_tabs[1]:
        search_q = st.text_input("Search case studies", placeholder="e.g., DHL, pallet, picking...")
        if search_q:
            results = search_case_studies(conn, search_q)
            if results:
                st.markdown(f"Found {len(results)} result(s):")
                for cs in results:
                    st.markdown(f"""
                    <div style="border:1px solid rgba(128,128,128,0.2);border-radius:8px;padding:12px;margin-bottom:8px">
                        <div style="display:flex;justify-content:space-between;align-items:center">
                            <strong>{cs['title']}</strong>
                            <span style="font-size:0.85em;opacity:0.7">{cs['company_name']}</span>
                        </div>
                        <div style="margin-top:4px;font-size:0.9em;opacity:0.85">{cs['customer']} · {cs['industry']}</div>
                        <div style="margin-top:4px;font-size:0.9em">{cs['results'][:200]}...</div>
                        <div style="margin-top:4px;font-size:0.85em">
                            <span style="background:rgba(0,100,150,0.12);border-radius:4px;padding:1px 6px">{cs['metrics'][:80]}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No results found.")

    with cs_tabs[2]:
        industries = get_case_study_industries(conn)
        ind_opts = {"All Industries": None}
        ind_opts.update({i: i for i in industries})
        sel_industry = st.selectbox("Select industry", list(ind_opts.keys()), key="cs_industry_filter")
        industry_val = ind_opts[sel_industry]

        by_industry_cs = get_all_case_studies(conn, industry=industry_val)
        for cs in by_industry_cs:
            st.markdown(f"""
            <div style="border:1px solid rgba(128,128,128,0.2);border-radius:8px;padding:12px;margin-bottom:8px">
                <strong>{cs['title']}</strong>
                <div style="margin-top:4px;font-size:0.9em;opacity:0.85">{cs['customer']} — {cs['company_name']}</div>
                <div style="margin-top:4px;font-size:0.9em">{cs['results'][:150]}...</div>
            </div>
            """, unsafe_allow_html=True)

with tabs[5]:
    st.subheader("Company Association Network")
    st.markdown("Interactive graph of company relationships — drag, zoom, and click nodes to explore.")

    associations = get_all_associations(conn)

    if not associations:
        st.info("No association data available yet.")
    else:
        type_colors = {
            "corporation": "#1E88E5",
            "educational": "#43A047",
            "investor": "#FB8C00",
            "parent": "#E53935",
            "customer": "#8E24AA",
            "person": "#FFD700",
        }
        type_shapes = {
            "corporation": "dot",
            "educational": "square",
            "parent": "triangle",
            "investor": "diamond",
            "customer": "dot",
            "person": "star",
        }

        # --- Network Settings ---
        all_type_options = ["corporation", "educational", "parent", "investor", "customer", "person"]
        type_labels = {"corporation": "Robotics Companies", "educational": "Universities",
                       "parent": "Parent Companies", "investor": "Investors",
                       "customer": "Customers", "person": "People / Leaders"}

        with st.expander("⚙️ Network Settings", expanded=False):
            with st.form("net_settings_form"):
                st.markdown("**Visible Node Types**")
                show_types = []
                type_cols = st.columns(6)
                for i, t in enumerate(all_type_options):
                    with type_cols[i]:
                        if st.checkbox(type_labels[t], value=True, key=f"show_{t}"):
                            show_types.append(t)
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    gravity = st.slider("Gravity (gravitationalConstant)", -10000, -500, -3000, step=100,
                                       help="More negative = stronger pull toward center")
                    spring_len = st.slider("Spacing (springLength)", 50, 500, 200, step=10,
                                          help="Preferred edge length in pixels")
                with col2:
                    spring_k = st.slider("Edge Stiffness (springConstant)", 0.001, 0.2, 0.04, step=0.005,
                                        help="Higher = tighter / springier edges")
                    damping = st.slider("Damping", 0.01, 0.5, 0.09, step=0.01,
                                       help="Motion damping; higher = less oscillation")
                with col3:
                    node_size = st.slider("Node Size", 8, 50, 20, step=2,
                                         help="Base node diameter in pixels")
                    iterations = st.slider("Stabilization Iterations", 50, 1000, 200, step=50,
                                          help="More iterations = more stable layout")
                st.form_submit_button("🔄 Update Graph", use_container_width=True)

        from pyvis.network import Network
        import tempfile, os

        net = Network(height="600px", width="100%", bgcolor="#1a1a2e", font_color="white")
        net.set_options(f"""
        var options = {{
          "physics": {{
            "stabilization": {{"iterations": {iterations}}},
            "barnesHut": {{"gravitationalConstant": {gravity}, "springLength": {spring_len}, "springConstant": {spring_k}, "damping": {damping}}}
          }},
          "edges": {{
            "smooth": {{"type": "continuous"}},
            "font": {{"size": 10, "color": "#aaaaaa"}},
            "color": {{"color": "#555555", "highlight": "#ffffff"}},
            "arrows": {{"to": {{"enabled": true, "scaleFactor": 0.5}}}}
          }},
          "nodes": {{
            "borderWidth": 2,
            "borderWidthSelected": 3,
            "font": {{"size": 14, "strokeWidth": 2, "strokeColor": "#1a1a2e"}}
          }},
          "interaction": {{
            "hover": true,
            "tooltipDelay": 200,
            "zoomView": true,
            "dragView": true,
            "dragNodes": true
          }}
        }}
        """)

        companies_info = {}
        for c in get_all_companies(conn):
            companies_info[c["name"]] = c

        added = set()
        for a in associations:
            c_name = a["company_name"]
            ac_name = a.get("associated_company_name") or a.get("association_name")

            def _should_show(name):
                ct = companies_info.get(name, {}).get("company_type", "corporation") or "corporation"
                return ct in show_types

            if c_name and c_name not in added and _should_show(c_name):
                ctype = companies_info.get(c_name, {}).get("company_type", "corporation") or "corporation"
                net.add_node(c_name, label=c_name, color=type_colors.get(ctype, "#1E88E5"),
                             shape=type_shapes.get(ctype, "dot"), size=node_size,
                             title=f"{c_name}<br>({ctype})")
                added.add(c_name)
            if ac_name and ac_name not in added and _should_show(ac_name):
                ctype = companies_info.get(ac_name, {}).get("company_type", "corporation") or "corporation"
                net.add_node(ac_name, label=ac_name, color=type_colors.get(ctype, "#1E88E5"),
                             shape=type_shapes.get(ctype, "dot"), size=max(node_size - 4, 8),
                             title=f"{ac_name}<br>({ctype})")
                added.add(ac_name)
            if c_name and ac_name and _should_show(c_name) and _should_show(ac_name):
                atype = a["association_type"].replace("_", " ")
                net.add_edge(c_name, ac_name, title=atype, label=atype,
                             color="#888888")

        # --- Add People nodes + person_roles edges ---
        if "person" in show_types:
            people_roles = get_all_person_roles(conn)
            for pr in people_roles:
                person_name = pr["person_name"]
                entity_name = pr.get("entity_name", "")
                role = pr.get("role", "")
                if person_name and person_name not in added:
                    net.add_node(person_name, label=person_name,
                                 color=type_colors["person"],
                                 shape=type_shapes["person"],
                                 size=max(node_size - 2, 10),
                                 title=f"{person_name}<br>({role})")
                    added.add(person_name)
                if person_name and entity_name and entity_name in added:
                    net.add_edge(person_name, entity_name, title=role, label=role,
                                 color="#FFD700")

        tmp = tempfile.NamedTemporaryFile(suffix=".html", delete=False)
        net.save_graph(tmp.name)
        with open(tmp.name, "r") as f:
            html_content = f.read()
        os.unlink(tmp.name)

        # Inject legend into the graph HTML
        legend_svg = '''
        <div style="position:absolute;top:16px;right:16px;z-index:1000;background:rgba(26,26,46,0.88);border:1px solid #555;border-radius:8px;padding:10px 14px;font:13px/1.9 Arial,sans-serif;color:#ccc;min-width:140px">
          <div style="font-weight:700;color:#fff;font-size:14px;margin-bottom:2px">Legend</div>
          <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#1E88E5;margin-right:7px;vertical-align:middle"></span>Corporation<br>
          <span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:#43A047;margin-right:7px;vertical-align:middle"></span>Educational<br>
          <span style="display:inline-block;width:10px;height:10px;background:#FB8C00;clip-path:polygon(50% 0%,100% 100%,0% 100%);margin-right:7px;vertical-align:middle"></span>Investor<br>
          <span style="display:inline-block;width:0;height:0;border-left:6px solid transparent;border-right:6px solid transparent;border-bottom:10px solid #E53935;margin-right:7px;vertical-align:middle"></span>Parent<br>
          <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#8E24AA;margin-right:7px;vertical-align:middle"></span>Customer<br>
          <span style="display:inline-block;width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:10px solid #FFD700;margin-right:7px;vertical-align:middle"></span>People / Leaders
          <div style="margin-top:5px;border-top:1px solid #444;padding-top:3px;font-size:11px;color:#888">
            <span style="display:inline-block;width:18px;height:2px;background:#777;margin-right:5px;vertical-align:middle"></span>→ relationship
          </div>
        </div>
        '''
        html_content = html_content.replace("<body>", "<body>" + legend_svg)

        st.components.v1.html(html_content, height=620)

        st.markdown("### Association Details")
        assoc_data = []
        for a in associations:
            target = a.get("associated_company_name") or a.get("association_name", "")
            assoc_data.append({
                "Company": a["company_name"],
                "Associated With": target,
                "Type": a["association_type"].replace("_", " ").title(),
                "Notes": a.get("notes", ""),
            })
        if assoc_data:
            st.dataframe(pd.DataFrame(assoc_data), use_container_width=True)

with tabs[6]:
    st.subheader("Manage")

    mgmt_tabs = st.tabs(["Companies", "Products", "Capabilities", "Scrape", "Associations", "Images", "Case Studies"])

    with mgmt_tabs[0]:
        st.markdown("#### Add Company")
        with st.form("add_company_form"):
            c_name = st.text_input("Company Name", placeholder="e.g., Pickle Robotics")
            c_slug = st.text_input("Slug", placeholder="e.g., pickle-robotics",
                                   help="URL-friendly identifier (lowercase, hyphens)")
            c_short = st.text_input("Short Description", placeholder="e.g., AI-powered truck unloading robots")
            c_desc = st.text_area("Full Description", height=120)
            c_website = st.text_input("Website URL", placeholder="https://...")
            c_hq = st.text_input("Headquarters", placeholder="City, State")
            c_country = st.text_input("Country", placeholder="e.g., USA, Germany, Japan")
            c_founded = st.number_input("Founded Year", min_value=1900, max_value=2026, value=2020, step=1)
            c_funding = st.text_input("Total Funding", placeholder="e.g., $50M+")
            c_bmodel = st.selectbox("Business Model", ["", "RaaS", "Purchase", "Hybrid", "RaaS / Hybrid", "Internal Use Only", "Public"])
            c_status = st.selectbox("Status", ["active", "acquired", "division", "defunct", "rebranded"])
            if st.form_submit_button("Add Company"):
                try:
                    conn.execute("""INSERT INTO companies (name, slug, short_description, description, website, headquarters, country,
                                    founded_year, funding_total_usd, business_model, status)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                 (c_name, c_slug or c_name.lower().replace(" ", "-"),
                                  c_short, c_desc, c_website or None,
                                  c_hq or None, c_country or None, c_founded or None,
                                  c_funding or None, c_bmodel or None, c_status))
                    conn.commit()
                    st.success(f"Added company: {c_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("#### Existing Companies")
        companies = get_all_companies(conn)
        for comp in companies:
            with st.expander(f"{comp['name']} (ID: {comp['id']})"):
                with st.form(f"edit_company_{comp['id']}"):
                    e_name = st.text_input("Name", value=comp["name"], key=f"ec_name_{comp['id']}")
                    e_short = st.text_input("Short Description", value=comp.get("short_description") or "",
                                            key=f"ec_short_{comp['id']}")
                    e_desc = st.text_area("Description", value=comp.get("description") or "", height=100,
                                          key=f"ec_desc_{comp['id']}")
                    e_website = st.text_input("Website", value=comp.get("website") or "",
                                             key=f"ec_web_{comp['id']}")
                    e_hq = st.text_input("HQ", value=comp.get("headquarters") or "", key=f"ec_hq_{comp['id']}")
                    e_country = st.text_input("Country", value=comp.get("country") or "", key=f"ec_country_{comp['id']}")
                    e_status = st.selectbox("Status", ["active", "acquired", "division", "defunct", "rebranded"],
                                            index=["active", "acquired", "division", "defunct", "rebranded"].index(comp.get("status", "active")) if comp.get("status", "active") in ["active", "acquired", "division", "defunct", "rebranded"] else 0,
                                            key=f"ec_status_{comp['id']}")
                    if st.form_submit_button("Update Company"):
                        conn.execute("""UPDATE companies SET name=?, short_description=?, description=?,
                                        website=?, headquarters=?, country=?, status=? WHERE id=?""",
                                     (e_name, e_short, e_desc, e_website or None, e_hq or None, e_country or None, e_status, comp["id"]))
                        conn.commit()
                        st.success("Updated!")
                        st.rerun()
                    if st.form_submit_button("Delete Company", type="secondary"):
                        conn.execute("DELETE FROM companies WHERE id=?", (comp["id"],))
                        conn.commit()
                        st.success("Deleted!")
                        st.rerun()

    with mgmt_tabs[1]:
        st.markdown("#### Add Product")
        companies_list = get_all_companies(conn)
        company_map = {c["name"]: c["id"] for c in companies_list}

        with st.form("add_product_form"):
            p_company = st.selectbox("Company", list(company_map.keys()))
            p_name = st.text_input("Product Name")
            p_slug = st.text_input("Slug (leave blank to auto-generate)")
            p_desc = st.text_area("Description", height=80)
            p_category = st.selectbox("Category", ["AMR", "ASRS", "Cube Storage", "Mobile Manipulation", "Robotic Arm", "Software"])
            p_url = st.text_input("Product URL", placeholder="https://...")
            p_img = st.text_input("Image URL", placeholder="https://... (optional)")
            p_year = st.number_input("Release Year", min_value=2000, max_value=2026, value=2024, step=1)
            p_status = st.selectbox("Product Status", ["current", "discontinued", "legacy", "rebranded", "acquired_product"])

            st.markdown("**Initial Specs (optional)**")
            spec_rows_val = []
            for i in range(5):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    sn = st.text_input(f"Spec name {i+1}", key=f"ps_name_{i}",
                                       placeholder="e.g., payload_capacity")
                with col2:
                    sv = st.text_input(f"Value {i+1}", key=f"ps_val_{i}",
                                       placeholder="e.g., 600")
                with col3:
                    su = st.text_input(f"Unit {i+1}", key=f"ps_unit_{i}",
                                       placeholder="kg")
                if sn and sv:
                    spec_rows_val.append((sn, sv, su))

            if st.form_submit_button("Add Product"):
                try:
                    slug = p_slug or p_name.lower().replace(" ", "-")
                    conn.execute("""INSERT INTO products (company_id, name, slug, description, category, product_url, image_url, release_year, status)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                                 (company_map[p_company], p_name, slug, p_desc, p_category, p_url or None, p_img or None, p_year, p_status))
                    prod_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                    for sn, sv, su in spec_rows_val:
                        if sn and sv:
                            conn.execute("INSERT INTO product_specs (product_id, spec_name, spec_value, unit) VALUES (?, ?, ?, ?)",
                                         (prod_id, sn, sv, su or None))
                    conn.commit()
                    st.success(f"Added product: {p_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("#### Existing Products")
        all_prods = get_all_products(conn)
        for prod in all_prods:
            with st.expander(f"{prod['company_name']} — {prod['name']}"):
                col_img, col_info = st.columns([1, 3])
                with col_img:
                    if _is_valid_image_url(prod.get("image_url")):
                        st.image(prod["image_url"], width=160)
                    else:
                        st.markdown("🤖")
                with col_info:
                    st.markdown(f"**Category:** {prod.get('category', 'N/A')}  ·  **Status:** {prod.get('status', 'current')}")
                    if prod.get("description"):
                        st.markdown(prod["description"])
                    img_url = st.text_input("Image URL", value=prod.get("image_url") or "",
                                            key=f"edit_img_{prod['id']}")
                    if st.button("Update Image", key=f"save_img_{prod['id']}"):
                        conn.execute("UPDATE products SET image_url=? WHERE id=?",
                                     (img_url or None, prod["id"]))
                        conn.commit()
                        st.success("Image updated!")
                        st.rerun()
                specs = get_product_specs(conn, prod["id"])
                if specs:
                    st.markdown("**Specs:**")
                    for s in specs:
                        val = s["spec_value"]
                        if s["unit"]:
                            val += f" {s['unit']}"
                        st.markdown(f"- {s['display_name']}: {val}")
                caps = get_product_capabilities(conn, prod["id"])
                if caps:
                    st.markdown("**Capabilities:** " + ", ".join(c["name"] for c in caps))

    with mgmt_tabs[2]:
        st.markdown("#### Capabilities")
        cap_cats = get_capability_categories(conn)
        for cat in cap_cats:
            st.markdown(f"**{cat}**")
            caps = [c for c in get_all_capabilities(conn, category=cat)]
            st.markdown(", ".join(c["name"] for c in caps))

        st.markdown("---")
        st.markdown("#### Add Capability")
        with st.form("add_cap_form"):
            cap_name = st.text_input("Capability Name")
            cap_desc = st.text_input("Description")
            cap_cat = st.selectbox("Category", ["Picking", "Storage", "Material Handling", "Receiving", "Shipping",
                                                  "Inventory", "Reverse Logistics", "Specialty"])
            if st.form_submit_button("Add Capability"):
                try:
                    conn.execute("INSERT INTO capabilities (name, description, category) VALUES (?, ?, ?)",
                                 (cap_name, cap_desc, cap_cat))
                    conn.commit()
                    st.success(f"Added capability: {cap_name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("#### Assign Capabilities to Products")
        all_prods = get_all_products(conn)
        prod_options = {f"{p['company_name']} — {p['name']}": p["id"] for p in all_prods}
        assign_prod = st.selectbox("Select Product", list(prod_options.keys()), key="assign_cap_prod")
        if assign_prod:
            pid = prod_options[assign_prod]
            current_caps = [c["id"] for c in get_product_capabilities(conn, pid)]
            all_avail_caps = get_all_capabilities(conn)
            cap_options = {f"{c['name']} ({c['category']})": c["id"] for c in all_avail_caps}
            selected_caps = st.multiselect(
                "Capabilities",
                options=list(cap_options.keys()),
                default=[k for k, v in cap_options.items() if v in current_caps],
                key="assign_caps_multi"
            )
            if st.button("Update Capabilities"):
                conn.execute("DELETE FROM product_capabilities WHERE product_id=?", (pid,))
                for cap_key in selected_caps:
                    conn.execute("INSERT INTO product_capabilities (product_id, capability_id) VALUES (?, ?)",
                                 (pid, cap_options[cap_key]))
                conn.commit()
                st.success("Capabilities updated!")

    with mgmt_tabs[3]:
        st.markdown("#### Product Images")
        st.markdown("Auto-discover product images using multi-strategy search (og:image, page scrape, DuckDuckGo).")

        all_prods = get_all_products(conn)
        missing = [p for p in all_prods if not p.get("image_url") or p["image_url"] in (None, "None", "")]
        has_img = [p for p in all_prods if p.get("image_url") and p["image_url"] not in (None, "None", "")]

        col1, col2 = st.columns(2)
        col1.metric("Total Products", len(all_prods))
        col2.metric("Missing Images", len(missing))

        if missing:
            st.markdown("##### Batch Scan")
            st.markdown(f"**{len(missing)}** products without images. Scan all at once:")

            if st.button("🔍 Scan All Missing Products", type="primary"):
                from scraper.base import batch_find_images
                progress_bar = st.progress(0, text="Scanning products...")
                status_text = st.empty()
                found_count = 0

                def on_progress(current, total, name, result):
                    progress_bar.progress(current / total)
                    if result:
                        status_text.markdown(f"✅ **{name}** — found via *{result['strategy']}*")
                    else:
                        status_text.markdown(f"❌ **{name}** — no image found")

                results = batch_find_images(missing, progress_callback=on_progress)
                progress_bar.empty()
                status_text.empty()

                if results:
                    saved = 0
                    for prod_id, url, strategy in results:
                        try:
                            conn.execute("UPDATE products SET image_url=? WHERE id=?", (url, prod_id))
                            conn.commit()
                            saved += 1
                        except Exception:
                            pass
                    st.success(f"Found and saved **{saved}** image{'s' if saved != 1 else ''}!")
                else:
                    st.warning("No images found via any strategy.")

                if len(results) < len(missing):
                    remaining = len(missing) - len(results)
                    st.info(f"{remaining} product{'s' if remaining != 1 else ''} still need images. Try individual search below.")

                st.rerun()

        st.markdown("##### Single Product Search")
        prod_opts = {f"{p['company_name']} — {p['name']}": p for p in all_prods}
        sel_prod = st.selectbox("Select product", list(prod_opts.keys()), key="scrape_img_prod")
        if sel_prod:
            prod = prod_opts[sel_prod]
            st.markdown(f"**Current image:**")
            if _is_valid_image_url(prod.get("image_url")):
                st.image(prod["image_url"], width=200)
            else:
                st.markdown("_No image set_ — will use robot emoji placeholder in cards_")

            if prod.get("product_url"):
                company = get_company(conn, prod["company_id"])
                company_url = company.get("website", "") if company else ""
                st.markdown(f"Product page: [{prod['product_url']}]({prod['product_url']})")
                if st.button("🔍 Find Image (Multi-Strategy)"):
                    from scraper.base import find_product_image_multi
                    with st.spinner("Searching via og:image, page scrape, company site, and DuckDuckGo..."):
                        result = find_product_image_multi(
                            prod["product_url"],
                            product_name=prod["name"],
                            company_name=prod["company_name"],
                            company_url=company_url
                        )
                        if result and _is_valid_image_url(result.get("url")):
                            st.success(f"Found via **{result['strategy']}**")
                            st.image(result["url"], width=200, caption="Found image")
                            if st.button("💾 Save This Image", key="save_found_img"):
                                conn.execute("UPDATE products SET image_url=? WHERE id=?",
                                             (result["url"], prod["id"]))
                                conn.commit()
                                st.success("Image saved!")
                                st.rerun()
                        else:
                            st.warning("No image found via any strategy. Try a DuckDuckGo search or paste a URL below.")

            st.markdown("##### DuckDuckGo Image Search")
            ddg_q = st.text_input("Search query", value=prod.get("name", ""),
                                  key="ddg_query", placeholder=f"e.g., {prod['company_name']} {prod['name']} robot")
            if st.button("🔎 Search DuckDuckGo"):
                import requests
                from bs4 import BeautifulSoup
                with st.spinner("Searching..."):
                    try:
                        resp = requests.post("https://html.duckduckgo.com/html/",
                                             data={"q": ddg_q}, timeout=10,
                                             headers={"User-Agent": "Mozilla/5.0"})
                        if resp.status_code == 200:
                            soup = BeautifulSoup(resp.text, "lxml")
                            results = soup.select(".result__body")
                            if results:
                                st.markdown("**Search results — click one to try image discovery:**")
                                for r in results[:8]:
                                    link = r.select_one(".result__a")
                                    snippet = r.select_one(".result__snippet")
                                    if link:
                                        href = link.get("href", "")
                                        title = link.get_text(strip=True)
                                        if href and "duckduckgo" not in href:
                                            key = f"ddg_{hash(href)}"
                                            if st.button(f"📷 {title[:80]}", key=key):
                                                from scraper.base import find_product_image_multi
                                                r2 = find_product_image_multi(
                                                    href,
                                                    product_name=prod["name"],
                                                    company_name=prod["company_name"],
                                                    company_url=company_url
                                                )
                                                if r2 and _is_valid_image_url(r2.get("url")):
                                                    st.image(r2["url"], width=200, caption=f"Found via {r2['strategy']}")
                                                    if st.button("💾 Save", key=f"save_ddg_{key}"):
                                                        conn.execute("UPDATE products SET image_url=? WHERE id=?",
                                                                     (r2["url"], prod["id"]))
                                                        conn.commit()
                                                        st.success("Saved!")
                                                        st.rerun()
                                                else:
                                                    st.info("No image found on that page. Try another result.")
                                            if snippet:
                                                st.caption(snippet.get_text(strip=True)[:120])
                            else:
                                st.warning("No search results found.")
                    except Exception as e:
                        st.error(f"Search error: {e}")

            st.markdown("##### Manual URL Entry")
            img_manual = st.text_input("Or paste an image URL directly", key="manual_img_url",
                                       placeholder="https://...")
            if st.button("Save Image URL", key="save_manual_img"):
                conn.execute("UPDATE products SET image_url=? WHERE id=?",
                             (img_manual or None, prod["id"]))
                conn.commit()
                st.success("Image saved!")
                st.rerun()

    with mgmt_tabs[4]:
        st.markdown("#### Associations")

        mgmt_assoc_tabs = st.tabs(["View All", "Add Association", "Discover from Wikipedia", "People", "Auto-Discovery"])

        with mgmt_assoc_tabs[0]:
            assocs = get_all_associations(conn)
            if assocs:
                data = []
                for a in assocs:
                    target = a.get("associated_company_name") or a.get("association_name", "")
                    data.append({
                        "Company": a["company_name"],
                        "Target": target,
                        "Type": a["association_type"].replace("_", " ").title(),
                        "Notes": a.get("notes", ""),
                    })
                st.dataframe(pd.DataFrame(data), use_container_width=True)
            else:
                st.info("No associations found.")

        with mgmt_assoc_tabs[1]:
            companies = get_all_companies(conn)
            name_map = {c["name"]: c for c in companies}
            c_names = [c["name"] for c in companies]

            with st.form("add_assoc_form"):
                col1, col2 = st.columns(2)
                with col1:
                    source = st.selectbox("Company", c_names, key="assoc_source")
                with col2:
                    target = st.selectbox("Associated With", [""] + c_names, key="assoc_target")
                target_name = st.text_input("Or type external name (if not in DB)",
                                            placeholder="e.g., SoftBank Vision Fund")
                atype = st.selectbox("Association Type", [
                    "parent", "division_of", "spin_off_from", "academic_origin",
                    "invested_in", "customer_of", "partner", "subsidiary",
                ])
                notes = st.text_area("Notes", placeholder="e.g., Acquired by X in 2021 for $1B")
                if st.form_submit_button("Add Association"):
                    source_id = name_map[source]["id"]
                    target_id = None
                    if target:
                        target_id = name_map[target]["id"]
                    conn.execute("""INSERT INTO company_associations
                                    (company_id, associated_company_id, association_name, association_type, notes)
                                    VALUES (?, ?, ?, ?, ?)""",
                                 (source_id, target_id, target_name or None, atype, notes or None))
                    conn.commit()
                    st.success("Association added!")
                    st.rerun()

        with mgmt_assoc_tabs[2]:
            st.markdown("Discover potential relationships from Wikipedia for any company.")
            companies = get_all_companies(conn)
            disc_slug = st.selectbox("Select company to analyze",
                                     [c["slug"] for c in companies],
                                     format_func=lambda s: next(c["name"] for c in companies if c["slug"] == s),
                                     key="disc_slug")
            if st.button("🔍 Scrape Wikipedia for Associations", type="primary"):
                from scraper.associations import discover_associations, slugify_wiki_title
                with st.spinner("Fetching Wikipedia data..."):
                    suggestions = discover_associations(disc_slug)
                if suggestions:
                    st.markdown(f"Found **{len(suggestions)}** potential associations:")
                    for s in suggestions:
                        wiki_slug = slugify_wiki_title(s["entity"])
                        existing = conn.execute("SELECT id, name, slug FROM companies WHERE slug = ? OR name LIKE ?",
                                                (wiki_slug, f"%{s['entity']}%")).fetchone()
                        col1, col2, col3 = st.columns([3, 2, 2])
                        with col1:
                            st.markdown(f"**{s['entity']}**")
                            st.caption(f"Matched: `{s['matched_keyword']}`")
                        with col2:
                            if existing:
                                st.success(f"→ {existing['name']} (in DB)")
                            else:
                                st.info("Not in database")
                        with col3:
                            if existing:
                                if st.button("Link as parent", key=f"link_p_{s['entity']}"):
                                    source_id = next(c["id"] for c in companies if c["slug"] == disc_slug)
                                    conn.execute("""INSERT INTO company_associations
                                                    (company_id, associated_company_id, association_type, notes)
                                                    VALUES (?, ?, ?, ?)""",
                                                 (source_id, existing["id"], "parent",
                                                  f"Discovered from Wikipedia: {s['matched_keyword']}"))
                                    conn.commit()
                                    st.success("Linked!")
                                    st.rerun()
                                if st.button("Link as spin-off", key=f"link_s_{s['entity']}"):
                                    source_id = next(c["id"] for c in companies if c["slug"] == disc_slug)
                                    conn.execute("""INSERT INTO company_associations
                                                    (company_id, associated_company_id, association_type, notes)
                                                    VALUES (?, ?, ?, ?)""",
                                                 (source_id, existing["id"], "spin_off_from",
                                                  f"Discovered from Wikipedia: {s['matched_keyword']}"))
                                    conn.commit()
                                    st.success("Linked!")
                                    st.rerun()
                else:
                    st.warning("No associations found on Wikipedia for this company.")

        with mgmt_assoc_tabs[3]:
            st.markdown("#### People / Leaders")
            people = get_all_people(conn)
            if people:
                for p in people:
                    with st.expander(f"{p['name']} — {p.get('title', '')}"):
                        if p.get("bio"):
                            st.markdown(p["bio"])
                        roles = get_person_roles(conn, p["id"])
                        if roles:
                            st.markdown("**Roles:**")
                            for r in roles:
                                st.markdown(f"- {r.get('role', 'N/A')} at **{r.get('entity_name', 'N/A')}**")
            else:
                st.info("No people data yet.")

            st.markdown("---")
            st.markdown("#### Add Person")
            with st.form("add_person_form"):
                ppl_name = st.text_input("Name", placeholder="e.g., John Smith")
                ppl_title = st.text_input("Title", placeholder="e.g., CEO of Robotics Inc.")
                ppl_bio = st.text_area("Bio", height=80, placeholder="Brief biography...")
                companies = get_all_companies(conn)
                c_names = [""] + [c["name"] for c in companies]
                with_company = st.selectbox("Link to company (optional)", c_names, key="person_company")
                ppl_role = st.text_input("Role at company", placeholder="e.g., Founder, CEO, CTO")
                if st.form_submit_button("Add Person"):
                    slug = ppl_name.lower().strip().replace(" ", "-")
                    conn.execute("""INSERT OR IGNORE INTO people (name, slug, title, bio)
                                    VALUES (?, ?, ?, ?)""",
                                 (ppl_name, slug, ppl_title or None, ppl_bio or None))
                    if with_company and ppl_role:
                        person_row = conn.execute("SELECT id FROM people WHERE slug = ?", (slug,)).fetchone()
                        company_row = conn.execute("SELECT id FROM companies WHERE name = ?", (with_company,)).fetchone()
                        if person_row and company_row:
                            conn.execute("""INSERT INTO person_roles (person_id, entity_id, entity_type, role)
                                            VALUES (?, ?, 'company', ?)""",
                                         (person_row[0], company_row[0], ppl_role))
                    conn.commit()
                    st.success(f"Added person: {ppl_name}")
                    st.rerun()

        with mgmt_assoc_tabs[4]:
            st.markdown("#### Auto-Discovery")
            st.markdown("Run web scrapers to discover people, academic ties, and more associations from Wikipedia and company websites.")

            if st.button("🔁 Run Full Auto-Discovery", type="primary"):
                from scraper.associations import auto_discover_everything
                with st.spinner("Running auto-discovery across all companies (this may take a minute)..."):
                    result = auto_discover_everything(conn)
                st.success(f"Discovery complete! Found **{result['people']}** new people and **{result['associations']}** new associations.")
                st.rerun()

    with mgmt_tabs[5]:
        st.subheader("Image Manager")
        st.markdown("Browse and select images for products and companies. Selected images are locked (won't be overwritten by scrapers).")

        entity_type = st.radio("Entity Type", ["Products", "Companies"], horizontal=True, key="img_entity_type")

        if entity_type == "Products":
            all_ps = get_all_products(conn)
            opts = {f"{p['company_name']} — {p['name']}": p for p in all_ps}
            sel = st.selectbox("Select Product", list(opts.keys()), key="img_product_select")
            entity = opts[sel]

            hide_img = product_img_html(entity.get("image_url", ""), entity.get("name", ""), 200)
            st.markdown(f"**Current Image** (source: `{entity.get('image_source', 'auto')}`)")
            st.markdown(hide_img, unsafe_allow_html=True)

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🔍 Scrape Candidates", key="img_scrape_prod"):
                    with st.spinner("Fetching images..."):
                        cand, msg = scrape_product_image_candidates(conn, entity["id"])
                    st.info(msg)
                    if cand:
                        st.rerun()

            with col2:
                if entity.get("image_source") == "manual" and st.button("↩ Reset to Auto", key="img_reset_prod"):
                    reset_product_image(conn, entity["id"])
                    st.success("Reset to auto")
                    st.rerun()

            candidates = get_product_image_candidates(conn, entity["id"])
            if candidates:
                st.markdown(f"**Candidates ({len(candidates)})**")
                cols = st.columns(min(len(candidates), 5))
                for i, cand in enumerate(candidates[:25]):
                    with cols[i % 5]:
                        is_current = cand["image_url"] == entity.get("image_url", "")
                        if _is_valid_image_url(cand["image_url"]):
                            st.image(cand["image_url"], width=120, caption=cand["source"])
                        else:
                            st.caption(f"⛔ {cand['source']} (invalid url)")
                        if is_current:
                            st.caption("✅ Current")
                        else:
                            if st.button("Select", key=f"img_sel_prod_{cand['id']}"):
                                set_product_image(conn, entity["id"], cand["image_url"])
                                st.success("Selected!")
                                st.rerun()

            st.markdown("---")
            if st.button("🔄 Scrape All Product Images"):
                with st.spinner("Scraping all products..."):
                    results = scrape_all_product_image_candidates(conn)
                for name, msg in results:
                    st.text(f"{name}: {msg}")
                st.rerun()

        else:
            all_cos = get_all_companies(conn)
            opts = {c["name"]: c for c in all_cos}
            sel = st.selectbox("Select Company", list(opts.keys()), key="img_company_select")
            entity = opts[sel]

            st.markdown(f"**Current Logo** (source: `{entity.get('image_source', 'auto')}`)")
            if _is_valid_image_url(entity.get("logo_url")):
                st.image(entity["logo_url"], width=200)

            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button("🔍 Scrape Candidates", key="img_scrape_comp"):
                    with st.spinner("Fetching images..."):
                        cand, msg = scrape_company_image_candidates(conn, entity["id"])
                    st.info(msg)
                    if cand:
                        st.rerun()

            with col2:
                if entity.get("image_source") == "manual" and st.button("↩ Reset to Auto", key="img_reset_comp"):
                    reset_company_image(conn, entity["id"])
                    st.success("Reset to auto")
                    st.rerun()

            candidates = get_company_image_candidates(conn, entity["id"])
            if candidates:
                st.markdown(f"**Candidates ({len(candidates)})**")
                cols = st.columns(min(len(candidates), 5))
                for i, cand in enumerate(candidates[:25]):
                    with cols[i % 5]:
                        is_current = cand["image_url"] == entity.get("logo_url", "")
                        if _is_valid_image_url(cand["image_url"]):
                            st.image(cand["image_url"], width=120, caption=cand["source"])
                        else:
                            st.caption(f"⛔ {cand['source']} (invalid url)")
                        if is_current:
                            st.caption("✅ Current")
                        else:
                            if st.button("Select", key=f"img_sel_comp_{cand['id']}"):
                                set_company_image(conn, entity["id"], cand["image_url"])
                                st.success("Selected!")
                                st.rerun()

            st.markdown("---")
            if st.button("🔄 Scrape All Company Images"):
                with st.spinner("Scraping all companies..."):
                    results = scrape_all_company_image_candidates(conn)
                for name, msg in results:
                    st.text(f"{name}: {msg}")
                st.rerun()

    with mgmt_tabs[6]:
        st.subheader("Case Studies")
        st.markdown("Discover and import case studies from company websites.")

        all_cos = get_all_companies(conn)
        cos_with_sites = [c for c in all_cos if c.get("website") and c.get("website", "").strip()]

        def _count_cs(company_id):
            return len(get_existing_cs_urls(conn, company_id))

        sel_company = st.selectbox(
            "Select Company",
            cos_with_sites,
            format_func=lambda c: f"{c['name']} ({_count_cs(c['id'])} existing)" if _count_cs(c['id']) else c['name'],
            key="cs_mgmt_company",
        )

        if sel_company:
            cid = sel_company["id"]
            existing = get_existing_cs_urls(conn, cid)
            if existing:
                with st.expander(f"Existing Case Studies ({len(existing)})"):
                    for url in existing:
                        cs_row = get_case_study_by_url(conn, url)
                        if cs_row:
                            st.markdown(f"- [{cs_row['title'] or 'Untitled'}]({url})")
            else:
                st.info("No case studies imported yet for this company.")

            if st.button("🔍 Discover & Import", key=f"cs_discover_{cid}", use_container_width=True):
                with st.spinner(f"Scanning {sel_company['website']}..."):
                    results = cs_scraper.scrape_company_case_studies(conn, sel_company)
                st.markdown(f"**Found {len(results)} candidate pages**")

                importable = [r for r in results if r.get("status") == "parsed"]
                existing_urls_found = [r for r in results if r.get("status") == "exists"]
                unreachable = [r for r in results if r.get("status") == "unreachable"]

                if importable:
                    st.markdown(f"**{len(importable)} new case studies ready to import**")
                    st.markdown("Preview:")
                    for r in importable:
                        title = (r.get("title") or "Untitled")[:100]
                        cust = r.get("customer", "")
                        industry = r.get("industry", "")
                        preview = f"- **{title}**"
                        if cust:
                            preview += f" — *{cust}*"
                        if industry:
                            preview += f" [{industry}]"
                        st.markdown(preview)

                    if st.button("📥 Import All", key=f"cs_import_{cid}", use_container_width=True):
                        imported = 0
                        for r in importable:
                            cs_id = cs_scraper.import_case_study(conn, cid, r)
                            if cs_id:
                                imported += 1
                        if imported:
                            extract_case_study_metrics(conn, cs_id)
                            st.success(f"Imported {imported} case studies!")
                            st.rerun()
                        else:
                            st.warning("No new case studies were imported.")
                else:
                    st.info("No new case studies found to import.")

                if existing_urls_found:
                    st.caption(f"{len(existing_urls_found)} already exist (skipped)")
                if unreachable:
                    st.caption(f"{len(unreachable)} pages were unreachable")

        st.markdown("---")
        st.markdown("#### Bulk Scrape All Companies")

        if st.button("🔄 Scrape All Companies for Case Studies", use_container_width=True, type="primary"):
            with st.spinner("Scraping all companies (this may take a while)..."):
                total_imported = 0
                for c in cos_with_sites:
                    results = cs_scraper.scrape_company_case_studies(conn, c)
                    parsed = [r for r in results if r.get("status") == "parsed"]
                    exists = sum(1 for r in results if r.get("status") == "exists")
                    if parsed:
                        for r in parsed:
                            cs_id = cs_scraper.import_case_study(conn, c["id"], r)
                            if cs_id:
                                total_imported += 1
                                extract_case_study_metrics(conn, cs_id)
                        st.text(f"{c['name']}: {len(parsed)} new, {exists} existing ({len(results)} total)")
                    else:
                        st.text(f"{c['name']}: no new candidates ({exists} existing)")
                if total_imported:
                    st.success(f"Imported {total_imported} total case studies!")
                    st.rerun()
                else:
                    st.info("No new case studies found across any company.")

        st.markdown("---")
        st.markdown("#### Manual Add")
        with st.form("add_case_study_form"):
            cs_company = st.selectbox("Company", all_cos, format_func=lambda c: c["name"], key="cs_manual_company")
            cs_title = st.text_input("Title", placeholder="e.g., DHL Reduces Unload Time by 60%")
            cs_customer = st.text_input("Customer", placeholder="e.g., DHL Supply Chain")
            cs_industry = st.text_input("Industry", placeholder="e.g., Logistics / 3PL")
            cs_url = st.text_input("Case Study URL", placeholder="https://...")
            cs_challenge = st.text_area("Challenge", height=80)
            cs_solution = st.text_area("Solution", height=80)
            cs_results = st.text_area("Results", height=80)
            cs_metrics = st.text_area("Metrics", placeholder="e.g., 60% faster | 85% fewer injuries", height=60)
            cs_featured_image = st.text_input("Featured Image URL")
            cs_published = st.text_input("Published Date")
            if st.form_submit_button("Add Case Study", use_container_width=True):
                data = {
                    "company_id": cs_company["id"] if cs_company else None,
                    "product_id": None,
                    "title": cs_title,
                    "customer": cs_customer,
                    "industry": cs_industry,
                    "challenge": cs_challenge,
                    "solution": cs_solution,
                    "results": cs_results,
                    "metrics": cs_metrics,
                    "url": cs_url,
                    "featured_image": cs_featured_image,
                    "published_date": cs_published,
                }
                cs_id = upsert_case_study(conn, data)
                if cs_id:
                    extract_case_study_metrics(conn, cs_id)
                    st.success(f"Case study added! (ID: {cs_id})")
                    st.rerun()
                else:
                    st.error("Failed to add case study.")

conn.close()
