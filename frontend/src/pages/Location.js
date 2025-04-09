// src/pages/Location.js
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import Header from '../components/Header';
import Footer from '../components/Footer';
import '../styles/Location.css';

const Location = () => {
  const [location, setLocation] = useState('');
  const [locationChanged, setLocationChanged] = useState(false);
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

  useEffect(() => {
    // Load current location
    const storedLocation = localStorage.getItem('userLocation');
    if (storedLocation) {
      setLocation(storedLocation);
    }
    
    // Add subtle background animation
    document.body.classList.add('animated-bg');
    
    return () => {
      document.body.classList.remove('animated-bg');
    };
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    
    // Trim the location to avoid empty spaces
    const trimmedLocation = location.trim();
    
    if (trimmedLocation) {
      // Store clean location in localStorage
      localStorage.setItem('userLocation', trimmedLocation);
      setLocationChanged(true);
      
      // Add a small delay before navigation for the success animation
      setTimeout(() => {
        navigate('/dashboard');
      }, 1000);
    }
  };

  return (
    <motion.div 
      className="location-page"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6 }}
    >
      <Header />
      
      <main className="location-container">
        <motion.div 
          className="location-content"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.h2 variants={itemVariants}>Update Your Location</motion.h2>
          <motion.p variants={itemVariants}>Your location helps us find professionals in your area.</motion.p>
          
          {locationChanged && (
            <motion.div 
              className="success-message"
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
            >
              Location updated successfully!
            </motion.div>
          )}
          
          <motion.form 
            onSubmit={handleSubmit} 
            className="location-form"
            variants={itemVariants}
          >
            <motion.div className="form-group" variants={itemVariants}>
              <label>Your Location (City)</label>
              <motion.input
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                placeholder="e.g., Islamabad"
                required
                whileFocus={{ boxShadow: "0 0 0 3px rgba(37, 99, 235, 0.2)" }}
              />
              <small className="input-hint">Enter only your city name (e.g., "Islamabad"). Your queries will automatically include this location.</small>
            </motion.div>
            <motion.div className="button-group" variants={itemVariants}>
              <motion.button 
                type="submit" 
                className="save-button"
                whileHover={{ scale: 1.02, boxShadow: "0 4px 12px rgba(37, 99, 235, 0.25)" }}
                whileTap={{ scale: 0.98 }}
              >
                Save Location
              </motion.button>
              <motion.button 
                type="button" 
                className="cancel-button"
                onClick={() => navigate('/dashboard')}
                whileHover={{ scale: 1.02, backgroundColor: "#f9fafb" }}
                whileTap={{ scale: 0.98 }}
              >
                Cancel
              </motion.button>
            </motion.div>
          </motion.form>
        </motion.div>
      </main>
      
      <Footer />
    </motion.div>
  );
};

export default Location;  