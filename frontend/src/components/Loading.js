// src/components/Loading.js (updated with animations)
import React from 'react';
import { motion } from 'framer-motion';
import '../styles/Loading.css';

const Loading = ({ message = "Loading..." }) => {
  return (
    <motion.div 
      className="loading-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div 
        className="loading-content"
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="loading-spinner-large"></div>
        <p>{message}</p>
      </motion.div>
    </motion.div>
  );
};

export default Loading;