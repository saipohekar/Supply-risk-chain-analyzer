"""
Research Agent — searches for supply chain disruptions, geopolitical risks,
and logistics news using Tavily's search API.
Falls back to rich mock data when no Tavily key is configured.
"""
import logging
from utils.models import SearchResult
from utils.config import TAVILY_API_KEY, TAVILY_MAX_RESULTS, TAVILY_SEARCH_DEPTH

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rich mock data — used when TAVILY_API_KEY is not configured
# ---------------------------------------------------------------------------
_MOCK_RESULTS_TEMPLATE = [
    {
        "title": "Semiconductor Supply Chain Under Pressure as Taiwan Strait Tensions Rise",
        "url": "https://reuters.com/tech/semiconductor-taiwan-strait-2025",
        "content": "The global semiconductor industry faces mounting risks as military exercises near Taiwan escalate. TSMC, responsible for over 90% of the world's most advanced chips, has contingency plans but analysts warn a blockade would be catastrophic. Apple, NVIDIA, and AMD have begun quietly diversifying orders to Samsung and Intel fabs, though analysts note capacity constraints make a full pivot impossible before 2027.",
        "score": 0.94,
    },
    {
        "title": "China Tightens Rare Earth Export Controls, Threatening EV and Electronics Supply Chains",
        "url": "https://ft.com/rare-earth-export-controls-china-2025",
        "content": "Beijing has announced new export licensing requirements for gallium, germanium, and graphite — critical materials for semiconductors, EV batteries, and solar panels. The restrictions affect roughly 35% of global supply. Industry groups warn that without stockpiles or alternative suppliers in Australia and Canada, manufacturers face production slowdowns within 6-9 months.",
        "score": 0.91,
    },
    {
        "title": "Red Sea Shipping Crisis: Transit Times Up 40%, Freight Rates Spike 300%",
        "url": "https://ft.com/red-sea-shipping-crisis-2025",
        "content": "Houthi attacks in the Red Sea have forced major shipping lines including Maersk, MSC, and CMA CGM to reroute around the Cape of Good Hope, adding 10-14 days to Europe-Asia transits. Freight rates on key lanes have tripled. Electronics importers report lead time extensions of 3-5 weeks, with inventory buffers running thin for just-in-time manufacturers.",
        "score": 0.89,
    },
    {
        "title": "US-China Tariff Escalation: 145% Duties Now Cover Most Electronics Imports",
        "url": "https://wsj.com/us-china-tariffs-electronics-2025",
        "content": "The US has extended tariffs to cover consumer electronics, components, and industrial machinery from China. Companies are scrambling to qualify Vietnam, Mexico, and India alternatives. However, supply chain experts warn that true diversification takes 3-5 years, and many suppliers rely on Chinese sub-components regardless of final assembly location.",
        "score": 0.87,
    },
    {
        "title": "Japanese Earthquake Disrupts Auto and Semiconductor Output in Key Industrial Belt",
        "url": "https://bloomberg.com/japan-earthquake-supply-chain-2025",
        "content": "A 7.2 magnitude earthquake near Kumamoto, Japan has damaged facilities operated by TSMC Japan (熊本), Renesas Electronics, and multiple tier-2 automotive suppliers. Toyota suspended operations at 14 plants. Recovery estimates range from 4 to 12 weeks. The event highlights concentration risk in Japan's industrial corridor which produces critical specialty semiconductors unavailable elsewhere.",
        "score": 0.85,
    },
    {
        "title": "Port of Shanghai Congestion Reaches Record Levels, Dwell Times Double",
        "url": "https://supplychainbrain.com/shanghai-port-congestion-2025",
        "content": "Shanghai port is experiencing its worst congestion since COVID-19 lockdowns, with average dwell times increasing from 3 to 7 days. Contributing factors include a truck driver shortage, new customs inspection requirements, and a surge in exports ahead of US tariff deadlines. Electronics shippers report critical components stuck at port with no clear resolution timeline.",
        "score": 0.83,
    },
    {
        "title": "Single-Source Supplier Risk: Study Finds 68% of Electronics OEMs Lack Qualified Alternates",
        "url": "https://gartner.com/supply-chain-single-source-risk-2025",
        "content": "A Gartner survey of 400 electronics manufacturers reveals that 68% have critical components sourced from a single qualified supplier. Meanwhile, only 23% have conducted supplier financial health audits in the past year. The report recommends supplier diversification programs, safety stock policies, and digital supply chain visibility platforms as top mitigation priorities.",
        "score": 0.80,
    },
    {
        "title": "Cyber Attacks on Supply Chain IT Infrastructure Surge 200% — Manufacturers at Risk",
        "url": "https://darkreading.com/supply-chain-cyber-attacks-2025",
        "content": "Manufacturing sector supply chains saw a 200% year-over-year increase in cyber attacks in 2025, with ransomware targeting ERP, MES, and logistics platforms. Notable incidents at a major PCB substrate maker caused 3-week production halts affecting downstream semiconductor clients. Experts urge zero-trust architecture, third-party risk assessments, and incident response plan testing.",
        "score": 0.76,
    },
]


