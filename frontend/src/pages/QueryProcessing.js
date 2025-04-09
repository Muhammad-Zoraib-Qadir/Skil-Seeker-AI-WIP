import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Header from '../components/Header';
import Footer from '../components/Footer';
import Loading from '../components/Loading';
import { processQuery, submitAnswers } from '../services/queryService';
import '../styles/QueryProcessing.css';

const QueryProcessing = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { category, query, userLocation } = location.state || {};
  
  const [processId, setProcessId] = useState(null);
  const [currentStep, setCurrentStep] = useState('loading');
  const [synthesis, setSynthesis] = useState('');
  const [followUpQuestions, setFollowUpQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [professionals, setProfessionals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [originalQuery, setOriginalQuery] = useState('');
  const [activeQuestion, setActiveQuestion] = useState(0);
  const [progress, setProgress] = useState(0);
  const [showSynthesis, setShowSynthesis] = useState(true);
  
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { 
        duration: 0.6, 
        when: "beforeChildren", 
        staggerChildren: 0.12,
        ease: "easeOut"
      }
    },
    exit: { 
      opacity: 0, 
      y: 20, 
      transition: { 
        duration: 0.5,
        ease: "easeInOut" 
      } 
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
  
  useEffect(() => {
    // Inside useEffect in QueryProcessing.js
    const processUserQuery = async () => {
      setLoading(true);
      try {
        // Clean up query and ensure proper formatting
        let queryText = typeof query === 'string' ? query.trim() : String(query || '').trim();
        
        // Store the original query for display purposes
        setOriginalQuery(queryText);
        
        console.log(location);
        // Get stored location from localStorage if not provided in state
        let userLocationValue = userLocation;
        if (!userLocationValue) {
          userLocationValue = localStorage.getItem('userLocation');
        }
        
        // If location is available, ensure it's in the correct format
        if (userLocationValue) {
          // First remove any location information that might already be in the query
          // Both "in [location]" or "and my location is in [location]" patterns
          queryText = queryText
            .replace(/\s+in\s+([A-Za-z\s]+)$/i, '')
            .replace(/\s+and my location is in\s+([A-Za-z\s]+)$/i, '')
            .trim();
          
          // Always format with the expected pattern for API
          const formattedQueryForAPI = `${queryText} and my location is in ${userLocationValue}`;
          
          console.log("Sending query with formatted location:", formattedQueryForAPI);
          
          // Start the process and get initial synthesis and questions
          const response = await processQuery(category, formattedQueryForAPI);
          
          // Rest of the processing logic...
          if (response.data.status === 'questions') {
            setProcessId(response.data.processId);
            setSynthesis(response.data.synthesis);
            
            // Extract questions - ensure it's always an array
            let questions = [];
            
            if (Array.isArray(response.data.questions)) {
              questions = [...response.data.questions];
            } else if (typeof response.data.questions === 'string') {
              try {
                const parsed = JSON.parse(response.data.questions);
                if (Array.isArray(parsed)) {
                  questions = parsed;
                } else {
                  questions = [response.data.questions];
                }
              } catch (e) {
                questions = [response.data.questions];
              }
            } else if (response.data.questions && typeof response.data.questions === 'object') {
              questions = Object.values(response.data.questions);
            }
            
            // Create a separate copy of the array to avoid reference issues
            const questionsCopy = [...questions];
            
            setFollowUpQuestions(questionsCopy);
            setCurrentStep('questions');
            setLoading(false);
          } else {
            setError('Unexpected response format');
            setLoading(false);
          }
        } else {
          // Handle case where location is not available
          console.log("Sending query without location:", queryText);
          
          const response = await processQuery(category, queryText);
          
          // Handle response same as above
          if (response.data.status === 'questions') {
            setProcessId(response.data.processId);
            setSynthesis(response.data.synthesis);
            
            let questions = [];
            
            if (Array.isArray(response.data.questions)) {
              questions = [...response.data.questions];
            } else if (typeof response.data.questions === 'string') {
              try {
                const parsed = JSON.parse(response.data.questions);
                if (Array.isArray(parsed)) {
                  questions = parsed;
                } else {
                  questions = [response.data.questions];
                }
              } catch (e) {
                questions = [response.data.questions];
              }
            } else if (response.data.questions && typeof response.data.questions === 'object') {
              questions = Object.values(response.data.questions);
            }
            
            const questionsCopy = [...questions];
            
            setFollowUpQuestions(questionsCopy);
            setCurrentStep('questions');
            setLoading(false);
          } else {
            setError('Unexpected response format');
            setLoading(false);
          }
        }
      } catch (err) {
        console.error('Error processing query:', err);
        setError('Failed to process your query: ' + (err.message || 'Unknown error'));
        setLoading(false);
      }
    };
    
    if (category && query) {
      processUserQuery();
    } else {
      setError('Missing required information. Please go back and try again.');
      setLoading(false);
    }
  }, [category, query, userLocation, location]);
  
  // Effect to update progress based on answered questions
  useEffect(() => {
    if (followUpQuestions.length > 0) {
      const answeredCount = Object.keys(answers).length;
      const percentage = Math.floor((answeredCount / followUpQuestions.length) * 100);
      setProgress(percentage);
    }
  }, [answers, followUpQuestions]);
  
  const handleAnswerChange = (question, answer) => {
    setAnswers({
      ...answers,
      [question]: answer
    });
  };
  
  const handleNextQuestion = () => {
    if (activeQuestion < followUpQuestions.length - 1) {
      setActiveQuestion(activeQuestion + 1);
    }
  };

  const handlePrevQuestion = () => {
    if (activeQuestion > 0) {
      setActiveQuestion(activeQuestion - 1);
    }
  };
  
  const handleSubmitAnswers = async () => {
    if (!processId) {
      setError('No active process found');
      return;
    }
    
    setLoading(true);
    try {
      const response = await submitAnswers(processId, answers);
      
      if (response.data.status === 'results') {
        setProfessionals(response.data.professionals);
        setCurrentStep('results');
        setLoading(false);
      } else {
        setError('Unexpected response format');
        setLoading(false);
      }
    } catch (err) {
      console.error('Error submitting answers:', err);
      setError('Failed to process answers: ' + (err.message || 'Unknown error'));
      setLoading(false);
    }
  };
  
  const handleViewResults = () => {
    // Get the stored location if it wasn't provided in state
    let userLocationValue = userLocation;
    if (!userLocationValue) {
      userLocationValue = localStorage.getItem('userLocation');
    }
    
    // Make sure to include location in the state when navigating to results
    // Pass the original query without the appended location string
    navigate('/results', { 
      state: { 
        professionals, 
        category, 
        query: originalQuery, // Use the original query for display 
        synthesis, 
        followUpQA: answers, 
        userLocation: userLocationValue 
      } 
    });
  };

  // Get appropriate category icon
  const getCategoryIcon = () => {
    if (!category) return '🔍';
    
    const categoryName = category.replace(' Classifier', '').toLowerCase();
    
    switch(categoryName) {
      case 'medical':
        return '⚕️';
      case 'legal':
        return '⚖️';
      case 'cs':
        return '💻';
      case 'seo':
        return '📊';
      default:
        return '🔍';
    }
  };

  // Get appropriate category color
  const getCategoryColor = () => {
    if (!category) return '#4F46E5';
    
    const categoryName = category.replace(' Classifier', '').toLowerCase();
    
    switch(categoryName) {
      case 'medical':
        return '#059669';
      case 'legal':
        return '#7C3AED';
      case 'cs':
        return '#2563EB';
      case 'seo':
        return '#F59E0B';
      default:
        return '#4F46E5';
    }
  };

  const toggleSynthesis = () => {
    setShowSynthesis(!showSynthesis);
  };

  const allQuestionsAnswered = followUpQuestions.length > 0 && 
    Object.keys(answers).length >= followUpQuestions.length &&
    Object.values(answers).every(answer => answer.trim() !== '');
  
  return (
    <motion.div 
      className="query-processing-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <div className="page-background">
        <div className="gradient-orb orb-1"></div>
        <div className="gradient-orb orb-2"></div>
      </div>
      
      <Header />
      
      <motion.main 
        className="processing-container"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
      >
        {error ? (
          <motion.div 
            className="error-container"
            variants={cardVariants}
          >
            <div className="error-icon">⚠️</div>
            <h2>Error</h2>
            <p>{error}</p>
            <motion.button 
              onClick={() => navigate('/dashboard')}
              whileHover={{ 
                scale: 1.05, 
                boxShadow: "0 8px 20px rgba(37, 99, 235, 0.3)" 
              }}
              whileTap={{ scale: 0.95 }}
              className="primary-button"
            >
              Back to Dashboard
            </motion.button>
          </motion.div>
        ) : currentStep === 'loading' ? (
          <Loading message="Analyzing your query..." />
        ) : currentStep === 'questions' ? (
          <motion.div 
            className="questions-section"
            variants={containerVariants}
          >
            <motion.div className="page-header" variants={itemVariants}>
              <motion.div className="category-indicator" style={{ backgroundColor: `${getCategoryColor()}20`, color: getCategoryColor() }}>
                <span className="category-icon">{getCategoryIcon()}</span>
                <span className="category-name">{category?.replace(' Classifier', '')}</span>
              </motion.div>
              
              <motion.h2>Query Analysis</motion.h2>
              
              <motion.div className="progress-container">
                <div className="progress-text">
                  <span>Progress: {progress}%</span>
                  <span>{Object.keys(answers).length} of {followUpQuestions.length} questions answered</span>
                </div>
                <div className="progress-bar-container">
                  <motion.div 
                    className="progress-bar" 
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5 }}
                    style={{ backgroundColor: getCategoryColor() }}
                  ></motion.div>
                </div>
              </motion.div>
            </motion.div>
            
            <motion.div className="query-info-section" variants={itemVariants}>
              <motion.div 
                className="query-synthesis-container"
                animate={{ height: showSynthesis ? 'auto' : '60px' }}
                transition={{ duration: 0.3 }}
              >
                <motion.div 
                  className="synthesis-header"
                  onClick={toggleSynthesis}
                >
                  <h3>Our Understanding</h3>
                  <motion.div 
                    className="toggle-icon"
                    animate={{ rotate: showSynthesis ? 0 : 180 }}
                    transition={{ duration: 0.3 }}
                  >
                    ▲
                  </motion.div>
                </motion.div>
                
                {showSynthesis && (
                  <motion.div 
                    className="synthesis-content"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <p>{synthesis}</p>
                  
                    <div className="query-display">
                      <div className="query-field">
                        <span className="query-label">Your Query:</span>
                        <span className="query-value">{originalQuery}</span>
                      </div>
                      
                      {userLocation && (
                        <div className="query-field">
                          <span className="query-label">Location:</span>
                          <span className="query-value">{userLocation}</span>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </motion.div>
            </motion.div>
            
            <motion.h3 className="questions-title" variants={itemVariants}>
              <span className="highlight-text">We need a few more details</span>
            </motion.h3>
            
            {followUpQuestions.length > 0 ? (
              <motion.div className="questions-container" variants={containerVariants}>
                <div className="questions-cards-wrapper">
                  <AnimatePresence mode="wait">
                    <motion.div 
                      key={`question-${activeQuestion}`}
                      className="question-card"
                      variants={cardVariants}
                      initial="hidden"
                      animate="visible"
                      exit={{ opacity: 0, x: -100 }}
                      transition={{ duration: 0.3 }}
                    >
                      <div className="question-number">
                        <span className="number-badge">{activeQuestion + 1}</span>
                        <span className="total-indicator">of {followUpQuestions.length}</span>
                      </div>
                      
                      <p className="question-text">{followUpQuestions[activeQuestion]}</p>
                      
                      <textarea
                        placeholder="Your answer..."
                        value={answers[followUpQuestions[activeQuestion]] || ''}
                        onChange={(e) => handleAnswerChange(followUpQuestions[activeQuestion], e.target.value)}
                        rows={3}
                        autoFocus
                      />
                      
                      {answers[followUpQuestions[activeQuestion]]?.trim() && (
                        <motion.div 
                          className="answer-indicator"
                          initial={{ opacity: 0, scale: 0.5 }}
                          animate={{ opacity: 1, scale: 1 }}
                          style={{ backgroundColor: getCategoryColor() }}
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                            <path d="M5 12L10 17L19 8" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                          <span>Answered</span>
                        </motion.div>
                      )}
                    </motion.div>
                  </AnimatePresence>
                </div>
                
                <motion.div className="navigation-controls" variants={itemVariants}>
                  <motion.button 
                    onClick={handlePrevQuestion}
                    disabled={activeQuestion === 0}
                    className="nav-button prev-button"
                    whileHover={activeQuestion !== 0 ? { scale: 1.05, x: -3 } : {}}
                    whileTap={activeQuestion !== 0 ? { scale: 0.95 } : {}}
                  >
                    <span className="button-icon">←</span>
                    <span>Previous</span>
                  </motion.button>
                  
                  {activeQuestion < followUpQuestions.length - 1 ? (
                    <motion.button 
                      onClick={handleNextQuestion}
                      disabled={!answers[followUpQuestions[activeQuestion]]?.trim()}
                      className="nav-button next-button"
                      whileHover={answers[followUpQuestions[activeQuestion]]?.trim() ? { scale: 1.05, x: 3 } : {}}
                      whileTap={answers[followUpQuestions[activeQuestion]]?.trim() ? { scale: 0.95 } : {}}
                    >
                      <span>Next</span>
                      <span className="button-icon">→</span>
                    </motion.button>
                  ) : (
                    <motion.button 
                      onClick={handleSubmitAnswers}
                      disabled={!allQuestionsAnswered || loading}
                      className="submit-button"
                      whileHover={allQuestionsAnswered && !loading ? { 
                        scale: 1.05, 
                        boxShadow: "0 10px 25px rgba(37, 99, 235, 0.25)" 
                      } : {}}
                      whileTap={allQuestionsAnswered && !loading ? { scale: 0.95 } : {}}
                      style={{ 
                        backgroundColor: allQuestionsAnswered && !loading ? getCategoryColor() : '#94a3b8' 
                      }}
                    >
                      {loading ? (
                        <div className="loading-content">
                          <span className="spinner"></span>
                          <span>Processing...</span>
                        </div>
                      ) : (
                        <>
                          <span>Find Professionals</span>
                          <span className="button-icon">✓</span>
                        </>
                      )}
                    </motion.button>
                  )}
                </motion.div>
                
                <motion.div className="questions-indicators" variants={itemVariants}>
                  {followUpQuestions.map((_, index) => (
                    <motion.div 
                      key={index}
                      className={`indicator ${index === activeQuestion ? 'active' : ''} ${answers[followUpQuestions[index]]?.trim() ? 'answered' : ''}`}
                      onClick={() => setActiveQuestion(index)}
                      whileHover={{ scale: 1.2 }}
                      whileTap={{ scale: 0.9 }}
                      style={{ 
                        backgroundColor: index === activeQuestion ? getCategoryColor() : 
                                         answers[followUpQuestions[index]]?.trim() ? `${getCategoryColor()}80` : '#cbd5e1'
                      }}
                    />
                  ))}
                </motion.div>
              </motion.div>
            ) : (
              <motion.div className="no-questions" variants={itemVariants}>
                <div className="empty-state-icon">❓</div>
                <p>No questions available. Please try again.</p>
                <motion.button 
                  onClick={() => navigate('/dashboard')}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="primary-button"
                >
                  Back to Dashboard
                </motion.button>
              </motion.div>
            )}
          </motion.div>
        ) : currentStep === 'results' ? (
          <motion.div 
            className="results-found"
            variants={cardVariants}
            initial="hidden"
            animate="visible"
          >
            <div className="results-icon">✅</div>
            <h2>Matching Professionals Found!</h2>
            <p>We've identified the best professionals for your needs based on your query and answers.</p>
            
            <motion.div 
              className="professionals-preview"
              animate={{ 
                y: [0, -10, 0],
                transition: {
                  y: {
                    duration: 2,
                    repeat: Infinity,
                    repeatType: "reverse"
                  }
                }
              }}
            >
              <div className="preview-card-stack">
                {Array(3).fill(0).map((_, index) => (
                  <div 
                    key={index} 
                    className="preview-card"
                    style={{
                      transform: `translateY(${index * -8}px) scale(${1 - index * 0.05})`, 
                      zIndex: 3 - index,
                      opacity: 1 - index * 0.2
                    }}
                  />
                ))}
              </div>
            </motion.div>
            
            <motion.button 
              onClick={handleViewResults} 
              className="view-results-button"
              whileHover={{ 
                scale: 1.05, 
                boxShadow: "0 15px 30px rgba(37, 99, 235, 0.3)" 
              }}
              whileTap={{ scale: 0.95 }}
              style={{ backgroundColor: getCategoryColor() }}
            >
              <span>View Recommended Professionals</span>
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
            </motion.button>
          </motion.div>
        ) : null}
      </motion.main>
      
      <Footer />
      
      {(currentStep === 'loading' || loading) && <Loading message="Processing..." />}
    </motion.div>
  );
};

export default QueryProcessing;