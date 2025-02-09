from datetime import datetime
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass, field
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

# Added import for CDP Agentkit
from cdp_langchain.agent_toolkits import CdpToolkit
from cdp_langchain.utils import CdpAgentkitWrapper

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
    final_analysis: Dict = None
    input_type: str = None
    github_url: str = None
    contract_address: str = None
    project_name: str = None
    errors: List[str] = None
    conversation_history: List[Dict] = field(default_factory=list)
    context: Dict = field(default_factory=dict)
    trading_decision: str = None  # New field for trading decision
    trading_result: str = None    # New field for trading result

    def __post_init__(self):

        if self.errors is None:

            self.errors = []

    def add_to_history(self, role: str, content: str):
        self.conversation_history.append({
            "role": role,
            "content": content
        })

def initialize_trading_agent():
    """Initialize the CDP trading agent"""
    llm = ChatOpenAI(model="gpt-4")
    
    # Initialize CDP Agentkit
    agentkit = CdpAgentkitWrapper()
    cdp_toolkit = CdpToolkit.from_cdp_agentkit_wrapper(agentkit)
    tools = cdp_toolkit.get_tools()
    
    # Create system prompt for the trading agent with all required variables
    prompt_template = """You are a trading agent that can execute token purchases using CDP AgentKit. 
    When asked to buy a token, you should:
    1. Check if you have sufficient funds using get_wallet_details
    2. If on base-sepolia, request funds from faucet if needed
    3. Execute the purchase using swap_tokens
    4. Confirm the transaction completed successfully
    Be concise in your responses and focus on execution.

    Tools available:
    {tools}

    Use the following format:

    Question: the input question you must answer
    Thought: you should always think about what to do
    Action: the action to take, should be one of [{tool_names}]
    Action Input: the input to the action
    Observation: the result of the action
    ... (this Thought/Action/Action Input/Observation can repeat N times)
    Thought: I now know what to do
    Final Answer: the final answer to the original input question

    Begin!

    Question: {input}
    {agent_scratchpad}"""

    prompt = PromptTemplate(
        template=prompt_template,
        input_variables=["input", "tools", "tool_names", "agent_scratchpad"]
    )
    
    # Create trading agent with correct parameters
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    
    # Create agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True
    )
    
    return agent_executor


def execute_trade(state: AgentState, agent_executor) -> str:
    """Execute token purchase using CDP agent"""
    if not state.contract_address:
        return "Error: No contract address provided for trading"
        
    try:
        # Construct trading instruction
        trading_instruction = (
            f"Please buy the token at address {state.contract_address}. "
            "First check wallet details, then execute the purchase using appropriate tools."
        )
        
        # Execute trade
        response = agent_executor.invoke(
            {"input": trading_instruction}
        )
        
        return response["output"]
    except Exception as e:
        return f"Trading error: {str(e)}"
    

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

@dataclass
class AnalysisMetrics:
    rating: float  # 0-10 scale
    comment: str
    error: str | None = None

@dataclass
class InvestmentAnalysis:
    code_activity: AnalysisMetrics
    smart_contract_risk: AnalysisMetrics
    token_performance: AnalysisMetrics
    social_sentiment: AnalysisMetrics
    risk_reward_ratio: float  # 0-5 scale
    confidence_score: float   # 0-100%
    final_recommendation: str
    timestamp: str = datetime.now().isoformat()

