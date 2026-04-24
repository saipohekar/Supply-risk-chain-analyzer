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
from utils.config import validate_config, GROQ_API_KEY, TAVILY_API_KEY
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
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@500;700;900&family=Rajdhani:wght@500;600;700&family=Share+Tech+Mono&display=swap');

/* ── Global Reset & Typography ── */
html, body, [class*="css"] {
    font-family: 'Rajdhani', sans-serif;
    color: #aed9e0;
}
h1, h2, h3, h4, h5, h6 { font-family: 'Orbitron', sans-serif !important; text-transform: uppercase; }
.hero-title, .metric-value, .score-number { font-family: 'Orbitron', sans-serif !important; }

/* Hide streamlit branding */
#MainMenu, footer, header { visibility: hidden; }

/* ── Cyber Grid Background ── */
.stApp {
    background-color: #030308;
    background-image:
        linear-gradient(rgba(0, 243, 255, 0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0, 243, 255, 0.05) 1px, transparent 1px),
        radial-gradient(circle at 10% 20%, rgba(255, 0, 85, 0.1) 0%, transparent 40%),
        radial-gradient(circle at 90% 80%, rgba(0, 243, 255, 0.1) 0%, transparent 40%);
    background-size: 50px 50px, 50px 50px, 100% 100%, 100% 100%;
    min-height: 100vh;
}

/* ── Scan line overlay ── */
.stApp::after {
    content: '';
    position: fixed;
    top: 0; left: 0; width: 100%; height: 100%;
    background: repeating-linear-gradient(
        0deg,
        rgba(0,0,0,0.15) 0px,
        rgba(0,0,0,0.15) 1px,
        transparent 1px,
        transparent 3px
    );
    pointer-events: none;
    z-index: 10000;
}

/* ── Keyframe Animations ── */
@keyframes slideUpFade {
    0%   { opacity: 0; transform: translateY(40px) scale(0.98); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes neonPulse {
    0%, 100% { box-shadow: 0 0 10px rgba(0,243,255,0.4), 0 0 30px rgba(0,243,255,0.1); }
    50%      { box-shadow: 0 0 25px rgba(0,243,255,0.8), 0 0 50px rgba(0,243,255,0.3), inset 0 0 15px rgba(0,243,255,0.2); }
}
@keyframes holoScan {
    0%   { transform: translateY(-100%) rotate(0deg); opacity: 0; }
    50%  { opacity: 0.3; }
    100% { transform: translateY(1000%) rotate(0deg); opacity: 0; }
}
@keyframes glitchText {
    0%, 100% { text-shadow: 2px 0 rgba(255,0,85,0.8), -2px 0 rgba(0,243,255,0.8); }
    33%      { text-shadow: -2px 0 rgba(255,0,85,0.8), 2px 0 rgba(0,243,255,0.8); }
    66%      { text-shadow: 2px 0 rgba(0,243,255,0.8), -2px 0 rgba(255,0,85,0.8); }
}
@keyframes textGlow {
    from { filter: drop-shadow(0 0 5px rgba(255,0,85,0.5)); }
    to   { filter: drop-shadow(0 0 15px rgba(255,0,85,0.9)); }
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(3,3,8,0.98) !important;
    border-right: 2px solid #00f3ff !important;
    box-shadow: 5px 0 20px rgba(0,243,255,0.1);
}
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #00f3ff !important;
    font-size: 1.1rem !important;
    letter-spacing: 3px;
    text-transform: uppercase;
    text-shadow: 0 0 8px rgba(0,243,255,0.6);
}

/* ── Hero Banner ── */
.hero-banner {
    position: relative; overflow: hidden;
    background: linear-gradient(135deg, rgba(8,8,15,0.95), rgba(3,3,8,0.98));
    padding: 3.5rem 3rem;
    margin-bottom: 2.5rem;
    border-left: 4px solid #ff0055;
    border-right: 4px solid #00f3ff;
    clip-path: polygon(0 0, 100% 0, 100% calc(100% - 20px), calc(100% - 20px) 100%, 0 100%, 0 0);
    box-shadow: 0 0 40px rgba(0,243,255,0.1);
    animation: slideUpFade 0.6s cubic-bezier(0.2,1,0.3,1) forwards;
}
.hero-banner::after {
    content: ''; position: absolute; top: -100px; left: -50%;
    width: 200%; height: 50px;
    background: linear-gradient(180deg, transparent, rgba(0,243,255,0.5), transparent);
    animation: holoScan 4s linear infinite;
    pointer-events: none;
}
.hero-title {
    font-size: 3rem; font-weight: 900;
    color: #fff;
    animation: glitchText 4s infinite reverse;
    margin: 0; line-height: 1;
    letter-spacing: 4px;
    text-transform: uppercase;
}
.hero-subtitle {
    font-family: 'Share Tech Mono', monospace;
    color: #00f3ff;
    font-size: 1rem; margin-top: 1.2rem;
    line-height: 1.6;
    letter-spacing: 1px;
    text-shadow: 0 0 5px rgba(0,243,255,0.3);
}
.hero-badges { display: flex; gap: 1rem; margin-top: 2rem; flex-wrap: wrap; }
.badge {
    background: transparent;
    border: 1px solid #ff0055;
    padding: 0.4rem 1.2rem;
    font-size: 0.75rem;
    font-family: 'Share Tech Mono', monospace;
    color: #ff0055;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    box-shadow: 0 0 10px rgba(255,0,85,0.2), inset 0 0 5px rgba(255,0,85,0.2);
    transition: all 0.2s;
    clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px);
}
.badge:hover {
    background: #ff0055;
    color: #000;
    box-shadow: 0 0 20px rgba(255,0,85,0.6);
}

