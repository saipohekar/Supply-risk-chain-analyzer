import logging
import json
import time
from typing import Optional
from groq import Groq
from utils.models import SourcingAlternatives, AlternativeSourcing
from utils.config import GROQ_API_KEY, GROQ_MODEL

logger = logging.getLogger(__name__)

class SourcingAgent:
    """
    Agent that scours for alternative manufacturing/sourcing hubs when a region is deemed risky.
    It performs its own rapid targeted search using an LLM-supplied Tool and evaluates viable alternatives.
    """

    def __init__(self):
        if not GROQ_API_KEY:
             raise ValueError("GROQ_API_KEY environment variable not set.")
        self.client = Groq(api_key=GROQ_API_KEY)
        from utils.config import TAVILY_API_KEY
        self._tavily_key = TAVILY_API_KEY

    def scout_alternatives(self, product_category: str, current_region: str, progress_cb: Optional[callable] = None) -> SourcingAlternatives:
        """Find alternatives to the current sourcing region for the given product using tool calls."""
        if progress_cb:
            progress_cb(f"🌍 Sourcing Agent analyzing alternatives to {current_region} via Tool Calls...")
            
        def search_sourcing_web(query: str) -> str:
            '''Search the web for intelligence about alternative sourcing regions or manufacturing hubs.'''
            if progress_cb:
                progress_cb(f"🔍 LLM Agent triggered tool: search_sourcing_web('{query}')")
            logger.info("Tool called by LLM: search_sourcing_web(query=%s)", query)
            try:
                if not self._tavily_key or "your_" in self._tavily_key:
                    return "No Tavily API key provided. Fallback: return default knowledge about Mexico, Vietnam or India."
                from tavily import TavilyClient
                tc = TavilyClient(api_key=self._tavily_key)
                resp = tc.search(query=query, search_depth="basic", max_results=3, include_answer=False)
                lines = []
                for r in resp.get("results", []):
                     lines.append(f"Title: {r.get('title')}\nContent: {r.get('content')}")
                return "\n---\n".join(lines)
            except Exception as e:
                logger.error("Sourcing Tavily search tool failed: %s", e)
                return f"Search failed: {e}. Try to answer with general knowledge instead."
        
        prompt = f"""You are a Strategic Sourcing Expert.
The company currently sources '{product_category}' from '{current_region}', but wants to diversify due to high risk.

You MUST use the `search_sourcing_web` tool to find the most current and viable alternative countries/regions for sourcing this product.

After reading the search results, recommend up to 3 alternative countries/regions.
For each, list 2-3 brief PROS and 2-3 brief CONS. Give a viability score out of 10.

Output strictly as JSON matching this schema:
{{
  "recommended_alternatives": [
    {{
      "region": "<Country Name>",
      "pros": ["<pro 1>", "<pro 2>"],
      "cons": ["<con 1>", "<con 2>"],
      "viability_score": <float 0-10>
    }}
  ]
}}
"""

        model_to_use = GROQ_MODEL
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_sourcing_web",
                    "description": "Search the web for intelligence about alternative sourcing regions or manufacturing hubs.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query."
                            }
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

        wait_times = [15, 30]
        for attempt, wait in enumerate(wait_times + [None], start=1):
            try:
                messages = [{"role": "user", "content": prompt}]
                response = self.client.chat.completions.create(
                    model=model_to_use, 
                    messages=messages, 
                    tools=tools, 
                    tool_choice="auto",
                    temperature=0.2
                )
                
                # Check if the model decided to call the tool
                if response.choices[0].message.tool_calls:
                    messages.append(response.choices[0].message)
                    for tool_call in response.choices[0].message.tool_calls:
                        if tool_call.function.name == "search_sourcing_web":
                            args = json.loads(tool_call.function.arguments)
                            tool_result = search_sourcing_web(args.get("query", ""))
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "name": "search_sourcing_web",
                                "content": tool_result
                            })
                    # Request the final JSON output
                    final_response = self.client.chat.completions.create(
                        model=model_to_use, 
                        messages=messages, 
                        temperature=0.2,
                        response_format={"type": "json_object"}
                    )
                    text = final_response.choices[0].message.content.strip()
                else:
                    text = response.choices[0].message.content.strip()

                if text.startswith("```"):
                   text = text.split("```")[1]
                   if text.startswith("json"):
                       text = text[4:]
                   text = text.rsplit("```", 1)[0].strip()
                   
                data = json.loads(text)
                alts = []
                for a in data.get("recommended_alternatives", []):
                    alts.append(AlternativeSourcing(**a))
                return SourcingAlternatives(recommended_alternatives=alts)
                
            except json.JSONDecodeError as exc:
                logger.error("JSON parse error: %s", exc)
                return SourcingAlternatives(recommended_alternatives=[])
            except Exception as exc:
                exc_str = str(exc).lower()
                if "400" in exc_str and "json" in exc_str:
                    logger.error("Bad Request for JSON structure or tool schema: %s", exc)
                    break
                if not any(k in exc_str for k in ("429", "503", "500", "resourceexhausted", "serviceunavailable", "unavailable", "exhausted", "rate_limit")):
                    logger.error("Non-retriable error in Sourcing Agent: %s", exc)
                    import traceback
                    traceback.print_exc()
                    break
                
                if wait is None:
                    logger.error("API quota exhausted in SourcingAgent. Skipping.")
                    break
                    
                if progress_cb:
                    progress_cb(f"⏳ Sourcing Agent API limit hit — auto-retrying in {wait}s...")
                time.sleep(wait)
        
        return SourcingAlternatives(recommended_alternatives=[])