def assess_investment_potential(
    github_data: Dict,
    contract_analysis: str,
    token_metrics: Dict,
    llm
) -> Dict:
    """Generate structured investment recommendation based on all collected data"""
    
    try:
        response = llm.with_structured_output(InvestmentAnalysis).invoke(
            f"""Analyze the following cryptocurrency investment data and provide a detailed assessment.
            
            GitHub Analysis Data:
            {github_data}
            
            Smart Contract Security Analysis:
            {contract_analysis}
            
            Token and socialmedia Metrics:
            {token_metrics}

            Instructions:
            1. Analyze each aspect thoroughly
            2. Provide ratings on a 0-10 scale (0 for missing/invalid data)
            3. Include brief but specific comments
            4. Note any data issues or anomalies as errors
            5. Calculate risk/reward ratio (0-5) and confidence score (0-100%)
            6. Provide a final investment recommendation
            7. *If Data is missing or invalid data the error should be "Not enough data"*
            8. Social sentiment should be based on twitter numbers and price movement in recent times

            If any data is missing or invalid in a section, set its rating to 0 and include an error message.
            Keep comments concise but informative (30-50 words).
            Base the final recommendation on the weighted average of all metrics.
            """
        )
        
        return response
        
    except Exception as e:
        print(f"Error generating recommendation: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Error generating recommendation: {str(e)}",
            "code_activity": {"rating": 0, "comment": "", "error": "Analysis failed"},
            "smart_contract_risk": {"rating": 0, "comment": "", "error": "Analysis failed"},
            "token_performance": {"rating": 0, "comment": "", "error": "Analysis failed"},
            "social_sentiment": {"rating": 0, "comment": "", "error": "Analysis failed"},
            "risk_reward_ratio": 0,
            "confidence_score": 0,
            "final_recommendation": "Analysis failed due to error",
            "timestamp": datetime.now().isoformat()
        }
    
def handle_followup_question(state: AgentState, question: str, llm) -> str:
    """Handle follow-up questions using summarized conversation history"""
    
    # Create a concise context from conversation history
    context = "\n".join([
        f"{entry['role']}: {entry['content']}"
        for entry in state.conversation_history[-2:]  # Only use last interaction
    ])
    
    prompt = f"""Based on this previous analysis:

{context}

Please answer this follow-up question: {question}

Provide a specific answer based on the available information."""

    try:
        message = HumanMessage(content=prompt)
        response = llm.invoke([message])
        return response.content
    except Exception as e:
        return f"Error processing follow-up question: {str(e)}"

class ResearchBot:
    def __init__(self):
        self.llm = ChatOpenAI(temperature=0, model="gpt-4")
        self.state = None
        self.research_graph = create_research_graph()

    def _create_summary(self, state: AgentState) -> str:
        """Create a summary of the research findings"""
        summary_parts = []
        
        # Add GitHub analysis if available
        if state.github_data:
            if isinstance(state.github_data, dict) and "error" not in state.github_data:
                repo_info = state.github_data.get("repository", {})
                summary_parts.append(
                    f"GitHub Analysis:\n"
                    f"Repository: {repo_info.get('name')}\n"
                    f"Stars: {repo_info.get('stars')}\n"
                    f"Forks: {repo_info.get('forks')}\n"
                    f"Rating: {state.github_data.get('rating', 'N/A')}"
                )
            else:
                summary_parts.append(f"GitHub Analysis Error: {state.github_data.get('error', 'Unknown error')}")

        # Add contract analysis if available
        if state.contract_data:
            summary_parts.append(
                f"\nContract Analysis:\n{state.contract_data.get('analysis', 'No analysis available')}"
            )

        # Add token data if available
        if state.token_data:
            summary_parts.append(
                f"\nToken Metrics:\n"
                f"Price: ${state.token_data.get('current_price_usd', 'N/A')}\n"
                f"Market Cap: ${state.token_data.get('market_cap_usd', 'N/A')}\n"
                f"24h Change: {state.token_data.get('price_change_percentage_24h', 'N/A')}%"
            )

        # Add final analysis if available
        if state.final_analysis:
            summary_parts.append(f"\n{state.final_analysis}")
        
        # If no data is available, provide a status message
        if not summary_parts:
            return "Analysis in progress... No data available yet."
            
        return "\n".join(summary_parts)

    def process_initial_query(self, query: str) -> str:
        """Process the initial research query"""
        self.state = AgentState(
            messages=[HumanMessage(content=query)],
            current_step="start"
        )
        
        final_state_dict = self.research_graph.invoke(self.state)
        self.state = AgentState(**final_state_dict)
        
        summary = self.state.final_analysis
        # summary = self._create_summary(self.state)
        self.state.add_to_history("user", query)
        self.state.add_to_history("assistant", summary)
        
        return summary

    def process_trading_decision(self, decision: str) -> str:
        """Process user's trading decision"""
        if not self.state:
            return "Please provide an initial query first."
            
        self.state.trading_decision = decision
        final_state_dict = self.research_graph.invoke(self.state)
        self.state = AgentState(**final_state_dict)
        
        if self.state.trading_result:
            return self.state.trading_result
        return "Trading decision processed."

    def process_followup(self, question: str) -> str:
        """Process follow-up questions"""
        if not self.state:
            return "Please provide an initial query first."
            
        response = handle_followup_question(self.state, question, self.llm)
        self.state.add_to_history("user", question)
        self.state.add_to_history("assistant", response)
        
        return response

