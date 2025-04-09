// src/components/Footer.js (updated with animations)
import React from 'react';
import { motion } from 'framer-motion';
import '../styles/Footer.css';

const Footer = () => {
  return (
    <motion.footer 
      className="footer"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5, delay: 0.5 }}
    >
      <div className="footer-content">
        <p>&copy; {new Date().getFullYear()} Skill Seeker. All rights reserved.</p>
        <div className="footer-links">
          <motion.a 
            href="#" 
            whileHover={{ scale: 1.1, color: "#3b82f6" }}
          >
            Privacy Policy
          </motion.a>
          <motion.a 
            href="#" 
            whileHover={{ scale: 1.1, color: "#3b82f6" }}
          >
            Terms of Service
          </motion.a>
          <motion.a 
            href="#" 
            whileHover={{ scale: 1.1, color: "#3b82f6" }}
          >
            Contact Us
          </motion.a>
        </div>
      </div>
    </motion.footer>
  );
};

export default Footer;