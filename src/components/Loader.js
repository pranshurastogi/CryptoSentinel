import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Messages to cycle through while loading.
const messages = [
  "Searching data...",
  "Our agents are at work...",
  "Analyzing market trends...",
  "Gathering intelligence..."
];

const Loader = () => {
  const [messageIndex, setMessageIndex] = useState(0);

  // Cycle messages every 3 seconds.
  useEffect(() => {
    const interval = setInterval(() => {
      setMessageIndex((prevIndex) => (prevIndex + 1) % messages.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="loader-container">
      <div className="spinner"></div>
      <AnimatePresence mode="wait">
        <motion.p
          key={messages[messageIndex]}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.4 }}
          className="loader-message"
        >
          {messages[messageIndex]}
        </motion.p>
      </AnimatePresence>
    </div>
  );
};

export default Loader;
