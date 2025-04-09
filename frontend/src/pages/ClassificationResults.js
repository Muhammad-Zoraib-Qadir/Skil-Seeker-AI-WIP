import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import Header from '../components/Header';
import Footer from '../components/Footer';
import Loading from '../components/Loading';
import '../styles/ClassificationResults.css';

const ClassificationResults = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { classifications, query, userLocation } = location.state || {};
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Enhanced animation variants with spring physics for more natural movement
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
    hidden: { scale: 0.92, opacity: 0 },
    visible: { 
      scale: 1, 
      opacity: 1, 
      transition: { 
        type: "spring", 
        stiffness: 400, 
        damping: 30 
      } 
    },
    hover: { 
      scale: 1.04, 
      boxShadow: "0 15px 35px rgba(0, 0, 0, 0.2)",
      y: -5,
      transition: {
        type: "spring",
        stiffness: 400,
        damping: 15
      }
    },
    selected: {
      scale: 1.05,
      boxShadow: "0 18px 40px rgba(37, 99, 235, 0.3)",
      y: -8,
      transition: {
        type: "spring",
        stiffness: 400,
        damping: 20
      }
    }
  };
  
  // Gradient background animations
  const gradientVariants = {
    initial: { 
      background: "linear-gradient(135deg, rgba(59, 130, 246, 0.6) 0%, rgba(147, 51, 234, 0.6) 100%)",
      opacity: 0
    },
    animate: { 
      background: "linear-gradient(135deg, rgba(59, 130, 246, 0.8) 0%, rgba(147, 51, 234, 0.8) 100%)",
      opacity: 1,
      transition: { duration: 0.5 }
    }
  };
  
  // Clean the query to ensure we don't display location info in the query field
  const cleanedQuery = React.useMemo(() => {
    if (!query) return '';
    
    // Remove any "in [location]" or "and my location is in [location]" from the query
    return query
      .replace(/\s+in\s+([A-Za-z\s]+)$/i, '')
      .replace(/\s+and my location is in\s+([A-Za-z\s]+)$/i, '')
      .trim();
  }, [query]);
  
  // Process classifications to handle all potential data formats
  const processedCategories = React.useMemo(() => {
    if (!classifications) return [];
    
    // Filter out "Other" classifications and "Selected category"
    return Object.entries(classifications)
      .filter(([key, value]) => 
        value !== "Other" && 
        key !== "Selected category" && 
        value !== "Selected category" &&
        !key.includes("Selected")
      )
      .map(([key, value]) => {
        // For standard categories, use the value (Medical, Legal, etc.)
        const displayName = ['Medical', 'Legal', 'CS', 'SEO'].includes(value) 
          ? value 
          : key.replace(' Classifier', '');
        
        // Assign category-specific icons and colors
        let icon = '🔍'; // Default icon
        let color = '#4F46E5'; // Default color (indigo)
        
        switch(displayName.toLowerCase()) {
          case 'medical':
            icon = '⚕️';
            color = '#059669'; // Emerald
            break;
          case 'legal':
            icon = '⚖️';
            color = '#7C3AED'; // Violet
            break;
          case 'cs':
            icon = '💻';
            color = '#2563EB'; // Blue
            break;
          case 'seo':
            icon = '📊';
            color = '#F59E0B'; // Amber
            break;
          default:
            icon = '🔍';
            color = '#4F46E5'; // Indigo
        }
          
        return {
          displayName,
          originalKey: key,
          icon,
          color
        };
      });
  }, [classifications]);
  
  useEffect(() => {
    // Add entrance animation for the categories
    if (processedCategories.length > 0) {
      const categoryCards = document.querySelectorAll('.category-card');
      categoryCards.forEach((card, index) => {
        setTimeout(() => {
          card.classList.add('appear');
        }, 120 * index);
      });
    }
  }, [processedCategories]);
  
  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
  };
  
  const handleContinue = () => {
    if (selectedCategory) {
      setLoading(true);
      
      // Find the original classifier key for the selected category
      const selected = processedCategories.find(c => c.displayName === selectedCategory);
      
      // Ensure we pass a proper category string with "Classifier" suffix
      let categoryToPass;
      
      if (selected && selected.originalKey) {
        // If we have the original key (which should include "Classifier"), use it
        categoryToPass = selected.originalKey;
      } else {
        // Otherwise, append "Classifier" to ensure proper format
        categoryToPass = `${selectedCategory} Classifier`;
      }
      
      console.log("Navigating with category:", categoryToPass);
      
      // Add a small delay for the animation to complete
      setTimeout(() => {
        navigate('/processing', { 
          state: { 
            category: categoryToPass, 
            query: cleanedQuery, // Pass the cleaned query
            userLocation 
          }
        });
      }, 600);
    }
  };
  
  if (!classifications) {
    return (
      <motion.div 
        className="classification-page error-page"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
      >
        <Header />
        <motion.div 
          className="error-container"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ 
            type: "spring", 
            stiffness: 300, 
            damping: 25 
          }}
        >
          <motion.div 
            className="error-icon"
            animate={{ 
              scale: [1, 1.1, 1],
              rotate: [0, 5, -5, 0] 
            }}
            transition={{ 
              duration: 2, 
              repeat: Infinity, 
              repeatType: "reverse" 
            }}
          >
            ⚠️
          </motion.div>
          <h2>No classification data available</h2>
          <p>Please go back to the dashboard and try again with a new query.</p>
          <motion.button 
            onClick={() => navigate('/dashboard')}
            whileHover={{ 
              scale: 1.05, 
              boxShadow: "0 8px 20px rgba(37, 99, 235, 0.3)" 
            }}
            whileTap={{ scale: 0.95 }}
            className="primary-button with-icon"
          >
            <span>←</span> Back to Dashboard
          </motion.button>
        </motion.div>
        <Footer />
      </motion.div>
    );
  }
  
  return (
    <motion.div 
      className="classification-page"
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
        className="classification-container"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        exit="exit"
      >
        <motion.div className="page-title-container" variants={itemVariants}>
          <div className="title-decoration"></div>
          <h2>Query Classification Results</h2>
          <div className="title-decoration"></div>
        </motion.div>
        
        <motion.div 
          className="query-information"
          variants={itemVariants}
        >
          <div className="query-card">
            <div className="query-icon">🔍</div>
            <div className="query-details">
              <p className="query-label">Your query:</p>
              <p className="query-text">"{cleanedQuery}"</p>
              {userLocation && (
                <div className="location-info">
                  <span className="location-icon">📍</span>
                  <p className="location-text">{userLocation}</p>
                </div>
              )}
            </div>
          </div>
        </motion.div>
        
        <motion.div 
          className="classification-results"
          variants={itemVariants}
        >
          <motion.h3 
            variants={itemVariants}
            className="results-heading"
          >
            <span className="heading-highlight">Your query matches these categories:</span>
          </motion.h3>
          
          {processedCategories.length > 0 ? (
            <motion.div 
              className="category-options"
              variants={containerVariants}
            >
              <AnimatePresence>
                {processedCategories.map(({ displayName, icon, color, originalKey }, index) => (
                  <motion.div 
                    key={displayName}
                    className={`category-card ${selectedCategory === displayName ? 'selected' : ''}`}
                    onClick={() => handleCategorySelect(displayName)}
                    variants={cardVariants}
                    initial="hidden"
                    animate={selectedCategory === displayName ? "selected" : "visible"}
                    whileHover={selectedCategory === displayName ? {} : "hover"}
                    custom={index}
                    transition={{ delay: index * 0.15 }}
                    style={{
                      borderTop: selectedCategory === displayName ? `4px solid ${color}` : '1px solid rgba(255, 255, 255, 0.1)'
                    }}
                  >
                    <div className="card-content">
                      <div 
                        className="category-icon" 
                        style={{ 
                          backgroundColor: `${color}20`,
                          color: color
                        }}
                      >
                        <span>{icon}</span>
                      </div>
                      <h4>{displayName}</h4>
                      <p>Specialists in this field can help with your query.</p>
                      
                      {selectedCategory === displayName && (
                        <motion.div 
                          className="selection-indicator"
                          initial={{ opacity: 0, scale: 0.8 }}
                          animate={{ opacity: 1, scale: 1 }}
                          transition={{ duration: 0.3 }}
                        >
                          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <circle cx="10" cy="10" r="10" fill={color} />
                            <path d="M6 10L9 13L14 7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                          </svg>
                        </motion.div>
                      )}
                    </div>
                    
                    <motion.div 
                      className="card-background"
                      initial={{ opacity: 0 }}
                      animate={{ 
                        opacity: selectedCategory === displayName ? 1 : 0,
                        background: selectedCategory === displayName 
                          ? `linear-gradient(135deg, ${color}10 0%, ${color}30 100%)` 
                          : 'transparent'
                      }}
                      transition={{ duration: 0.4 }}
                    />
                  </motion.div>
                ))}
              </AnimatePresence>
            </motion.div>
          ) : (
            <motion.div 
              className="no-results"
              variants={itemVariants}
            >
              <div className="no-results-icon">🔎</div>
              <p>No matching categories found. Please try refining your query.</p>
              <motion.button 
                onClick={() => navigate('/dashboard')}
                whileHover={{ 
                  scale: 1.05, 
                  boxShadow: "0 8px 20px rgba(37, 99, 235, 0.3)" 
                }}
                whileTap={{ scale: 0.95 }}
                className="primary-button"
              >
                Try Again
              </motion.button>
            </motion.div>
          )}
        </motion.div>
        
        <AnimatePresence>
          {selectedCategory && (
            <motion.div 
              className="action-buttons"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 30 }}
              transition={{ 
                type: "spring", 
                stiffness: 500, 
                damping: 30 
              }}
            >
              <motion.button 
                onClick={handleContinue} 
                className="continue-button"
                disabled={loading}
                whileHover={{ 
                  scale: 1.05, 
                  boxShadow: "0 12px 25px rgba(37, 99, 235, 0.35)" 
                }}
                whileTap={{ scale: 0.97 }}
              >
                {loading ? (
                  <div className="loading-content">
                    <span className="loading-spinner"></span>
                    <span>Processing...</span>
                  </div>
                ) : (
                  <>
                    <span>Continue with {selectedCategory}</span>
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
            </motion.div>
          )}
        </AnimatePresence>
      </motion.main>
      
      <Footer />
      
      {loading && <Loading message="Processing your query..." />}
    </motion.div>
  );
};

export default ClassificationResults;