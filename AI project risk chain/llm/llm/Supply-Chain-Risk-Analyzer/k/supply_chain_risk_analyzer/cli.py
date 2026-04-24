import sys
import sys
import codecs
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())
import json
import json
import argparse
from typing import Optional
from dotenv import load_dotenv

# Load explicitly to avoid Streamlit reliance
load_dotenv()

from utils.config import validate_config
from agents.pipeline import SupplyChainPipeline


def run_cli_analysis(product: str, region: str, verbose: bool = False):
    """
    Run the supply chain analysis directly in the terminal,
    removing the 'frontend' (Streamlit UI) concept.
    """
    is_valid, errors = validate_config()
    if not is_valid:
        print("❌ Cannot run analysis — API keys not configured:")
        for err in errors:
            print(f"  • {err}")
        sys.exit(1)

    print(f"==================================================")
    print(f" Supply Chain Risk Analyzer (CLI Mode)")
    print(f"==================================================")
    print(f" Product : {product}")
    print(f" Region  : {region}")
    print(f"==================================================\n")

    def progress_cb(msg: str):
        if verbose:
            print(f"[*] {msg}")

    try:
        pipeline = SupplyChainPipeline()
        if not verbose:
            print("🚀 Running analysis pipeline (this may take a minute)...")
            
        result = pipeline.run(
            product_category=product,
            sourcing_region=region,
            progress_callback=progress_cb
        )

        
        # Output Summary
        print("\n✅ ANALYSIS COMPLETE\n")
        
        # Extract fields
        assessment = result.risk_assessment
        evaluation = result.judge_evaluation
        
        print(f"Overall Risk Level: {assessment.overall_risk_level.value}")
        print(f"Confidence Score  : {assessment.confidence_score * 100:.0f}%")
        print(f"LLM Judge Quality : {evaluation.overall_score:.1f}/10\n")
        
        print("--- Executive Summary ---")
        print(assessment.executive_summary)
        print("\n--- Key Vulnerabilities ---")
        for v in assessment.key_vulnerabilities:
            print(f"  - {v}")
            
        print("\n--- Mitigation Strategies ---")
        for m in assessment.mitigation_strategies:
            print(f"  [{m.priority}] {m.strategy}")

        print("\n==================================================")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Supply Chain Risk Analyzer (CLI)")
    parser.add_argument("product", help="The product category being sourced (e.g., 'Semiconductors')")
    parser.add_argument("region", help="The sourcing region to analyze (e.g., 'Taiwan')")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print pipeline progress steps")

    args = parser.parse_args()
    run_cli_analysis(args.product, args.region, args.verbose)
