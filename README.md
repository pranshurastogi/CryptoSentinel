# CryptoSentinel

<div align="center">
  <img src="https://github.com/user-attachments/assets/aab7f925-b6a1-4424-9bfa-45188b7d5dfe" alt="image">
</div>

Below is an example of a comprehensive README for your CryptoSentinel repository:

---

```markdown
# CryptoSentinel

CryptoSentinel is an AI-powered crypto analysis tool that helps users make informed trading decisions by analyzing multiple data points such as social sentiment, technical metrics, smart contract risks, and more. Built with React and Framer Motion, this application offers an engaging, animated UI that guides users through the analysis process and ultimately prompts them with a trading decision.

## Features

- **Token Analysis**: Enter a token’s contract address to start the analysis.
- **Animated Loaders**: Enjoy engaging animated loaders and reassuring messages while the system gathers data.
- **Comprehensive Report**: Get a detailed analysis including:
  - **Code Activity** (GitHub metrics)
  - **Smart Contract Risk**
  - **Token Performance**
  - **Social Sentiment**
  - **Risk Reward Ratio** (displayed out of 5)
  - **Confidence Score** (displayed out of 100)
- **Dynamic Progress Bars**: Each metric is displayed with a progress bar that fills based on the score and is color-coded according to predefined ranges.
- **Trading Decision Prompt**: After viewing the analysis report, users are prompted to confirm whether they wish to trade the token.
- **Error Handling**: If the trading decision API call fails (e.g., due to network or status code errors), the app displays an error message such as "Error: Please switch to Base network."

## Getting Started

### Prerequisites

- [Node.js](https://nodejs.org/) (version 12 or later)
- npm (comes with Node.js) or [Yarn](https://yarnpkg.com/)

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/yourusername/crypto-sentinel.git
   ```

2. **Navigate to the Project Directory**

   ```bash
   cd crypto-sentinel
   ```

3. **Install Dependencies**

   Using npm:
   ```bash
   npm install
   ```
   or using Yarn:
   ```bash
   yarn install
   ```

### Environment Variables

Create a `.env` file in the root directory and set the API base URL. For example:

```env
REACT_APP_API_BASE_URL=http://localhost:8000
```

This variable is used throughout the app to dynamically reference the backend API endpoints.

### Running the Application

Start the development server with:

Using npm:
```bash
npm start
```
or using Yarn:
```bash
yarn start
```

This command launches the app in your default browser at [http://localhost:3000](http://localhost:3000). You can then enter a token contract address to begin the analysis.

## Project Structure

```
crypto-sentinel/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── AnalysisSummary.js       # Displays the detailed analysis report
│   │   ├── BuyDecision.js           # Yes/No trading decision buttons
│   │   ├── DecisionLoader.js        # Animated loader for processing decisions (blinking dots)
│   │   ├── Loader.js                # Animated loader for token analysis with cycling messages
│   │   └── TokenInput.js            # Input form for the token contract address
│   ├── App.js                       # Main component managing application flow and state
│   ├── App.css                      # Global styles and layout definitions
│   └── index.js                     # Application entry point
├── .env                             # Environment variable definitions
└── package.json                     # Project configuration and dependencies
```

## Code Overview

- **App.js**: Manages the application state and controls the flow between token input, analysis loading, analysis summary, decision processing, and result display.
- **TokenInput.js**: Renders the form where users enter the token contract address.
- **Loader.js**: Displays a full-page loader with cycling messages (e.g., "Searching data...", "Our agents are at work...") during the analysis phase.
- **DecisionLoader.js**: Shows a “Processing your decision...” message with animated blinking dots while the trading decision API is processing.
- **AnalysisSummary.js**: Presents a detailed report that includes dynamic progress bars with color-coded fills based on score ranges. It also displays the final recommendation, timestamp, and a prompt for a trading decision.
- **BuyDecision.js**: Renders Yes/No buttons that trigger trading decision or reset API calls.

## API Integration

The front-end communicates with backend endpoints via POST requests:

1. **Analysis Endpoint**  
   When a user submits a token address, the app sends:
   ```bash
   POST /api/analyze
   Content-Type: application/json

   {
     "query": "0x123...abc",
     "session_id": "unique-session-id"
   }
   ```

2. **Trading Decision Endpoint**  
   If the user selects "yes", the app sends:
   ```bash
   POST /api/trading-decision
   Content-Type: application/json

   {
     "decision": "yes",
     "session_id": "unique-session-id"
   }
   ```

3. **Reset Endpoint**  
   If the user selects "no", the app sends:
   ```bash
   POST /api/reset
   Content-Type: application/json

   {
     "session_id": "unique-session-id"
   }
   ```

If the **trading-decision** API returns a non-200 status code, the app displays the error message:  
`"Error: Please switch to Base network."`

## Contributing

Contributions are welcome! If you have suggestions, bug fixes, or new features to add, please open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [React](https://reactjs.org/)
- [Framer Motion](https://www.framer.com/motion/)
- [uuid](https://www.npmjs.com/package/uuid)
- Special thanks to all contributors and open source projects that helped build CryptoSentinel.
```

---

This README provides a thorough overview of the project, setup instructions, usage, and details about the application structure and API integration. Feel free to adjust any sections as needed to better fit your project specifics.
