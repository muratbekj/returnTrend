from langchain_ollama import OllamaLLM

class SimpleLLMConnector:
    def __init__(self, model_name="llama3.2"):
        self.ollama_model = model_name
    
    def create_prompt(self, articles_dict):
        """Create a prompt from articles dictionary"""
        prompt = "You are a helpful assistant that can summarize articles.\n"
        prompt += "Here are the articles:\n\n"
        
        for title, details in articles_dict.items():
            prompt += f"Title: {title}\n"
            prompt += f"Summary: {details.get('summary', 'No summary available')}\n"
            prompt += f"Source: {details.get('source', 'Unknown')}\n"
            prompt += f"Link: {details.get('link', 'No link')}\n"
            prompt += f"Published: {details.get('published_at', 'Unknown date')}\n"
            prompt += "-" * 50 + "\n"
        
        prompt += "\nPlease summarize the articles in a concise manner.\n"
        prompt += "Please return the summary in the following format:\n"
        prompt += "Here are the articles for today:\n"
        prompt += "Title of article: Summary of the article (max 150 words) and the link to the article\n"
        
        return prompt
    
    def generate_summary(self, articles_dict):
        """Generate summary using Ollama"""
        if not articles_dict:
            return "No articles to summarize."
        
        prompt = self.create_prompt(articles_dict)
        
        try:
            ollama_model = OllamaLLM(model=self.ollama_model)
            print(f"Starting Ollama model: {self.ollama_model}")
            response = ollama_model.invoke(prompt)
            print("Ollama model completed")
            return response if isinstance(response, str) else str(response)
        except Exception as e:
            print(f"Ollama API call failed: {e}")
            return self._generate_fallback_summary(articles_dict)
    
    def _generate_fallback_summary(self, articles_dict):
        """Generate a simple fallback summary when Ollama is not available"""
        summary = "Here are the articles for today:\n\n"
        
        for title, details in list(articles_dict.items())[:10]:  # Limit to first 10
            summary += f"**{title}**\n"
            summary += f"Summary: {details.get('summary', 'No summary available')[:150]}...\n"
            summary += f"Source: {details.get('source', 'Unknown')}\n"
            summary += f"Link: {details.get('link', 'No link available')}\n\n"
        
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