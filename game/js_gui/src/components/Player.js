import React from 'react';
import Card from './Card';
import './Player.css';

const Player = ({ 
  player, 
  isCurrentPlayer = false, 
  onAction = null,
  playerIndex = 0,
  animationState = '' // Animation state for player actions
}) => {
  
  const {
    name = 'Unknown Player',
    hand = [],
    known_cards = [],
    score = 0,
    hand_size = 0,
    is_gym_player = false
  } = player || {};

  const renderPlayerHand = () => {
    const maxCards = 4;
    const cards = [];
    
    for (let i = 0; i < maxCards; i++) {
      const card = i < hand.length ? hand[i] : null;
      const isKnown = i < known_cards.length ? known_cards[i] : false;
      const isEmpty = !card || card === 'None' || card === null;
      
      // Determine card animation based on player animation state
      let cardAnimation = '';
      if (animationState === 'dealing' && !isEmpty) {
        // Stagger card dealing animations
        cardAnimation = 'dealing';
      } else if (animationState === 'discarding' && i === 0) {
        // Only animate first card for discard
        cardAnimation = 'discarding';
      } else if (isCurrentPlayer && !isEmpty) {
        cardAnimation = 'floating';
      }
      
      cards.push(
        <Card
          key={i}
          card={isEmpty ? null : card}
          isKnown={isKnown}
          isRevealed={is_gym_player || isKnown}
          size="normal"
          className={`hand-card hand-card--${i}`}
          onClick={() => onAction && onAction('card_click', { player: name, position: i })}
          isHighlighted={isCurrentPlayer && !isEmpty}
          animationState={cardAnimation}
          style={{
            animationDelay: animationState === 'dealing' ? `${i * 0.2}s` : '0s'
          }}
        />
      );
    }
    
    return (
      <div className={`player-hand ${animationState ? `player-hand--${animationState}` : ''}`}>
        {cards}
      </div>
    );
  };

  const renderPlayerInfo = () => (
    <div className={`player-info ${isCurrentPlayer ? 'player-info--current' : ''}`}>
      <div className="player-header">
        <h3 className="player-name">
          {name}
          {is_gym_player && <span className="gym-badge">🤖 AI</span>}
        </h3>
        {isCurrentPlayer && (
          <div className="current-indicator">
            <span className="current-arrow">▶</span>
            <span className="current-text">PLAYING</span>
          </div>
        )}
      </div>
      
      <div className="player-stats">
        <div className="stat">
          <span className="stat-label">Score</span>
          <span className={`stat-value ${score <= 15 ? 'stat-value--good' : score >= 25 ? 'stat-value--bad' : ''}`}>
            {score}
          </span>
        </div>
        <div className="stat">
          <span className="stat-label">Cards</span>
          <span className="stat-value">{hand_size}</span>
        </div>
        {is_gym_player && (
          <div className="stat">
            <span className="stat-label">Known</span>
            <span className="stat-value stat-value--special">
              {known_cards.filter(Boolean).length}/{hand_size}
            </span>
          </div>
        )}
      </div>
      
      {/* Action indicator */}
      {animationState && (
        <div className="action-status">
          <div className={`action-icon action-icon--${animationState}`}>
            {getActionIcon(animationState)}
          </div>
          <span className="action-text">
            {getActionText(animationState)}
          </span>
        </div>
      )}
    </div>
  );

  const getActionIcon = (action) => {
    const iconMap = {
      'dealing': '📥',
      'discarding': '📤', 
      'drawing': '🎯',
      'pulsing': '⚡'
    };
    return iconMap[action] || '⚙️';
  };

  const getActionText = (action) => {
    const textMap = {
      'dealing': 'Receiving cards...',
      'discarding': 'Discarding card...',
      'drawing': 'Drawing card...',
      'pulsing': 'Thinking...'
    };
    return textMap[action] || 'Taking action...';
  };

  const getPlayerTypeClass = () => {
    if (is_gym_player) return 'player--gym';
    return 'player--ai';
  };

  const getPlayerPositionClass = () => {
    return `player--position-${playerIndex}`;
  };

  const getScoreClass = () => {
    if (score <= 15) return 'player--winning';
    if (score >= 25) return 'player--losing';
    return '';
  };

  return (
    <div className={`
      player 
      ${getPlayerTypeClass()} 
      ${getPlayerPositionClass()}
      ${getScoreClass()}
      ${isCurrentPlayer ? 'player--current' : ''}
      ${animationState ? `player--${animationState}` : ''}
    `}>
      {renderPlayerInfo()}
      {renderPlayerHand()}
      
      {/* Activity indicator for current player */}
      {isCurrentPlayer && (
        <div className="player-activity">
          <div className="activity-pulse"></div>
          <div className="activity-text">Active Turn</div>
        </div>
      )}
      
      {/* Score trend indicator */}
      <div className="score-trend">
        {score <= 15 && <div className="trend-indicator trend-indicator--good">🔥</div>}
        {score >= 25 && <div className="trend-indicator trend-indicator--bad">⚠️</div>}
      </div>
    </div>
  );
};

export default Player; 