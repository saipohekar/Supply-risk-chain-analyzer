"""
Pipeline orchestrator — coordinates Research, Risk Assessment, Judge, and Sourcing agents
to produce a complete AnalysisResult.
"""
import time
import logging
from typing import Optional, Callable
from utils.models import AnalysisResult
from agents.research_agent import ResearchAgent
from agents.risk_assessment_agent import RiskAssessmentAgent
from agents.judge_agent import JudgeAgent
from agents.sourcing_agent import SourcingAgent

logger = logging.getLogger(__name__)


class SupplyChainPipeline:
    """
    End-to-end pipeline that orchestrates the three-agent workflow:
      1. ResearchAgent → gather real-time intelligence via Tavily
      2. RiskAssessmentAgent → synthesize into structured assessment via Gemini
      3. JudgeAgent → independently evaluate quality via LLM-as-Judge
    """

    def __init__(self):
        self.researcher = ResearchAgent()
        self.assessor = RiskAssessmentAgent()
        self.judge = JudgeAgent()
        self.sourcing = SourcingAgent()
        logger.info("SupplyChainPipeline initialized with all four agents.")

    def run(
        self,
        product_category: str,
        sourcing_region: str,
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> AnalysisResult:
        """
        Execute the full analysis pipeline.

        Args:
            product_category : Category of product being sourced
            sourcing_region  : Geographic region of supply
            progress_callback: Optional UI progress update callable

        Returns:
            AnalysisResult with all pipeline outputs.
        """
        start_time = time.time()

        if progress_callback:
            progress_callback("🚀 Initiating Supply Chain Risk Analysis pipeline…")

        # ── Stage 1: Research ──────────────────────────────────────────────
        if progress_callback:
            progress_callback("📡 Stage 1/4 → Research Agent gathering intelligence…")

        search_results = self.researcher.research(
            product_category=product_category,
            sourcing_region=sourcing_region,
            progress_callback=progress_callback,
        )
        logger.info("Pipeline stage 1 complete: %d results", len(search_results))

        # ── Stage 2: Risk Assessment ───────────────────────────────────────
        if progress_callback:
            progress_callback("📊 Stage 2/4 → Risk Assessment Agent analysing data…")

        assessment = self.assessor.assess(
            product_category=product_category,
            sourcing_region=sourcing_region,
            search_results=search_results,
            progress_callback=progress_callback,
        )
        logger.info(
            "Pipeline stage 2 complete: %s risk, %.2f confidence",
            assessment.overall_risk_level,
            assessment.confidence_score,
        )

        # ── Stage 3: LLM-as-Judge ──────────────────────────────────────────
        if progress_callback:
            progress_callback("⚖️  Stage 3/4 → Judge Agent evaluating quality…")

        evaluation = self.judge.evaluate(
            product_category=product_category,
            sourcing_region=sourcing_region,
            assessment=assessment,
            progress_callback=progress_callback,
        )
        logger.info(
            "Pipeline stage 3 complete: Judge score %.1f/10", evaluation.overall_score
        )

        # ── Stage 4: Alternative Sourcing ──────────────────────────────────
        if progress_callback:
            progress_callback("🌍 Stage 4/4 → Sourcing Agent scouting alternative hubs…")
            
        alts = self.sourcing.scout_alternatives(
            product_category=product_category,
            current_region=sourcing_region,
            progress_cb=progress_callback
        )
        logger.info("Pipeline stage 4 complete: Found %d alternative hubs.", len(alts.recommended_alternatives))

        processing_time = time.time() - start_time
        if progress_callback:
            progress_callback(
                f"✅ Analysis complete in {processing_time:.1f}s — "
                f"Risk: {assessment.overall_risk_level.value} | "
                f"Quality Score: {evaluation.overall_score:.1f}/10"
            )

        return AnalysisResult(
            query_params={
                "product_category": product_category,
                "sourcing_region": sourcing_region,
            },
            search_results=search_results,
            risk_assessment=assessment,
            judge_evaluation=evaluation,
            sourcing_alternatives=alts,
            processing_time_seconds=round(processing_time, 2),
        )
