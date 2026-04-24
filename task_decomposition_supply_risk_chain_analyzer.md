# Task Decomposition & Specifications

## Agent 1 — Research Agent
- Input: Nothing (starts automatically)
- Action: Runs 5 targeted Tavily searches across disruptions, geopolitics, logistics, environmental, and supplier risks
- Output: Raw text of live supply chain risk news and intelligence articles
- Tool Used: Tavily Search API

## Agent 2 — Risk Assessment Agent
- Input: Raw research text from Agent 1
- Action: Sends to Gemini Pro LLM to synthesize intelligence into a structured risk report
- Output: Structured JSON report with up to 8 risk factors and 6 mitigation strategies
- Decision Point: If research is empty or insufficient, returns error message

## Agent 3 — Sourcing Agent
- Input: Structured JSON report from Agent 2
- Action: Extracts and traces all sources referenced across the risk report
- Output: Verified source list mapped to each risk factor and mitigation strategy
- Decision Point: Flags risk factors with missing or unverifiable sources

## Agent 4 — Judge Agent
- Input: Full risk report from Agent 2 + Source list from Agent 3
- Action: Independent Gemini Flash evaluation scoring report quality using a weighted rubric
- Output: JSON with scores 0–10 per criterion + overall grade A/B/C/D + feedback
- Rubric: Depth (35%), Actionability (40%), Coverage (25%)
