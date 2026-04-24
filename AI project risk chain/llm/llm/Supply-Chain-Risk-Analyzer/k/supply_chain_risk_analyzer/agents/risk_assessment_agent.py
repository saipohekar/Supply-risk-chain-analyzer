"""
Risk Assessment Agent — uses Gemini Pro to analyze gathered search intelligence
and produce a structured, comprehensive risk assessment.
"""
import json
import logging
import time
from typing import Optional
from groq import Groq
from utils.models import (
    SearchResult, RiskAssessment, RiskFactor, MitigationStrategy, RiskLevel
)
from utils.config import GROQ_API_KEY, GROQ_MODEL, MAX_RISK_FACTORS, MAX_MITIGATION_STRATEGIES

logger = logging.getLogger(__name__)


class RiskAssessmentAgent:
    """
    LLM-powered agent that synthesizes search intelligence into a structured
    risk assessment with identified vulnerabilities and actionable recommendations.
    """

    def __init__(self):
        if not GROQ_API_KEY or "your_" in GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is missing or is a placeholder. "
                "Please set it in your .env file."
            )
        self.client = Groq(api_key=GROQ_API_KEY)
        logger.info("RiskAssessmentAgent initialized with model: %s", GROQ_MODEL)

    def _safe_generate(self, model: str, prompt: str) -> str:
        """
        Call Groq with automatic retry on quota exhaustion (429).
        Attempts: 1st try → wait 25s → 2nd try → wait 60s → 3rd try → raise.
        """
        wait_times = [25, 60]
        for attempt, wait in enumerate(wait_times + [None], start=1):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content.strip()
            except Exception as exc:
                exc_str = str(exc).lower()
                if not any(k in exc_str for k in ("429", "503", "500", "resourceexhausted", "serviceunavailable", "unavailable", "exhausted", "rate_limit")):
                    raise
                if wait is None:
                    logger.error("API error or quota exhausted after %d attempts. Giving up.", attempt)
                    raise
                logger.warning(
                    "API issue (503/429) (attempt %d/%d). Sleeping %ds before retry…",
                    attempt, len(wait_times) + 1, wait,
                )
                if getattr(self, '_progress_cb', None):
                    self._progress_cb(
                        f"⏳ API load/quota hit — auto-retrying in {wait}s "
                        f"(attempt {attempt}/{len(wait_times)+1})…"
                    )
                time.sleep(wait)


    def _format_search_context(self, results: list[SearchResult]) -> str:
        """Convert search results into a readable context block for the LLM."""
        lines = []
        for i, r in enumerate(results, 1):
            lines.append(f"[Source {i}] {r.title}")
            lines.append(f"URL: {r.url}")
            lines.append(f"Content: {r.content[:800]}")
            lines.append("---")
        return "\n".join(lines)

    def _build_prompt(
        self, product_category: str, sourcing_region: str, context: str
    ) -> str:
        return f"""You are an expert Supply Chain Risk Analyst with deep knowledge of global trade,
geopolitics, logistics, and procurement. Your task is to produce a comprehensive, structured
risk assessment for a company sourcing products from the given region.

## INPUT PARAMETERS
- Product Category: {product_category}
- Sourcing Region: {sourcing_region}

## INTELLIGENCE GATHERED (Real-time News & Analysis)
{context}

## YOUR TASK
Analyze the intelligence above and produce a detailed risk assessment. Return a valid JSON object
matching this EXACT schema (no extra keys, no markdown fences):

{{
  "product_category": "<string>",
  "sourcing_region": "<string>",
  "overall_risk_level": "<Low|Medium|High|Critical>",
  "executive_summary": "<2-3 paragraph executive summary>",
  "risk_factors": [
    {{
      "category": "<Geopolitical|Logistics|Supplier|Economic|Environmental|Regulatory|Cybersecurity>",
      "description": "<detailed description>",
      "severity": "<Low|Medium|High|Critical>",
      "likelihood": "<Low|Medium|High|Critical>",
      "affected_areas": ["<area1>", "<area2>"]
    }}
  ],
  "mitigation_strategies": [
    {{
      "risk_category": "<matching risk category>",
      "strategy": "<specific, actionable strategy>",
      "timeframe": "<Immediate|Short-term|Long-term>",
      "estimated_impact": "<expected outcome>",
      "priority": "<High|Medium|Low>"
    }}
  ],
  "key_vulnerabilities": ["<vulnerability 1>", "<vulnerability 2>", ...],
  "recommended_actions": ["<action 1>", "<action 2>", ...],
  "data_sources": ["<source URL or title>", ...],
  "confidence_score": <0.0-1.0 float based on data quality>
}}

REQUIREMENTS:
- Identify {MAX_RISK_FACTORS} distinct risk factors across multiple categories
- Provide {MAX_MITIGATION_STRATEGIES} specific, actionable mitigation strategies
- Each strategy must be concrete and implementable, NOT generic advice
- Base all findings on the intelligence provided above
- Rank vulnerabilities from most to least critical
- confidence_score reflects how well the gathered data supports your conclusions
- Return ONLY the JSON object, no preamble, no markdown."""

    def assess(
        self,
        product_category: str,
        sourcing_region: str,
        search_results: list[SearchResult],
        progress_callback=None,
    ) -> RiskAssessment:
        """
        Generate a structured risk assessment from the research results.

        Args:
            product_category: The product being analyzed
            sourcing_region : The sourcing geography
            search_results  : Results from the ResearchAgent
            progress_callback: Optional callable for UI progress updates

        Returns:
            RiskAssessment Pydantic model
        """
        if progress_callback:
            progress_callback("🧠 Synthesizing intelligence with Gemini…")
        self._progress_cb = progress_callback  # allow _safe_generate to relay retry msgs

        context = self._format_search_context(search_results)
        prompt = self._build_prompt(product_category, sourcing_region, context)

        logger.info("Sending assessment prompt to Gemini (%d chars)", len(prompt))

        try:
            raw_text = self._safe_generate(
                model=GROQ_MODEL,
                prompt=prompt,
            )

            # Strip potential markdown code fences
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.rsplit("```", 1)[0]
            raw_text = raw_text.strip()

            data = json.loads(raw_text)

            # Build Pydantic model from parsed JSON
            assessment = RiskAssessment(
                product_category=data["product_category"],
                sourcing_region=data["sourcing_region"],
                overall_risk_level=RiskLevel(data["overall_risk_level"]),
                executive_summary=data["executive_summary"],
                risk_factors=[
                    RiskFactor(
                        category=rf["category"],
                        description=rf["description"],
                        severity=RiskLevel(rf["severity"]),
                        likelihood=RiskLevel(rf["likelihood"]),
                        affected_areas=rf["affected_areas"],
                    )
                    for rf in data.get("risk_factors", [])
                ],
                mitigation_strategies=[
                    MitigationStrategy(
                        risk_category=ms["risk_category"],
                        strategy=ms["strategy"],
                        timeframe=ms["timeframe"],
                        estimated_impact=ms["estimated_impact"],
                        priority=ms["priority"],
                    )
                    for ms in data.get("mitigation_strategies", [])
                ],
                key_vulnerabilities=data.get("key_vulnerabilities", []),
                recommended_actions=data.get("recommended_actions", []),
                data_sources=data.get("data_sources", []),
                confidence_score=float(data.get("confidence_score", 0.7)),
            )
            logger.info(
                "Risk assessment complete. Overall: %s, Confidence: %.2f",
                assessment.overall_risk_level,
                assessment.confidence_score,
            )
            return assessment

        except json.JSONDecodeError as exc:
            logger.error("JSON parse error: %s\nRaw response: %s", exc, raw_text[:500])
            raise RuntimeError(f"Gemini returned invalid JSON: {exc}") from exc
        except Exception as exc:
            logger.error("Risk assessment failed: %s", exc)
            raise