def create_research_graph():
    # Initialize LLM
    llm = ChatOpenAI(
        temperature=0,
        model="gpt-4o"
    )
    trading_agent = initialize_trading_agent()
    
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
        """Generate final analysis and handle trading prompt"""
        if state.token_data and state.github_data and state.contract_data:
            recommendation = assess_investment_potential(
                state.github_data,
                state.contract_data["analysis"],
                state.token_data,
                llm
            )
            state.final_analysis = recommendation
            
            # Add trading prompt
            trading_prompt = "\n\nWould you like me to buy this token for you? (yes/no): "
            # state.final_analysis += trading_prompt
            state.current_step = "await_trading_decision"
            
        elif state.github_data:
            state.final_analysis = f"GitHub Analysis Only:\n{state.github_data}"
            
        return state
        
    def handle_trading_decision(state):
        """Process user's trading decision"""
        if state.trading_decision and state.trading_decision.lower() == "yes":
            trading_result = execute_trade(state, trading_agent)
            state.trading_result = trading_result
            
        return state

    def end_node(state):
        """Final node to properly end the workflow"""
        return state
    
    # Add nodes to graph
    workflow.add_node("input_analysis", input_analysis)
    workflow.add_node("github_search", github_search)
    workflow.add_node("github_research", github_research)
    workflow.add_node("contract_analysis", contract_analysis)
    workflow.add_node("token_analysis", token_analysis)
    workflow.add_node("generate_analysis", generate_analysis)
    workflow.add_node("handle_trading_decision", handle_trading_decision)
    workflow.add_node("end", end_node)  # Add the end node explicitly
    
    # Set entry point
    workflow.set_entry_point("input_analysis")
    
    # Define edges with proper conditional routing
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
    
    workflow.add_conditional_edges(
        "generate_analysis",
        lambda x: "handle_trading_decision" if x.current_step == "await_trading_decision" else "end"
    )
    
    workflow.add_conditional_edges(
        "handle_trading_decision",
        lambda x: "end"
    )
    
    # Set proper end point
    workflow.set_finish_point("end")
    
    return workflow.compile()

def main():
    bot = ResearchBot()
    
    print("Welcome to the Research Bot! Enter 'quit' to exit.")
    
    while True:
        if not bot.state:
            query = input("\nEnter project name, contract address, or GitHub URL to analyze: ")
            if query.lower() == 'quit':
                break
                
            result = bot.process_initial_query(query)
            print("\nAnalysis:")
            print(result)
            
            if "Would you like me to buy this token for you?" in result:
                decision = input().lower()
                if decision in ['yes', 'no']:
                    trading_result = bot.process_trading_decision(decision)
                    print("\nTrading Result:")
                    print(trading_result)
                    bot.state = None  # Reset for new query
                
        else:
            follow_up = input("\nAsk a follow-up question (or 'new' for new analysis, 'quit' to exit): ")
            if follow_up.lower() == 'quit':
                break
            elif follow_up.lower() == 'new':
                bot.state = None
                continue
                
            response = bot.process_followup(follow_up)
            print("\nResponse:")
            print(response)

# if __name__ == "__main__":
#     try:
#         main()
#     except Exception as e:
#         import traceback
#         traceback.print_exc()