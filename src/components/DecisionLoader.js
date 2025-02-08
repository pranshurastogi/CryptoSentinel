import React from 'react';

const DecisionLoader = () => {
  return (
    <div className="decision-loader">
      <p>
        Processing your decision
        <span className="dot" style={{ animationDelay: '0.2s' }}>.</span>
        <span className="dot" style={{ animationDelay: '0.4s' }}>.</span>
        <span className="dot" style={{ animationDelay: '0.6s' }}>.</span>
      </p>
    </div>
  );
};

export default DecisionLoader;
