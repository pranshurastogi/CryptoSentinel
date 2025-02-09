# CryptoSentinel

CryptoSentinel is an advanced cryptocurrency research and trading bot that automates project analysis and trading decisions using AI-powered insights. It combines GitHub repository analysis, smart contract security scanning, and token metrics to provide comprehensive investment recommendations.

## Features

- **Multi-Source Analysis**
  - GitHub repository metrics and activity assessment
  - Smart contract security analysis
  - Token performance metrics
  - Social sentiment analysis

- **Flexible Input Processing**
  - GitHub URLs
  - Smart contract addresses
  - Project names

- **Interactive Trading**
  - Automated trading execution via CDP AgentKit
  - Risk assessment and recommendations
  - Trading confirmation workflow

- **Conversational Interface**
  - Follow-up questions support
  - Context-aware responses
  - Session management

## Prerequisites

- Python 3.8+
- Node.js 14+ (for web interface)
- Access to required API services:
  - OpenAI API
  - CDP AgentKit
  - GitHub API
  - Tavily API
  - Twitter API
  - Etherscan API
  - LangSmith (optional, for debugging)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/cryptosentinel.git
cd cryptosentinel
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables by creating a `.env` file:
```env
CDP_API_KEY_NAME=your_cdp_key_name
BASE_SEPOLIA_RPC_URL=your_rpc_url
CDP_API_KEY_PRIVATE_KEY=your_private_key
OPENAI_API_KEY=your_openai_key
TAVILY_API_KEY=your_tavily_key
GITHUB_TOKEN=your_github_token
TWITTER_BEARER_TOKEN=your_twitter_token
ETHERSCAN_API_KEY=your_etherscan_key
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT="pr-grumpy-advertising-62"
```

## Project Structure

```
cryptosentinel/
├── server.py          # FastAPI server implementation
├── agent.py           # Research bot and analysis logic
├── requirements.txt   # Python dependencies
├── .env              # Environment variables
└── src/
    └── utils/
        ├── github.py        # GitHub analysis utilities
        ├── contract_code.py # Smart contract analysis
        └── trading_data.py  # Trading metrics utilities
```

## Usage

1. Start the API server:
```bash
python server.py
```

2. The server will start on `http://localhost:8000` with the following endpoints:

- `POST /api/analyze`: Submit initial analysis request
- `POST /api/trading-decision`: Process trading decisions
- `POST /api/followup`: Handle follow-up questions
- `POST /api/reset`: Reset session state
- `GET /api/health`: Health check endpoint

### API Examples

1. Initial Analysis:
```bash
curl -X POST http://localhost:8000/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"query": "github.com/username/repo", "session_id": "123"}'
```

2. Trading Decision:
```bash
curl -X POST http://localhost:8000/api/trading-decision \
  -H "Content-Type: application/json" \
  -d '{"decision": "yes", "session_id": "123"}'
```

3. Follow-up Question:
```bash
curl -X POST http://localhost:8000/api/followup \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the token's market cap?", "session_id": "123"}'
```

## Core Components

### ResearchBot

The main class that orchestrates the analysis workflow:
- Input analysis and classification
- GitHub repository analysis
- Smart contract security scanning
- Token metrics collection
- Investment recommendation generation
- Trading execution

### State Management

Uses `AgentState` class to maintain conversation context and analysis results:
- Conversation history
- Analysis results
- Trading decisions
- Error handling

### Research Graph

Implements a directed workflow using LangGraph:
1. Input Analysis
2. GitHub Research
3. Contract Analysis
4. Token Analysis
5. Final Recommendation
6. Trading Execution

## Security Considerations

- API keys and private keys should be kept secure
- Use environment variables for sensitive data
- Implement rate limiting for production deployments
- Add authentication for API endpoints
- Validate all input data
- Monitor trading transactions

## Error Handling

The system includes comprehensive error handling:
- Invalid input detection
- API failure recovery
- Missing data management
- Trading execution safety checks

## Agent Flow

## Screenshots:

### Landing Page

### Analysis Page

### Decision Page

### video Demo

