"""
app.py
Project Griffin — Financial Model Dashboard
Run: streamlit run app.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data_loader

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Project Griffin",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── STYLING ─────────────────────────────────────────────────────────────────

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #0f1117; }
  [data-testid="stHeader"] { background: transparent; }
  .block-container { padding: 1.5rem 2rem 2rem; }
  h1 { font-family: monospace; letter-spacing: 0.06em; font-size: 1.3rem !important; color: #e8e8e8 !important; }
  .metric-card {
    background: #1a1d27; border: 1px solid #2a2d3a; border-radius: 8px;
    padding: 14px 16px; margin-bottom: 4px;
  }
  .metric-label { font-family: monospace; font-size: 0.65rem; color: #6b7280;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 4px; }
  .metric-value { font-family: monospace; font-size: 1.35rem; font-weight: 600;
    color: #e8e8e8; line-height: 1; }
  .metric-sub { font-family: monospace; font-size: 0.65rem; color: #4b5563; margin-top: 3px; }
  .delta-up { color: #1D9E75; font-size: 0.75rem; margin-top: 3px; }
  .delta-dn { color: #D85A30; font-size: 0.75rem; margin-top: 3px; }
  div[data-testid="stTabs"] button { font-family: monospace; font-size: 0.8rem; }
  .stSlider > div { padding-top: 0; }
  div[data-baseweb="select"] { font-family: monospace; font-size: 0.85rem; }
  .sens-note { font-family: monospace; font-size: 0.72rem; color: #6b7280; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# ─── PLOTLY THEME ─────────────────────────────────────────────────────────────

PLOT_BG = "#0f1117"
PAPER_BG = "#0f1117"
GRID_COLOR = "rgba(255,255,255,0.05)"
TICK_COLOR = "#6b7280"
FONT = dict(family="monospace", color="#9ca3af", size=11)

def base_layout(**kwargs):
    d = dict(
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=PLOT_BG,
        font=FONT,
        margin=dict(l=8, r=8, t=24, b=8),
        showlegend=False,
    )
    d.update(kwargs)
    return d

def style_axes(fig, xgrid=False, ygrid=True):
    fig.update_xaxes(
        gridcolor=GRID_COLOR if xgrid else "rgba(0,0,0,0)",
        tickfont=dict(family="monospace", color=TICK_COLOR, size=10),
        linecolor="#2a2d3a", zeroline=False,
    )
    fig.update_yaxes(
        gridcolor=GRID_COLOR if ygrid else "rgba(0,0,0,0)",
        tickfont=dict(family="monospace", color=TICK_COLOR, size=10),
        linecolor="#2a2d3a", zeroline=False,
    )
    return fig

# ─── COLORS ──────────────────────────────────────────────────────────────────

COLORS = {
    "bess_cap":     "#378ADD",
    "bess_ds3":     "#185FA5",
    "bess_dassa":   "#85B7EB",
    "bess_merchant":"#B5D4F4",
    "sc_ds3":       "#1D9E75",
    "sc_lcis":      "#5DCAA5",
    "sc_lpf":       "#9FE1CB",
    "cfads":        "#378ADD",
    "dividends":    "#D4537E",
    "cost":         ["#BA7517","#EF9F27","#FAC775","#B4B2A9","#73726c","#D3D1C7"],
    "green":        "#1D9E75",
    "amber":        "#EF9F27",
    "teal":         "#9FE1CB",
    "blue":         "#378ADD",
}

# ─── DATA LOADING ─────────────────────────────────────────────────────────────

@st.cache_data
def load_all():
    try:
        df = data_loader.get_annual_cashflows()
    except Exception as e:
        st.warning(f"엑셀 파일을 읽지 못했어요 — 샘플 데이터로 실행합니다. ({e})")
        df = _sample_cashflows()
    metrics = data_loader.get_summary_metrics()
    lcis_metrics = data_loader.get_lcis_scenario_metrics()
    rev_breakdown = data_loader.get_lifetime_revenue_breakdown()
    cost_breakdown = data_loader.get_lifetime_cost_breakdown()
    dr_by_cf = data_loader.get_discount_rates_by_cashflow()
    capex = data_loader.get_capex_breakdown()
    sensitivity = data_loader.get_sensitivity_matrix()
    scenarios = data_loader.get_scenario_presets()
    return df, metrics, lcis_metrics, rev_breakdown, cost_breakdown, dr_by_cf, capex, sensitivity, scenarios

def _sample_cashflows():
    """Fallback sample data if Excel is unavailable."""
    years = list(range(2024, 2043))
    bess_cap   = [0,0.4,4.2,4.2,4.2,4.2,4.2,4.2,4.2,4.2,4.2,2.0,1.9,1.9,1.9,1.9,1.9,5.5,5.9]
    bess_ds3   = [0,0,4.1,6.2,3.9,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    bess_dassa = [0,0,0,0,0.8,2.7,2.0,2.2,2.3,2.5,2.3,2.6,2.4,2.2,2.0,1.9,1.9,1.3,1.4]
    bess_merch = [0,0.1,1.1,1.6,1.9,2.7,2.4,2.5,2.6,2.8,2.8,2.7,2.9,2.9,2.9,2.8,3.0,8.0,8.1]
    sc_ds3     = [0,0.6,6.8,6.9,5.2,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    sc_lpf     = [0,0,0,0,8.8,21.2,20.8,21.2,21.6,24.5,27.8,31.3,39.6,40.2,39.6,38.7,38.2,39.2,40.5]
    cfads      = [-41,-46.7,5.0,9.5,15.2,21.1,19.7,20.1,20.5,23.7,25.2,24.7,31.5,31.7,30.8,29.6,-20.7,38.0,39.2]
    dividends  = [0,0,0,0,0,0,0,0,4.0,23.7,25.2,24.7,31.5,31.7,30.8,29.6,42.7,22.5,23.8]
    df = pd.DataFrame({
        "year": years,
        "bess_cap": bess_cap, "bess_ds3": bess_ds3,
        "bess_dassa": bess_dassa, "bess_merchant": bess_merch,
        "sc_ds3": sc_ds3, "sc_lcis": [0]*19, "sc_lpf": sc_lpf,
        "cfads": cfads, "dividends": [-d for d in dividends],
        "dividends_pos": dividends,
    })
    df["bess_total"] = df["bess_cap"]+df["bess_ds3"]+df["bess_dassa"]+df["bess_merchant"]
    df["sc_total"] = df["sc_ds3"]+df["sc_lcis"]+df["sc_lpf"]
    df["total_revenue"] = df["bess_total"]+df["sc_total"]
    return df

df, metrics, lcis_metrics, rev_bkd, cost_bkd, dr_cf, capex_bkd, sens, scenarios = load_all()

# ─── HEADER ───────────────────────────────────────────────────────────────────

col_title, col_scen = st.columns([3, 2])
with col_title:
    st.markdown("# ⚡ PROJECT GRIFFIN")
    st.caption("Rubicon Capital Advisors · Oct 2025 Draft")

with col_scen:
    scenario_choice = st.radio(
        "Active Scenario",
        ["Base Case w/o LCIS DR2", "11 Sep Case (LCIS DR2)"],
        horizontal=True,
        label_visibility="collapsed",
    )

active = metrics if "Base" in scenario_choice else lcis_metrics

st.divider()

# ─── KPI ROW ──────────────────────────────────────────────────────────────────

k1, k2, k3, k4 = st.columns(4)

def kpi(col, label, value, sub, delta=None):
    delta_html = ""
    if delta:
        cls = "delta-up" if delta.startswith("+") else "delta-dn"
        delta_html = f'<div class="{cls}">{delta}</div>'
    col.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">{label}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-sub">{sub}</div>
      {delta_html}
    </div>""", unsafe_allow_html=True)

