import React from 'react';
import { motion } from 'framer-motion';
import BuyDecision from './BuyDecision';

function AnalysisSummary({ summary, onDecision }) {
  const { result, has_trading_prompt } = summary;

  // Helper for ratings (out of 10)
  function getRatingColor(rating) {
    const value = Number(rating);
    if (value <= 2) return "#f44336";       // Red
    else if (value <= 5) return "#ff9800";    // Orange
    else if (value < 8) return "#ffeb3b";     // Yellow
    else return "#4caf50";                    // Green
  }

  // Helper for risk_reward_ratio (out of 5)
  function getRiskRewardColor(ratio) {
    const value = Number(ratio);
    if (value <= 2) return "#f44336";
    else if (value <= 3) return "#ff9800";
    else if (value < 4) return "#ffeb3b";
    else return "#4caf50";
  }

  // Helper for confidence_score (out of 100)
  function getConfidenceColor(score) {
    const value = Number(score);
    if (value <= 25) return "#f44336";
    else if (value <= 50) return "#ff9800";
    else if (value <= 75) return "#ffeb3b";
    else return "#4caf50";
  }

  // Render a progress bar with a default empty state and a fill portion.
  const renderProgressBar = (fillWidth, fillColor, label) => (
    <div className="rating">
      <div className="progress-bar-container">
        <div
          className="progress-bar-fill"
          style={{
            width: fillWidth,
            backgroundColor: fillColor
          }}
        ></div>
      </div>
      <span className="rating-text">{label}</span>
    </div>
  );
  

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
          {renderProgressBar(
            `${Number(result.code_activity.rating) * 10}%`,
            getRatingColor(result.code_activity.rating),
            `${result.code_activity.rating} / 10`
          )}
          <p>{result.code_activity.comment}</p>
          {result.code_activity.error && (
            <p className="error">Error: {result.code_activity.error}</p>
          )}
        </div>

        {/* Smart Contract Risk */}
        <div className="metric-card">
          <h3>Smart Contract Risk</h3>
          {renderProgressBar(
            `${Number(result.smart_contract_risk.rating) * 10}%`,
            getRatingColor(result.smart_contract_risk.rating),
            `${result.smart_contract_risk.rating} / 10`
          )}
          <p>{result.smart_contract_risk.comment}</p>
        </div>

        {/* Token Performance */}
        <div className="metric-card">
          <h3>Token Performance</h3>
          {renderProgressBar(
            `${Number(result.token_performance.rating) * 10}%`,
            getRatingColor(result.token_performance.rating),
            `${result.token_performance.rating} / 10`
          )}
          <p>{result.token_performance.comment}</p>
        </div>

        {/* Social Sentiment */}
        <div className="metric-card">
          <h3>Social Sentiment</h3>
          {renderProgressBar(
            `${Number(result.social_sentiment.rating) * 10}%`,
            getRatingColor(result.social_sentiment.rating),
            `${result.social_sentiment.rating} / 10`
          )}
          <p>{result.social_sentiment.comment}</p>
          {result.social_sentiment.error && (
            <p className="error">Error: {result.social_sentiment.error}</p>
          )}
        </div>

        {/* Risk Reward Ratio (out of 5) */}
        <div className="metric-card">
          <h3>Risk Reward Ratio</h3>
          {renderProgressBar(
            `${(Number(result.risk_reward_ratio) / 5) * 100}%`,
            getRiskRewardColor(result.risk_reward_ratio),
            `${result.risk_reward_ratio} / 5`
          )}
        </div>

        {/* Confidence Score (out of 100) */}
        <div className="metric-card">
          <h3>Confidence Score</h3>
          {renderProgressBar(
            `${Number(result.confidence_score)}%`,
            getConfidenceColor(result.confidence_score),
            `${result.confidence_score} / 100`
          )}
        </div>
      </div>

      <div className="final-recommendation">
        <h3>Final Recommendation</h3>
        <p>{result.final_recommendation}</p>
        <p className="timestamp">
          Analyzed at: {new Date(result.timestamp).toLocaleString()}
        </p>
      </div>

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
