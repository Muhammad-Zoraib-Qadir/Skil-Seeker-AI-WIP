// src/pages/SignUp.js
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { signup } from '../services/authService';
import '../styles/Auth.css';
import CryptoJS from 'crypto-js';

const SignUp = () => {
  const [formData, setFormData] = useState({
    name: '',
    username: '',
    password: '',
    confirmPassword: ''
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { duration: 0.5, when: "beforeChildren", staggerChildren: 0.2 }
    }
  };
  
  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1, transition: { duration: 0.4 } }
  };

  const successVariants = {
    hidden: { scale: 0.8, opacity: 0 },
    visible: { 
      scale: 1, 
      opacity: 1,
      transition: { 
        type: "spring",
        stiffness: 200,
        damping: 10
      }
    }
  };
  
  const backgroundVariants = {
    initial: { 
      backgroundPosition: '0% 0%',
    },
    animate: { 
      backgroundPosition: '100% 100%',
      transition: { 
        duration: 25,
        ease: "linear",
        repeat: Infinity,
        repeatType: "mirror"
      }
    }
  };

  useEffect(() => {    
    // Add floating elements animation
    const createFloatingElements = () => {
      const container = document.querySelector('.auth-sidebar');
      if (!container) return;
      
      for (let i = 0; i < 15; i++) {
        const element = document.createElement('div');
        element.className = 'floating-element';
        
        // Random size between 10px and 30px
        const size = Math.random() * 20 + 10;
        element.style.width = `${size}px`;
        element.style.height = `${size}px`;
        
        // Random position
        element.style.left = `${Math.random() * 100}%`;
        element.style.top = `${Math.random() * 100}%`;
        
        // Random opacity
        element.style.opacity = (Math.random() * 0.5 + 0.1).toString();
        
        // Random animation duration between 20s and 40s
        const duration = Math.random() * 20 + 20;
        element.style.animationDuration = `${duration}s`;
        
        // Random animation delay
        element.style.animationDelay = `${Math.random() * 5}s`;
        
        container.appendChild(element);
      }
    };
    
    createFloatingElements();
    
    return () => {
      const elements = document.querySelectorAll('.floating-element');
      elements.forEach(el => el.remove());
    };
  }, []);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    
    // Clear error when user starts typing
    if (error) setError('');
  };

  const validateForm = () => {
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return false;
    }
    
    if (formData.password.length < 6) {
      setError('Password must be at least 6 characters long');
      return false;
    }
    
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    
    try {
      // Hash password before sending to server
      const hashedData = {
        name: formData.name,
        username: formData.username,
        password: CryptoJS.SHA256(formData.password).toString()
      };
      
      await signup(hashedData);
      
      setLoading(false);
      setSuccess(true);
      
      // Navigate with a slight delay to allow animation to complete
      setTimeout(() => {
        navigate('/login');
      }, 1500);
    } catch (err) {
      setLoading(false);
      setError(err.response?.data?.message || 'Username already exists');
    }
  };

  const validatePasswordMatch = () => {
    if (formData.confirmPassword && formData.password !== formData.confirmPassword) {
      return false;
    }
    return true;
  };

  return (
    <div className="auth-page-container">
      <motion.div 
        className="auth-background"
        variants={backgroundVariants}
        initial="initial"
        animate="animate"
      ></motion.div>
      
      <motion.div 
        className="auth-container"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <motion.div 
          className="auth-sidebar"
          initial={{ x: -50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          <div className="sidebar-content">
            <motion.div
              className="logo-container"
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              <div className="logo-icon">
                <svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 5C13.925 5 9 9.925 9 16V24C9 30.075 13.925 35 20 35C26.075 35 31 30.075 31 24V16C31 9.925 26.075 5 20 5ZM28 24C28 28.4 24.4 32 20 32C15.6 32 12 28.4 12 24V16C12 11.6 15.6 8 20 8C24.4 8 28 11.6 28 16V24Z" fill="white"/>
                  <path d="M20 12C17.8 12 16 13.8 16 16V24C16 26.2 17.8 28 20 28C22.2 28 24 26.2 24 24V16C24 13.8 22.2 12 20 12ZM21 24C21 24.55 20.55 25 20 25C19.45 25 19 24.55 19 24V16C19 15.45 19.45 15 20 15C20.55 15 21 15.45 21 16V24Z" fill="white"/>
                </svg>
              </div>
              <h1>Skill Seeker</h1>
            </motion.div>
            
            <motion.div 
              className="sidebar-text"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.5 }}
            >
              <h2>Join our community of professionals</h2>
              <p>Create an account to connect with experts and get your projects done right.</p>
            </motion.div>
            
            <motion.div 
              className="feature-list"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.5 }}
            >
              <div className="feature-item">
                <div className="feature-icon">✓</div>
                <span>Free account creation</span>
              </div>
              <div className="feature-item">
                <div className="feature-icon">✓</div>
                <span>Access to top professionals</span>
              </div>
              <div className="feature-item">
                <div className="feature-icon">✓</div>
                <span>Secure and private</span>
              </div>
            </motion.div>
          </div>
        </motion.div>
        
        <motion.div 
          className="auth-form-container"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <AnimatePresence>
            {success ? (
              <motion.div 
                className="success-message"
                variants={successVariants}
                initial="hidden"
                animate="visible"
              >
                <div className="success-icon">✓</div>
                <h3>Account Created!</h3>
                <p>Your account has been created successfully. Redirecting to login...</p>
                <motion.div 
                  className="success-loader"
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 1.5, ease: "easeInOut" }}
                ></motion.div>
              </motion.div>
            ) : (
              <>
                <motion.div className="auth-header" variants={itemVariants}>
                  <h2>Create Your Account</h2>
                  <p>Fill in your details to get started</p>
                </motion.div>
                
                <AnimatePresence>
                  {error && (
                    <motion.div 
                      className="error-container"
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                    >
                      <p className="error-message">{error}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
                
                <motion.form 
                  onSubmit={handleSubmit}
                  variants={containerVariants}
                  className={error ? 'shake-animation' : ''}
                >
                  <motion.div className="form-group" variants={itemVariants}>
                    <label>Full Name</label>
                    <div className="input-container">
                      <motion.input
                        type="text"
                        name="name"
                        value={formData.name}
                        onChange={handleChange}
                        placeholder="         Enter your full name"
                        required
                        whileFocus={{ boxShadow: "0 0 0 2px rgba(59, 130, 246, 0.5)" }}
                      />
                      <div className="input-icon">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M10 10C12.2091 10 14 8.20914 14 6C14 3.79086 12.2091 2 10 2C7.79086 2 6 3.79086 6 6C6 8.20914 7.79086 10 10 10Z" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M16 18C16 15.7909 13.3137 14 10 14C6.68629 14 4 15.7909 4 18" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                    </div>
                  </motion.div>
                  
                  <motion.div className="form-group" variants={itemVariants}>
                    <label>Username</label>
                    <div className="input-container">
                      <motion.input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        placeholder="      Choose a username"
                        required
                        whileFocus={{ boxShadow: "0 0 0 2px rgba(59, 130, 246, 0.5)" }}
                      />
                      <div className="input-icon">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M3.8 6.8C3.8 5.11984 3.8 4.27976 4.14142 3.63803C4.44427 3.07354 4.9269 2.6048 5.50693 2.31142C6.16349 1.98 7.02254 1.98 8.74064 1.98H11.2594C12.9775 1.98 13.8365 1.98 14.4931 2.31142C15.0731 2.6048 15.5557 3.07354 15.8586 3.63803C16.2 4.27976 16.2 5.11984 16.2 6.8V13.2C16.2 14.8802 16.2 15.7202 15.8586 16.362C15.5557 16.9265 15.0731 17.3952 14.4931 17.6886C13.8365 18 12.9775 18 11.2594 18H8.74064C7.02254 18 6.16349 18 5.50693 17.6886C4.9269 17.3952 4.44427 16.9265 4.14142 16.362C3.8 15.7202 3.8 14.8802 3.8 13.2V6.8Z" stroke="#6B7280" strokeWidth="1.5"/>
                          <path d="M10 14V14.01" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round"/>
                        </svg>
                      </div>
                    </div>
                  </motion.div>
                  
                  <motion.div className="form-group" variants={itemVariants}>
                    <label>Password</label>
                    <div className="input-container">
                      <motion.input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        placeholder="      Create a strong password"
                        required
                        whileFocus={{ boxShadow: "0 0 0 2px rgba(59, 130, 246, 0.5)" }}
                      />
                      <div className="input-icon">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M15 7H5C3.89543 7 3 7.89543 3 9V15C3 16.1046 3.89543 17 5 17H15C16.1046 17 17 16.1046 17 15V9C17 7.89543 16.1046 7 15 7Z" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M10 14C10.5523 14 11 13.5523 11 13C11 12.4477 10.5523 12 10 12C9.44772 12 9 12.4477 9 13C9 13.5523 9.44772 14 10 14Z" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M7 7V5C7 3.89543 7.89543 3 9 3H11C12.1046 3 13 3.89543 13 5V7" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                    </div>
                    <span className="input-hint">Must be at least 6 characters</span>
                  </motion.div>
                  
                  <motion.div className="form-group" variants={itemVariants}>
                    <label>Confirm Password</label>
                    <div className="input-container">
                      <motion.input
                        type="password"
                        name="confirmPassword"
                        value={formData.confirmPassword}
                        onChange={handleChange}
                        placeholder="     Re-enter your password"
                        required
                        className={formData.confirmPassword && !validatePasswordMatch() ? 'error-input' : ''}
                        whileFocus={{ boxShadow: "0 0 0 2px rgba(59, 130, 246, 0.5)" }}
                      />
                      <div className="input-icon">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M15 7H5C3.89543 7 3 7.89543 3 9V15C3 16.1046 3.89543 17 5 17H15C16.1046 17 17 16.1046 17 15V9C17 7.89543 16.1046 7 15 7Z" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M10 14C10.5523 14 11 13.5523 11 13C11 12.4477 10.5523 12 10 12C9.44772 12 9 12.4477 9 13C9 13.5523 9.44772 14 10 14Z" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M7 7V5C7 3.89543 7.89543 3 9 3H11C12.1046 3 13 3.89543 13 5V7" stroke="#6B7280" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                      {formData.confirmPassword && !validatePasswordMatch() && (
                        <div className="error-icon">
                          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
                            <path d="M10 18C14.4183 18 18 14.4183 18 10C18 5.58172 14.4183 2 10 2C5.58172 2 2 5.58172 2 10C2 14.4183 5.58172 18 10 18Z" stroke="#EF4444" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                            <path d="M10 6V10" stroke="#EF4444" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                            <path d="M10 14H10.01" stroke="#EF4444" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                        </div>
                      )}
                    </div>
                    {formData.confirmPassword && !validatePasswordMatch() && (
                      <span className="input-error">Passwords do not match</span>
                    )}
                  </motion.div>
                  
                  <motion.div className="terms-agreement" variants={itemVariants}>
                    <input type="checkbox" id="terms" required />
                    <label htmlFor="terms">
                      I agree to the <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>
                    </label>
                  </motion.div>
                  
                  <motion.button 
                    type="submit" 
                    className="auth-button" 
                    disabled={loading || (formData.confirmPassword && !validatePasswordMatch())}
                    variants={itemVariants}
                    whileHover={{ scale: 1.02, boxShadow: "0 4px 12px rgba(59, 130, 246, 0.25)" }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {loading ? (
                      <div className="loading-content">
                        <div className="loading-spinner"></div>
                        <span>Creating account...</span>
                      </div>
                    ) : 'Create Account'}
                  </motion.button>
                </motion.form>
                
                <motion.p 
                  className="auth-redirect"
                  variants={itemVariants}
                >
                  Already have an account? <Link to="/login">Log in</Link>
                </motion.p>
              </>
            )}
          </AnimatePresence>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default SignUp;