class ResearchAgent:
    """
    Autonomous agent responsible for gathering real-time intelligence
    about supply chain risks using multi-query Tavily searches.
    Falls back to rich mock data when TAVILY_API_KEY is not configured.
    """

    def __init__(self):
        self._use_mock = not TAVILY_API_KEY or "your_" in TAVILY_API_KEY
        if self._use_mock:
            logger.warning(
                "TAVILY_API_KEY not configured — ResearchAgent will use mock data."
            )
        else:
            from tavily import TavilyClient
            self.client = TavilyClient(api_key=TAVILY_API_KEY)
            logger.info("ResearchAgent initialized with live Tavily client.")

    def _build_queries(self, product_category: str, sourcing_region: str) -> list[str]:
        """Generate targeted search queries covering all risk dimensions."""
        return [
            f"{product_category} supply chain disruption {sourcing_region} 2024 2025",
            f"{sourcing_region} geopolitical risk trade sanctions export controls {product_category}",
            f"{product_category} logistics shipping delays port congestion {sourcing_region}",
            f"{sourcing_region} natural disaster flood earthquake factory shutdown {product_category}",
            f"{product_category} supplier shortage raw material scarcity {sourcing_region}",
        ]

    def _deduplicate(self, results: list[SearchResult]) -> list[SearchResult]:
        """Remove duplicate URLs from results."""
        seen_urls = set()
        unique = []
        for r in results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique.append(r)
        return unique

    def research(
        self,
        product_category: str,
        sourcing_region: str,
        progress_callback=None,
    ) -> list[SearchResult]:
        """
        Execute multi-query research across all risk dimensions.

        Args:
            product_category: Product type being sourced (e.g., "semiconductors")
            sourcing_region : Geographic region supplying the product (e.g., "Taiwan")
            progress_callback: Optional callable(message: str) for live UI updates

        Returns:
            List of deduplicated SearchResult objects.
        """
        if self._use_mock:
            return self._mock_research(product_category, sourcing_region, progress_callback)
        return self._live_research(product_category, sourcing_region, progress_callback)

    def _mock_research(
        self, product_category: str, sourcing_region: str, progress_callback=None
    ) -> list[SearchResult]:
        """Return pre-built mock results enriched with the query context."""
        import time
        if progress_callback:
            progress_callback("ℹ️ No Tavily key — using built-in intelligence dataset (mock mode)")

        results = []
        for i, item in enumerate(_MOCK_RESULTS_TEMPLATE):
            if progress_callback and i % 2 == 0:
                progress_callback(
                    f"📄 Loading intelligence source [{i+1}/{len(_MOCK_RESULTS_TEMPLATE)}]: "
                    f"{item['title'][:60]}…"
                )
            time.sleep(0.05)  # small delay for realistic feel
            results.append(SearchResult(
                title=item["title"],
                url=item["url"],
                content=item["content"],
                score=item["score"],
            ))

        logger.info("Mock ResearchAgent returned %d results.", len(results))
        return results

    def _live_research(
        self, product_category: str, sourcing_region: str, progress_callback=None
    ) -> list[SearchResult]:
        """Execute live Tavily searches."""
        queries = self._build_queries(product_category, sourcing_region)
        all_results: list[SearchResult] = []

        for i, query in enumerate(queries):
            if progress_callback:
                progress_callback(f"🔍 Searching [{i+1}/{len(queries)}]: {query[:70]}…")
            logger.info("Tavily query: %s", query)

            try:
                response = self.client.search(
                    query=query,
                    search_depth=TAVILY_SEARCH_DEPTH,
                    max_results=TAVILY_MAX_RESULTS // len(queries) + 2,
                    include_answer=False,
                    include_raw_content=False,
                )
                for item in response.get("results", []):
                    all_results.append(
                        SearchResult(
                            title=item.get("title", ""),
                            url=item.get("url", ""),
                            content=item.get("content", ""),
                            score=item.get("score"),
                        )
                    )
            except Exception as exc:
                logger.warning("Tavily search failed for query '%s': %s", query, exc)

        deduplicated = self._deduplicate(all_results)
        deduplicated.sort(key=lambda r: r.score or 0, reverse=True)
        final = deduplicated[:TAVILY_MAX_RESULTS]
        logger.info("ResearchAgent gathered %d unique live results.", len(final))
        return final

