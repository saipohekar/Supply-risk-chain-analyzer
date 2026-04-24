# Problem Statement

## Project Name
Supply Risk Chain Analyzer

## The Problem
Supply chains face constant disruptions including supplier failures,
geopolitical instability, logistics breakdowns, raw material shortages,
and compliance violations. Procurement and supply chain teams currently
spend hours manually tracking supplier risks, identifying vulnerability
points, and writing risk assessment reports across multi-tier supplier
networks.

## User
Supply chain managers, procurement officers, operations heads, and
compliance teams at manufacturing companies, retailers, and logistics
firms.

## Need
An automated system that instantly generates a real-time structured
supply chain risk analysis — including active supplier threats,
disruption propagation paths, vulnerability nodes, mitigation steps,
and compliance gaps against ISO 28000 and ESG supply chain standards.

## Why Agentic
This problem requires multiple sequential reasoning steps:
- Searching live supplier risk and geopolitical intelligence (Tavily)
- Mapping multi-tier supplier dependencies into a chain structure (LLM reasoning)
- Simulating disruption propagation across supply nodes (Gemini/Groq)
- Writing a professional supply risk briefing report (Gemini/Groq)
- Evaluating output quality and chain coverage (LLM-as-Judge)
- Checking compliance rules (ISO 28000 + ESG Supply Chain Standards)

No single AI call can perform all these steps. Each step depends
on the output of the previous one. Only an agentic architecture
where agents act autonomously and sequentially can solve this
problem end-to-end.
