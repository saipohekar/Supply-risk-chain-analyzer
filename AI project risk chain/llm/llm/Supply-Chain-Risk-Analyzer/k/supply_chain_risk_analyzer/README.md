# 🔗 Supply Chain Risk Analyzer

> AI-powered supply chain intelligence — real-time disruption monitoring, geopolitical risk assessment & mitigation strategy generation via a three-agent pipeline.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Research Agent** | 5 targeted Tavily searches across disruptions, geopolitics, logistics, environmental, and supplier risks |
| **Risk Assessment Agent** | Gemini Pro synthesizes intelligence into a structured JSON report with up to 8 risk factors and 6 mitigation strategies |
| **LLM-as-Judge** | Independent Gemini Flash evaluation scoring Depth (35%), Actionability (40%), Coverage (25%) on a 0–10 scale |
| **Rich UI** | Dark glassmorphism Streamlit app with animated hero, tabbed results, metric cards, score bars |

---

## 🏗️ Architecture

```
User Input (Product + Region)
         │
         ▼
┌─────────────────────┐
│   Research Agent    │  ← Tavily Multi-Query (5 searches)
│  (research_agent.py)│
└────────┬────────────┘
         │ 8 deduplicated SearchResult objects
         ▼
┌─────────────────────────────┐
│  Risk Assessment Agent      │  ← Gemini Pro (JSON-structured)
│  (risk_assessment_agent.py) │
└────────┬────────────────────┘
         │ RiskAssessment (Pydantic)
         ▼
┌─────────────────────┐
│    Judge Agent      │  ← Gemini Flash (independent evaluator)
│  (judge_agent.py)   │
└────────┬────────────┘
         │ JudgeEvaluation (Pydantic)
         ▼
    AnalysisResult → Streamlit UI
```

---

## 📁 Project Structure

```
supply_chain_risk_analyzer/
├── app.py                          # Streamlit UI (main entry point)
├── requirements.txt
├── .env                            # API keys (you fill this in)
├── .env.example
├── agents/
│   ├── __init__.py
│   ├── pipeline.py                 # Orchestrator
│   ├── research_agent.py           # Tavily multi-query agent
│   ├── risk_assessment_agent.py    # Gemini Pro structured assessment
│   └── judge_agent.py              # LLM-as-Judge evaluator
└── utils/
    ├── __init__.py
    ├── config.py                   # Environment & settings
    └── models.py                   # Pydantic data models
```

---

## 🚀 Quick Start

### 1. Get API Keys

| Service | Get Key | Cost |
|---|---|---|
| **Google Gemini** | [aistudio.google.com](https://aistudio.google.com) | Free tier available |
| **Tavily** | [tavily.com](https://tavily.com) | Free tier (1000 req/mo) |

### 2. Configure `.env`

```bash
# supply_chain_risk_analyzer/.env
GEMINI_API_KEY=AIza...your_real_key...
TAVILY_API_KEY=tvly-...your_real_key...
```

### 3. Install & Run

```bash
cd e:\k\supply_chain_risk_analyzer
pip install -r requirements.txt
streamlit run app.py
```

App runs at **http://localhost:8501**

---

## 🤖 Agent Details

### Research Agent
- Executes **5 parallel Tavily queries** covering:
  - Recent supply chain disruptions
  - Geopolitical risks & trade sanctions
  - Logistics/shipping delays & port congestion
  - Natural disasters & factory shutdowns
  - Supplier shortages & raw material scarcity
- Deduplicates results by URL, sorts by Tavily relevance score
- Returns top-8 most relevant articles

### Risk Assessment Agent
- Processes up to 8 search results as structured context
- Prompted with strict JSON schema (validated via Pydantic)
- Produces `RiskAssessment` with:
  - `overall_risk_level` → Low / Medium / High / Critical
  - `risk_factors` → Category, severity, likelihood, affected areas
  - `mitigation_strategies` → Specific, timeframe-tagged, prioritized
  - `key_vulnerabilities` + `recommended_actions`
  - `confidence_score` (0–1)

### LLM-as-Judge Agent
- Uses **separate model** (Gemini Flash) to avoid self-evaluation bias
- Scores on structured rubric:
  - **Depth** (35%): Quality of risk identification
  - **Actionability** (40%): Concreteness of recommendations
  - **Coverage** (25%): Breadth across 7 risk dimensions
- Returns `strengths`, `improvements`, and full `verdict`

---

## 📊 Risk Taxonomy

| Category | Examples |
|---|---|
| Geopolitical | Sanctions, trade wars, diplomatic tensions |
| Logistics | Port congestion, shipping delays, carrier capacity |
| Supplier | Single-source dependency, financial instability |
| Economic | Currency volatility, inflation, recession risk |
| Environmental | Natural disasters, climate events, regulatory ESG |
| Regulatory | Export controls, compliance changes, tariffs |
| Cybersecurity | Supply chain attacks, data breaches, ransomware |
