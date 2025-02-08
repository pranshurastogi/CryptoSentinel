import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { motion } from 'framer-motion';
import TokenInput from './components/TokenInput';
import AnalysisSummary from './components/AnalysisSummary';
import Loader from './components/Loader';
import DecisionLoader from './components/DecisionLoader';

// API base URL from environment variable
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

function App() {
  const [sessionId, setSessionId] = useState('');
  const [step, setStep] = useState('input'); // 'input', 'loading', 'summary', 'processingDecision', 'result'
  const [analysisSummary, setAnalysisSummary] = useState(null);
  const [buyResult, setBuyResult] = useState(null);

  useEffect(() => {
    setSessionId(uuidv4());
  }, []);

  // Call analyze API
  const handleTokenSubmit = async (address) => {
    setStep('loading');
    try {
      const response = await fetch(`${API_BASE_URL}/api/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: address, session_id: sessionId })
      });
      const data = await response.json();
      setAnalysisSummary(data);
      setStep('summary');
    } catch (error) {
      console.error('Error analyzing token:', error);
      // Handle error state as needed
    }
  };

  // Call trading-decision or reset API
 // Call the trading decision API or reset API based on the user's choice.
const handleDecision = async (decision) => {
  setStep('processingDecision');
  try {
    const endpoint =
      decision === 'yes'
        ? `${API_BASE_URL}/api/trading-decision`
        : `${API_BASE_URL}/api/reset`;

    const payload =
      decision === 'yes'
        ? { decision, session_id: sessionId }
        : { session_id: sessionId };

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    // If the response status is not OK, set an error result.
    if (!response.ok) {
      setBuyResult('Error: Please switch to Base network.');
      setStep('result');
      return;
    }

    const data = await response.json();
    setBuyResult(data.message || 'Operation successful.');
    setStep('result');
  } catch (error) {
    console.error('Error processing decision:', error);
    setBuyResult('Error: Please switch to Base network.');
    setStep('result');
  }
};


  return (
    <div className="app">
      <header className="app-header">
        <h1>CryptoSentinel</h1>
        <p>
          An AI-powered crypto analysis tool to help you make informed trading decisions by analyzing social sentiment, technical metrics, and smart contract risks.
        </p>
      </header>

      <main className="app-main">
        {step === 'input' && <TokenInput onSubmit={handleTokenSubmit} />}
        {step === 'loading' && <Loader />}
        {step === 'summary' && analysisSummary && (
          <AnalysisSummary summary={analysisSummary} onDecision={handleDecision} />
        )}
        {step === 'processingDecision' && <DecisionLoader />}
        {step === 'result' && (
          <motion.div className="result" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
            <h2>Result</h2>
            <p>{buyResult}</p>
          </motion.div>
        )}
      </main>

      <footer className="app-footer">
        <p>&copy; {new Date().getFullYear()} CryptoSentinel</p>
      </footer>
    </div>
  );
}

export default App;
