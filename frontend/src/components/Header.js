// src/components/Header.js (updated with animations and Preferences button)
import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import '../styles/Header.css';

const Header = () => {
  const [userData, setUserData] = useState(null);
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  
  useEffect(() => {
    // Load user data from localStorage
    const storedUserData = localStorage.getItem('userData');
    if (storedUserData) {
      setUserData(JSON.parse(storedUserData));
    }
    
    // Close menu when location changes
    setMenuOpen(false);
  }, [location]);
  
  const handleLogout = () => {
    localStorage.removeItem('userData');
    navigate('/login');
  };
  
  return (
    <motion.header 
      className="header"
      initial={{ y: -50, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="header-content">
        <motion.div 
          className="logo"
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <Link to="/dashboard">Skill Seeker</Link>
        </motion.div>
        
        {userData ? (
          <nav className={`nav-menu ${menuOpen ? 'open' : ''}`}>
            <motion.ul
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2, staggerChildren: 0.1 }}
            >
              <motion.li 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link to="/dashboard">Query</Link>
              </motion.li>
              <motion.li 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link to="/preferences">Preferences</Link>
              </motion.li>
              <motion.li className="user-info">
                <div className="user-avatar">
                  {userData && userData.name ? userData.name.charAt(0) : '?'}
                </div>
                <span>{userData.name}</span>
              </motion.li>
              <motion.li 
                className="logout-button"
                whileHover={{ scale: 1.05, backgroundColor: "#dc2626" }}
                whileTap={{ scale: 0.95 }}
                onClick={handleLogout}
              >
                Logout
              </motion.li>
            </motion.ul>
          </nav>
        ) : (
          <nav className="auth-nav">
            <motion.ul
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.2 }}
            >
              <motion.li 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link to="/login">Login</Link>
              </motion.li>
              <motion.li 
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Link to="/signup">Sign Up</Link>
              </motion.li>
            </motion.ul>
          </nav>
        )}
        
        <motion.div 
          className="menu-toggle"
          onClick={() => setMenuOpen(!menuOpen)}
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
        >
          <div className={`hamburger ${menuOpen ? 'active' : ''}`}>
            <span></span>
            <span></span>
            <span></span>
          </div>
        </motion.div>
      </div>
    </motion.header>
  );
};

export default Header;