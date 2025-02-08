import React from 'react';
import { motion } from 'framer-motion';
import BuyDecision from './BuyDecision';

function AnalysisSummary({ summary, onDecision }) {
  return (
    <motion.div
      className="analysis-summary"
      initial={{ x: 100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <h2>Analysis Summary</h2>
      <ul className="summary-list">
        <li>
          <strong>Twitter Sentiment:</strong> {summary.sentiment}
        </li>
        <li>
          <strong>GitHub Activity:</strong> {summary.githubActivity}
        </li>
        <li>
          <strong>Smart Contract Risk:</strong> {summary.smartContractRisk}
        </li>
        <li>
          <strong>Wallet Distribution:</strong> {summary.walletDistribution}
        </li>
      </ul>
      <p className="buy-prompt">Would you like to buy this token?</p>
      <BuyDecision onDecision={onDecision} />
    </motion.div>
  );
}

export default AnalysisSummary;
