// src/pages/Dashboard.js
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Header from '../components/Header';
import Footer from '../components/Footer';
import { classifyQuery } from '../services/queryService';
import '../styles/Dashboard.css';

const Dashboard = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [userLocation, setUserLocation] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [inputFocus, setInputFocus] = useState(false);
  const [characterCount, setCharacterCount] = useState(0);
  const [showHelpPanel, setShowHelpPanel] = useState(false);
  const [activeTheme, setActiveTheme] = useState('blue'); // 'blue', 'purple', 'green'
  const [showThemeSelector, setShowThemeSelector] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const textareaRef = useRef(null);
  const navigate = useNavigate();

  const exampleQueries = [
    "I need a lawyer who specializes in copyright law",
    "Looking for a cardiologist with experience in heart valve surgery",
    "Need a web developer who can build an e-commerce site with React",
    "Seeking a marketing specialist for my new restaurant business"
  ];
  
  const themes = {
    blue: {
      primary: '#3b82f6',
      secondary: '#6366f1',
      accent: '#60a5fa',
      gradient: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
      bgGradient: 'linear-gradient(135deg, rgba(59, 130, 246, 0.12) 0%, rgba(147, 51, 234, 0.12) 100%)'
    },
    purple: {
      primary: '#8b5cf6',
      secondary: '#ec4899',
      accent: '#a78bfa',
      gradient: 'linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%)',
      bgGradient: 'linear-gradient(135deg, rgba(139, 92, 246, 0.12) 0%, rgba(236, 72, 153, 0.12) 100%)'
    },
    green: {
      primary: '#10b981',
      secondary: '#3b82f6',
      accent: '#34d399',
      gradient: 'linear-gradient(135deg, #10b981 0%, #3b82f6 100%)',
      bgGradient: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(59, 130, 246, 0.12) 100%)'
    }
  };

  const currentTheme = themes[activeTheme];

  // Quick questions for the help panel
  const quickQuestions = [
    "How does professional matching work?",
    "What information should I include in my query?",
    "How quickly will I be connected with professionals?",
    "What if none of the professionals are a good match?",
    "Can I request specific qualifications?"
  ];

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { duration: 0.6, when: "beforeChildren", staggerChildren: 0.15 }
    }
  };
  
  const itemVariants = {
    hidden: { y: 30, opacity: 0 },
    visible: { 
      y: 0, 
      opacity: 1, 
      transition: { 
        type: "spring", 
        stiffness: 300, 
        damping: 24 
      } 
    }
  };

  const cardVariants = {
    hidden: { scale: 0.96, opacity: 0 },
    visible: { 
      scale: 1, 
      opacity: 1, 
      transition: { 
        type: "spring", 
        stiffness: 400, 
        damping: 25 
      } 
    },
    hover: { 
      scale: 1.02, 
      boxShadow: "0 10px 30px rgba(0, 0, 0, 0.15)",
      y: -5,
      transition: {
        type: "spring",
        stiffness: 400,
        damping: 15
      }
    }
  };

  const suggestionsVariants = {
    hidden: { opacity: 0, y: 10, height: 0 },
    visible: { 
      opacity: 1, 
      y: 0, 
      height: 'auto',
      transition: { 
        duration: 0.3, 
        ease: "easeOut" 
      } 
    },
    exit: { 
      opacity: 0, 
      y: -10, 
      height: 0,
      transition: { 
        duration: 0.2, 
        ease: "easeIn" 
      } 
    }
  };
  
  const helpPanelVariants = {
    closed: { 
      x: '100%',
      boxShadow: "0 0 0 rgba(0, 0, 0, 0)" 
    },
    open: { 
      x: 0,
      boxShadow: "-5px 0 25px rgba(0, 0, 0, 0.1)" 
    }
  };
  
  const tabVariants = {
    rest: { scale: 1 },
    hover: { scale: 1.05 },
    tap: { scale: 0.95 }
  };

  const loadingOverlayVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1, 
      transition: { duration: 0.3 }
    },
    exit: { 
      opacity: 0, 
      transition: { duration: 0.3, delay: 0.2 }
    }
  };

  // Background particles config
  const particlesConfig = {
    count: 50,
    size: { min: 2, max: 8 },
    speed: { min: 0.5, max: 1.5 },
    colors: ['#E0F2FE', '#BFDBFE', '#93C5FD', '#60A5FA']
  };

  useEffect(() => {
    // Load user location from localStorage when component mounts
    const storedLocation = localStorage.getItem('userLocation');
    if (storedLocation) {
      setUserLocation(storedLocation);
    }
    
    // Add subtle background animation
    document.body.classList.add('animated-bg');
    
    // Create background particles
    createParticles();
    
    // Set up mousemove event for spotlight effect
    document.addEventListener('mousemove', handleMouseMove);
    
    return () => {
      document.body.classList.remove('animated-bg');
      // Clean up particles
      const particlesContainer = document.getElementById('particles-container');
      if (particlesContainer) {
        particlesContainer.innerHTML = '';
      }
      document.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

  // Update character count when query changes
  useEffect(() => {
    setCharacterCount(query.length);
  }, [query]);
  
  // Update theme color on theme change
  useEffect(() => {
    document.documentElement.style.setProperty('--primary-color', currentTheme.primary);
    document.documentElement.style.setProperty('--secondary-color', currentTheme.secondary);
    document.documentElement.style.setProperty('--accent-color', currentTheme.accent);
    document.documentElement.style.setProperty('--gradient', currentTheme.gradient);
    document.documentElement.style.setProperty('--bg-gradient', currentTheme.bgGradient);
  }, [activeTheme, currentTheme]);

  // Simulated progress for loading animation
  useEffect(() => {
    let interval;
    if (loading) {
      setLoadingProgress(0);
      interval = setInterval(() => {
        setLoadingProgress(prev => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90; // Hold at 90% until actual completion
          }
          return prev + Math.random() * 15;
        });
      }, 400);
    }
    
    return () => {
      if (interval) clearInterval(interval);
      if (!loading) setLoadingProgress(0);
    };
  }, [loading]);

  const handleMouseMove = (e) => {
    const spotlight = document.getElementById('spotlight');
    if (spotlight) {
      spotlight.style.background = `radial-gradient(circle at ${e.clientX}px ${e.clientY}px, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0) 50%)`;
    }
  };

  const createParticles = () => {
    const container = document.getElementById('particles-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    for (let i = 0; i < particlesConfig.count; i++) {
      const size = Math.random() * (particlesConfig.size.max - particlesConfig.size.min) + particlesConfig.size.min;
      const speed = Math.random() * (particlesConfig.speed.max - particlesConfig.speed.min) + particlesConfig.speed.min;
      const color = particlesConfig.colors[Math.floor(Math.random() * particlesConfig.colors.length)];
      
      const particle = document.createElement('div');
      particle.className = 'particle';
      particle.style.width = `${size}px`;
      particle.style.height = `${size}px`;
      particle.style.backgroundColor = color;
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.top = `${Math.random() * 100}%`;
      particle.style.animationDuration = `${speed * 60}s`;
      particle.style.animationDelay = `${Math.random() * 10}s`;
      particle.style.opacity = `${Math.random() * 0.6 + 0.1}`;
      
      container.appendChild(particle);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a query');
      // Shake the textarea to indicate error
      textareaRef.current.classList.add('shake-animation');
      setTimeout(() => {
        textareaRef.current?.classList.remove('shake-animation');
      }, 600);
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      // Enhance query with location if available
      const enhancedQuery = userLocation ? `${query} in ${userLocation}` : query;
      console.log(`Processing enhanced query: ${enhancedQuery}`);
      
      const response = await classifyQuery(enhancedQuery);
      
      // Set progress to 100% on completion
      setLoadingProgress(100);
      
      // Add a small delay for the animation to complete
      setTimeout(() => {
        navigate('/classification', { 
          state: { 
            classifications: response.data.classifications,
            query: enhancedQuery, // Pass enhanced query to next page
            userLocation // Also pass the location separately
          }
        });
      }, 500);
    } 
    catch (err) {
      setError('Error processing query: ' + (err.response?.data?.message || err.message));
      // Visual feedback for error
      const formElement = document.querySelector('.query-form');
      formElement.classList.add('error-shake');
      setTimeout(() => {
        formElement.classList.remove('error-shake');
      }, 500);
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setQuery(suggestion);
    setShowSuggestions(false);
    // Focus the textarea
    textareaRef.current.focus();
  };

  const handleFocus = () => {
    setInputFocus(true);
    // Show suggestions after a short delay
    setTimeout(() => setShowSuggestions(true), 300);
  };

  const handleBlur = () => {
    setInputFocus(false);
    // Hide suggestions after a short delay (allows for clicking on suggestions)
    setTimeout(() => setShowSuggestions(false), 200);
  };
  
  const handleHelpQuestionClick = (question) => {
    // Add the question to the textarea
    setQuery(question);
    setShowHelpPanel(false);
    // Focus the textarea
    textareaRef.current.focus();
  };
  
  const toggleThemeSelector = () => {
    setShowThemeSelector(!showThemeSelector);
  };
  
  const changeTheme = (theme) => {
    setActiveTheme(theme);
    setShowThemeSelector(false);
  };

  return (
    <motion.div 
      className={`dashboard-page theme-${activeTheme}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <div id="particles-container" className="particles-background"></div>
      <div id="spotlight" className="spotlight-effect"></div>
      
      <div className="page-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
      </div>
      
      <Header />
      
      <motion.main className="dashboard-container">
        <motion.div 
          className="dashboard-content"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Theme selector */}
          <motion.div className="theme-selector-container">
            <motion.button 
              className="theme-toggle-button"
              onClick={toggleThemeSelector}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              style={{ background: currentTheme.gradient }}
            >
              <span className="theme-icon">🎨</span>
            </motion.button>
            
            <AnimatePresence>
              {showThemeSelector && (
                <motion.div 
                  className="theme-options"
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.9 }}
                >
                  <motion.div 
                    className={`theme-option ${activeTheme === 'blue' ? 'active' : ''}`}
                    style={{ background: themes.blue.gradient }}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => changeTheme('blue')}
                  >
                    <motion.div className="theme-check" animate={{ opacity: activeTheme === 'blue' ? 1 : 0 }}>✓</motion.div>
                  </motion.div>
                  
                  <motion.div 
                    className={`theme-option ${activeTheme === 'purple' ? 'active' : ''}`}
                    style={{ background: themes.purple.gradient }}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => changeTheme('purple')}
                  >
                    <motion.div className="theme-check" animate={{ opacity: activeTheme === 'purple' ? 1 : 0 }}>✓</motion.div>
                  </motion.div>
                  
                  <motion.div 
                    className={`theme-option ${activeTheme === 'green' ? 'active' : ''}`}
                    style={{ background: themes.green.gradient }}
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => changeTheme('green')}
                  >
                    <motion.div className="theme-check" animate={{ opacity: activeTheme === 'green' ? 1 : 0 }}>✓</motion.div>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
          
          <motion.div className="dashboard-header" variants={itemVariants}>
            <h2>Find the perfect professional for your needs</h2>
            <div className="underline-decoration"></div>
            <p>Describe your project or requirements, and we'll match you with the best experts.</p>
          </motion.div>
          
          <motion.div 
            className="dashboard-card"
            variants={cardVariants}
          >
            {userLocation && (
              <motion.div 
                className="location-indicator"
                variants={itemVariants}
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
              >
                <span className="location-icon">📍</span>
                <span className="location-text">Your location: <strong>{userLocation}</strong></span>
                <motion.button 
                  className="change-location-btn"
                  onClick={() => navigate('/location')}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  Change
                </motion.button>
              </motion.div>
            )}
            
            <AnimatePresence>
              {error && (
                <motion.div 
                  className="error-message"
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <span className="error-icon">⚠️</span>
                  {error}
                </motion.div>
              )}
            </AnimatePresence>
            
            <motion.form 
              onSubmit={handleSubmit} 
              className="query-form"
              variants={itemVariants}
            >
              <div className="textarea-container">
                <motion.textarea
                  ref={textareaRef}
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="E.g., I need a doctor who specializes in pediatric neurology..."
                  rows={5}
                  required
                  onFocus={handleFocus}
                  onBlur={handleBlur}
                  variants={itemVariants}
                  animate={inputFocus ? { boxShadow: `0 0 0 3px ${currentTheme.primary}40` } : {}}
                />
                
                <div className="textarea-footer">
                  <div className="character-counter">
                    <motion.span 
                      animate={{ 
                        color: characterCount > 300 ? currentTheme.primary : 
                               characterCount > 0 ? '#6B7280' : '#D1D5DB' 
                      }}
                    >
                      {characterCount} characters
                    </motion.span>
                  </div>
                  
                  <div className="textarea-hint">
                    Be specific about what you need
                  </div>
                </div>
                
                <AnimatePresence>
                  {showSuggestions && (
                    <motion.div 
                      className="query-suggestions"
                      variants={suggestionsVariants}
                      initial="hidden"
                      animate="visible"
                      exit="exit"
                    >
                      <div className="suggestions-title">Examples:</div>
                      <div className="suggestions-list">
                        {exampleQueries.map((suggestion, index) => (
                          <motion.div 
                            key={index}
                            className="suggestion-item"
                            whileHover={{ backgroundColor: `${currentTheme.primary}15` }}
                            onClick={() => handleSuggestionClick(suggestion)}
                            initial={{ opacity: 0, x: -5 }}
                            animate={{ 
                              opacity: 1, 
                              x: 0,
                              transition: { delay: index * 0.1 }
                            }}
                          >
                            <span className="suggestion-icon">💡</span>
                            <span className="suggestion-text">{suggestion}</span>
                          </motion.div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
              
              <motion.button 
                type="submit" 
                disabled={loading}
                className="submit-button"
                variants={itemVariants}
                whileHover={!loading ? { scale: 1.03, boxShadow: `0 15px 30px ${currentTheme.primary}40` } : {}}
                whileTap={!loading ? { scale: 0.97 } : {}}
                style={{ background: currentTheme.gradient }}
              >
                {loading ? (
                  <div className="loading-content">
                    <span className="loading-spinner"></span>
                    <span>Finding the best match...</span>
                  </div>
                ) : (
                  <>
                    <span>Find Professionals</span>
                    <motion.span 
                      className="button-arrow"
                      animate={{ x: [0, 5, 0] }}
                      transition={{ 
                        duration: 1.5, 
                        repeat: Infinity, 
                        repeatType: "loop" 
                      }}
                    >
                      →
                    </motion.span>
                  </>
                )}
              </motion.button>
            </motion.form>
          </motion.div>
          
          <motion.div 
            className="additional-info"
            variants={itemVariants}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <motion.div 
              className="info-item"
              whileHover={{ 
                y: -5, 
                boxShadow: "0 10px 25px rgba(0, 0, 0, 0.08)"
              }}
            >
              <div className="info-icon" style={{ backgroundColor: `${currentTheme.primary}15`, color: currentTheme.primary }}>🔍</div>
              <div className="info-text">
                <h3>Precise Matching</h3>
                <p>Our AI analyzes your query to match you with the perfect specialist</p>
              </div>
            </motion.div>
            
            <motion.div 
              className="info-item"
              whileHover={{ 
                y: -5, 
                boxShadow: "0 10px 25px rgba(0, 0, 0, 0.08)"
              }}
            >
              <div className="info-icon" style={{ backgroundColor: `${currentTheme.primary}15`, color: currentTheme.primary }}>⚡</div>
              <div className="info-text">
                <h3>Fast Results</h3>
                <p>Get connected with qualified professionals within minutes</p>
              </div>
            </motion.div>
            
            <motion.div 
              className="info-item"
              whileHover={{ 
                y: -5, 
                boxShadow: "0 10px 25px rgba(0, 0, 0, 0.08)"
              }}
            >
              <div className="info-icon" style={{ backgroundColor: `${currentTheme.primary}15`, color: currentTheme.primary }}>🔒</div>
              <div className="info-text">
                <h3>Secure Process</h3>
                <p>Your information is protected and only shared with matched professionals</p>
              </div>
            </motion.div>
          </motion.div>
        </motion.div>
      </motion.main>
      
      {/* Fixed Help Tab */}
      <motion.div className="fixed-help-tab-container">
        <motion.div 
          className="help-tab"
          onClick={() => setShowHelpPanel(!showHelpPanel)}
          variants={tabVariants}
          initial="rest"
          whileHover="hover"
          whileTap="tap"
          style={{ background: currentTheme.gradient }}
        >
          <span className="tab-icon">{showHelpPanel ? '✕' : '?'}</span>
          <span className="tab-text">Ask Additional Questions</span>
        </motion.div>
        
        <motion.div 
          className="help-panel"
          variants={helpPanelVariants}
          initial="closed"
          animate={showHelpPanel ? "open" : "closed"}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        >
          <div className="help-panel-header">
            <h3>Common Questions</h3>
            <motion.button 
              className="close-panel-button"
              onClick={() => setShowHelpPanel(false)}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              ✕
            </motion.button>
          </div>
          
          <div className="help-panel-content">
            <p className="help-description">
              Click on any question below to add it to your query:
            </p>
            
            <div className="quick-questions-list">
              {quickQuestions.map((question, index) => (
                <motion.div 
                  key={index}
                  className="quick-question-item"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ 
                    opacity: 1, 
                    x: 0,
                    transition: { delay: index * 0.1 }
                  }}
                  whileHover={{ 
                    backgroundColor: `${currentTheme.primary}15`,
                    x: 5
                  }}
                  onClick={() => handleHelpQuestionClick(question)}
                >
                  <span className="question-icon">❓</span>
                  <span className="question-text">{question}</span>
                </motion.div>
              ))}
            </div>
            
            <div className="help-contact">
              <p>Can't find what you're looking for?</p>
              <motion.button 
                className="contact-support-button"
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                style={{ background: currentTheme.gradient }}
              >
                Contact Support
              </motion.button>
            </div>
          </div>
        </motion.div>
      </motion.div>
      
      {/* Beautiful full-screen loading overlay */}
      <AnimatePresence>
        {loading && (
          <motion.div 
            className="loading-overlay"
            variants={loadingOverlayVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
          >
            <div className="loading-container">
              <div className="loading-content-container">
                <motion.div 
                  className="loading-pulse"
                  animate={{
                    scale: [1, 1.1, 1],
                    opacity: [0.7, 1, 0.7]
                  }}
                  transition={{
                    duration: 2,
                    repeat: Infinity,
                    ease: "easeInOut"
                  }}
                  style={{ 
                    background: currentTheme.gradient 
                  }}
                ></motion.div>
                
                <div className="loading-text-container">
                  <h3>Finding the Perfect Match</h3>
                  <p className="loading-description">We're analyzing your requirements to connect you with the best professionals.</p>
                  
                  <div className="progress-bar-container">
                    <div 
                      className="progress-bar-fill" 
                      style={{ 
                        width: `${loadingProgress}%`,
                        background: currentTheme.gradient
                      }}
                    ></div>
                  </div>
                  
                  <div className="loading-steps">
                    <div className={`loading-step ${loadingProgress >= 20 ? 'active' : ''}`}>
                      <div className="step-number" style={{ borderColor: currentTheme.primary }}>1</div>
                      <div className="step-text">Analyzing query</div>
                    </div>
                    <div className={`loading-step ${loadingProgress >= 40 ? 'active' : ''}`}>
                      <div className="step-number" style={{ borderColor: currentTheme.primary }}>2</div>
                      <div className="step-text">Matching categories</div>
                    </div>
                    <div className={`loading-step ${loadingProgress >= 60 ? 'active' : ''}`}>
                      <div className="step-number" style={{ borderColor: currentTheme.primary }}>3</div>
                      <div className="step-text">Finding professionals</div>
                    </div>
                    <div className={`loading-step ${loadingProgress >= 80 ? 'active' : ''}`}>
                      <div className="step-number" style={{ borderColor: currentTheme.primary }}>4</div>
                      <div className="step-text">Ranking results</div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="loading-animation">
                <div className="loading-orbit">
                  <div className="loading-planet" style={{ background: currentTheme.gradient }}></div>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <Footer />
    </motion.div>
  );
};

export default Dashboard;