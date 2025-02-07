from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import Graph, StateGraph
from langgraph.prebuilt import ToolExecutor
from langchain_openai import ChatOpenAI
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.text_splitter import RecursiveCharacterTextSplitter
import operator
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize components from the provided functions
from src.utils.github import parse_github_url, fetch_user_data, fetch_repo_data, rate_repo_activity
from src.utils.contract_code import fetch_contract_source_code
from src.utils.trading_data import get_details

# Initialize search tool
tavily_search = TavilySearchResults(max_results=3)

@dataclass
class AgentState:
    """State object for the research workflow"""
    messages: List[BaseMessage]
    github_data: Dict = None
    contract_data: Dict = None
    token_data: Dict = None
    current_step: str = "start"
    final_analysis: str = ""

# [Previous helper functions remain the same]
def analyze_github_repo(url: str) -> Dict:
    """
    Analyze a GitHub repository and returns metrics and rating.
    Args:
        url (str): GitHub repository URL
    Returns:
        Dict: Repository metrics and analysis
    """
    try:
        # Parse the GitHub URL
        parsed = parse_github_url(url)
        if parsed["type"] != "repo":
            return {"error": "Not a valid repository URL"}
            
        # Get repository data
        repo_data = fetch_repo_data(parsed["username"], parsed["repo"])
        
        # Get user data for additional context
        user_data = fetch_user_data(parsed["username"])
        
        # Get repository rating
        repo_rating = rate_repo_activity(repo_data)
        
        # Combine all data
        analysis = {
            "repository": {
                "name": f"{parsed['username']}/{parsed['repo']}",
                "stars": repo_data.get("stars", 0),
                "forks": repo_data.get("forks", 0),
                "watchers": repo_data.get("watchers", 0),
                "open_issues": repo_data.get("open_issues", 0)
            },
            "developer": {
                "username": parsed["username"],
                "followers": user_data.get("followers", 0),
                "public_repos": user_data.get("public_repos", 0),
                "total_stars": user_data.get("total_stars", 0),
                "total_forks": user_data.get("total_forks", 0)
            },
            "rating": repo_rating,
            "url": url
        }
        
        return analysis
        
    except Exception as e:
        return {"error": f"Failed to analyze repository: {str(e)}"}

def analyze_blockchain_security(contract_code: str, llm) -> str:
    """Analyze smart contract for security issues"""
    prompt = """Analyze this smart contract code for:
    1. Security vulnerabilities (reentrancy, overflow, etc.)
    2. Access control and ownership patterns
    3. Potential centralization risks
    4. Common best practices compliance
    
    Provide a clear summary of findings:
    """
    
    try:
        message = HumanMessage(content=f"{prompt}\n\nContract:\n{contract_code}")
        response = llm.invoke([message])
        return response.content
    except Exception as e:
        return f"Error analyzing contract: {str(e)}"

def assess_investment_potential(
    github_data: Dict,
    contract_analysis: str,
    token_metrics: Dict,
    llm
) -> str:
    """Generate investment recommendation based on all collected data"""
    prompt = f"""Based on the following data, provide an investment recommendation:

    GitHub Analysis:
    {github_data}
    
    Security Analysis:
    {contract_analysis}
    
    Token Metrics:
    - Current Price: ${token_metrics.get('current_price_usd')}
    - Market Cap: ${token_metrics.get('market_cap_usd')}
    - Price Change 24h: {token_metrics.get('price_change_percentage_24h')}%
    - ATH: ${token_metrics.get('ath_usd')}
    - ATH Change: {token_metrics.get('ath_change_percentage_usd')}%
    
    Consider:
    1. Project development activity and community
    2. Security risks and centralization
    3. Market timing and price action
    4. Overall risk/reward ratio
    
    Provide a detailed recommendation:"""
    
    try:
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        return response.content
    except Exception as e:
        return f"Error generating recommendation: {str(e)}"

def create_research_graph():
    # Initialize LLM
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o",  # Using standard GPT-4
    )
    
    # Create workflow graph
    workflow = StateGraph(AgentState)
    
    # Define nodes
    def github_research(state):
        """Find and analyze GitHub repository"""
        if not state.messages:
            return state
        
        query = state.messages[-1].content
        search_results = tavily_search.run(f"github repository {query}")
        if search_results:
            github_url = search_results[0]["url"]
            github_data = analyze_github_repo(github_url)
            state.github_data = github_data
            state.current_step = "contract_analysis"
        return state
    
    def contract_analysis(state):
        """Analyze smart contract code"""
        if not state.github_data:
            return state
            
        contract_addr = state.messages[-1].content
        contract_data = fetch_contract_source_code(contract_addr)
        if contract_data["success"]:
            security_analysis = analyze_blockchain_security(
                contract_data["data"],
                llm
            )
            state.contract_data = {
                "code": contract_data["data"],
                "analysis": security_analysis
            }
            state.current_step = "token_analysis"
        return state
    
    def token_analysis(state):
        """Analyze token metrics and generate recommendation"""
        if not state.contract_data:
            return state
            
        token_addr = state.messages[-1].content
        token_data = get_details(token_addr)
        state.token_data = token_data
        
        recommendation = assess_investment_potential(
            state.github_data,
            state.contract_data["analysis"],
            token_data,
            llm
        )
        
        state.final_analysis = recommendation
        state.current_step = "complete"
        return state
    
    # Add nodes to graph
    workflow.add_node("github_research", github_research)
    workflow.add_node("contract_analysis", contract_analysis)
    workflow.add_node("token_analysis", token_analysis)
    
    # Add entry point from START to github_research
    workflow.set_entry_point("github_research")
    
    # Define edges between nodes
    workflow.add_conditional_edges(
        "github_research",
        lambda x: "token_analysis" if x.contract_data else "contract_analysis"
    )
    
    workflow.add_conditional_edges(
        "contract_analysis",
        lambda x: "complete" if x.token_data else "token_analysis"
    )
    
    # Set end condition
    workflow.set_finish_point("token_analysis")
    
    return workflow.compile()

def main():
    # Create research workflow
    research_graph = create_research_graph()
    
    # Get project name or token address from user
    query = input("Enter project name or token address to analyze: ")
    
    # Initialize state
    initial_state = AgentState(
        messages=[HumanMessage(content=query)],
        github_data=None,
        contract_data=None,
        token_data=None,
        current_step="start",
        final_analysis=""
    )
    
    # Run analysis
    final_state = research_graph.invoke(initial_state)
    
    # Print results
    print("\nAnalysis Results:")
    if isinstance(final_state, dict) and 'final_analysis' in final_state:
        print(final_state['final_analysis'])
    elif hasattr(final_state, 'final_analysis'):
        print(final_state.final_analysis)
    else:
        print("Analysis completed but no final results available.")
        print("State:", final_state)

if __name__ == "__main__":
    main()