// src/pages/Login.js
import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { login } from '../services/authService';
import '../styles/Auth.css';
import CryptoJS from 'crypto-js';

const Login = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: ''
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
    // Check if user is already logged in
    const userData = localStorage.getItem('userData');
    if (userData) {
      navigate('/dashboard');
    }
    
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
  }, [navigate]);

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    
    // Clear error when user starts typing
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Hash password before sending to server
      const loginData = {
        username: formData.username,
        password: CryptoJS.SHA256(formData.password).toString()
      };
      
      const userData = await login(loginData);
      
      // Store user data in localStorage
      localStorage.setItem('userData', JSON.stringify({
        name: userData.Name,
        username: userData.Username,
        conversation: userData.Conversation || []
      }));
      
      setLoading(false);
      setSuccess(true);
      
      // Navigate directly to dashboard after successful login with a short delay
      setTimeout(() => {
        navigate('/dashboard');
      }, 1200);
    } catch (err) {
      setLoading(false);
      setError('Invalid username or password');
    }
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
              <h2>Find the perfect professional for your needs</h2>
              <p>Connect with experts in various fields and get your projects done right.</p>
            </motion.div>
            
            <motion.div 
              className="feature-list"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.5 }}
            >
              <div className="feature-item">
                <div className="feature-icon">✓</div>
                <span>Verified professionals</span>
              </div>
              <div className="feature-item">
                <div className="feature-icon">✓</div>
                <span>Secure messaging</span>
              </div>
              <div className="feature-item">
                <div className="feature-icon">✓</div>
                <span>Custom matching algorithm</span>
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
                <h3>Login Successful!</h3>
                <p>Redirecting you to dashboard...</p>
                <motion.div 
                  className="success-loader"
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 1.2, ease: "easeInOut" }}
                ></motion.div>
              </motion.div>
            ) : (
              <>
                <motion.div className="auth-header" variants={itemVariants}>
                  <h2>Welcome Back</h2>
                  <p>Log in to your account to continue</p>
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
                    <label>Username</label>
                    <div className="input-container">
                      <motion.input
                        type="text"
                        name="username"
                        value={formData.username}
                        onChange={handleChange}
                        placeholder="       Enter your username"
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
                    <label>Password</label>
                    <div className="input-container">
                      <motion.input
                        type="password"
                        name="password"
                        value={formData.password}
                        onChange={handleChange}
                        placeholder="      Enter your password"
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
                  </motion.div>
                  
                  <motion.div className="form-options" variants={itemVariants}>
                    <div className="remember-me">
                      <input type="checkbox" id="remember" />
                      <label htmlFor="remember">Remember me</label>
                    </div>
      
                  </motion.div>
                  
                  <motion.button 
                    type="submit" 
                    className="auth-button" 
                    disabled={loading}
                    variants={itemVariants}
                    whileHover={{ scale: 1.02, boxShadow: "0 4px 12px rgba(59, 130, 246, 0.25)" }}
                    whileTap={{ scale: 0.98 }}
                  >
                    {loading ? (
                      <div className="loading-content">
                        <div className="loading-spinner"></div>
                        <span>Logging in...</span>
                      </div>
                    ) : 'Log in'}
                  </motion.button>
                </motion.form>
                
                <motion.div className="auth-divider" variants={itemVariants}>
                  <span>OR</span>
                </motion.div>
                
             
                
                <motion.p 
                  className="auth-redirect"
                  variants={itemVariants}
                >
                  Don't have an account? <Link to="/signup">Sign Up</Link>
                </motion.p>
              </>
            )}
          </AnimatePresence>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default Login;