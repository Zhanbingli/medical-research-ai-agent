"""
True AI Agent with tool calling and autonomous reasoning.
Can plan, execute multiple steps, and make decisions.
"""
import json
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data_sources import PubMedClient
from src.utils import AIClientManager


@dataclass
class Tool:
    """Represents a tool the agent can use."""
    name: str
    description: str
    parameters: Dict[str, str]
    function: Callable


class MedicalResearchAgent:
    """
    Autonomous AI Agent for medical literature research.

    Can:
    - Search PubMed
    - Analyze articles
    - Answer complex questions
    - Make multi-step plans
    - Use tools autonomously
    """

    def __init__(self, provider: str = "claude"):
        """
        Initialize agent.

        Args:
            provider: AI provider to use for reasoning
        """
        self.ai_manager = AIClientManager()
        self.pubmed = PubMedClient()
        self.provider = provider

        # Register available tools
        self.tools = self._register_tools()

        # Conversation history for context
        self.conversation_history: List[Dict[str, str]] = []

    def _register_tools(self) -> Dict[str, Tool]:
        """Register tools available to the agent."""
        tools = {}

        # Tool 1: Search PubMed
        tools["search_pubmed"] = Tool(
            name="search_pubmed",
            description="Search PubMed database for medical literature. Returns list of articles with titles, abstracts, and metadata.",
            parameters={
                "query": "Search query string (e.g., 'diabetes machine learning')",
                "max_results": "Maximum number of results to return (default: 5)"
            },
            function=self._search_pubmed
        )

        # Tool 2: Get article details
        tools["get_article_details"] = Tool(
            name="get_article_details",
            description="Get full details of a specific article by PMID",
            parameters={
                "pmid": "PubMed ID of the article"
            },
            function=self._get_article_details
        )

        # Tool 3: Analyze text
        tools["analyze_text"] = Tool(
            name="analyze_text",
            description="Analyze and extract insights from text",
            parameters={
                "text": "Text to analyze",
                "task": "Type of analysis (summarize, extract_key_points, etc.)"
            },
            function=self._analyze_text
        )

        # Tool 4: Compare studies
        tools["compare_studies"] = Tool(
            name="compare_studies",
            description="Compare multiple studies to find similarities and differences",
            parameters={
                "articles": "List of article data to compare"
            },
            function=self._compare_studies
        )

        return tools

    def _search_pubmed(self, query: str, max_results: int = 5) -> List[Dict]:
        """Tool: Search PubMed."""
        return self.pubmed.search_and_fetch(query, max_results=max_results)

    def _get_article_details(self, pmid: str) -> Dict:
        """Tool: Get article details."""
        articles = self.pubmed.fetch_details([pmid])
        return articles[0] if articles else {}

    def _analyze_text(self, text: str, task: str = "summarize") -> str:
        """Tool: Analyze text with AI."""
        prompt = f"Task: {task}\n\nText:\n{text}\n\nAnalysis:"

        return self.ai_manager.generate(
            prompt=prompt,
            provider=self.provider,
            max_tokens=1000
        )

    def _compare_studies(self, articles: List[Dict]) -> str:
        """Tool: Compare multiple studies."""
        articles_text = "\n\n".join([
            f"Study {i+1}:\nTitle: {art['title']}\nAbstract: {art.get('abstract', 'N/A')}"
            for i, art in enumerate(articles)
        ])

        prompt = f"""Compare these medical studies and identify:
1. Common findings
2. Contradictions
3. Methodological differences
4. Clinical implications

{articles_text}

Comparison:"""

        return self.ai_manager.generate(
            prompt=prompt,
            provider=self.provider,
            max_tokens=1500
        )

    def _format_tools_for_prompt(self) -> str:
        """Format tools description for AI prompt."""
        tools_desc = []

        for tool_name, tool in self.tools.items():
            params = "\n".join([
                f"  - {name}: {desc}"
                for name, desc in tool.parameters.items()
            ])

            tools_desc.append(
                f"**{tool.name}**\n"
                f"Description: {tool.description}\n"
                f"Parameters:\n{params}"
            )

        return "\n\n".join(tools_desc)

    def _parse_tool_call(self, response: str) -> Optional[Dict]:
        """
        Parse tool call from AI response.

        Expected format:
        <tool>tool_name</tool>
        <parameters>{"param1": "value1"}</parameters>
        """
        try:
            # Extract tool name
            if "<tool>" not in response or "</tool>" not in response:
                return None

            tool_start = response.find("<tool>") + 6
            tool_end = response.find("</tool>")
            tool_name = response[tool_start:tool_end].strip()

            # Extract parameters
            if "<parameters>" not in response or "</parameters>" not in response:
                return {"tool": tool_name, "parameters": {}}

            params_start = response.find("<parameters>") + 12
            params_end = response.find("</parameters>")
            params_json = response[params_start:params_end].strip()

            parameters = json.loads(params_json)

            return {
                "tool": tool_name,
                "parameters": parameters
            }

        except Exception as e:
            print(f"Error parsing tool call: {e}")
            return None

    def _execute_tool(self, tool_call: Dict) -> Any:
        """Execute a tool call."""
        tool_name = tool_call["tool"]
        parameters = tool_call["parameters"]

        if tool_name not in self.tools:
            return f"Error: Unknown tool '{tool_name}'"

        tool = self.tools[tool_name]

        try:
            result = tool.function(**parameters)
            return result
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"

    def think(self, user_query: str, max_iterations: int = 5) -> str:
        """
        Agent reasoning loop with tool use.

        Args:
            user_query: User's question or request
            max_iterations: Maximum reasoning iterations

        Returns:
            Final answer
        """
        # Add user query to history
        self.conversation_history.append({
            "role": "user",
            "content": user_query
        })

        tools_description = self._format_tools_for_prompt()

        system_prompt = f"""You are an expert medical research agent. You can use tools to search literature and analyze information.

Available Tools:
{tools_description}

To use a tool, format your response as:
<tool>tool_name</tool>
<parameters>{{"param1": "value1", "param2": "value2"}}</parameters>

After using tools, provide a final answer starting with "Final Answer: "

Think step by step and use tools as needed to answer the user's question comprehensively."""

        for iteration in range(max_iterations):
            # Build context with conversation history
            context = f"User Query: {user_query}\n\n"

            if len(self.conversation_history) > 1:
                context += "Previous steps:\n"
                for msg in self.conversation_history[1:]:
                    context += f"{msg['role']}: {msg['content'][:200]}...\n"

            context += "\nWhat should you do next?"

            # Get AI's next action
            response = self.ai_manager.generate(
                prompt=context,
                system_prompt=system_prompt,
                provider=self.provider,
                max_tokens=1500,
                temperature=0.7
            )

            # Check if this is the final answer
            if "Final Answer:" in response:
                final_answer = response.split("Final Answer:")[1].strip()
                self.conversation_history.append({
                    "role": "assistant",
                    "content": final_answer
                })
                return final_answer

            # Parse and execute tool call
            tool_call = self._parse_tool_call(response)

            if tool_call:
                print(f"[Agent] Using tool: {tool_call['tool']}")

                tool_result = self._execute_tool(tool_call)

                self.conversation_history.append({
                    "role": "tool",
                    "content": f"Tool: {tool_call['tool']}\nResult: {json.dumps(tool_result, default=str)[:500]}"
                })

            else:
                # No tool call detected, ask for clarification
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })

        # Max iterations reached
        return "Unable to complete the task within the iteration limit. Please try a simpler query."

    def quick_answer(self, query: str) -> str:
        """
        Quick answer without multi-step reasoning.

        Args:
            query: User's question

        Returns:
            Direct answer
        """
        return self.ai_manager.generate(
            prompt=query,
            provider=self.provider,
            max_tokens=1000
        )

    def reset_conversation(self):
        """Clear conversation history."""
        self.conversation_history = []


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    agent = MedicalResearchAgent(provider="claude")

    # Test autonomous reasoning
    query = "What are the latest treatments for type 2 diabetes? Find relevant studies and summarize key findings."

    print(f"User: {query}\n")
    print("Agent is thinking...\n")

    answer = agent.think(query, max_iterations=5)

    print(f"\nFinal Answer:\n{answer}")
