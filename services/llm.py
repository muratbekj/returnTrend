import json
import re
from datetime import datetime

from langchain_ollama import OllamaLLM

class SimpleLLMConnector:
    def __init__(self, model_name="gpt-oss:20b"):
        self.ollama_model = model_name
    
    def _invoke_model(self, prompt: str) -> str:
        """Invoke configured Ollama model and return text response."""
        ollama_model = OllamaLLM(model=self.ollama_model)
        response = ollama_model.invoke(prompt)
        return response if isinstance(response, str) else str(response)

    def _create_ranking_prompt(self, articles_dict):
        """Create ranking prompt to judge impact and reading priority."""
        print(f"Creating ranking prompt for {len(articles_dict)} articles")
        prompt = (
            "You are an AI news editor assigning reading priority.\n"
            "Rank the most impactful stories for a general tech audience.\n"
            "Focus on real-world impact, industry significance, and novelty.\n\n"
            "Return STRICT JSON only in this schema:\n"
            "{\n"
            "  \"ranked\": [\n"
            "    {\n"
            "      \"title\": \"exact article title\",\n"
            "      \"score\": <integer 1-10>,\n"
            "      \"reason\": \"short reason under 20 words\"\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Articles:\n"
        )

        for i, (title, details) in enumerate(articles_dict.items(), 1):
            prompt += f"\n{i}. Title: {title}\n"
            prompt += f"   Summary: {details.get('summary', 'No summary available')}\n"
            prompt += f"   Source: {details.get('source', 'Unknown')}\n"
            prompt += f"   Published: {details.get('published_at', 'Unknown date')}\n"

        print(f"Ranking prompt created successfully for {len(articles_dict)} articles")

        return prompt

    def _extract_json(self, raw_response: str):
        """Try to parse model output into JSON object."""
        if not raw_response:
            return None

        cleaned = raw_response.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

        # Fallback: pick first JSON object block.
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                return None
        return None

    def _heuristic_sort(self, articles_dict):
        """Fallback ranking when LLM judge is unavailable."""
        def score_item(item):
            _, details = item
            summary = details.get("summary", "") or ""
            summary_score = min(len(summary), 300) / 100.0

            date_score = 0.0
            raw_date = details.get("published_at", "")
            try:
                published_dt = datetime.fromisoformat(raw_date)
                age_hours = max((datetime.now() - published_dt).total_seconds() / 3600, 0)
                date_score = max(0.0, 10.0 - (age_hours / 12.0))
            except Exception:
                date_score = 0.0

            return date_score + summary_score

        return sorted(articles_dict.items(), key=score_item, reverse=True)

    def rank_articles(self, articles_dict, top_n=None):
        """Rank articles by impact and reading priority."""
        if not articles_dict:
            return {}

        try:
            prompt = self._create_ranking_prompt(articles_dict)
            response = self._invoke_model(prompt)
            parsed = self._extract_json(response)

            if not parsed or "ranked" not in parsed or not isinstance(parsed["ranked"], list):
                raise ValueError("Invalid ranking response")

            original_titles = list(articles_dict.keys())
            rank_map = {}

            for item in parsed["ranked"]:
                if not isinstance(item, dict):
                    continue
                title = item.get("title")
                if title not in articles_dict:
                    continue
                rank_map[title] = {
                    "score": int(item.get("score", 5)),
                    "reason": str(item.get("reason", "High relevance today")),
                }

            # Keep judged titles first, then append any missing titles.
            ranked_titles = sorted(rank_map.keys(), key=lambda t: rank_map[t]["score"], reverse=True)
            for title in original_titles:
                if title not in rank_map:
                    rank_map[title] = {"score": 5, "reason": "Relevant update worth tracking"}
                    ranked_titles.append(title)

            if top_n:
                ranked_titles = ranked_titles[:top_n]

            ranked_articles = {}
            for title in ranked_titles:
                details = dict(articles_dict[title])
                details["judge_score"] = rank_map[title]["score"]
                details["judge_reason"] = rank_map[title]["reason"]
                ranked_articles[title] = details

            return ranked_articles

        except Exception as e:
            print(f"Ranking failed, using heuristic fallback: {e}")
            sorted_items = self._heuristic_sort(articles_dict)
            if top_n:
                sorted_items = sorted_items[:top_n]

            ranked_articles = {}
            for title, details in sorted_items:
                item = dict(details)
                item["judge_score"] = 5
                item["judge_reason"] = "Prioritized by recency and content richness"
                ranked_articles[title] = item
            return ranked_articles

    def create_prompt(self, articles_dict):
        """Create a prompt from articles dictionary"""
        prompt = "You are an AI news editor.\n"
        prompt += "Write a clean, neutral summary for Telegram users.\n"
        prompt += "Keep the response concise and practical.\n\n"
        prompt += "Articles:\n\n"
        
        for title, details in articles_dict.items():
            prompt += f"Title: {title}\n"
            prompt += f"Summary: {details.get('summary', 'No summary available')}\n"
            prompt += f"Source: {details.get('source', 'Unknown')}\n"
            prompt += f"Link: {details.get('link', 'No link')}\n"
            prompt += f"Published: {details.get('published_at', 'Unknown date')}\n"
            prompt += "-" * 50 + "\n"
        
        prompt += (
            "\nOutput requirements:\n"
            "1) Start with a 2-3 sentence overview of the biggest trends.\n"
            "2) Then list the top 5 stories as bullets in this format:\n"
            "- <title>: <1 sentence why it matters>. <link>\n"
            "3) Keep total length below 350 words.\n"
            "4) Avoid hype and avoid repeating the same point.\n"
        )
        
        return prompt
    
    def generate_summary(self, articles_dict):
        """Generate summary using Ollama"""
        if not articles_dict:
            return "No articles to summarize."
        
        prompt = self.create_prompt(articles_dict)
        
        try:
            print(f"Starting Ollama model: {self.ollama_model}")
            response = self._invoke_model(prompt)
            print("Ollama model completed")
            return response
        except Exception as e:
            print(f"Ollama API call failed: {e}")
            return self._generate_fallback_summary(articles_dict)
    
    def _generate_fallback_summary(self, articles_dict):
        """Generate a simple fallback summary when Ollama is not available"""
        summary = "Quick AI news roundup:\n\n"
        
        for title, details in list(articles_dict.items())[:10]:  # Limit to first 10
            clean_summary = details.get('summary', 'No summary available')[:160]
            summary += f"- {title}\n"
            summary += f"  Why it matters: {clean_summary}...\n"
            summary += f"  Source: {details.get('source', 'Unknown')}\n"
            summary += f"  Read: {details.get('link', 'No link available')}\n\n"
        
        if len(articles_dict) > 10:
            summary += f"... and {len(articles_dict) - 10} more articles.\n"
        
        return summary
    
    def process_articles(self, articles_dict):
        """Main method to process articles and return summary"""
        print(f"Processing {len(articles_dict)} articles...")
        summary = self.generate_summary(articles_dict)
        return summary

# Usage:
# llm = SimpleLLMConnector()
# summary_text = llm.process_articles(articles_dict)
# print(summary_text)