import React from 'react';
import '../styles/components/ProfessionalCard.css';

const ProfessionalCard = ({ professional, isSelected, onClick }) => {
  // Determine the professional name based on available fields
  const name = professional.Name || professional['Doctor Name'] || 'Professional';
  // Determine title/expertise based on available fields
  const title = professional['Gig Title'] || professional.Expertise || professional.Category || professional.Skills || '';
  // Determine rating
  const rating = professional.Rating || professional['Success_Rate'] || '4.8';
  // Determine contact info
  const contact = professional['Contact Number'] || professional.Phone || '';
  // Determine location
  const location = professional.City || (professional.Locations && professional.Locations[0]) || '';
  
  return (
    <div 
      className={`professional-card ${isSelected ? 'selected' : ''}`}
      onClick={onClick}
    >
      <h4>{name}</h4>
      <p className="title">{title}</p>
      <div className="rating">
        Rating: {rating} ★
      </div>
      <div className="contact-info">
        {contact && <p>{contact}</p>}
        {location && <p>{location}</p>}
      </div>
    </div>
  );
};

export default ProfessionalCard;