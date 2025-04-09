// src/components/EmailModal.js
import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import emailjs from '@emailjs/browser';
import '../styles/EmailModal.css';

const EmailModal = ({ professional, query, onClose }) => {
  const [email, setEmail] = useState('');
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');
  const formRef = useRef();
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!email || !message) {
      setError('Please fill in all fields');
      return;
    }
    
    setSending(true);
    setError('');
    
    // Prepare template parameters
    const templateParams = {
      to_email: 'i212654@nu.edu.pk',
      user_email: email,
      cc_email: email, // Added this parameter to CC the user
      message: message,
      professional_name: professional?.['Doctor Name'] || professional?.Name || 'Professional',
      query: query || 'General inquiry'
    };
    
    // Send email using EmailJS
    emailjs.send(
      'service_sv72fsb', // replace with your service ID
      'template_v2r51xe', // replace with your template ID
      templateParams,
      'Cb3oxYZ95vaSu6HWA' // replace with your user ID
    )
    .then((response) => {
      console.log('Email sent successfully:', response);
      setSending(false);
      setSent(true);
      
      // Close modal after showing success message
      setTimeout(() => {
        onClose();
      }, 2000);
    })
    .catch((err) => {
      console.error('Failed to send email:', err);
      setSending(false);
      setError('Failed to send email. Please try again later.');
    });
  };
  
  const backdrop = {
    visible: { opacity: 1 },
    hidden: { opacity: 0 }
  };
  
  const modal = {
    hidden: { y: "-100vh", opacity: 0 },
    visible: { 
      y: "0", 
      opacity: 1,
      transition: { delay: 0.2 }
    }
  };
  
  return (
    <AnimatePresence>
      <motion.div 
        className="modal-backdrop"
        variants={backdrop}
        initial="hidden"
        animate="visible"
        exit="hidden"
        onClick={onClose}
      >
        <motion.div 
          className="modal-content"
          variants={modal}
          onClick={(e) => e.stopPropagation()}
        >
          <div className="modal-header">
            <h2>Contact {professional?.['Doctor Name'] || professional?.Name || 'Professional'}</h2>
            <motion.button 
              className="close-button"
              onClick={onClose}
              whileHover={{ scale: 1.1, rotate: 90 }}
              whileTap={{ scale: 0.9 }}
            >
              &times;
            </motion.button>
          </div>
          
          {sent ? (
            <motion.div 
              className="success-message"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              <div className="success-icon">
                <svg viewBox="0 0 24 24">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z" fill="currentColor" />
                </svg>
              </div>
              <p>Your message has been sent successfully!</p>
              <p className="small-text">A copy has been sent to your email.</p>
            </motion.div>
          ) : (
            <form ref={formRef} onSubmit={handleSubmit}>
              <div className="modal-body">
                <div className="form-group">
                  <label>Your Email</label>
                  <motion.input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    whileFocus={{ boxShadow: "0 0 0 3px rgba(59, 130, 246, 0.2)" }}
                  />
                </div>
                <div className="form-group">
                  <label>Message</label>
                  <motion.textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    placeholder={`Hi, I'm interested in consulting about: "${query}"`}
                    rows={5}
                    whileFocus={{ boxShadow: "0 0 0 3px rgba(59, 130, 246, 0.2)" }}
                  />
                </div>
                
                {error && (
                  <motion.div 
                    className="error-message"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.3 }}
                  >
                    {error}
                  </motion.div>
                )}
              </div>
              
              <div className="modal-footer">
                <motion.button 
                  type="button" 
                  className="cancel-button"
                  onClick={onClose}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  Cancel
                </motion.button>
                <motion.button 
                  type="submit" 
                  className="send-button"
                  disabled={sending}
                  whileHover={{ scale: 1.05, boxShadow: "0 4px 12px rgba(37, 99, 235, 0.25)" }}
                  whileTap={{ scale: 0.95 }}
                >
                  {sending ? (
                    <>
                      <span className="loading-spinner"></span>
                      Sending...
                    </>
                  ) : 'Send Message'}
                </motion.button>
              </div>
            </form>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default EmailModal;