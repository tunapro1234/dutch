import React, { useState, useEffect, useCallback } from 'react';
import GameBoard from './components/GameBoard';
import './App.css';

// Game modes
const GAME_MODES = {
  AI_VS_AI: 'ai_vs_ai',
  HUMAN_VS_AI: 'human_vs_ai',
  HUMAN_VS_HUMAN: 'human_vs_human',
  REAL_LIFE: 'real_life'
};

function App() {
  const [gameState, setGameState] = useState(null);
  const [players, setPlayers] = useState([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedMode, setSelectedMode] = useState(null);
  const [gameInitialized, setGameInitialized] = useState(false);
  const [humanPlayer, setHumanPlayer] = useState(null);
  const [pendingAction, setPendingAction] = useState(null);

  // API base URL
  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:5001';

  // Check backend connection on load
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/health`);
        if (response.ok) {
          setConnected(true);
        }
      } catch (err) {
        setConnected(false);
      }
    };
    
    checkConnection();
    const interval = setInterval(checkConnection, 5000); // Check every 5 seconds
    return () => clearInterval(interval);
  }, [API_BASE]);

  // Fetch game state from backend
  const fetchGameState = useCallback(async () => {
    if (!connected) return;
    
    try {
      const response = await fetch(`${API_BASE}/api/game/state`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      const data = await response.json();
      
      setGameState(data.game_state || {});
      setPlayers(data.players || []);
      
      // Find human player
      const human = data.players?.find(p => p.is_human);
      setHumanPlayer(human);
      
      // Set pending action if waiting for human
      if (data.game_state?.pending_action) {
        setPendingAction(data.game_state.pending_action);
      } else {
        setPendingAction(null);
      }
      
      setError(null);
      
    } catch (err) {
      console.error('Failed to fetch game state:', err);
      setError(err.message);
    }
  }, [API_BASE, connected]);

  // Initialize game with selected mode
  const initializeGame = useCallback(async (mode) => {
    try {
      setLoading(true);
      setError(null);
      
      let playerConfigs = [];
      
      switch (mode) {
        case GAME_MODES.AI_VS_AI:
          playerConfigs = [
            { name: 'SmartBayes AI', type: 'ai', is_gym_player: true },
            { name: 'SimpleAI', type: 'ai', is_gym_player: false }
          ];
          break;
          
        case GAME_MODES.HUMAN_VS_AI:
          playerConfigs = [
            { name: 'You', type: 'human' },
            { name: 'SmartBayes AI', type: 'ai', is_gym_player: true }
          ];
          break;
          
        case GAME_MODES.HUMAN_VS_HUMAN:
          playerConfigs = [
            { name: 'Player 1', type: 'human' },
            { name: 'Player 2', type: 'human' }
          ];
          break;
          
        case GAME_MODES.REAL_LIFE:
          playerConfigs = [
            { name: 'Real Player 1', type: 'human' },
            { name: 'Real Player 2', type: 'human' },
            { name: 'Real Player 3', type: 'human' }
          ];
          break;
          
        default:
          throw new Error('Unknown game mode');
      }
      
      const response = await fetch(`${API_BASE}/api/game/init`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          players: playerConfigs,
          mode: mode
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to initialize game: ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('Game initialized:', data);
      
      setGameInitialized(true);
      
      // Fetch initial state
      await fetchGameState();
      
    } catch (err) {
      console.error('Failed to initialize game:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [API_BASE, fetchGameState]);

  // Handle human actions
  const handleHumanAction = useCallback(async (action, data = {}) => {
    try {
      const response = await fetch(`${API_BASE}/api/game/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action,
          ...data
        })
      });
      
      if (response.ok) {
        const result = await response.json();
        console.log('Action result:', result);
        
        // Clear pending action on successful action
        setPendingAction(null);
        
        // Refresh game state after action
        setTimeout(fetchGameState, 100);
        
        return result;
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Action failed');
      }
    } catch (err) {
      console.error('Failed to handle human action:', err);
      setError(err.message);
      return { error: err.message };
    }
  }, [API_BASE, fetchGameState]);

  // Handle card clicks
  const handleCardClick = useCallback(async (cardType) => {
    console.log('Card clicked:', cardType);
  }, []);

  // Handle player actions
  const handlePlayerAction = useCallback(async (action, data) => {
    console.log('Player action:', action, data);
    
    if (action === 'card_click' && data.player === humanPlayer?.name) {
      if (pendingAction && pendingAction.type === 'choose_action' && data.position !== undefined) {
        await handleHumanAction('replace', { position: data.position });
      }
    }
  }, [humanPlayer, pendingAction, handleHumanAction]);

  // Auto-refresh game state when game is running
  useEffect(() => {
    if (connected && gameInitialized) {
      const interval = setInterval(fetchGameState, 1000);
      return () => clearInterval(interval);
    }
  }, [connected, gameInitialized, fetchGameState]);

  // Reset game
  const resetGame = () => {
    setGameInitialized(false);
    setSelectedMode(null);
    setGameState(null);
    setPlayers([]);
    setHumanPlayer(null);
    setPendingAction(null);
    setError(null);
  };

  // Render connection error
  if (!connected) {
    return (
      <div className="app">
        <div className="app-error">
          <h2>🚫 Backend Not Connected</h2>
          <p>Cannot connect to backend server at {API_BASE}</p>
          <div className="error-details">
            <p>Make sure you started the game with:</p>
            <code>python dutch_gui.py</code>
          </div>
        </div>
      </div>
    );
  }

  // Render mode selection
  if (!selectedMode) {
    return (
      <div className="app">
        <div className="mode-selection">
          <h1>🃏 Dutch Cabo Card Game</h1>
          <h2>Choose Your Game Mode</h2>
          
          <div className="mode-grid">
            <div 
              className="mode-card mode-card--ai-vs-ai"
              onClick={() => setSelectedMode(GAME_MODES.AI_VS_AI)}
            >
              <div className="mode-icon">🤖</div>
              <h3>AI vs AI</h3>
              <p>Watch AI players compete against each other</p>
              <div className="mode-features">
                <span>• SmartBayes vs SimpleAI</span>
                <span>• Automatic gameplay</span>
                <span>• Learn strategies</span>
              </div>
            </div>
            
            <div 
              className="mode-card mode-card--human-vs-ai"
              onClick={() => setSelectedMode(GAME_MODES.HUMAN_VS_AI)}
            >
              <div className="mode-icon">🎯</div>
              <h3>Human vs AI</h3>
              <p>Play against smart AI opponents</p>
              <div className="mode-features">
                <span>• Interactive gameplay</span>
                <span>• Challenge yourself</span>
                <span>• Real-time decisions</span>
              </div>
            </div>
            
            <div 
              className="mode-card mode-card--human-vs-human"
              onClick={() => setSelectedMode(GAME_MODES.HUMAN_VS_HUMAN)}
            >
              <div className="mode-icon">🎭</div>
              <h3>Human vs Human</h3>
              <p>Play with friends on the same device</p>
              <div className="mode-features">
                <span>• 2 players</span>
                <span>• Turn-based</span>
                <span>• Social gaming</span>
              </div>
            </div>
            
            <div 
              className="mode-card mode-card--real-life"
              onClick={() => setSelectedMode(GAME_MODES.REAL_LIFE)}
            >
              <div className="mode-icon">🎮</div>
              <h3>Real Life Mode</h3>
              <p>Use as assistant for physical card game</p>
              <div className="mode-features">
                <span>• Track game state</span>
                <span>• Score calculation</span>
                <span>• Rule enforcement</span>
              </div>
            </div>
          </div>
          
          <div className="mode-info">
            <p>Click on a mode to start playing. Each mode offers a different experience!</p>
          </div>
        </div>
      </div>
    );
  }

  // Render loading state
  if (loading) {
    return (
      <div className="app">
        <div className="app-loading">
          <div className="loading-spinner"></div>
          <h2>Starting {getModeDisplayName(selectedMode)}...</h2>
          <p>Setting up the game</p>
          <button className="back-button" onClick={resetGame}>← Back to Mode Selection</button>
        </div>
      </div>
    );
  }

  // Render error state
  if (error && !gameInitialized) {
    return (
      <div className="app">
        <div className="app-error">
          <h2>🚫 Game Error</h2>
          <p>{error}</p>
          <div className="error-actions">
            <button className="retry-button" onClick={() => initializeGame(selectedMode)}>
              🔄 Try Again
            </button>
            <button className="back-button" onClick={resetGame}>
              ← Back to Mode Selection
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Initialize game if mode selected but not initialized
  if (selectedMode && !gameInitialized && !loading) {
    initializeGame(selectedMode);
    return (
      <div className="app">
        <div className="app-loading">
          <div className="loading-spinner"></div>
          <h2>Initializing...</h2>
        </div>
      </div>
    );
  }

  // Render main game interface
  return (
    <div className="app">
      <div className="game-header">
        <h1>🃏 Dutch Cabo - {getModeDisplayName(selectedMode)}</h1>
        <button className="mode-reset-button" onClick={resetGame}>
          🔄 Change Mode
        </button>
      </div>
      
      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
        </div>
      )}
      
      <GameBoard 
        gameState={gameState}
        players={players}
        onCardClick={handleCardClick}
        onPlayerAction={handlePlayerAction}
      />
      
      {renderGameControls()}
    </div>
  );

  // Helper functions
  function getModeDisplayName(mode) {
    switch (mode) {
      case GAME_MODES.AI_VS_AI: return 'AI vs AI';
      case GAME_MODES.HUMAN_VS_AI: return 'Human vs AI';
      case GAME_MODES.HUMAN_VS_HUMAN: return 'Human vs Human';
      case GAME_MODES.REAL_LIFE: return 'Real Life Mode';
      default: return 'Unknown Mode';
    }
  }

  function renderGameControls() {
    if (selectedMode === GAME_MODES.AI_VS_AI) {
      // AI vs AI - just show game status
      return (
        <div className="game-controls">
          <div className="ai-game-status">
            <h3>🤖 AI Game in Progress</h3>
            <p>Watch the AI players compete!</p>
            {gameState?.game_status === 'ended' && (
              <button className="new-game-button" onClick={() => initializeGame(selectedMode)}>
                🎮 Start New Game
              </button>
            )}
          </div>
        </div>
      );
    }

    if (selectedMode === GAME_MODES.HUMAN_VS_AI && humanPlayer) {
      return renderHumanControls();
    }

    if (selectedMode === GAME_MODES.HUMAN_VS_HUMAN) {
      return renderHumanVsHumanControls();
    }

    if (selectedMode === GAME_MODES.REAL_LIFE) {
      return renderRealLifeControls();
    }

    return null;
  }

  function renderHumanControls() {
    if (!humanPlayer || gameState?.game_status === 'ended') {
      return (
        <div className="game-controls">
          <div className="game-ended">
            <h3>🏁 Game Ended</h3>
            <p>Final Score: {humanPlayer?.score || 0}</p>
            <button className="new-game-button" onClick={() => initializeGame(selectedMode)}>
              🎮 Play Again
            </button>
          </div>
        </div>
      );
    }

    const isHumanTurn = gameState?.is_human_turn;
    const waitingForHuman = gameState?.waiting_for_human;

    if (!isHumanTurn) {
      return (
        <div className="game-controls">
          <div className="turn-status turn-status--waiting">
            <h3>⏳ AI Turn</h3>
            <p>Current Player: {gameState?.current_player}</p>
            <div className="waiting-animation">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          </div>
        </div>
      );
    }

    if (waitingForHuman && pendingAction) {
      const drawnCard = pendingAction.drawn_card;
      
      return (
        <div className="game-controls">
          <div className="human-action-controls">
            <h3>🎯 Your Turn!</h3>
            <p>You drew: <strong>{drawnCard}</strong></p>
            
            <div className="action-buttons">
              <button 
                className="control-button control-button--discard"
                onClick={() => handleHumanAction('discard')}
              >
                🗑️ Discard Card
              </button>
              
              <button 
                className="control-button control-button--dutch"
                onClick={() => handleHumanAction('call_dutch')}
              >
                🇳🇱 Call DUTCH!
              </button>
            </div>
            
            <div className="replace-instruction">
              <p>💡 Or click on one of your cards to replace it!</p>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="game-controls">
        <div className="turn-status">
          <h3>🎯 Your Turn!</h3>
          <p>Waiting for your action...</p>
        </div>
      </div>
    );
  }

  function renderHumanVsHumanControls() {
    return (
      <div className="game-controls">
        <div className="human-vs-human-controls">
          <h3>🎭 Human vs Human</h3>
          <p>Current Player: {gameState?.current_player}</p>
          {gameState?.game_status === 'ended' && (
            <button className="new-game-button" onClick={() => initializeGame(selectedMode)}>
              🎮 Play Again
            </button>
          )}
        </div>
      </div>
    );
  }

  function renderRealLifeControls() {
    return (
      <div className="game-controls">
        <div className="real-life-controls">
          <h3>🎮 Real Life Assistant</h3>
          <p>Use this interface to track your physical card game</p>
          <div className="assistant-features">
            <span>• Score tracking</span>
            <span>• Rule reminders</span>
            <span>• Turn management</span>
          </div>
        </div>
      </div>
    );
  }
}

export default App; 