import React, { useState } from 'react';
import { motion } from 'framer-motion';
import TokenInput from './components/TokenInput';
import AnalysisSummary from './components/AnalysisSummary';

function App() {
  // Application steps: 'input' → 'loading' → 'summary' → 'processingDecision' → 'result'
  const [step, setStep] = useState('input');
  const [analysisSummary, setAnalysisSummary] = useState(null);
  const [buyResult, setBuyResult] = useState(null);

  // Simulate backend API call to analyze token address
  const handleTokenSubmit = (address) => {
    setStep('loading');

    // Replace this with your actual API call
    setTimeout(() => {
      setAnalysisSummary({
        sentiment: 'Positive',
        githubActivity: 'Very Active',
        smartContractRisk: 'Low',
        walletDistribution: 'Well Distributed',
      });
      setStep('summary');
    }, 2000);
  };

  // Simulate processing the user's buy decision
  const handleDecision = (decision) => {
    setStep('processingDecision');
    setTimeout(() => {
      setBuyResult(
        decision === 'yes'
          ? 'Trade executed successfully!'
          : 'No action taken.'
      );
      setStep('result');
    }, 2000);
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>CryptoSentinel</h1>
        <p>
          An AI-powered crypto analysis tool to help you make informed trading
          decisions by analyzing social sentiment, technical metrics, and smart
          contract risks.
        </p>
      </header>

      <main className="app-main">
        {step === 'input' && <TokenInput onSubmit={handleTokenSubmit} />}

        {step === 'loading' && (
          <motion.div
            className="message"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <p>Analyzing token data...</p>
          </motion.div>
        )}

        {step === 'summary' && analysisSummary && (
          <AnalysisSummary summary={analysisSummary} onDecision={handleDecision} />
        )}

        {step === 'processingDecision' && (
          <motion.div
            className="message"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            <p>Processing your decision...</p>
          </motion.div>
        )}

        {step === 'result' && (
          <motion.div
            className="result"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
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
