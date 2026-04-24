"""
LLM-as-Judge Agent — independently evaluates the risk assessment for:
  1. Depth of risk identification
  2. Actionability of mitigation recommendations
  3. Coverage across risk dimensions
"""
import json
import logging
import time
from groq import Groq
from utils.models import RiskAssessment, JudgeEvaluation
from utils.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)


class JudgeAgent:
    """
    An independent LLM evaluator that critiques the risk assessment
    using a standardized rubric. Uses a separate, faster model to avoid
    self-evaluation bias in the same generation context.
    """

    RUBRIC = """
EVALUATION RUBRIC:

1. DEPTH OF RISK IDENTIFICATION (0-10):
   - 9-10: Covers all major risk categories with specific, evidence-backed details
   - 7-8 : Identifies most risk categories with good specificity
   - 5-6 : Covers basic risks but misses important nuances or categories
   - 3-4 : Superficial coverage; generic risks not specific to the context
   - 0-2 : Very poor depth; obvious risks missed

2. ACTIONABILITY OF RECOMMENDATIONS (0-10):
   - 9-10: All strategies are concrete, measurable, and immediately implementable
   - 7-8 : Most strategies are specific with clear steps
   - 5-6 : Strategies exist but are somewhat generic or vague
   - 3-4 : Recommendations are too high-level to act upon
   - 0-2 : Recommendations are useless or inapplicable

3. COVERAGE SCORE (0-10):
   - Measures breadth across: Geopolitical, Logistics, Supplier, Economic,
     Environmental, Regulatory, Cybersecurity dimensions
   - 9-10: All 7 dimensions addressed
   - 7-8 : 5-6 dimensions addressed
   - 5-6 : 3-4 dimensions addressed
   - 3-4 : 1-2 dimensions addressed
   - 0-2 : No meaningful coverage
"""

    def __init__(self):
        if not GROQ_API_KEY or "your_" in GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY is missing or is a placeholder.")
        self.client = Groq(api_key=GROQ_API_KEY)
        logger.info("JudgeAgent initialized with model: %s", GROQ_MODEL)

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
                    temperature=0.1,
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

    def _build_evaluation_prompt(
        self,
        product_category: str,
        sourcing_region: str,
        assessment: RiskAssessment,
    ) -> str:
        risk_factors_summary = "\n".join(
            f"  - [{rf.severity.value}] {rf.category}: {rf.description[:200]}"
            for rf in assessment.risk_factors
        )
        strategies_summary = "\n".join(
            f"  - [{ms.priority}|{ms.timeframe}] {ms.risk_category}: {ms.strategy[:200]}"
            for ms in assessment.mitigation_strategies
        )
        vulnerabilities_summary = "\n".join(
            f"  - {v}" for v in assessment.key_vulnerabilities
        )

        return f"""You are an independent, strict Quality Evaluator for supply chain risk assessments.
Your role is to objectively critique the following risk assessment.

## CONTEXT
- Product Category: {product_category}
- Sourcing Region: {sourcing_region}
- Overall Risk Level Declared: {assessment.overall_risk_level.value}
- Confidence Score: {assessment.confidence_score:.2f}

## ASSESSMENT BEING EVALUATED

### Executive Summary
{assessment.executive_summary[:600]}

### Risk Factors Identified ({len(assessment.risk_factors)} total)
{risk_factors_summary}

### Mitigation Strategies ({len(assessment.mitigation_strategies)} total)
{strategies_summary}

### Key Vulnerabilities
{vulnerabilities_summary}

### Recommended Actions
{chr(10).join(f'  - {a}' for a in assessment.recommended_actions)}

{self.RUBRIC}

## YOUR TASK
Evaluate the assessment against the rubric above. Return ONLY a valid JSON object:

{{
  "overall_score": <weighted average: depth*0.35 + actionability*0.40 + coverage*0.25>,
  "depth_score": <0.0-10.0>,
  "actionability_score": <0.0-10.0>,
  "coverage_score": <0.0-10.0>,
  "depth_feedback": "<specific critique of risk identification depth>",
  "actionability_feedback": "<specific critique of how actionable the recommendations are>",
  "coverage_feedback": "<specific critique of dimension coverage>",
  "strengths": ["<strength 1>", "<strength 2>", "<strength 3>"],
  "improvements": ["<improvement 1>", "<improvement 2>", "<improvement 3>"],
  "verdict": "<one paragraph final verdict>"
}}

Be CRITICAL and SPECIFIC. Reward depth and penalise vague, generic content.
Return ONLY the JSON object, no preamble or markdown."""

    def evaluate(
        self,
        product_category: str,
        sourcing_region: str,
        assessment: RiskAssessment,
        progress_callback=None,
    ) -> JudgeEvaluation:
        """
        Independently evaluate the risk assessment using the LLM-as-Judge pattern.

        Returns:
            JudgeEvaluation Pydantic model with scores and feedback.
        """
        if progress_callback:
            progress_callback("⚖️  LLM Judge evaluating the risk assessment…")
        self._progress_cb = progress_callback  # allow _safe_generate to relay retry msgs

        prompt = self._build_evaluation_prompt(product_category, sourcing_region, assessment)
        logger.info("Sending evaluation prompt to Judge model (%d chars)", len(prompt))

        try:
            raw_text = self._safe_generate(
                model=GROQ_MODEL,
                prompt=prompt,
            )

            # Strip markdown fences
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.rsplit("```", 1)[0]
            raw_text = raw_text.strip()

            data = json.loads(raw_text)
            evaluation = JudgeEvaluation(
                overall_score=float(data.get("overall_score", 5.0)),
                depth_score=float(data.get("depth_score", 5.0)),
                actionability_score=float(data.get("actionability_score", 5.0)),
                coverage_score=float(data.get("coverage_score", 5.0)),
                depth_feedback=data.get("depth_feedback", "No feedback provided."),
                actionability_feedback=data.get("actionability_feedback", "No feedback provided."),
                coverage_feedback=data.get("coverage_feedback", "No feedback provided."),
                strengths=data.get("strengths", []),
                improvements=data.get("improvements", []),
                verdict=data.get("verdict", "No final verdict returned."),
            )
            logger.info(
                "Judge evaluation complete. Overall: %.1f/10", evaluation.overall_score
            )
            return evaluation

        except json.JSONDecodeError as exc:
            logger.error("Judge JSON parse error: %s", exc)
            raise RuntimeError(f"Judge returned invalid JSON: {exc}") from exc
        except Exception as exc:
            logger.error("Judge evaluation failed: %s", exc)
            raise
