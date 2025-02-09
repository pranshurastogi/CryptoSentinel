import os
# from langchain.llms import OpenAI
from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set your Tavily API key (ensure this key is kept secure)
# os.environ["TAVILY_API_KEY"] = "your_tavily_api_key_here"  # Replace with your actual Tavily API key

# Initialize the Tavily search tool with desired parameters (e.g., max_results=3)
tavily_search = TavilySearchResults(max_results=3)

def search_and_extract(query):
    results = tavily_search.run(query)
    # Extract and return just the URLs
    return "\n".join([res["url"] for res in results])

tools = [
    Tool(
        name="Tavily Web Search",
        func=search_and_extract,  # Use custom function
        description="Retrieves up-to-date information and provides URLs.",
        return_direct=True
    )
]


# Initialize the language model (using OpenAI as an example)
llm = ChatOpenAI(temperature=0)

# Create the agent, specifying the agent type that can decide when to call the tool.
agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)

# Ask the user for a query
query = input("What would you like to search for? ")

# Run the agent with the user-provided query
result = agent.run(query)

# Display the final result
print("\nFinal Result:")
print(result)
