import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const Preferences = () => {
  const [preferences, setPreferences] = useState({
    generalUnderstanding: "",
    professionals: []
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Fetch user preferences from the API
    const fetchPreferences = async () => {
      setLoading(true);
      try {
        // Get user ID from localStorage or context
        const userId = localStorage.getItem('userId');
        
        if (!userId) {
          setError("User not authenticated. Please log in to view preferences.");
          setLoading(false);
          return;
        }
        
        // Fetch preferences from API using fetch instead of axios
        const response = await fetch(`/api/user/preferences/${userId}`);
        
        if (!response.ok) {
          throw new Error(`Error ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Format the data based on MongoDB structure
        // In your backend, DoctorNames = expert names, Education = ratings, 
        // Expertise = package prices, ContactNumbers = links
        const { DoctorNames, Education, Expertise, ContactNumbers, Conversation } = data;
        
        // Find technical summary from conversation
        let generalUnderstanding = "Your project requirements will appear here.";
        
        if (Conversation && Conversation.length > 0) {
          const technicalSummary = Conversation.find(item => item.query === "technical_summary");
          if (technicalSummary) {
            generalUnderstanding = technicalSummary.response;
          }
        }
        
        // Format professionals data
        const professionals = [];
        
        // Zip together the data from different arrays
        for (let i = 0; i < DoctorNames.length; i++) {
          professionals.push({
            id: i + 1,
            name: DoctorNames[i] || 'Professional',
            profession: 'Technical Expert',
            location: 'Remote',
            rating: Education[i] || '4.5',
            price: Expertise[i] || 'Custom pricing',
            link: ContactNumbers[i] || '#',
            avatar: '/api/placeholder/40/40'
          });
        }
        
        setPreferences({
          generalUnderstanding,
          professionals
        });
        
        setLoading(false);
      } catch (err) {
        console.error("Error fetching preferences:", err);
        setError("Failed to load preferences. Please try again later.");
        setLoading(false);
      }
    };
    
    fetchPreferences();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-white">
      <div className="container mx-auto px-4 py-12">
        <motion.h1 
          className="text-5xl font-bold text-center mb-16"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          Preferences
        </motion.h1>
        
        {loading ? (
          <div className="flex justify-center items-center h-64">
            <div className="w-12 h-12 border-4 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : error ? (
          <div className="bg-red-800 bg-opacity-50 p-6 rounded-lg text-center">
            <p className="text-xl">{error}</p>
            <button 
              className="mt-4 bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg transition-colors"
              onClick={() => window.location.href = '/dashboard'}
            >
              Back to Dashboard
            </button>
          </div>
        ) : (
          <div className="space-y-24">
            {/* General Understanding Section */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <h2 className="text-4xl font-bold mb-12">General Understanding</h2>
              <div className="bg-gray-800 bg-opacity-50 p-8 rounded-lg">
                <p className="text-xl leading-relaxed">{preferences.generalUnderstanding}</p>
              </div>
            </motion.section>
            
            {/* Previous Professionals Section */}
            <motion.section
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
            >
              <h2 className="text-4xl font-bold mb-12">Previous Professionals</h2>
              
              {preferences.professionals.length === 0 ? (
                <div className="text-center py-12 bg-gray-800 bg-opacity-50 rounded-lg">
                  <p className="text-xl">No saved professionals yet.</p>
                  <button 
                    className="mt-4 bg-blue-600 hover:bg-blue-700 px-6 py-2 rounded-lg transition-colors"
                    onClick={() => window.location.href = '/dashboard'}
                  >
                    Find Professionals
                  </button>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                  {preferences.professionals.map((professional, index) => (
                    <motion.div
                      key={professional.id}
                      className="bg-indigo-600 rounded-lg overflow-hidden shadow-lg"
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ duration: 0.4, delay: 0.2 + (index * 0.1) }}
                      whileHover={{ y: -5, transition: { duration: 0.2 } }}
                    >
                      <div className="p-6">
                        <div className="flex items-center mb-4">
                          <img 
                            src={professional.avatar} 
                            alt={professional.name} 
                            className="w-10 h-10 rounded-full mr-3"
                          />
                          <h3 className="text-xl font-semibold">{professional.name}</h3>
                        </div>
                        <div className="text-4xl font-bold mb-2">{professional.profession}</div>
                        <div className="flex justify-between items-center mb-3">
                          <span>{professional.location}</span>
                          <span className="bg-indigo-500 px-2 py-1 rounded text-sm">
                            ★ {professional.rating}
                          </span>
                        </div>
                        <div className="pt-3 border-t border-indigo-500 flex justify-between items-center">
                          <span className="font-medium">{professional.price}</span>
                          <a 
                            href={professional.link} 
                            className="text-sm hover:underline"
                            target="_blank" 
                            rel="noopener noreferrer"
                          >
                            More →
                          </a>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.section>
          </div>
        )}
      </div>
    </div>
  );
};

export default Preferences;