eq_delta = f'+€{active["equity_value_80pct"]-77.0:.1f}m vs Base' if active["equity_value_80pct"] != 77.0 else None
ev_delta = f'+€{active["enterprise_value"]-177.4:.1f}m vs Base' if active["enterprise_value"] != 177.4 else None

kpi(k1, "Equity Value (80%)", f'€{active["equity_value_80pct"]:.1f}m', "Dec-2025 · 10% DR", eq_delta)
kpi(k2, "Enterprise Value", f'€{active["enterprise_value"]:.1f}m', "at ops start", ev_delta)
kpi(k3, "Total Revenue", "€2.24B", "BESS + Sync Condenser")
kpi(k4, "CFADS (life)", "€1.41B", "post-capex · €140m capex")

st.markdown("<br>", unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────

tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Cashflows", "🎯 Sensitivity", "🔀 Scenarios"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

with tab1:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Revenue by stream — life total (€m)**")
        labels = list(rev_bkd.keys())
        values = list(rev_bkd.values())
        colors = [COLORS["bess_cap"], COLORS["bess_ds3"], COLORS["bess_dassa"],
                  COLORS["bess_merchant"], COLORS["sc_ds3"], COLORS["sc_lpf"]]
        fig = go.Figure(go.Pie(
            labels=labels, values=values,
            marker_colors=colors,
            hole=0.62,
            textinfo="label+percent",
            textfont=dict(family="monospace", size=10, color="#9ca3af"),
            hovertemplate="<b>%{label}</b><br>€%{value:.0f}m<br>%{percent}<extra></extra>",
        ))
        fig.update_layout(**base_layout(height=280))
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.markdown("**Operating costs — life total (€m)**")
        cost_labels = list(cost_bkd.keys())
        cost_vals = list(cost_bkd.values())
        fig = go.Figure(go.Bar(
            x=cost_vals, y=cost_labels,
            orientation="h",
            marker_color=COLORS["cost"],
            text=[f"€{v:.0f}m" for v in cost_vals],
            textposition="outside",
            textfont=dict(family="monospace", size=10, color="#9ca3af"),
            hovertemplate="<b>%{y}</b>: €%{x:.0f}m<extra></extra>",
        ))
        fig.update_layout(**base_layout(height=280))
        fig.update_xaxes(tickprefix="€", ticksuffix="m")
        style_axes(fig, xgrid=True, ygrid=False)
        st.plotly_chart(fig, use_container_width=True)

    col_c, col_d = st.columns(2)

    with col_c:
        st.markdown("**Equity discount rate by cashflow type (%)**")
        dr_labels = list(dr_cf.keys())
        dr_vals = list(dr_cf.values())
        bar_colors = ["#9FE1CB","#B5D4F4","#85B7EB","#85B7EB","#85B7EB","#9FE1CB","#9FE1CB","#378ADD"]
        fig = go.Figure(go.Bar(
            x=dr_vals, y=dr_labels, orientation="h",
            marker_color=bar_colors,
            text=[f"{v}%" for v in dr_vals],
            textposition="outside",
            textfont=dict(family="monospace", size=10, color="#9ca3af"),
            hovertemplate="<b>%{y}</b>: %{x}%<extra></extra>",
        ))
        fig.update_layout(**base_layout(height=260))
        fig.update_xaxes(range=[5, 17], ticksuffix="%")
        style_axes(fig, xgrid=True, ygrid=False)
        st.plotly_chart(fig, use_container_width=True)

    with col_d:
        st.markdown("**CAPEX breakdown (€m)**")
        cap_labels = list(capex_bkd.keys())
        cap_vals = list(capex_bkd.values())
        fig = go.Figure(go.Bar(
            x=cap_labels, y=cap_vals,
            marker_color=["#378ADD","#B5D4F4","#85B7EB","#E6F1FB"],
            text=[f"€{v:.0f}m" for v in cap_vals],
            textposition="outside",
            textfont=dict(family="monospace", size=10, color="#9ca3af"),
            hovertemplate="<b>%{x}</b>: €%{y:.0f}m<extra></extra>",
        ))
        fig.update_layout(**base_layout(height=260))
        fig.update_yaxes(tickprefix="€", ticksuffix="m")
        style_axes(fig, xgrid=False, ygrid=True)
        st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CASHFLOWS
# ══════════════════════════════════════════════════════════════════════════════

with tab2:
    st.markdown("**Annual cashflows 2024–2042 (€m) — stacked revenue bars · CFADS & dividend lines**")

    fig = go.Figure()

    # Stacked bars: BESS total, SC DS3, SC LPF
    fig.add_trace(go.Bar(name="BESS streams", x=df["year"], y=df["bess_total"],
        marker_color=COLORS["bess_cap"], hovertemplate="BESS: €%{y:.1f}m<extra></extra>"))
    fig.add_trace(go.Bar(name="SC DS3", x=df["year"], y=df["sc_ds3"],
        marker_color=COLORS["sc_ds3"], hovertemplate="SC DS3: €%{y:.1f}m<extra></extra>"))
    fig.add_trace(go.Bar(name="SC LPF", x=df["year"], y=df["sc_lpf"],
        marker_color=COLORS["sc_lpf"], hovertemplate="SC LPF: €%{y:.1f}m<extra></extra>"))

    # Lines: CFADS and Dividends
    fig.add_trace(go.Scatter(name="CFADS", x=df["year"], y=df["cfads"],
        line=dict(color=COLORS["cfads"], width=2),
        mode="lines", hovertemplate="CFADS: €%{y:.1f}m<extra></extra>"))
    fig.add_trace(go.Scatter(name="Dividends", x=df["year"], y=df["dividends_pos"],
        line=dict(color=COLORS["dividends"], width=1.5, dash="dash"),
        mode="lines", hovertemplate="Dividends: €%{y:.1f}m<extra></extra>"))

    fig.update_layout(
        **base_layout(height=320, barmode="stack"),
        showlegend=True,
        legend=dict(orientation="h", y=1.08, x=0,
            font=dict(family="monospace", size=10, color="#9ca3af")),
        hovermode="x unified",
    )
    fig.update_yaxes(tickprefix="€", ticksuffix="m")
    style_axes(fig, xgrid=False, ygrid=True)
    st.plotly_chart(fig, use_container_width=True)

    col_e, col_f = st.columns(2)

    with col_e:
        st.markdown("**Revenue by stream per year (€m)**")
        fig2 = go.Figure()
        stream_map = [
            ("bess_cap", "BESS Cap", COLORS["bess_cap"]),
            ("bess_ds3", "BESS DS3", COLORS["bess_ds3"]),
            ("bess_dassa", "BESS DASSA", COLORS["bess_dassa"]),
            ("bess_merchant", "BESS Merchant", COLORS["bess_merchant"]),
            ("sc_ds3", "SC DS3", COLORS["sc_ds3"]),
            ("sc_lpf", "SC LPF", COLORS["sc_lpf"]),
        ]
        for col, name, color in stream_map:
            fig2.add_trace(go.Bar(name=name, x=df["year"], y=df[col],
                marker_color=color,
                hovertemplate=f"{name}: €%{{y:.1f}}m<extra></extra>"))
        fig2.update_layout(**base_layout(height=260, barmode="stack"), showlegend=True,
            legend=dict(orientation="h", y=1.08, x=0,
                font=dict(family="monospace", size=9, color="#9ca3af")))
        fig2.update_yaxes(tickprefix="€", ticksuffix="m")
        style_axes(fig2, xgrid=False, ygrid=True)
        st.plotly_chart(fig2, use_container_width=True)

    with col_f:
        st.markdown("**BESS vs Sync Condenser split (€m/yr)**")
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name="BESS", x=df["year"], y=df["bess_total"],
            marker_color=COLORS["bess_cap"],
            hovertemplate="BESS: €%{y:.1f}m<extra></extra>"))
        fig3.add_trace(go.Bar(name="Sync Condenser", x=df["year"], y=df["sc_total"],
            marker_color=COLORS["sc_ds3"],
            hovertemplate="SC: €%{y:.1f}m<extra></extra>"))
        fig3.update_layout(**base_layout(height=260, barmode="stack"), showlegend=True,
            legend=dict(orientation="h", y=1.08, x=0,
                font=dict(family="monospace", size=10, color="#9ca3af")))
        fig3.update_yaxes(tickprefix="€", ticksuffix="m")
        style_axes(fig3, xgrid=False, ygrid=True)
        st.plotly_chart(fig3, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SENSITIVITY
# ══════════════════════════════════════════════════════════════════════════════

with tab3:
    st.markdown("**LCIS Strike Price × Discount Rate → Equity Value at 80% stake (€m)**")
    st.markdown('<div class="sens-note">Green = higher equity · Amber = lower · Calibrated to Base Case (10% DR, €0) = €77.0m and LCIS DR2 anchor (~€75/MWh)</div>',
        unsafe_allow_html=True)

    # Heatmap
    drs = sens["discount_rates"]
    strikes = sens["strike_prices"]
    matrix = np.array(sens["matrix"])

    fig_heat = go.Figure(go.Heatmap(
        z=matrix,
        x=[f"€{s}/MWh" for s in strikes],
        y=[f"{d}%" for d in drs],
        colorscale=[
            [0.0, "#BA7517"],
            [0.4, "#EF9F27"],
            [0.7, "#1D9E75"],
            [1.0, "#085041"],
        ],
        text=[[f"€{v:.1f}m" for v in row] for row in matrix],
        texttemplate="%{text}",
        textfont=dict(family="monospace", size=11),
        showscale=True,
        colorbar=dict(
            tickfont=dict(family="monospace", size=9, color="#9ca3af"),
            tickprefix="€", ticksuffix="m",
            bgcolor=PAPER_BG, bordercolor="#2a2d3a",
        ),
        hovertemplate="DR: %{y}<br>Strike: %{x}<br>Equity (80%%): %{text}<extra></extra>",
    ))

    # Highlight base case and LCIS DR2 anchor
    fig_heat.add_shape(type="rect", x0=-0.5, x1=0.5, y0=-0.5, y1=0.5,
        line=dict(color=COLORS["green"], width=2.5))
    fig_heat.add_shape(type="rect", x0=2.5, x1=3.5, y0=-0.5, y1=0.5,
        line=dict(color=COLORS["blue"], width=2.5))

    fig_heat.add_annotation(x=0, y=5.0, text="Base Case", showarrow=False,
        font=dict(family="monospace", size=9, color=COLORS["green"]))
    fig_heat.add_annotation(x=3, y=5.0, text="LCIS DR2 ~€75", showarrow=False,
        font=dict(family="monospace", size=9, color=COLORS["blue"]))

    fig_heat.update_layout(**base_layout(height=260))
    fig_heat.update_xaxes(side="bottom")
    style_axes(fig_heat, xgrid=False, ygrid=False)
    st.plotly_chart(fig_heat, use_container_width=True)

    st.divider()

    # LCIS Slider sensitivity
    st.markdown("**LCIS Strike Price Sensitivity (at 10% Discount Rate)**")
    strike_val = st.slider("Strike Price (€/MWh)", 0, 150, 0, step=5)

    annual_rev = round(strike_val * 100 * 8760 * 0.95 / 1e6, 1)
    eq_val = round(77.0 + strike_val * 0.028, 1)
    ev_val = round(177.4 + strike_val * 0.029, 1)
    eq_delta = round(eq_val - 77.0, 1)

    s1, s2, s3 = st.columns(3)
    s1.metric("LCIS Revenue (annual)", f"€{annual_rev}m/yr", help="Illustrative · 100MW × 8,760h × 95% availability")
    s2.metric("Equity Value (80%)", f"€{eq_val}m", delta=f"+€{eq_delta}m vs Base" if eq_delta > 0 else None)
    s3.metric("Enterprise Value", f"€{ev_val}m", delta=f"+€{round(ev_val-177.4,1)}m vs Base" if ev_val > 177.4 else None)

    # Sensitivity line chart
    strike_range = list(range(0, 155, 5))
    eq_line = [round(77.0 + s * 0.028, 2) for s in strike_range]

    fig_line = go.Figure()
    fig_line.add_trace(go.Scatter(
        x=strike_range, y=eq_line,
        mode="lines",
        line=dict(color=COLORS["blue"], width=2),
        fill="tozeroy", fillcolor="rgba(55,138,221,0.08)",
        hovertemplate="Strike: €%{x}/MWh<br>Equity: €%{y:.1f}m<extra></extra>",
    ))
    fig_line.add_vline(x=strike_val, line_dash="dot", line_color=COLORS["amber"],
        annotation_text=f"  €{strike_val}/MWh", annotation_font_color=COLORS["amber"],
        annotation_font_size=10)
    fig_line.update_layout(**base_layout(height=180))
    fig_line.update_xaxes(tickprefix="€", ticksuffix="/MWh", title_text="Strike Price")
    fig_line.update_yaxes(tickprefix="€", ticksuffix="m", range=[75, 82])
    style_axes(fig_line, xgrid=False, ygrid=True)
    st.plotly_chart(fig_line, use_container_width=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — SCENARIOS
# ══════════════════════════════════════════════════════════════════════════════

with tab4:
    st.markdown("**Sub-scenario controls**")

    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        rev_scen = st.selectbox("Revenue Scenario", [
            "Afry Central w/o LCIS",
            "LCIS 2 | Afry Central",
            "High Case (+10%)",
            "Low Case (−10%)",
        ])
    with sc2:
        fund_scen = st.selectbox("Funding", ["w/o LCIS (Base)", "SHL Funding"])
    with sc3:
        debt_scen = st.selectbox("Debt Structure", ["No Refinancing", "Refi at LCIS Date"])

    rev_impact = {"Afry Central w/o LCIS": 0, "LCIS 2 | Afry Central": 2.4,
                  "High Case (+10%)": 5.5, "Low Case (−10%)": -6.2}
    fund_impact = {"w/o LCIS (Base)": 0, "SHL Funding": 1.0}
    debt_impact = {"No Refinancing": 0, "Refi at LCIS Date": -0.5}

    custom_eq = round(77.0 + rev_impact[rev_scen] + fund_impact[fund_scen] + debt_impact[debt_scen], 1)
    custom_delta = round(custom_eq - 77.0, 1)
    custom_ev = round(177.4 + custom_delta, 1)

    st.markdown("<br>", unsafe_allow_html=True)
    out1, out2, out3 = st.columns(3)
    label = "Base Case" if custom_delta == 0 else "Custom combination"
    out1.metric("Equity Value (80%)", f"€{custom_eq}m",
        delta=f"+€{custom_delta}m vs Base" if custom_delta > 0 else (f"€{custom_delta}m vs Base" if custom_delta < 0 else None))
    out2.metric("Delta vs Base", f"+€{custom_delta}m" if custom_delta >= 0 else f"€{custom_delta}m")
    out3.metric("Enterprise Value", f"€{custom_ev}m")

    st.caption(f"Active combination: {rev_scen} · {fund_scen} · {debt_scen}")
    st.divider()

    st.markdown("**Scenario comparison — equity value at 80% (€m)**")

    scen_labels = [s["label"] for s in scenarios] + ["→ Custom"]
    scen_vals = [s["equity_80"] for s in scenarios] + [custom_eq]
    scen_colors = [
        COLORS["green"] if v == 77.0 else (COLORS["amber"] if i == len(scen_labels) - 1 else "#2a4a7f")
        for i, v in enumerate(scen_vals)
    ]

    fig_sc = go.Figure(go.Bar(
        x=scen_vals, y=scen_labels,
        orientation="h",
        marker_color=scen_colors,
        text=[f"€{v:.1f}m" for v in scen_vals],
        textposition="outside",
        textfont=dict(family="monospace", size=10, color="#9ca3af"),
        hovertemplate="<b>%{y}</b>: €%{x:.1f}m<extra></extra>",
    ))
    fig_sc.update_layout(**base_layout(height=250))
    fig_sc.update_xaxes(range=[63, 87], tickprefix="€", ticksuffix="m")
    fig_sc.add_vline(x=77.0, line_dash="dot", line_color="#4b5563",
        annotation_text="  Base", annotation_font_color="#6b7280", annotation_font_size=9)
    style_axes(fig_sc, xgrid=True, ygrid=False)
    st.plotly_chart(fig_sc, use_container_width=True)

# ─── FOOTER ───────────────────────────────────────────────────────────────────

st.divider()
st.caption("Project Griffin · Rubicon Capital Advisors · Draft Oct 2025 · Illustrative sensitivity figures only")
