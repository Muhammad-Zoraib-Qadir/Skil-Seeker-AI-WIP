// src/services/preferencesService.js

/**
 * Fetches user preferences from the backend API
 * @param {string} userId - User ID to fetch preferences for
 * @returns {Promise<Object>} - The user's preferences
 */
export const fetchUserPreferences = async (userId) => {
    try {
      const response = await fetch(`/api/user/preferences/${userId}`);
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error fetching preferences:', error);
      throw error;
    }
  };
  
  /**
   * Saves user preferences to the backend API
   * @param {string} userId - User ID to save preferences for
   * @param {Object} preferences - The preferences object to save
   * @returns {Promise<Object>} - The response from the server
   */
  export const saveUserPreferences = async (userId, preferences) => {
    try {
      const response = await fetch(`/api/user/preferences/${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(preferences)
      });
      
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Error saving preferences:', error);
      throw error;
    }
  };
  
  /**
   * Converts MongoDB data structure to frontend professional objects
   * @param {Object} mongoData - The data from MongoDB
   * @returns {Object} - Formatted preferences object
   */
  export const formatPreferencesData = (mongoData) => {
    const { DoctorNames, Education, Expertise, ContactNumbers, Conversation } = mongoData;
    
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
    if (DoctorNames && DoctorNames.length > 0) {
      for (let i = 0; i < DoctorNames.length; i++) {
        professionals.push({
          id: i + 1,
          name: DoctorNames[i] || 'Professional',
          profession: 'Technical Expert',
          location: 'Remote',
          rating: Education && Education[i] ? Education[i] : '4.5',
          price: Expertise && Expertise[i] ? Expertise[i] : 'Custom pricing',
          link: ContactNumbers && ContactNumbers[i] ? ContactNumbers[i] : '#',
          avatar: '/api/placeholder/40/40'
        });
      }
    }
    
    return {
      generalUnderstanding,
      professionals
    };
  };