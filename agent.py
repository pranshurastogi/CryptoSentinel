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
import re

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
    input_type: str = None
    github_url: str = None
    contract_address: str = None
    project_name: str = None
    errors: List[str] = None  # Track errors for reporting

    def __post_init__(self):

        if self.errors is None:

            self.errors = []

def analyze_user_input(input_text: str, llm) -> Dict:
    """
    Analyze user input to determine its type and extract relevant information
    """
    # Basic validation patterns
    github_pattern = r'github\.com/[\w-]+/[\w-]+'
    eth_address_pattern = r'0x[a-fA-F0-9]{40}'
    
    try:
        # First try to extract GitHub URL and contract address from the text
        print('inside analyze_user_input')
        github_match = re.search(github_pattern, input_text)
        eth_address_match = re.search(eth_address_pattern, input_text)
        print('inside analyze_user_input var',github_match, eth_address_match)
        if github_match:
            print('inside analyze_user_input if', github_match)
            return {"type": "github_url", "value": github_match.group(), "confidence": "high"}
        elif eth_address_match:
            print('inside analyze_user_input elif', eth_address_match)
            return {"type": "contract_address", "value": eth_address_match.group(), "confidence": "high"}
        
        # If no matches, treat as project name
        print('inside analyze_user_input else', input_text)
        return {"type": "project_name", "value": input_text.strip(), "confidence": "medium"}
            
    except Exception as e:
        print(f"Error during input analysis: {e}")
        return {"type": "project_name", "value": input_text.strip(), "confidence": "low"}
    
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
        model="gpt-4o"
    )
    
    # Create workflow graph
    workflow = StateGraph(AgentState)
    
    # Define nodes
    def input_analysis(state: AgentState) -> AgentState:
        """Analyze user input and determine next steps"""
        if not state.messages:
            return state
            
        query = state.messages[-1].content
        analysis = analyze_user_input(query, llm)
        
        state.input_type = analysis["type"]
        
        if analysis["type"] == "github_url":
            state.github_url = analysis["value"]
            state.current_step = "github_research"
        elif analysis["type"] == "contract_address":
            state.contract_address = analysis["value"]
            state.current_step = "contract_analysis"
        else:
            state.project_name = analysis["value"]
            state.current_step = "generate_analysis"
            
        return state
    
    def github_search(state: AgentState) -> AgentState:
        """Search for GitHub repository if only project name is provided"""
        if state.github_url:  # Skip if we already have a GitHub URL
            return state
            
        search_results = tavily_search.run(f"github repository {state.project_name}")
        if search_results:
            state.github_url = search_results[0]["url"]
        state.current_step = "generate_analysis"
        return state
    
    def github_research(state):
        """Analyze GitHub repository"""
        if not state.github_url:
            return state
            
        github_data = analyze_github_repo(state.github_url)
        state.github_data = github_data
        
        if state.contract_address:
            state.current_step = "contract_analysis"
        else:
            state.current_step = "final_analysis"
        return state
    
    def contract_analysis(state):
        """Analyze smart contract code"""
        if not state.contract_address:
            return state
            
        contract_data = fetch_contract_source_code(state.contract_address)
        if contract_data["success"]:
            security_analysis = analyze_blockchain_security(
                contract_data["data"],
                llm
            )
            state.contract_data = {
                "code": contract_data["data"],
                "analysis": security_analysis
            }
            
        if state.github_data:
            state.current_step = "token_analysis"
        else:
            state.current_step = "github_search"
        return state
    
    def token_analysis(state):
        """Analyze token metrics and generate recommendation"""
        if not state.contract_address:
            return state
            
        token_data = get_details(state.contract_address)
        state.token_data = token_data
        
        state.current_step = "final_analysis"
        return state
    
    def generate_analysis(state):
        """Generate final analysis and recommendation"""
        if state.token_data and state.github_data and state.contract_data:
            recommendation = assess_investment_potential(
                state.github_data,
                state.contract_data["analysis"],
                state.token_data,
                llm
            )
            state.final_analysis = recommendation
        elif state.github_data:
            state.final_analysis = f"GitHub Analysis Only:\n{state.github_data}"
        
        return state
    
    # Add nodes to graph
    workflow.add_node("input_analysis", input_analysis)
    workflow.add_node("github_search", github_search)
    workflow.add_node("github_research", github_research)
    workflow.add_node("contract_analysis", contract_analysis)
    workflow.add_node("token_analysis", token_analysis)
    workflow.add_node("generate_analysis", generate_analysis)
    
    # Set entry point
    workflow.set_entry_point("input_analysis")
    
    # Define conditional edges
    workflow.add_conditional_edges(
        "input_analysis",
        lambda x: {
            "github_url": "github_research",
            "contract_address": "contract_analysis",
            "project_name": "github_search"
        }[x.input_type]
    )
    
    workflow.add_conditional_edges(
        "github_search",
        lambda x: "github_research"
    )
    
    workflow.add_conditional_edges(
        "github_research",
        lambda x: "contract_analysis" if x.contract_address else "generate_analysis"
    )
    
    workflow.add_conditional_edges(
        "contract_analysis",
        lambda x: "token_analysis" if x.github_data else "github_search"
    )
    
    workflow.add_conditional_edges(
        "token_analysis",
        lambda x: "generate_analysis"
    )
    
    # Set final_analysis as the end point
    workflow.set_finish_point("generate_analysis")
    
    graph =  workflow.compile()
    # print(graph.get_graph().draw_mermaid())
    return graph

def main():
    # Create research workflow
    research_graph = create_research_graph()
    
    # Get user input
    query = input("Enter project name, contract address, or GitHub URL to analyze: ")
    
    # Initialize state
    initial_state = AgentState(
        messages=[HumanMessage(content=query)],
        current_step="start"
    )
    
    # Run analysis
    final_state_dict = research_graph.invoke(initial_state)
    # Convert the AddableValuesDict to AgentState
    final_state = AgentState(**final_state_dict)
    
    # Print results
    print("\nAnalysis Results:")
    if final_state.final_analysis:
        print(final_state.final_analysis)
    else:
        print("Analysis completed. Available data:")
        if final_state.github_data:
            print("\nGitHub Analysis:", final_state.github_data)
        if final_state.contract_data:
            print("\nContract Analysis:", final_state.contract_data["analysis"])
        if final_state.token_data:
            print("\nToken Analysis:", final_state.token_data)

if __name__ == "__main__":
    main()