/* ── Metric Cards ── */
.metric-card {
    position: relative;
    background: rgba(10,10,15,0.85);
    border: 1px solid rgba(0,243,255,0.2);
    padding: 1.5rem;
    backdrop-filter: blur(5px);
    transition: all 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
    clip-path: polygon(0 0, calc(100% - 15px) 0, 100% 15px, 100% 100%, 15px 100%, 0 calc(100% - 15px));
    animation: slideUpFade 0.5s ease-out forwards;
    opacity: 0;
}
.metric-card::before {
    content: '';
    position: absolute; top: 0; left: 0;
    width: 100%; height: 3px;
    background: #00f3ff;
    box-shadow: 0 0 10px #00f3ff;
    opacity: 0.5;
}
.metric-card:hover {
    transform: translateY(-8px);
    border-color: #00f3ff;
    background: rgba(0,243,255,0.05);
    box-shadow: 0 15px 40px rgba(0,0,0,0.8);
}
.metric-card:hover::before { background: #ff0055; box-shadow: 0 0 15px #ff0055; opacity: 1; }
.metric-label {
    color: #00f3ff;
    font-size: 0.75rem; font-weight: 700;
    font-family: 'Share Tech Mono', monospace;
    text-transform: uppercase; letter-spacing: 3px;
    margin-bottom: 0.8rem;
}
.metric-value {
    font-size: 2.8rem;
    color: #fff;
    text-shadow: 0 0 20px rgba(0,243,255,0.6);
}
.metric-sub { color: rgba(255,255,255,0.4); font-size: 0.85rem; margin-top: 0.6rem; font-family: 'Share Tech Mono', monospace; }

/* ── Risk Badges ── */
.risk-critical { color: #000; background: #ff0055; box-shadow: 0 0 15px #ff0055; }
.risk-high { color: #000; background: #ffaa00; box-shadow: 0 0 15px #ffaa00; }
.risk-medium { color: #000; background: #ffee00; box-shadow: 0 0 15px #ffee00; }
.risk-low { color: #000; background: #00f3ff; box-shadow: 0 0 15px #00f3ff; }
.risk-badge {
    display: inline-block; padding: 0.3rem 0.8rem;
    font-weight: 900; font-size: 0.75rem;
    letter-spacing: 2px; text-transform: uppercase;
    font-family: 'Orbitron', sans-serif;
    clip-path: polygon(5px 0, 100% 0, calc(100% - 5px) 100%, 0 100%);
}

/* ── Risk Factor Cards ── */
.risk-factor-card {
    background: rgba(10,12,18,0.9);
    border: 1px solid rgba(255,255,255,0.1);
    border-left: 4px solid #00f3ff;
    padding: 1.5rem;
    margin-bottom: 1rem;
    clip-path: polygon(0 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%);
    transition: all 0.3s;
}
.risk-factor-card:hover {
    background: rgba(20,25,35,0.95);
    border-left-color: #ff0055;
    transform: translateX(8px);
    box-shadow: -10px 0 20px rgba(255,0,85,0.1);
}

/* ── Section Headers ── */
.section-header {
    font-size: 1.3rem;
    color: #fff; margin-bottom: 1.8rem;
    padding-bottom: 0.5rem;
    border-bottom: 2px dashed rgba(0,243,255,0.3);
    text-transform: uppercase; letter-spacing: 3px;
    text-shadow: 0 0 10px rgba(0,243,255,0.5);
    position: relative;
}
.section-header::after {
    content: ''; position: absolute; left: 0; bottom: -2px;
    width: 50px; height: 2px; background: #00f3ff;
    box-shadow: 0 0 10px #00f3ff;
}

/* ── Score ── */
.score-ring { padding: 1rem; text-align: center; }
.score-number {
    font-size: 5.5rem;
    color: #fff;
    text-shadow: 0 0 30px #00f3ff, 0 0 10px #fff;
    margin-bottom: 0px;
}
.score-label { color: #00f3ff; font-size: 0.9rem; letter-spacing: 3px; font-family: 'Share Tech Mono', monospace; }

/* ── Progress Bars ── */
.custom-progress {
    background: #000;
    height: 8px;
    border: 1px solid rgba(0,243,255,0.3);
    position: relative; overflow: hidden;
}
.custom-progress-fill {
    height: 100%;
    background: repeating-linear-gradient(-45deg, #00f3ff, #00f3ff 10px, #00b4ff 10px, #00b4ff 20px);
    box-shadow: 0 0 15px #00f3ff;
    transition: width 1s ease-in-out;
}

/* ── Source Chips ── */
.source-chip {
    display: inline-block; background: rgba(0,243,255,0.1);
    border: 1px solid #00f3ff; padding: 0.3rem 0.6rem;
    font-size: 0.7rem; color: #00f3ff;
    margin: 0.2rem 0.3rem 0.2rem 0;
    font-family: 'Share Tech Mono', monospace;
    text-transform: uppercase; letter-spacing: 1px;
    clip-path: polygon(5px 0, 100% 0, calc(100% - 5px) 100%, 0 100%);
}
.source-chip:hover { background: #00f3ff; color: #000; box-shadow: 0 0 15px #00f3ff; }

/* ── Info Callouts ── */
.info-callout, .vuln-item, .action-item {
    background: rgba(0,0,0,0.8);
    padding: 1.2rem; margin: 0.8rem 0;
    font-size: 0.95rem; border: 1px solid rgba(255,255,255,0.1);
    clip-path: polygon(0 0, 100% 0, 100% calc(100% - 12px), calc(100% - 12px) 100%, 0 100%);
    font-family: 'Share Tech Mono', monospace;
}
.info-callout { border-left: 4px solid #00f3ff; box-shadow: inset 20px 0 40px -20px rgba(0,243,255,0.2); color: #00f3ff; }
.vuln-item { border-left: 4px solid #ff0055; box-shadow: inset 20px 0 40px -20px rgba(255,0,85,0.2); color: #ff0055; }
.action-item { border-left: 4px solid #ffee00; box-shadow: inset 20px 0 40px -20px rgba(255,238,0,0.2); color: #ffee00; }

/* ── Streamlit Component Overrides ── */
.stTextInput input, .stSelectbox select {
    background: rgba(0,0,0,0.6) !important;
    border: 1px solid #00f3ff !important;
    color: #fff !important;
    border-radius: 0 !important;
    padding: 0.8rem !important;
    font-size: 0.95rem !important;
    font-family: 'Share Tech Mono', monospace !important;
    box-shadow: inset 0 0 10px rgba(0,243,255,0.1) !important;
}
.stTextInput input:focus, .stSelectbox select:focus {
    border-color: #ff0055 !important;
    box-shadow: 0 0 15px rgba(255,0,85,0.4), inset 0 0 10px rgba(255,0,85,0.2) !important;
}
.stButton button {
    background: transparent !important;
    color: #00f3ff !important;
    border: 2px solid #00f3ff !important;
    border-radius: 0 !important;
    font-weight: 900 !important; font-size: 0.85rem !important;
    letter-spacing: 3px !important; text-transform: uppercase !important;
    padding: 0.8rem 0 !important;
    position: relative; overflow: hidden;
    clip-path: polygon(15px 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%, 0 15px) !important;
    box-shadow: inset 0 0 10px rgba(0,243,255,0.1), 0 0 10px rgba(0,243,255,0.1) !important;
}
.stButton button:hover {
    background: #00f3ff !important; color: #000 !important;
    box-shadow: 0 0 25px #00f3ff, inset 0 0 10px rgba(255,255,255,0.5) !important;
}

.stExpander {
    background: rgba(0,0,0,0.8) !important;
    border: 1px solid rgba(0,243,255,0.3) !important;
    border-radius: 0 !important;
    clip-path: polygon(0 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%, 0 0) !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 2px solid rgba(0,243,255,0.2); }
.stTabs [data-baseweb="tab"] {
    color: rgba(0,243,255,0.5) !important; font-family: 'Orbitron', sans-serif !important;
    font-size: 0.8rem !important; letter-spacing: 2px !important; text-transform: uppercase !important;
    padding: 1rem 1.5rem !important; border: none !important; background: transparent !important;
    clip-path: polygon(10px 0, 100% 0, 100% 100%, 0 100%, 0 10px) !important;
}
.stTabs [data-baseweb="tab"]:hover { background: rgba(0,243,255,0.1) !important; color: #00f3ff !important; }
.stTabs [aria-selected="true"] {
    color: #fff !important; background: #00f3ff !important;
    text-shadow: 0 0 10px rgba(0,0,0,0.8);
}

/* ── Selectbox dropdown styling ── */
[data-baseweb="select"] > div, [data-baseweb="popover"] {
    background: #000 !important; border: 1px solid #00f3ff !important;
    border-radius: 0 !important; color: #00f3ff !important;
}

/* ── Success / Error alerts ── */
.stAlert {
    border-radius: 0 !important; border: 1px solid #00f3ff !important;
    background: rgba(0,243,255,0.05) !important;
    clip-path: polygon(0 0, 100% 0, 100% calc(100% - 15px), calc(100% - 15px) 100%, 0 100%) !important;
}

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
            <span class="badge">🤖 Groq 70B</span>
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
        st.plotly_chart(fig, width='stretch')

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


@st.dialog("Impact & Cost Projection", width="large")
def show_mitigation_dialog(ms):
    st.markdown(f"<h2 style='color: #63b3ed; margin-bottom:0;'>{ms.risk_category} Mitigation</h2>", unsafe_allow_html=True)
    st.markdown(f"**Strategy:** {ms.strategy}")
    st.markdown(f"**Expected Impact:** {ms.estimated_impact}")
    st.divider()
    
    import datetime
    import random
    import numpy as np
    
    st.markdown("### 📊 Projected Implementation Impact")
    
    # Generate real-time future timeline starting from current month
    current_date = datetime.datetime.now()
    months = [(current_date + datetime.timedelta(days=30 * i)).strftime("%b %Y") for i in range(1, 7)]
    
    # Simulate a dynamic projection algorithm with noise based on timeframe
    base_costs = {"Immediate": 50000, "Short-term": 20000, "Long-term": 10000}.get(ms.timeframe, 15000)
    decay_rate = {"Immediate": 0.4, "Short-term": 0.7, "Long-term": 0.9}.get(ms.timeframe, 0.8)
    
    risk_reduction = []
    costs = []
    current_risk = 100.0
    
    for i in range(6):
        # Calculate dynamic risk reduction
        if i == 0:
            risk_reduction.append(round(current_risk, 1))
        else:
            jitter = random.uniform(-5.0, 5.0)
            current_risk = current_risk * decay_rate + jitter
            current_risk = max(5.0, min(100.0, current_risk))
            risk_reduction.append(round(current_risk, 1))
            
        # Calculate costs
        monthly_cost = base_costs * (0.8 ** i) * random.uniform(0.9, 1.1)
        costs.append(int(monthly_cost))
        
    df = pd.DataFrame({
        "Timeline": months,
        "Risk Exposure (%)": risk_reduction,
        "Est. Cost ($)": costs
    })
    
    col1, col2 = st.columns([3, 2])
    with col1:
        fig = px.area(df, x="Timeline", y="Risk Exposure (%)", title="Risk Exposure Over Time")
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='rgba(255,255,255,0.7)', family='Inter'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', range=[0, 105]),
            margin=dict(t=40, b=20, l=20, r=20),
            height=300
        )
        fig.update_traces(line_color='#69f0ae', fillcolor='rgba(105, 240, 174, 0.2)')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("<div style='margin-top:2.5rem;'></div>", unsafe_allow_html=True)
        st.dataframe(df, hide_index=True, use_container_width=True)


def render_mitigation_strategies(result: AnalysisResult):
    assessment = result.risk_assessment
    st.markdown(
        '<div class="section-header">🛡️ Mitigation Strategies</div>',
        unsafe_allow_html=True,
    )

    priority_colors = {"High": "#ff5252", "Medium": "#ff9800", "Low": "#69f0ae"}
    timeframe_icons = {"Immediate": "⚡", "Short-term": "📅", "Long-term": "🔭"}

    for idx, ms in enumerate(assessment.mitigation_strategies):
        p_color = priority_colors.get(ms.priority, "#63b3ed")
        t_icon = timeframe_icons.get(ms.timeframe, "📌")
        st.markdown(
            f"""
        <div class="risk-factor-card" style="border-left-color: {p_color}; margin-bottom: 0.2rem;">
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
        if st.button(f"📊 View {ms.risk_category} Impact Graph & Table", key=f"mit_btn_{idx}", use_container_width=True):
            show_mitigation_dialog(ms)
            
        st.markdown("<br>", unsafe_allow_html=True)


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
    st.plotly_chart(fig, width='stretch')

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
        <span style="color:#e3f2fd; font-weight:600; font-size:1.1rem;">{alt.region}</span>
        <div style="font-weight:700; color:{score_color};">Score: {alt.viability_score}/10</div>
    </div>
    <div style="display:flex; width:100%; gap:1rem; margin-top:0.5rem;">
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
        '<div class="section-header">◈ Analysis Parameters</div>',
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
<div style="background:rgba(0,255,200,0.04); border:1px solid rgba(0,255,200,0.2);
            border-radius:6px; padding:0.9rem 1.3rem; font-family:'JetBrains Mono',monospace;">
    <span style="color:rgba(0,255,200,0.5); font-size:0.65rem; letter-spacing:2px;">// PIPELINE STATUS</span><br>
    <span style="display:inline-block; width:8px; height:8px; background:#00ffc8;
                 border-radius:50%; margin-right:0.6rem; animation:blink 0.8s infinite;
                 box-shadow:0 0 8px #00ffc8;"></span>
    <span style="color:#00ffc8; font-size:0.88rem; letter-spacing:0.5px;">{msg}</span>
</div>
<style>@keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:0.15}}}}</style>
""",
                unsafe_allow_html=True,
            )
            log_messages.append(msg)
            log_placeholder.markdown(
                "<br>".join(
                    f'<span style="color:rgba(0,255,200,0.2); font-size:0.72rem; font-family:\'JetBrains Mono\',monospace;">  ▸ {m}</span>'
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
<div style="background:rgba(0,255,200,0.03); border:1px solid rgba(0,255,200,0.12);
            border-radius:6px; padding:0.6rem 1.3rem; margin-bottom:1rem;
            font-family:'JetBrains Mono',monospace; font-size:0.72rem; letter-spacing:0.5px;">
    <span style="color:rgba(0,255,200,0.4);">// ACTIVE REPORT &nbsp;▸ &nbsp;</span>
    <span style="color:#00ffc8;">{params.get('product', '')}</span>
    <span style="color:rgba(0,255,200,0.4);"> &nbsp;◈&nbsp; ORIGIN: </span>
    <span style="color:#00b4ff;">{params.get('region', '')}</span>
</div>
""",
            unsafe_allow_html=True,
        )
        render_result(st.session_state["last_result"])


if __name__ == "__main__":
    main()
