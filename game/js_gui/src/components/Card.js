import React, { useState, useEffect } from 'react';
import './Card.css';

const Card = ({ 
  card, 
  isKnown = false, 
  isRevealed = false,
  onClick = null,
  className = '',
  isHighlighted = false,
  size = 'normal', // 'small', 'normal', 'large'
  animationState = '', // 'dealing', 'flipping', 'discarding', 'drawing', 'revealing', 'floating', 'pulsing'
  isStacked = false,
  showTrail = false,
  cardType = '' // 'jack', 'queen', 'king', 'ace' for special effects
}) => {
  
  const [currentAnimation, setCurrentAnimation] = useState('');
  const [isAnimating, setIsAnimating] = useState(false);

  // Handle animation state changes
  useEffect(() => {
    if (animationState && animationState !== currentAnimation) {
      setCurrentAnimation(animationState);
      setIsAnimating(true);
      
      // Clear animation after it completes
      const animationDuration = getAnimationDuration(animationState);
      setTimeout(() => {
        setIsAnimating(false);
        setCurrentAnimation('');
      }, animationDuration);
    }
  }, [animationState, currentAnimation]);

  const getAnimationDuration = (animation) => {
    const durations = {
      'dealing': 1200,
      'flipping': 800,
      'discarding': 800,
      'drawing': 1000,
      'revealing': 600,
      'floating': 0, // infinite
      'pulsing': 0,  // infinite
      'sliding-in': 500,
      'sliding-out': 500
    };
    return durations[animation] || 300;
  };

  // Parse card string (e.g., "7♥", "K♠", "A♦")
  const parseCard = (cardStr) => {
    if (!cardStr || cardStr === '?' || cardStr === 'None') {
      return null;
    }
    
    const value = cardStr.slice(0, -1);
    const suit = cardStr.slice(-1);
    return { value, suit };
  };

  const getSuitIcon = (suit) => {
    const suitMap = {
      '♥': '♥', '♦': '♦', '♣': '♣', '♠': '♠',
      'H': '♥', 'D': '♦', 'C': '♣', 'S': '♠',
      'h': '♥', 'd': '♦', 'c': '♣', 's': '♠'
    };
    return suitMap[suit] || '?';
  };

  const getSuitColor = (suit) => {
    const redSuits = ['♥', '♦', 'H', 'D', 'h', 'd'];
    return redSuits.includes(suit) ? 'red' : 'black';
  };

  const getCardValue = (value) => {
    const valueMap = {
      '1': 'A', '11': 'J', '12': 'Q', '13': 'K'
    };
    return valueMap[value] || value;
  };

  const getCardType = (value) => {
    const typeMap = {
      '1': 'ace', 'A': 'ace',
      '11': 'jack', 'J': 'jack',
      '12': 'queen', 'Q': 'queen', 
      '13': 'king', 'K': 'king'
    };
    return typeMap[value] || '';
  };

  const parsedCard = parseCard(card);
  const isEmpty = !card || card === 'None';
  const isUnknown = card === '?' || (!isKnown && !isRevealed);
  
  const cardTypeClass = parsedCard ? getCardType(parsedCard.value) : cardType;
  
  const cardClasses = [
    'card',
    `card--${size}`,
    currentAnimation ? `card--${currentAnimation}` : '',
    isHighlighted ? 'card--highlighted' : '',
    isEmpty ? 'card--empty' : '',
    isUnknown ? 'card--unknown' : '',
    onClick ? 'card--clickable' : '',
    isStacked ? 'card--stacked' : '',
    showTrail ? 'card--with-trail' : '',
    cardTypeClass ? `card--${cardTypeClass}` : '',
    className
  ].filter(Boolean).join(' ');

  const renderCardFace = () => {
    if (isEmpty) {
      return (
        <div className="card__empty">
          <div className="card__empty-icon">⭘</div>
        </div>
      );
    }

    if (isUnknown) {
      return (
        <div className="card__back">
          <div className="card__back-pattern">
            <div className="card__back-diamond">♦</div>
            <div className="card__back-text">CABO</div>
          </div>
        </div>
      );
    }

    if (parsedCard) {
      const { value, suit } = parsedCard;
      const suitIcon = getSuitIcon(suit);
      const suitColor = getSuitColor(suit);
      const displayValue = getCardValue(value);

      return (
        <div className={`card__face card__face--${suitColor}`}>
          <div className="card__corner card__corner--top-left">
            <div className="card__value">{displayValue}</div>
            <div className="card__suit">{suitIcon}</div>
          </div>
          
          <div className="card__center">
            <div 
              className="card__center-suit" 
              style={{ color: suitColor === 'red' ? '#e74c3c' : '#2c3e50' }}
            >
              {suitIcon}
            </div>
          </div>
          
          <div className="card__corner card__corner--bottom-right">
            <div className="card__value">{displayValue}</div>
            <div className="card__suit">{suitIcon}</div>
          </div>
        </div>
      );
    }

    return (
      <div className="card__error">
        <span>?</span>
      </div>
    );
  };

  const handleClick = () => {
    if (onClick && !isAnimating) {
      // Add a small click animation
      setCurrentAnimation('pulsing');
      setIsAnimating(true);
      setTimeout(() => {
        setIsAnimating(false);
        setCurrentAnimation('');
      }, 300);
      
      onClick();
    }
  };

  return (
    <div 
      className={cardClasses}
      onClick={handleClick}
      title={isEmpty ? 'Empty slot' : isUnknown ? 'Unknown card' : card}
      style={{
        animationDelay: `${Math.random() * 0.1}s` // Small random delay for natural feel
      }}
    >
      {renderCardFace()}
      
      {isKnown && !isRevealed && !isEmpty && (
        <div className="card__known-indicator">✓</div>
      )}
      
      {/* Animation overlay for special effects */}
      {isAnimating && (currentAnimation === 'revealing' || currentAnimation === 'drawing') && (
        <div className="card__glow-overlay" />
      )}
    </div>
  );
};

export default Card; 