import React from 'react';
import { motion } from 'framer-motion';
import BuyDecision from './BuyDecision';

function AnalysisSummary({ summary, onDecision }) {
  // Destructure the API response to get the result and the trading prompt flag.
  const { result, has_trading_prompt } = summary;

  return (
    <motion.div
      className="analysis-summary"
      initial={{ x: 100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <h2>Analysis Summary</h2>

      <div className="metrics-grid">
        {/* Code Activity */}
        <div className="metric-card">
          <h3>Code Activity</h3>
          <div className="rating">
            <div
              className="progress-bar"
              style={{ width: `${result.code_activity.rating * 10}%` }}
            ></div>
            <span>{result.code_activity.rating} / 10</span>
          </div>
          <p>{result.code_activity.comment}</p>
          {result.code_activity.error && (
            <p className="error">Error: {result.code_activity.error}</p>
          )}
        </div>

        {/* Smart Contract Risk */}
        <div className="metric-card">
          <h3>Smart Contract Risk</h3>
          <div className="rating">
            <div
              className="progress-bar"
              style={{ width: `${result.smart_contract_risk.rating * 10}%` }}
            ></div>
            <span>{result.smart_contract_risk.rating} / 10</span>
          </div>
          <p>{result.smart_contract_risk.comment}</p>
        </div>

        {/* Token Performance */}
        <div className="metric-card">
          <h3>Token Performance</h3>
          <div className="rating">
            <div
              className="progress-bar"
              style={{ width: `${result.token_performance.rating * 10}%` }}
            ></div>
            <span>{result.token_performance.rating} / 10</span>
          </div>
          <p>{result.token_performance.comment}</p>
        </div>

        {/* Social Sentiment */}
        <div className="metric-card">
          <h3>Social Sentiment</h3>
          <div className="rating">
            <div
              className="progress-bar"
              style={{ width: `${result.social_sentiment.rating * 10}%` }}
            ></div>
            <span>{result.social_sentiment.rating} / 10</span>
          </div>
          <p>{result.social_sentiment.comment}</p>
          {result.social_sentiment.error && (
            <p className="error">Error: {result.social_sentiment.error}</p>
          )}
        </div>

        {/* Risk Reward Ratio (out of 5) */}
        <div className="metric-card">
          <h3>Risk Reward Ratio</h3>
          <div className="rating">
            <div
              className="progress-bar risk-reward"
              style={{ width: `${(result.risk_reward_ratio / 5) * 100}%` }}
            ></div>
            <span>{result.risk_reward_ratio} / 5</span>
          </div>
        </div>

        {/* Confidence Score (out of 100) */}
        <div className="metric-card">
          <h3>Confidence Score</h3>
          <div className="rating">
            <div
              className="progress-bar confidence"
              style={{ width: `${result.confidence_score}%` }}
            ></div>
            <span>{result.confidence_score} / 100</span>
          </div>
        </div>
      </div>

      <div className="final-recommendation">
        <h3>Final Recommendation</h3>
        <p>{result.final_recommendation}</p>
        <p className="timestamp">
          Analyzed at: {new Date(result.timestamp).toLocaleString()}
        </p>
      </div>

      {/* Show trading decision prompt if provided by the API */}
      {has_trading_prompt && (
        <>
          <p className="buy-prompt">Would you like to buy this token?</p>
          <BuyDecision onDecision={onDecision} />
        </>
      )}
    </motion.div>
  );
}

export default AnalysisSummary;
