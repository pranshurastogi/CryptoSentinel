import React, { useState } from 'react';
import { motion } from 'framer-motion';

function TokenInput({ onSubmit }) {
  const [address, setAddress] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (address.trim()) {
      onSubmit(address.trim());
    }
  };

  return (
    <motion.form
      className="token-input-form"
      onSubmit={handleSubmit}
      initial={{ y: -50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <label htmlFor="tokenAddress">Enter Token Contract Address:</label>
      <input
        type="text"
        id="tokenAddress"
        value={address}
        onChange={(e) => setAddress(e.target.value)}
        placeholder="0x..."
      />
      <button type="submit">Analyze</button>
    </motion.form>
  );
}

export default TokenInput;
