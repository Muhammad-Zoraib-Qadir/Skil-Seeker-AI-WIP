// src/pages/ProfessionalsResults.js (redesigned with enhanced UI)
import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Header from '../components/Header';
import Footer from '../components/Footer';
import ProfessionalCard from '../components/ProfessionalCard';
import SkillsChart from '../components/SkillsChart';
import EmailModal from '../components/EmailModal';
import Loading from '../components/Loading';
import { getConversationalResponse } from '../services/queryService';
import '../styles/ProfessionalsResults.css';

const ProfessionalsResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { professionals, category, query, synthesis, followUpQA } = location.state || {};
  
  const [selectedProfessional, setSelectedProfessional] = useState(null);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [showProfessionalModal, setShowProfessionalModal] = useState(false);
  const [showGraph, setShowGraph] = useState(false);
  const [conversation, setConversation] = useState([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [skillPercentages, setSkillPercentages] = useState({});
  
  const conversationEndRef = useRef(null);
  
  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { duration: 0.5, when: "beforeChildren", staggerChildren: 0.1 }
    }
  };
  
  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1, transition: { duration: 0.4 } }
  };
  
  const listItemVariants = {
    hidden: { x: -20, opacity: 0 },
    visible: custom => ({
      x: 0, 
      opacity: 1, 
      transition: { 
        delay: custom * 0.1,
        duration: 0.4 
      }
    })
  };

  const modalVariants = {
    hidden: { opacity: 0, scale: 0.8 },
    visible: { 
      opacity: 1, 
      scale: 1,
      transition: { 
        type: "spring", 
        stiffness: 400, 
        damping: 25 
      } 
    },
    exit: { 
      opacity: 0, 
      scale: 0.8,
      transition: { 
        duration: 0.2 
      } 
    }
  };
  
  useEffect(() => {
    // Scroll to bottom of conversation whenever it updates
    if (conversationEndRef.current) {
      conversationEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [conversation]);
  
  useEffect(() => {
    // Log what we received for debugging
    console.log("Location state:", location.state);
    console.log("Professionals received:", professionals);
    
    // Check if professionals is empty or undefined
    if (!professionals || professionals.length === 0) {
      setError("No professionals data found. Please try completing the query again.");
      return;
    }
    
    // Generate random skill percentages (all >= 87%)
    const skills = ['Expertise', 'Experience', 'Reputation', 'Availability', 'Patient Reviews'];
    const randomPercentages = {};
    
    skills.forEach(skill => {
      // Generate a random number between 87 and 99
      randomPercentages[skill] = Math.floor(Math.random() * (99 - 87 + 1)) + 87;
    });
    
    setSkillPercentages(randomPercentages);
    
    // Select first professional by default with a small delay for animation
    setTimeout(() => {
      setSelectedProfessional(professionals[0]);
    }, 500);
  }, [professionals, location.state]);
  
  // Function to handle professional selection
  const handleProfessionalClick = (professional) => {
    // Generate new random skill percentages when a new professional is selected
    const skills = ['Expertise', 'Experience', 'Reputation', 'Availability', 'Patient Reviews'];
    const randomPercentages = {};
    
    skills.forEach(skill => {
      // Generate a random number between 87 and 99
      randomPercentages[skill] = Math.floor(Math.random() * (99 - 87 + 1)) + 87;
    });
    
    setSkillPercentages(randomPercentages);
    setSelectedProfessional(professional);
    setShowProfessionalModal(true);
  };
  
  // Function to ask follow-up questions to the model
  const askQuestion = async () => {
    if (!currentQuestion.trim() || loading) return;
    
    setLoading(true);
    try {
      // Add user question to conversation
      const newConversation = [...conversation, { 
        type: 'question', 
        text: currentQuestion 
      }];
      
      setConversation(newConversation);
      setCurrentQuestion('');
      
      console.log("Sending conversation request with data:", {
        category,
        query,
        synthesis,
        professionals,
        followUpQA,
        question: currentQuestion
      });
      
      // Get response from model
      const response = await getConversationalResponse({
        category,
        query,
        synthesis,
        professionals,
        followUpQA,
        question: currentQuestion
      });
      
      console.log("Received conversation response:", response);
      
      // Add model response to conversation with typing animation
      setTimeout(() => {
        setConversation([...newConversation, { 
          type: 'answer', 
          text: response.data.response,
          isNew: true // Mark as new
        }]);
        setLoading(false);
        
        // Remove the "isNew" flag after 3 seconds
        setTimeout(() => {
          setConversation(prevConversation => 
            prevConversation.map((item, idx) => 
              idx === prevConversation.length - 1 ? { ...item, isNew: false } : item
            )
          );
        }, 3000);
      }, 800);
    } catch (err) {
      console.error("Error in conversation:", err);
      setConversation([...conversation, 
        { type: 'question', text: currentQuestion },
        { type: 'error', text: 'Sorry, there was an error processing your question. Please try again.' }
      ]);
      setLoading(false);
    }
  };
  
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  };

  const closeModal = () => {
    setShowProfessionalModal(false);
  };
  
  // If there's an error or no professionals, show error state
  if (error || !professionals || professionals.length === 0) {
    return (
      <motion.div 
        className="professionals-page"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <Header />
        <motion.div 
          className="error-container"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.4 }}
        >
          <h2>No professionals found</h2>
          <p>{error || "Please go back to the dashboard and try again."}</p>
          <motion.button 
            onClick={() => navigate('/dashboard')}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            Back to Dashboard
          </motion.button>
        </motion.div>
        <Footer />
      </motion.div>
    );
  }
  
  return (
    <motion.div 
      className="professionals-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <Header />
      
      {/* Summary Tab at Top Center */}
      <motion.div 
        className="summary-tab-container"
        variants={itemVariants}
        initial="hidden"
        animate="visible"
      >
        <motion.div 
          className="summary-card"
          variants={containerVariants}
        >
          <motion.div className="summary-header" variants={itemVariants}>
            <h2>{category ? category.replace(' Classifier', '') : 'Professional'} Services</h2>
            <div className="underline-decoration"></div>
          </motion.div>
          
          <motion.div className="query-summary" variants={itemVariants}>
            <p>{synthesis || 'Query synthesis not available'}</p>
          </motion.div>
          
          <motion.div className="summary-tags" variants={itemVariants}>
            {query && query.split(' ').filter(word => word.length > 4).slice(0, 5).map((tag, index) => (
              <motion.span 
                key={index} 
                className="summary-tag"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 + (index * 0.1) }}
              >
                {tag}
              </motion.span>
            ))}
          </motion.div>
        </motion.div>
      </motion.div>
      
      {/* New Main Layout: Professionals List (Left) + Q&A Tab (Right) */}
      <motion.main className="results-container new-layout">
        {/* Professionals List (Left Side) */}
        <motion.div 
          className="professionals-list-container"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div className="professionals-header" variants={itemVariants}>
            <h3>Recommended Professionals</h3>
            <p className="professionals-count">{professionals.length} matches found</p>
          </motion.div>
          
          <motion.div className="professionals-grid">
            {professionals.map((professional, index) => (
              <motion.div
                key={index}
                className="professional-card-wrapper"
                variants={listItemVariants}
                custom={index}
                whileHover={{ scale: 1.02, boxShadow: "0 8px 20px rgba(0, 0, 0, 0.1)" }}
                onClick={() => handleProfessionalClick(professional)}
              >
                <div className={`professional-card ${selectedProfessional === professional ? 'selected' : ''}`}>
                  <div className="card-avatar-container">
                    <div className="card-avatar">
                      {(professional['Doctor Name'] || professional.Name || 'P').charAt(0)}
                    </div>
                    {professional.Rating && (
                      <div className="card-rating">
                        <span className="star-icon">★</span>
                        <span>{professional.Rating}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="card-details">
                    <h4>{professional['Doctor Name'] || professional.Name || 'Professional'}</h4>
                    <p className="card-specialty">{professional.Expertise || professional.Skills || professional.Specialty || 'Specialized Professional'}</p>
                    <p className="card-location">
                      <span className="location-icon">📍</span>
                      {(professional.Locations && professional.Locations[0]) || 
                       professional.City || 
                       professional.Address ||
                       'London, UK'}
                    </p>
                  </div>
                  
                  <div className="view-profile-button">
                    View Profile
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        </motion.div>
        
        {/* Questions Tab (Right Side) */}
        <motion.div 
          className="questions-container"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div className="questions-header" variants={itemVariants}>
            <h3>Ask Additional Questions</h3>
            <p>Get more information about professionals or your specific needs</p>
          </motion.div>
          
          <motion.div 
            className="conversation-section"
            variants={itemVariants}
          >
            <div className="conversation-history">
              <AnimatePresence>
                {conversation.map((item, index) => (
                  <motion.div 
                    key={index} 
                    className={`conversation-item ${item.type}`}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    transition={{ duration: 0.3 }}
                  >
                    {item.type === 'question' ? (
                      <div className="user-question">
                        <span className="user-icon">👤</span>
                        <p>{item.text}</p>
                      </div>
                    ) : item.type === 'error' ? (
                      <div className="error-message">
                        <p>{item.text}</p>
                      </div>
                    ) : (
                      <div className={`model-answer ${item.isNew ? 'new-answer' : ''}`}>
                        <span className="model-icon">🤖</span>
                        <p>{item.text}</p>
                        {item.isNew && <span className="blinking-dot"></span>}
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              {loading && (
                <motion.div 
                  className="typing-indicator"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <p className="loading-text">Processing your question<span className="blinking-dot"></span><span className="blinking-dot"></span><span className="blinking-dot"></span></p>
                </motion.div>
              )}
              <div ref={conversationEndRef} />
            </div>
            
            <div className="question-input-container">
              <textarea
                value={currentQuestion}
                onChange={(e) => setCurrentQuestion(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask a question about the professionals or your specific needs..."
                disabled={loading}
                rows={3}
                className="question-textarea"
              />
              <motion.button 
                className="question-submit-button"
                onClick={askQuestion}
                disabled={!currentQuestion.trim() || loading}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {loading ? (
                  <span className="loading-spinner"></span>
                ) : (
                  <>
                    <span>Send</span>
                    <span className="send-icon">➤</span>
                  </>
                )}
              </motion.button>
            </div>
            
            <div className="suggested-questions">
              <h4>Suggested Questions</h4>
              <div className="question-chips">
                <motion.div 
                  className="question-chip"
                  whileHover={{ scale: 1.05, backgroundColor: "rgba(37, 99, 235, 0.1)" }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setCurrentQuestion("What qualifications should I look for?")}
                >
                  What qualifications should I look for?
                </motion.div>
                <motion.div 
                  className="question-chip"
                  whileHover={{ scale: 1.05, backgroundColor: "rgba(37, 99, 235, 0.1)" }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setCurrentQuestion("How do I choose between these professionals?")}
                >
                  How do I choose between these professionals?
                </motion.div>
                <motion.div 
                  className="question-chip"
                  whileHover={{ scale: 1.05, backgroundColor: "rgba(37, 99, 235, 0.1)" }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setCurrentQuestion("What's the average cost for these services?")}
                >
                  What's the average cost for these services?
                </motion.div>
                <motion.div 
                  className="question-chip"
                  whileHover={{ scale: 1.05, backgroundColor: "rgba(37, 99, 235, 0.1)" }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setCurrentQuestion("How long does it usually take to complete this type of project?")}
                >
                  How long does this type of project take?
                </motion.div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </motion.main>
      
      {/* Professional Modal Popup */}
      <AnimatePresence>
        {showProfessionalModal && selectedProfessional && (
          <motion.div 
            className="modal-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={closeModal}
          >
            <motion.div 
              className="professional-detail-modal"
              variants={modalVariants}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h3 className="modal-title">Professional Profile</h3>
                <motion.button 
                  className="close-modal-button"
                  onClick={closeModal}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  ✕
                </motion.button>
              </div>
              
              <div className="modal-content">
                <div className="professional-hero-section">
                  <div className="professional-avatar-large">
                    {(selectedProfessional['Doctor Name'] || selectedProfessional.Name || 'P').charAt(0)}
                  </div>
                  <div className="professional-hero-details">
                    <h2>{selectedProfessional['Doctor Name'] || selectedProfessional.Name || 'Professional Name'}</h2>
                    <p className="professional-tagline">{selectedProfessional.Expertise || selectedProfessional.Skills || selectedProfessional.Category || 'Specialized Professional'}</p>
                    
                    <div className="professional-meta-info">
                      {(selectedProfessional.Rating || selectedProfessional['Success_Rate']) && (
                        <div className="professional-rating-badge">
                          <div className="rating-stars">★★★★★</div>
                          <span className="rating-value">{selectedProfessional.Rating || selectedProfessional['Success_Rate'] || '80%'}</span>
                        </div>
                      )}
                      
                      {(selectedProfessional.Locations && selectedProfessional.Locations[0] || 
                        selectedProfessional.City || 
                        selectedProfessional.Address) && (
                        <div className="professional-location-badge">
                          <span className="location-pin">📍</span>
                          <span className="location-name">
                            {(selectedProfessional.Locations && selectedProfessional.Locations[0]) || 
                             selectedProfessional.City || 
                             selectedProfessional.Address ||
                             'London, UK'}
                          </span>
                        </div>
                      )}
                    </div>
                    
                    <div className="profile-action-buttons">
                      <motion.button 
                        className="contact-now-button"
                        onClick={() => {
                          closeModal();
                          setShowEmailModal(true);
                        }}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        Contact Now
                      </motion.button>
                      
                      <motion.button 
                        className="skills-button"
                        onClick={() => setShowGraph(!showGraph)}
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        Skills
                      </motion.button>
                    </div>
                  </div>
                </div>
                
                <div className="profile-details-content">
                  <div className="profile-info-section">
                    <h3>Professional Information</h3>
                    <div className="profile-info-grid">
                      <div className="profile-info-item">
                        <span className="info-label">Expertise:</span>
                        <span className="info-value">{selectedProfessional.Expertise || selectedProfessional.Skills || selectedProfessional.Category || 'Specialized Professional'}</span>
                      </div>
                      <div className="profile-info-item">
                        <span className="info-label">Experience:</span>
                        <span className="info-value">{selectedProfessional.Years_of_Experience || selectedProfessional.Experience || '8+ years'}</span>
                      </div>
                      {selectedProfessional.Education && (
                        <div className="profile-info-item">
                          <span className="info-label">Education:</span>
                          <span className="info-value">{selectedProfessional.Education}</span>
                        </div>
                      )}
                      {selectedProfessional.Qualifications && (
                        <div className="profile-info-item">
                          <span className="info-label">Qualifications:</span>
                          <span className="info-value">{selectedProfessional.Qualifications}</span>
                        </div>
                      )}
                      {(selectedProfessional.Phone || selectedProfessional['Contact Number']) && (
                        <div className="profile-info-item">
                          <span className="info-label">Contact:</span>
                          <span className="info-value">{selectedProfessional.Phone || selectedProfessional['Contact Number']}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {selectedProfessional.About && (
                    <div className="about-section">
                      <h3>About</h3>
                      <p>{selectedProfessional.About}</p>
                    </div>
                  )}
                  
                  {showGraph && (
                    <AnimatePresence>
                      <motion.div 
                        className="skills-modal-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={() => setShowGraph(false)}
                      >
                        <motion.div 
                          className="skills-showcase"
                          initial={{ scale: 0.9, opacity: 0 }}
                          animate={{ scale: 1, opacity: 1 }}
                          exit={{ scale: 0.9, opacity: 0 }}
                          transition={{ type: "spring", stiffness: 300, damping: 25 }}
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="skills-showcase-header">
                            <h2 className="skills-showcase-title">
                              {selectedProfessional['Doctor Name'] || selectedProfessional.Name || 'Professional'}'s Skills & Expertise
                            </h2>
                            <motion.button 
                              className="close-skills-button"
                              onClick={() => setShowGraph(false)}
                              whileHover={{ scale: 1.1 }}
                              whileTap={{ scale: 0.9 }}
                            >
                              ✕
                            </motion.button>
                          </div>
                          
                          <div className="skills-showcase-content">
                            <div className="skills-chart-section">
                              <h3>Expertise Distribution</h3>
                              <div className="skills-chart-container-showcase">
                                <SkillsChart professional={selectedProfessional} category={category} />
                              </div>
                            </div>
                            
                            <div className="skills-bars-section">
                              <h3>Skill Proficiency</h3>
                              <div className="skills-bars-container-showcase">
                                {Object.entries(skillPercentages).map(([skill, percentage], index) => (
                                  <div className="skill-bar-item-showcase" key={index}>
                                    <div className="skill-bar-label-showcase">{skill}</div>
                                    <div className="skill-bar-track-showcase">
                                      <motion.div 
                                        className="skill-bar-fill-showcase"
                                        initial={{ width: 0 }}
                                        animate={{ width: `${percentage}%` }}
                                        transition={{ duration: 1, delay: 0.2 + (index * 0.1) }}
                                      ></motion.div>
                                    </div>
                                    <div className="skill-bar-percentage-showcase">{percentage}%</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>
                        </motion.div>
                      </motion.div>
                    </AnimatePresence>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      
      <Footer />
      
      <AnimatePresence>
        {showEmailModal && (
          <EmailModal 
            professional={selectedProfessional}
            query={query}
            onClose={() => setShowEmailModal(false)}
          />
        )}
      </AnimatePresence>
      
      {/* Only show loading indicator when necessary */}
      {loading && !conversation.length && <Loading message="Processing your question..." />}
    </motion.div>
  );
};

export default ProfessionalsResults;