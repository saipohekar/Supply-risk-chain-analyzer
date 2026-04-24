"""
Pydantic models for Supply Chain Risk Analyzer data structures.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class SearchResult(BaseModel):
    title: str
    url: str
    content: str
    score: Optional[float] = None


class RiskFactor(BaseModel):
    category: str = Field(description="Risk category (e.g., Geopolitical, Logistics, Supplier)")
    description: str = Field(description="Detailed description of the risk")
    severity: RiskLevel = Field(description="Assessed severity level")
    likelihood: RiskLevel = Field(description="Likelihood of occurrence")
    affected_areas: List[str] = Field(description="Supply chain areas affected")


class MitigationStrategy(BaseModel):
    risk_category: str = Field(description="The risk category this addresses")
    strategy: str = Field(description="Specific mitigation strategy")
    timeframe: str = Field(description="Implementation timeframe (Immediate/Short-term/Long-term)")
    estimated_impact: str = Field(description="Expected impact of this mitigation")
    priority: str = Field(description="Priority level: High/Medium/Low")


class RiskAssessment(BaseModel):
    product_category: str
    sourcing_region: str
    overall_risk_level: RiskLevel
    executive_summary: str
    risk_factors: List[RiskFactor]
    mitigation_strategies: List[MitigationStrategy]
    key_vulnerabilities: List[str]
    recommended_actions: List[str]
    data_sources: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)


class JudgeEvaluation(BaseModel):
    overall_score: float = Field(ge=0.0, le=10.0)
    depth_score: float = Field(ge=0.0, le=10.0)
    actionability_score: float = Field(ge=0.0, le=10.0)
    coverage_score: float = Field(ge=0.0, le=10.0)
    depth_feedback: str
    actionability_feedback: str
    coverage_feedback: str
    strengths: List[str]
    improvements: List[str]
    verdict: str

class AlternativeSourcing(BaseModel):
    region: str = Field(description="Alternative country or region")
    pros: List[str] = Field(description="Pros of sourcing from here")
    cons: List[str] = Field(description="Cons or risks of sourcing from here")
    viability_score: float = Field(ge=0.0, le=10.0, description="Overall viability score 0-10")

class SourcingAlternatives(BaseModel):
    recommended_alternatives: List[AlternativeSourcing]


class AnalysisResult(BaseModel):
    query_params: dict
    search_results: List[SearchResult]
    risk_assessment: RiskAssessment
    judge_evaluation: JudgeEvaluation
    sourcing_alternatives: Optional[SourcingAlternatives] = None
    processing_time_seconds: float
