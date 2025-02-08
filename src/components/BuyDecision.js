import React from 'react';
import { motion } from 'framer-motion';

function BuyDecision({ onDecision }) {
  return (
    <motion.div
      className="buy-decision"
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <button className="buy-yes" onClick={() => onDecision('yes')}>
        Yes
      </button>
      <button className="buy-no" onClick={() => onDecision('no')}>
        No
      </button>
    </motion.div>
  );
}

export default BuyDecision;
