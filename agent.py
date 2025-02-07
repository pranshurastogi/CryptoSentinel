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
    messages: List[BaseMessage]
    github_data: Dict = None
    contract_data: Dict = None
    token_data: Dict = None
    current_step: str = "start"
    
def create_agent(llm):
    """Create an agent with tools"""
    tools = [
        Tool(
            name="search_github",
            func=lambda q: tavily_search.run(f"github repository {q}"),
            description="Search for GitHub repositories related to a blockchain project"
        ),
        Tool(
            name="analyze_github",
            func=lambda url: analyze_github_repo(url),
            description="Analyze a GitHub repository's metrics and activity"
        ),
        Tool(
            name="analyze_contract",
            func=lambda addr: fetch_contract_source_code(addr),
            description="Analyze smart contract source code for security issues"
        ),
        Tool(
            name="get_token_metrics",
            func=lambda addr: get_details(addr, "base"),
            description="Get detailed token metrics from CoinGecko"
        )
    ]
    
    prompt = PromptTemplate.from_template("""
    You are a blockchain project research assistant. Use the available tools to analyze projects.
    
    Tools available:
    search_github: Search for GitHub repositories
    analyze_github: Get repository metrics
    analyze_contract: Analyze smart contract code
    get_token_metrics: Get token market data
    
    Goal: {input}
    
    Take actions one step at a time. Think about which tool to use when.
    
    {agent_scratchpad}
    """)
    
    agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

def analyze_github_repo(url: str) -> Dict:
    """Analyze a GitHub repository and return metrics"""
    try:
        parsed = parse_github_url(url)
        if parsed["type"] == "repo":
            repo_data = fetch_repo_data(parsed["username"], parsed["repo"])
            rating = rate_repo_activity(repo_data)
            return {**repo_data, "rating": rating}
        return {"error": "Not a valid repository URL"}
    except Exception as e:
        return {"error": str(e)}

def analyze_blockchain_security(contract_code: str, llm) -> str:
    """Analyze smart contract for security issues with chunking support"""
    # Split contract into manageable chunks
    chunks = chunk_contract_code(contract_code)
    analyses = []
    
    # Analyze each chunk
    for i, chunk in enumerate(chunks):
        chunk_prompt = f"""Analyze this portion ({i+1}/{len(chunks)}) of the smart contract code for potential security issues, 
        focusing on:
        1. Reentrancy vulnerabilities
        2. Access control issues
        3. Centralization risks
        4. Potential rugpull vectors
        
        Contract code section:
        {chunk}
        
        Provide a focused analysis of this section:"""
        
        try:
            chunk_analysis = llm.predict(chunk_prompt)
            analyses.append(chunk_analysis)
        except Exception as e:
            analyses.append(f"Error analyzing chunk {i+1}: {str(e)}")
    
    # Combine and summarize analyses
    combined_analyses = "\n\n".join(analyses)
    
    summary_prompt = f"""Based on the detailed analyses of different sections of the contract, provide a comprehensive summary of security concerns:

    Individual analyses:
    {combined_analyses}
    
    Provide a consolidated security assessment:"""
    
    try:
        return llm.predict(summary_prompt)
    except Exception as e:
        return f"Error generating final summary: {str(e)}\n\nIndividual analyses:\n{combined_analyses}"

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
    
    return llm.predict(prompt)
def chunk_contract_code(contract_code: str, chunk_size: int = 6000) -> List[str]:
    """Split contract code into manageable chunks"""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=200,
        length_function=len,
        separators=["\n\n", "\n", " ", ""]
    )
    return text_splitter.split_text(contract_code)

def create_research_graph():
    # Initialize LLM
    llm = ChatOpenAI(temperature=0,model="gpt-4o")
    
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
        
        state.messages.append(AIMessage(content=recommendation))
        state.current_step = "complete"
        return state
    
    # Add nodes to graph
    workflow.add_node("github_research", github_research)
    workflow.add_node("contract_analysis", contract_analysis)
    workflow.add_node("token_analysis", token_analysis)
    
    # Define edges
    workflow.add_edge("github_research", "contract_analysis")
    workflow.add_edge("contract_analysis", "token_analysis")
    
    # Set entry point
    workflow.set_entry_point("github_research")
    
    return workflow.compile()

def main():
    # Create research workflow
    research_graph = create_research_graph()
    
    # Get project name or token address from user
    query = input("Enter project name or token address to analyze: ")
    
    # Initialize state
    state = AgentState(
        messages=[HumanMessage(content=query)]
    )
    
    # Run analysis
    final_state = research_graph.invoke(state)
    
    # Print results
    print("\nAnalysis Results:")
    print(final_state.messages[-1].content)

if __name__ == "__main__":
    main()