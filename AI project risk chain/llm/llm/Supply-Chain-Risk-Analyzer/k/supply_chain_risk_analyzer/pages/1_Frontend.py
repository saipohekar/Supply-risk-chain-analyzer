"""
Supply Chain Risk Analyzer — Streamlit Web Application.
Main entry point for the interactive UI.
"""
import sys
import os
import time
import logging
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.config import validate_config, GEMINI_API_KEY, TAVILY_API_KEY
from utils.models import RiskLevel, AnalysisResult

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Supply Chain Risk Analyzer",
    page_icon="🔗",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com",
        "About": "Supply Chain Risk Analyzer powered by Gemini + Tavily",
    },
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Global ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
h1, h2, h3, h4, h5, h6, .hero-title, .metric-value, .score-number { font-family: 'Outfit', sans-serif !important; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* ── App background ── */
.stApp {
    background: radial-gradient(circle at 50% 0%, #17243c 0%, #0d121f 40%, #05080f 100%);
    min-height: 100vh;
}

/* ── Animations ── */
@keyframes slideUpFade {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes pulseGlow {
    0% { box-shadow: 0 0 15px rgba(99, 179, 237, 0.2); }
    50% { box-shadow: 0 0 30px rgba(99, 179, 237, 0.5); }
    100% { box-shadow: 0 0 15px rgba(99, 179, 237, 0.2); }
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(13, 18, 31, 0.6);
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255,255,255,0.05);
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 { color: #82aaff; }

/* ── Hero banner ── */
.hero-banner {
    background: linear-gradient(145deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
    backdrop-filter: blur(12px);
    border-radius: 20px;
    padding: 3rem 2.5rem;
    margin-bottom: 2rem;
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 10px 40px -10px rgba(0,0,0,0.5);
    position: relative;
    overflow: hidden;
    animation: slideUpFade 0.6s ease-out forwards;
}
.hero-banner::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at 50% 50%, rgba(130, 170, 255, 0.1) 0%, transparent 60%);
    pointer-events: none;
    animation: pulse-bg 8s linear infinite;
}
@keyframes pulse-bg {
    0%, 100% { transform: scale(1) rotate(0deg); opacity: 0.6; }
    50% { transform: scale(1.05) rotate(180deg); opacity: 1; }
}
.hero-title {
    font-size: 2.8rem; font-weight: 800;
    background: linear-gradient(135deg, #ffffff, #a2ccfe, #63b3ed);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0; line-height: 1.1;
    letter-spacing: -0.5px;
}
.hero-subtitle {
    color: rgba(227,242,253,0.7); 
    font-size: 1.1rem; margin-top: 0.8rem;
    font-weight: 400; line-height: 1.6;
}
.hero-badges { display: flex; gap: 0.8rem; margin-top: 1.5rem; flex-wrap: wrap; }
.badge {
    background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.03));
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    border-radius: 20px; padding: 0.3rem 0.9rem;
    font-size: 0.8rem; color: #a2ccfe;
    font-weight: 500; letter-spacing: 0.5px;
    backdrop-filter: blur(5px);
    transition: transform 0.3s ease, background 0.3s ease;
}
.badge:hover {
    transform: translateY(-2px);
    background: linear-gradient(135deg, rgba(255,255,255,0.15), rgba(255,255,255,0.05));
}

/* ── Cards ── */
.metric-card {
    background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 16px; padding: 1.5rem;
    backdrop-filter: blur(12px);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    animation: slideUpFade 0.5s ease-out forwards;
    animation-delay: 0.1s;
    opacity: 0;
}
.metric-card:hover {
    transform: translateY(-5px);
    border-color: rgba(130, 170, 255, 0.3);
    box-shadow: 0 10px 30px rgba(130, 170, 255, 0.15);
}
.metric-label { 
    color: rgba(255,255,255,0.5); 
    font-size: 0.8rem; font-weight: 500;
    text-transform: uppercase; letter-spacing: 1.5px;
    margin-bottom: 0.5rem;
}
.metric-value { 
    font-size: 2.5rem; font-weight: 800; color: #ffffff;
    line-height: 1; letter-spacing: -1px;
}
.metric-sub { color: rgba(255,255,255,0.4); font-size: 0.85rem; margin-top: 0.4rem; font-weight: 400; }

/* ── Risk level badges ── */
.risk-critical { color: #ff4d4d; background: rgba(255,77,77,0.1); border: 1px solid rgba(255,77,77,0.3); box-shadow: 0 0 10px rgba(255,77,77,0.1); }
.risk-high     { color: #ff9f43; background: rgba(255,159,67,0.1); border: 1px solid rgba(255,159,67,0.3); box-shadow: 0 0 10px rgba(255,159,67,0.1); }
.risk-medium   { color: #feca57; background: rgba(254,202,87,0.1); border: 1px solid rgba(254,202,87,0.3); box-shadow: 0 0 10px rgba(254,202,87,0.1); }
.risk-low      { color: #1dd1a1; background: rgba(29,209,161,0.1); border: 1px solid rgba(29,209,161,0.3); box-shadow: 0 0 10px rgba(29,209,161,0.1); }
.risk-badge {
    display: inline-block; padding: 0.4rem 1.2rem;
    border-radius: 30px; font-weight: 600;
    font-size: 0.85rem; letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* ── Risk factor cards ── */
.risk-factor-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-left: 5px solid;
    border-radius: 12px; padding: 1.5rem;
    margin-bottom: 1rem;
    transition: all 0.3s ease;
    backdrop-filter: blur(8px);
}
.risk-factor-card:hover { 
    background: rgba(255,255,255,0.04); 
    transform: translateX(4px);
}

/* ── Section headers ── */
.section-header {
    font-family: 'Outfit', sans-serif;
    font-size: 1.4rem; font-weight: 700;
    color: #ffffff; margin-bottom: 1.5rem;
    padding-bottom: 0.8rem;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    display: flex; align-items: center; gap: 0.8rem;
    letter-spacing: -0.5px;
}

/* ── Score gauge ── */
.score-ring { text-align: center; padding: 1rem; }
.score-number { 
    font-size: 4.5rem; font-weight: 800; 
    background: linear-gradient(135deg, #1dd1a1, #00d2d3, #48dbfb);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    line-height: 1; margin-bottom: 0.5rem;
}
.score-label { color: rgba(255,255,255,0.5); font-size: 0.9rem; font-weight: 500; text-transform: uppercase; letter-spacing: 1px; }

/* ── Progress bar ── */
.custom-progress {
    background: rgba(255,255,255,0.05);
    border-radius: 10px; height: 8px;
    overflow: hidden; margin: 0.5rem 0;
    box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
}
.custom-progress-fill {
    height: 100%; border-radius: 10px;
    transition: width 1s cubic-bezier(0.1, 0.8, 0.3, 1);
}

/* ── Source chips ── */
.source-chip {
    display: inline-block; 
    background: rgba(130, 170, 255, 0.1);
    border: 1px solid rgba(130, 170, 255, 0.2);
    border-radius: 8px; padding: 0.3rem 0.8rem;
    font-size: 0.75rem; color: #a2ccfe;
    margin: 0.3rem 0.3rem 0.3rem 0;
    font-family: 'JetBrains Mono', monospace;
    transition: background 0.2s;
}
.source-chip:hover { background: rgba(130, 170, 255, 0.2); }

/* ── Info callout & vuln items ── */
.info-callout, .vuln-item, .action-item {
    background: rgba(255,255,255,0.03);
    border-radius: 10px; padding: 1.2rem;
    margin: 0.8rem 0;
    color: rgba(255,255,255,0.85);
    font-size: 0.95rem; line-height: 1.5;
    border: 1px solid rgba(255,255,255,0.05);
    transition: transform 0.2s;
}
.info-callout:hover, .vuln-item:hover, .action-item:hover { transform: translateY(-2px); }
.info-callout { border-left: 4px solid #82aaff; background: linear-gradient(90deg, rgba(130,170,255,0.05) 0%, transparent 100%); }
.vuln-item { border-left: 4px solid #ff4d4d; background: linear-gradient(90deg, rgba(255,77,77,0.05) 0%, transparent 100%); }
.action-item { border-left: 4px solid #1dd1a1; background: linear-gradient(90deg, rgba(29,209,161,0.05) 0%, transparent 100%); }

/* ── Streamlit overrides ── */
.stTextInput input, .stSelectbox select {
    background: rgba(255,255,255,0.03) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    color: #ffffff !important;
    border-radius: 12px !important;
    padding: 0.7rem 1rem !important;
    transition: border-color 0.3s, background 0.3s !important;
    font-size: 0.95rem !important;
}
.stTextInput input:focus, .stSelectbox select:focus {
    border-color: #82aaff !important;
    background: rgba(255,255,255,0.06) !important;
    box-shadow: 0 0 0 2px rgba(130,170,255,0.2) !important;
}
.stButton button {
    background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%) !important;
    color: white !important; border: none !important;
    border-radius: 12px !important;
    font-weight: 600 !important; font-family: 'Outfit', sans-serif !important;
    letter-spacing: 0.5px !important;
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
    box-shadow: 0 4px 15px rgba(59,130,246,0.3) !important;
    padding: 0.6rem 0 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
}
.stButton button:hover {
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 8px 25px rgba(59,130,246,0.5) !important;
    background: linear-gradient(135deg, #2563eb 0%, #60a5fa 100%) !important;
}
.stButton button:active {
    transform: translateY(0) scale(0.98) !important;
}

.stExpander {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    transition: background 0.3s !important;
}
.stExpander:hover { background: rgba(255,255,255,0.04) !important; }

/* Tabs matching pro theme */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(255,255,255,0.02);
    border-bottom: 1px solid rgba(255,255,255,0.05);
    padding: 0; gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    color: rgba(255,255,255,0.5) !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 1rem 1.5rem !important;
    font-weight: 500 !important;
    transition: all 0.3s !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    background: transparent !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: rgba(255,255,255,0.8) !important;
    background: rgba(255,255,255,0.02) !important;
}
.stTabs [aria-selected="true"] {
    color: #82aaff !important;
    border-bottom: 3px solid #82aaff !important;
    background: linear-gradient(180deg, transparent 0%, rgba(130,170,255,0.05) 100%) !important;
}

/* Hide status spinner widget from top */
div[data-testid="stStatusWidget"] { display: none; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Helper: risk level styling ────────────────────────────────────────────────
RISK_COLORS = {
    "Critical": ("#ff5252", "rgba(255,82,82,0.5)"),
    "High": ("#ff9800", "rgba(255,152,0,0.5)"),
    "Medium": ("#ffeb3b", "rgba(255,235,59,0.5)"),
    "Low": ("#69f0ae", "rgba(105,240,174,0.5)"),
}
RISK_CLASS = {
    "Critical": "risk-critical",
    "High": "risk-high",
    "Medium": "risk-medium",
    "Low": "risk-low",
}


def risk_badge(level: str) -> str:
    css_class = RISK_CLASS.get(level, "risk-medium")
    return f'<span class="risk-badge {css_class}">{level}</span>'


def score_bar(score: float, color: str = "#63b3ed", max_val: float = 10.0) -> str:
    pct = (score / max_val) * 100
    return f"""
<div class="custom-progress">
    <div class="custom-progress-fill" style="width:{pct}%; background: {color};"></div>
</div>"""


def render_hero():
    st.markdown(
        """
    <div class="hero-banner">
        <div class="hero-title">🔗 Supply Chain Risk Analyzer</div>
        <div class="hero-subtitle">
            AI-powered intelligence platform — real-time disruption monitoring, 
            geopolitical risk assessment & mitigation strategy generation
        </div>
        <div class="hero-badges">
            <span class="badge">🤖 Gemini Pro</span>
            <span class="badge">🔍 Tavily Search</span>
            <span class="badge">⚖️  LLM-as-Judge</span>
            <span class="badge">🧠 Multi-Agent</span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    pass

def render_metrics(result: AnalysisResult):
    assessment = result.risk_assessment
    evaluation = result.judge_evaluation
    risk_color, _ = RISK_COLORS.get(assessment.overall_risk_level.value, ("#ffeb3b", ""))

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Overall Risk</div>
            <div style="margin-top:0.5rem">{risk_badge(assessment.overall_risk_level.value)}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Quality Score</div>
            <div class="metric-value" style="color:#69f0ae;">{evaluation.overall_score:.1f}<span style="font-size:1rem; color:rgba(255,255,255,0.3)">/10</span></div>
            <div class="metric-sub">LLM Judge Rating</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Risk Factors</div>
            <div class="metric-value">{len(assessment.risk_factors)}</div>
            <div class="metric-sub">Identified</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Sources Analyzed</div>
            <div class="metric-value">{len(result.search_results)}</div>
            <div class="metric-sub">Real-time articles</div>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with col5:
        st.markdown(
            f"""
        <div class="metric-card">
            <div class="metric-label">Analysis Time</div>
            <div class="metric-value" style="font-size:1.6rem;">{result.processing_time_seconds:.0f}s</div>
            <div class="metric-sub">Confidence: {assessment.confidence_score:.0%}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )


@st.dialog("Risk Factor Deep Dive", width="large")
def show_risk_dialog(rf, result: AnalysisResult):
    color, _ = RISK_COLORS.get(rf.severity.value, ("#ffeb3b", ""))
    st.markdown(f"<h2 style='color: {color}; margin-bottom:0;'>{rf.category}</h2>", unsafe_allow_html=True)
    st.markdown(f"**Severity:** {rf.severity.value} &nbsp;|&nbsp; **Likelihood:** {rf.likelihood.value}")
    st.divider()
    
    st.markdown("### 📝 Detailed Description")
    st.write(rf.description)
    
    st.markdown("### 🎯 Affected Areas")
    for area in rf.affected_areas:
        st.markdown(f"- {area}")
        
    st.markdown("### 🔗 Relevant Intelligence Sources")
    st.caption("Auto-matched realtime sources related to this risk category.")
    
    # Match keywords from category
    keywords = rf.category.lower().split()
    shown = 0
    for src in result.search_results:
        # Simple heuristic to match sources with the risk factor
        if any(k in src.content.lower() or k in src.title.lower() for k in keywords) or shown < 3:
            with st.container():
                st.markdown(f"**[{src.title}]({src.url})**")
                st.markdown(f"<div style='color:rgba(255,255,255,0.6); font-size:0.85rem; margin-bottom:1rem;'>{src.content[:300]}...</div>", unsafe_allow_html=True)
                shown += 1


def render_risk_factors(result: AnalysisResult):
    assessment = result.risk_assessment
    st.markdown(
        '<div class="section-header">⚠️ Risk Factors Identified</div>',
        unsafe_allow_html=True,
    )

    # Donut Chart for Risk Severities
    severity_counts = {}
    for rf in assessment.risk_factors:
        severity_counts[rf.severity.value] = severity_counts.get(rf.severity.value, 0) + 1
    
    if severity_counts:
        df = pd.DataFrame(list(severity_counts.items()), columns=["Severity", "Count"])
        color_map = {
            "Critical": "#ff5252",
            "High": "#ff9800",
            "Medium": "#ffeb3b",
            "Low": "#69f0ae"
        }
        fig = px.pie(
            df, values='Count', names='Severity', hole=0.6,
            color='Severity', color_discrete_map=color_map
        )
        fig.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=True,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(255,255,255,0.7)', family='Inter'),
            height=300
        )
        fig.update_traces(textposition='inside', textinfo='percent', marker=dict(line=dict(color='rgba(255,255,255,0.1)', width=2)))
        st.plotly_chart(fig, use_container_width=True)

    for idx, rf in enumerate(assessment.risk_factors):
        color, border_color = RISK_COLORS.get(rf.severity.value, ("#ffeb3b", "rgba(255,235,59,0.5)"))
        st.markdown(
            f"""
        <div class="risk-factor-card" style="border-left-color: {color}; margin-bottom: 0.2rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.4rem;">
                <span style="color:#e3f2fd; font-weight:600; font-size:0.95rem;">
                    {rf.category}
                </span>
                <div>
                    {risk_badge(rf.severity.value)}
                    &nbsp;<span style="color:rgba(255,255,255,0.4); font-size:0.75rem;">likelihood: {rf.likelihood.value}</span>
                </div>
            </div>
            <div style="color:rgba(255,255,255,0.7); font-size:0.87rem; line-height:1.5;">{rf.description}</div>
            <div style="margin-top:0.5rem; display:flex; gap:0.4rem; flex-wrap:wrap;">
                {"".join(f'<span class="source-chip">{area}</span>' for area in rf.affected_areas)}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )
        # We place a button explicitly tied to opening the new modal
        if st.button(f"📄 View {rf.category} Detail & Links", key=f"dialog_btn_{rf.category}_{idx}", use_container_width=True):
            show_risk_dialog(rf, result)
        
        st.markdown("<br>", unsafe_allow_html=True)


def render_mitigation_strategies(result: AnalysisResult):
    assessment = result.risk_assessment
    st.markdown(
        '<div class="section-header">🛡️ Mitigation Strategies</div>',
        unsafe_allow_html=True,
    )

    priority_colors = {"High": "#ff5252", "Medium": "#ff9800", "Low": "#69f0ae"}
    timeframe_icons = {"Immediate": "⚡", "Short-term": "📅", "Long-term": "🔭"}

    for ms in assessment.mitigation_strategies:
        p_color = priority_colors.get(ms.priority, "#63b3ed")
        t_icon = timeframe_icons.get(ms.timeframe, "📌")
        st.markdown(
            f"""
        <div class="risk-factor-card" style="border-left-color: {p_color};">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
                <span style="color:#90caf9; font-size:0.8rem; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">
                    {ms.risk_category}
                </span>
                <div style="display:flex; gap:0.5rem; align-items:center;">
                    <span style="color:{p_color}; font-size:0.75rem; font-weight:700;">{ms.priority} Priority</span>
                    <span style="color:rgba(255,255,255,0.4); font-size:0.75rem;">{t_icon} {ms.timeframe}</span>
                </div>
            </div>
            <div style="color:#e3f2fd; font-weight:500; font-size:0.9rem; margin-bottom:0.4rem;">{ms.strategy}</div>
            <div style="color:rgba(255,255,255,0.5); font-size:0.8rem;">
                <span style="color:#69f0ae;">📈 Expected Impact:</span> {ms.estimated_impact}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_judge_panel(result: AnalysisResult):
    ev = result.judge_evaluation
    st.markdown(
        '<div class="section-header">⚖️ LLM-as-Judge Evaluation</div>',
        unsafe_allow_html=True,
    )

    # Radar Chart for Judge Metrics
    categories = ['Depth', 'Actionability', 'Coverage']
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[ev.depth_score, ev.actionability_score, ev.coverage_score],
        theta=categories,
        fill='toself',
        fillcolor='rgba(130, 170, 255, 0.2)',
        line=dict(color='#82aaff', width=2),
        marker=dict(color='#63b3ed', size=8)
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 10], color='rgba(255,255,255,0.4)', gridcolor='rgba(255,255,255,0.1)'),
            angularaxis=dict(color='rgba(255,255,255,0.8)', gridcolor='rgba(255,255,255,0.1)', linecolor='rgba(255,255,255,0.1)')
        ),
        showlegend=False,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='rgba(255,255,255,0.8)', family='Inter'),
        margin=dict(t=30, b=30, l=30, r=30),
        height=320
    )
    st.plotly_chart(fig, use_container_width=True)

    col_score, col_details = st.columns([1, 2])
    with col_score:
        overall_color = (
            "#69f0ae" if ev.overall_score >= 7
            else "#ff9800" if ev.overall_score >= 5
            else "#ff5252"
        )
        st.markdown(
            f"""
<div class="metric-card" style="text-align:center; padding: 2rem 1rem;">
    <div class="metric-label">Overall Score</div>
    <div style="font-size: 4rem; font-weight:800; color:{overall_color}; line-height:1;">
        {ev.overall_score:.1f}
    </div>
    <div style="color:rgba(255,255,255,0.4); font-size:0.8rem;">out of 10.0</div>
</div>

<div style="margin-top:1rem;">
    <div style="color:rgba(255,255,255,0.5); font-size:0.75rem; margin-bottom:0.3rem;">Depth</div>
    {score_bar(ev.depth_score, "#63b3ed")}
    <div style="color:#63b3ed; font-size:0.85rem; font-weight:600;">{ev.depth_score:.1f}/10</div>

    <div style="color:rgba(255,255,255,0.5); font-size:0.75rem; margin:0.5rem 0 0.3rem;">Actionability</div>
    {score_bar(ev.actionability_score, "#69f0ae")}
    <div style="color:#69f0ae; font-size:0.85rem; font-weight:600;">{ev.actionability_score:.1f}/10</div>

    <div style="color:rgba(255,255,255,0.5); font-size:0.75rem; margin:0.5rem 0 0.3rem;">Coverage</div>
    {score_bar(ev.coverage_score, "#ff9800")}
    <div style="color:#ff9800; font-size:0.85rem; font-weight:600;">{ev.coverage_score:.1f}/10</div>
</div>
""",
            unsafe_allow_html=True,
        )

    with col_details:
        st.markdown(
            f"""
        <div class="info-callout" style="border-left-color:#69f0ae;">
            <b style="color:#69f0ae;">📝 Judge Verdict</b><br>
            {ev.verdict}
        </div>
        """,
            unsafe_allow_html=True,
        )

        col_s, col_i = st.columns(2)
        with col_s:
            st.markdown(
                '<div style="color:#69f0ae; font-weight:600; font-size:0.85rem; margin-bottom:0.4rem;">✅ Strengths</div>',
                unsafe_allow_html=True,
            )
            for s in ev.strengths:
                st.markdown(
                    f'<div class="action-item">• {s}</div>', unsafe_allow_html=True
                )
        with col_i:
            st.markdown(
                '<div style="color:#ff9800; font-weight:600; font-size:0.85rem; margin-bottom:0.4rem;">🔧 Improvements</div>',
                unsafe_allow_html=True,
            )
            for imp in ev.improvements:
                st.markdown(
                    f'<div class="vuln-item" style="border-left-color:rgba(255,152,0,0.5);">• {imp}</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown(
            f"""
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.8rem; margin-top:0.5rem;">
            <div class="metric-card">
                <div class="metric-label">Depth Feedback</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.8rem; margin-top:0.4rem;">{ev.depth_feedback[:180]}…</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Actionability Feedback</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.8rem; margin-top:0.4rem;">{ev.actionability_feedback[:180]}…</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Coverage Feedback</div>
                <div style="color:rgba(255,255,255,0.7); font-size:0.8rem; margin-top:0.4rem;">{ev.coverage_feedback[:180]}…</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )


def render_sourcing_panel(result: AnalysisResult):
    st.markdown(
        '<div class="section-header">🌍 Alternative Sourcing Hubs</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<p style='color:rgba(255,255,255,0.7); font-size:0.9rem;'>The Sourcing Agent scouted the following regions as viable alternatives:</p>", unsafe_allow_html=True)
    
    for alt in result.sourcing_alternatives.recommended_alternatives:
        score_color = "#69f0ae" if alt.viability_score >= 7 else "#ffeb3b" if alt.viability_score >= 4 else "#ff5252"
        st.markdown(f"""
        <div class="risk-factor-card" style="border-left-color: {score_color}; margin-bottom: 0.2rem;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.4rem;">
                <span style="color:#e3f2fd; font-weight:600; font-size:1.1rem;">
                    {alt.region}
                </span>
                <div style="font-weight:700; color:{score_color};">
                    Score: {alt.viability_score}/10
                </div>
            </div>
            <div style="display:flex; width: 100%; gap: 1rem; margin-top: 0.5rem;">
                <div style="flex:1;">
                    <b style='color:#69f0ae; font-size:0.85rem;'>✅ Pros</b>
                    {''.join(f"<div style='color:rgba(255,255,255,0.8); font-size:0.85rem; margin-bottom:0.2rem;'>• {p}</div>" for p in alt.pros)}
                </div>
                <div style="flex:1;">
                    <b style='color:#ff5252; font-size:0.85rem;'>⚠️ Cons</b>
                    {''.join(f"<div style='color:rgba(255,255,255,0.8); font-size:0.85rem; margin-bottom:0.2rem;'>• {c}</div>" for c in alt.cons)}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("")


def render_result(result: AnalysisResult):
    assessment = result.risk_assessment

    st.markdown("<br>", unsafe_allow_html=True)
    render_metrics(result)
    st.markdown("<br>", unsafe_allow_html=True)

    # ── Executive Summary ──
    with st.expander("📋 Executive Summary", expanded=True):
        st.markdown(
            f"""
        <div style="color:rgba(255,255,255,0.8); line-height:1.8; font-size:0.92rem;">
            {assessment.executive_summary.replace(chr(10), '<br><br>')}
        </div>
        """,
            unsafe_allow_html=True,
        )

    # ── Main tabs ──
    tab1, tab2, tab_alt, tab3, tab4, tab5 = st.tabs(
        ["⚠️ Risk Factors", "🛡️ Mitigations", "🌍 Alt Sourcing", "⚖️ Judge Report", "🔍 Sources", "📊 Vulnerabilities"]
    )

    with tab1:
        render_risk_factors(result)

    with tab2:
        render_mitigation_strategies(result)

    with tab_alt:
        if getattr(result, "sourcing_alternatives", None) and getattr(result.sourcing_alternatives, "recommended_alternatives", None):
            render_sourcing_panel(result)
        else:
            st.info("No alternative sourcing hubs were identified or the agent was skipped.")

    with tab3:
        render_judge_panel(result)

    with tab4:
        st.markdown(
            '<div class="section-header">🔍 Intelligence Sources</div>',
            unsafe_allow_html=True,
        )
        for i, src in enumerate(result.search_results):
            with st.expander(f"[{i+1}] {src.title[:80]}", expanded=False):
                st.markdown(
                    f"""
                <div style="margin-bottom:0.5rem;">
                    <a href="{src.url}" target="_blank" style="color:#63b3ed; font-size:0.8rem;">
                        🔗 {src.url[:80]}
                    </a>
                    {f'<span style="color:rgba(255,255,255,0.3); font-size:0.75rem; margin-left:0.5rem;">Score: {src.score:.3f}</span>' if src.score else ''}
                </div>
                <div style="color:rgba(255,255,255,0.6); font-size:0.85rem; line-height:1.6;">
                    {src.content[:600]}…
                </div>
                """,
                    unsafe_allow_html=True,
                )

    with tab5:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(
                '<div class="section-header">🚨 Key Vulnerabilities</div>',
                unsafe_allow_html=True,
            )
            for v in assessment.key_vulnerabilities:
                st.markdown(
                    f'<div class="vuln-item">⚠️ {v}</div>', unsafe_allow_html=True
                )

        with col_right:
            st.markdown(
                '<div class="section-header">✅ Recommended Actions</div>',
                unsafe_allow_html=True,
            )
            for a in assessment.recommended_actions:
                st.markdown(
                    f'<div class="action-item">→ {a}</div>', unsafe_allow_html=True
                )


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    render_hero()
    render_sidebar()

    # ── Input form ──
    st.markdown(
        '<div class="section-header">🎯 Analysis Parameters</div>',
        unsafe_allow_html=True,
    )

    EXAMPLE_PRODUCTS = [
        "Semiconductors / Microchips",
        "Lithium Batteries / EV Components",
        "Pharmaceutical APIs",
        "Solar Panels / Photovoltaic Cells",
        "Rare Earth Elements",
        "Automotive Parts",
        "Medical Devices",
        "Textiles / Apparel",
        "Agricultural Commodities",
        "Custom...",
    ]
    EXAMPLE_REGIONS = [
        "China",
        "Taiwan",
        "Southeast Asia (Vietnam/Thailand/Malaysia)",
        "South Asia (India/Bangladesh/Pakistan)",
        "Eastern Europe (Poland/Ukraine/Romania)",
        "Middle East (UAE/Saudi Arabia)",
        "Sub-Saharan Africa",
        "Latin America (Mexico/Brazil)",
        "Custom...",
    ]

    col_cat, col_reg, col_btn = st.columns([2, 2, 1])
    with col_cat:
        product_choice = st.selectbox(
            "Product Category",
            EXAMPLE_PRODUCTS,
            index=0,
            key="product_select",
        )
        if product_choice == "Custom...":
            product_category = st.text_input(
                "Enter product category",
                placeholder="e.g., Advanced OLED Displays",
                key="product_custom",
            )
        else:
            product_category = product_choice

    with col_reg:
        region_choice = st.selectbox(
            "Sourcing Region",
            EXAMPLE_REGIONS,
            index=0,
            key="region_select",
        )
        if region_choice == "Custom...":
            sourcing_region = st.text_input(
                "Enter sourcing region",
                placeholder="e.g., Northern Mexico",
                key="region_custom",
            )
        else:
            sourcing_region = region_choice

    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        analyze_btn = st.button("🚀 Analyze Risk", use_container_width=True, type="primary")

    # ── Validation & Run ──
    if analyze_btn:
        if not product_category or not sourcing_region:
            st.error("Please select or enter both a product category and sourcing region.")
            return

        is_valid, errors = validate_config()
        if not is_valid:
            st.error("Cannot run analysis — API keys not configured:")
            for err in errors:
                st.error(f"  • {err}")
            return

        # Live progress UI
        status_container = st.container()
        with status_container:
            progress_placeholder = st.empty()
            log_placeholder = st.empty()

        log_messages = []

        def progress_callback(msg: str):
            progress_placeholder.markdown(
                f"""
            <div style="background:rgba(99,179,237,0.08); border:1px solid rgba(99,179,237,0.2); 
                        border-radius:10px; padding:0.8rem 1.2rem; color:#90caf9; font-size:0.9rem;">
                <div class="blinking-dot" style="display:inline-block; width:8px; height:8px; 
                     background:#63b3ed; border-radius:50%; margin-right:0.5rem; 
                     animation: blink 1s infinite;"></div>
                {msg}
            </div>
            <style>
            @keyframes blink {{ 0%,100%{{opacity:1}} 50%{{opacity:0.2}} }}
            </style>
            """,
                unsafe_allow_html=True,
            )
            log_messages.append(msg)
            log_placeholder.markdown(
                "<br>".join(
                    f'<span style="color:rgba(255,255,255,0.3); font-size:0.75rem;">  • {m}</span>'
                    for m in log_messages[-5:]
                ),
                unsafe_allow_html=True,
            )

        try:
            from agents.pipeline import SupplyChainPipeline

            pipeline = SupplyChainPipeline()
            result = pipeline.run(
                product_category=product_category,
                sourcing_region=sourcing_region,
                progress_callback=progress_callback,
            )

            # Clear progress UI
            progress_placeholder.empty()
            log_placeholder.empty()

            # Store result in session state
            st.session_state["last_result"] = result
            st.session_state["last_params"] = {
                "product": product_category,
                "region": sourcing_region,
            }

            st.success(
                f"✅ Analysis complete! Risk: **{result.risk_assessment.overall_risk_level.value}** | "
                f"Judge Score: **{result.judge_evaluation.overall_score:.1f}/10**"
            )

        except ValueError as exc:
            progress_placeholder.empty()
            log_placeholder.empty()
            st.error(f"Configuration Error: {exc}")
            return
        except Exception as exc:
            progress_placeholder.empty()
            log_placeholder.empty()
            st.error(f"Analysis Failed: {exc}")
            logger.exception("Pipeline run failed")
            return

    # ── Render stored result ──
    if "last_result" in st.session_state:
        params = st.session_state.get("last_params", {})
        st.markdown(
            f"""
        <div style="background:rgba(255,255,255,0.03); border:1px solid rgba(99,179,237,0.1); 
                    border-radius:10px; padding:0.6rem 1.2rem; margin-bottom:0.5rem;
                    color:rgba(255,255,255,0.5); font-size:0.8rem;">
            📊 Showing results for: 
            <b style="color:#90caf9;">{params.get('product', '')}</b> sourced from 
            <b style="color:#90caf9;">{params.get('region', '')}</b>
        </div>
        """,
            unsafe_allow_html=True,
        )
        render_result(st.session_state["last_result"])


if __name__ == "__main__":
    main()
