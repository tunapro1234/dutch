import React, { useState, useEffect, useRef } from 'react';
import Card from './Card';
import Player from './Player';
import './GameBoard.css';

const GameBoard = ({ 
  gameState, 
  players, 
  onCardClick = null,
  onPlayerAction = null
}) => {
  
  const [animationQueue, setAnimationQueue] = useState([]);
  const [deckAnimation, setDeckAnimation] = useState('');
  const [discardAnimation, setDiscardAnimation] = useState('');
  const [currentTurnAnimation, setCurrentTurnAnimation] = useState('');
  
  const prevGameStateRef = useRef();
  const prevPlayersRef = useRef();
  
  const {
    turn_count = 0,
    current_player = '',
    dutch_called = false,
    deck_size = 52,
    top_discard = null,
    game_status = 'playing'
  } = gameState || {};

  // Monitor game state changes for animations
  useEffect(() => {
    const prevGameState = prevGameStateRef.current;
    const prevPlayers = prevPlayersRef.current;
    
    if (prevGameState && prevPlayers) {
      // Detect turn changes
      if (prevGameState.current_player !== current_player) {
        setCurrentTurnAnimation('floating');
        setTimeout(() => setCurrentTurnAnimation(''), 2000);
      }
      
      // Detect deck size changes (card drawn)
      if (prevGameState.deck_size > deck_size) {
        setDeckAnimation('drawing');
        setTimeout(() => setDeckAnimation(''), 1000);
      }
      
      // Detect discard pile changes
      if (prevGameState.top_discard !== top_discard && top_discard) {
        setDiscardAnimation('dealing');
        setTimeout(() => setDiscardAnimation(''), 800);
      }
      
      // Detect Dutch call
      if (!prevGameState.dutch_called && dutch_called) {
        triggerDutchAnimation();
      }
      
      // Detect hand size changes (cards added/removed)
      if (players && prevPlayers) {
        players.forEach((player, index) => {
          const prevPlayer = prevPlayers[index];
          if (prevPlayer && prevPlayer.hand_size !== player.hand_size) {
            // Trigger hand animation
            schedulePlayerHandAnimation(player.name, player.hand_size > prevPlayer.hand_size ? 'dealing' : 'discarding');
          }
        });
      }
    }
    
    // Update refs
    prevGameStateRef.current = gameState;
    prevPlayersRef.current = players;
  }, [gameState, players, current_player, deck_size, top_discard, dutch_called]);

  const schedulePlayerHandAnimation = (playerName, animationType) => {
    const newAnimation = {
      id: Date.now(),
      playerName,
      animationType,
      timestamp: Date.now()
    };
    
    setAnimationQueue(prev => [...prev, newAnimation]);
    
    // Remove animation after completion
    setTimeout(() => {
      setAnimationQueue(prev => prev.filter(anim => anim.id !== newAnimation.id));
    }, 1500);
  };

  const triggerDutchAnimation = () => {
    // Create a ripple effect for Dutch call
    setCurrentTurnAnimation('pulsing');
    setTimeout(() => setCurrentTurnAnimation(''), 3000);
  };

  const formatPlayerName = (name) => {
    return name || 'Unknown Player';
  };

  const getPlayerAnimation = (playerName) => {
    const animation = animationQueue.find(anim => anim.playerName === playerName);
    return animation ? animation.animationType : '';
  };

  const renderDeckArea = () => (
    <div className="deck-area">
      {/* Deck */}
      <div className="deck-container">
        <div className="deck-label">DECK</div>
        <div className="deck-stack">
          <Card 
            card="?"
            size="large"
            className="deck-card"
            onClick={() => onCardClick && onCardClick('deck')}
            animationState={deckAnimation}
            isStacked={deck_size > 1}
          />
          <div className="deck-count">
            <span className={`deck-counter ${deckAnimation ? 'deck-counter--updating' : ''}`}>
              {deck_size} cards
            </span>
          </div>
        </div>
      </div>

      {/* Center Play Area */}
      <div className="center-play-area">
        <div className="game-flow-indicator">
          <div className={`flow-arrow flow-arrow--left ${deckAnimation === 'drawing' ? 'flow-arrow--active' : ''}`}>
            →
          </div>
          <div className="play-zone">
            <div className="play-zone-text">PLAY ZONE</div>
            <div className={`turn-indicator-center ${currentTurnAnimation ? `turn-indicator--${currentTurnAnimation}` : ''}`}>
              Turn {turn_count}
            </div>
          </div>
          <div className={`flow-arrow flow-arrow--right ${discardAnimation === 'dealing' ? 'flow-arrow--active' : ''}`}>
            →
          </div>
        </div>
      </div>

      {/* Discard Pile */}
      <div className="discard-container">
        <div className="discard-label">DISCARD</div>
        <div className="discard-stack">
          <Card 
            card={top_discard}
            size="large"
            isRevealed={true}
            className="discard-card"
            onClick={() => onCardClick && onCardClick('discard')}
            animationState={discardAnimation}
            showTrail={discardAnimation === 'dealing'}
          />
        </div>
      </div>
    </div>
  );

  const renderGameInfo = () => (
    <div className="game-info">
      <div className="game-info__header">
        <h1 className="game-title">🎮 DUTCH CABO</h1>
        <div className={`turn-indicator ${currentTurnAnimation ? `turn-indicator--${currentTurnAnimation}` : ''}`}>
          Turn {turn_count}
        </div>
      </div>
      
      <div className="game-status">
        <div className="current-player">
          <span className="label">Current Player:</span>
          <span className={`player-name ${current_player ? 'player-name--active' : ''}`}>
            {formatPlayerName(current_player)}
          </span>
        </div>
        
        {dutch_called && (
          <div className="dutch-indicator dutch-indicator--animated">
            <span className="dutch-text">🇳🇱 DUTCH CALLED!</span>
            <div className="dutch-ripple"></div>
          </div>
        )}
        
        <div className="game-state-indicator">
          <span className={`status-badge status-badge--${game_status}`}>
            {game_status.toUpperCase()}
          </span>
        </div>
      </div>
    </div>
  );

  const renderPlayersArea = () => {
    if (!players || players.length === 0) {
      return (
        <div className="players-area">
          <div className="no-players">
            <div className="no-players-icon">🎴</div>
            <div>No players connected</div>
            <div className="no-players-subtitle">Waiting for game to start...</div>
          </div>
        </div>
      );
    }

    return (
      <div className="players-area">
        <div className="players-grid">
          {players.map((player, index) => (
            <Player
              key={player.name || index}
              player={player}
              isCurrentPlayer={player.name === current_player}
              onAction={onPlayerAction}
              playerIndex={index}
              animationState={getPlayerAnimation(player.name)}
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="game-board">
      {renderGameInfo()}
      
      <div className="game-content">
        <div className="game-center">
          {renderDeckArea()}
        </div>
        
        {renderPlayersArea()}
      </div>
      
      <div className="game-footer">
        <div className="connection-status">
          <span className="status-dot status-dot--connected"></span>
          Connected to game
        </div>
        
        <div className="game-stats">
          <span className="stat">
            <span className="stat-label">Deck:</span>
            <span className="stat-value">{deck_size}</span>
          </span>
          <span className="stat">
            <span className="stat-label">Turn:</span>
            <span className="stat-value">{turn_count}</span>
          </span>
          <span className="stat">
            <span className="stat-label">Players:</span>
            <span className="stat-value">{players?.length || 0}</span>
          </span>
        </div>
      </div>
    </div>
  );
};

export default GameBoard; 