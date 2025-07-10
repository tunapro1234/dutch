"""
Flask API server for Dutch Cabo advanced GUI
"""

import sys
import os
import threading
import time
from flask import Flask, jsonify, request
from flask_cors import CORS

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

try:
    from game.engine.game_engine import GameEngine
    from game.engine.player_base import PlayerBase
    from players.bayes.smart_bayes import SmartBayesPlayer
    from players.simple_ai import SimpleAI
    from players.bayes_player import BayesPlayer
except ImportError as e:
    print(f"Warning: Could not import game modules: {e}")
    print("API will run in limited mode")


class APIHumanPlayer(PlayerBase):
    """Non-blocking human player for API interactions"""
    
    def __init__(self, name):
        super().__init__(name)
        self.is_human = True
        self.is_gym_player = False
        self.pending_action = None
        self.action_result = None
        self.waiting_for_action = False
        
    def choose_initial_peek(self):
        """Choose initial card to peek at (API will handle this)"""
        # Return 0 as default, frontend will handle the actual choice
        return 0
        
    def choose_action(self, drawn_card, game_state):
        """Choose what to do with drawn card (API will handle this)"""
        # Set waiting state
        self.waiting_for_action = True
        self.pending_action = {
            'type': 'choose_action',
            'drawn_card': str(drawn_card),
            'game_state': game_state
        }
        
        # Wait for API response (with timeout)
        timeout = 30  # 30 seconds timeout
        start_time = time.time()
        
        while self.waiting_for_action and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if self.waiting_for_action:
            # Timeout - return default action
            self.waiting_for_action = False
            return {"action": "discard", "position": None}
        
        return self.action_result or {"action": "discard", "position": None}
    
    def choose_swap_target(self, opponents, game_state):
        """Choose which opponent and position to swap with (when using Jack)"""
        # Default: swap with first opponent's first card
        if opponents:
            return (opponents[0], 0)
        return (None, 0)
    
    def choose_peek_target(self, opponents, game_state):
        """Choose which card to peek at (when using Queen)"""
        # Default: peek at own first card
        return (None, 0)
    
    def set_action_result(self, result):
        """Set the result of the pending action"""
        self.action_result = result
        self.waiting_for_action = False


class GameAPIServer:
    """API Server for Dutch Cabo game"""
    
    def __init__(self):
        self.game_engine = None
        self.players = []
        self.game_thread = None
        self.game_running = False
        self.turn_delay = 1.5  # Seconds between AI turns
        self.human_player = None
        self.waiting_for_human = False
        
    def initialize_game(self, player_configs):
        """Initialize new game with given player configurations"""
        try:
            # Create players
            self.players = []
            self.human_player = None
            
            for config in player_configs:
                player_type = config.get('type', 'ai')
                name = config.get('name', 'Player')
                is_gym = config.get('is_gym_player', False)
                
                if player_type == 'human':
                    # Create API human player
                    player = APIHumanPlayer(name)
                    self.human_player = player
                    self.players.append(player)
                elif player_type == 'ai':
                    # Determine AI type based on name
                    if 'Smart' in name:
                        player = SmartBayesPlayer(name)
                    elif 'Simple' in name:
                        player = SimpleAI(name)
                    else:
                        player = BayesPlayer(name)
                    
                    # Add gym player flag as attribute
                    setattr(player, 'is_gym_player', is_gym)
                    setattr(player, 'is_human', False)
                    self.players.append(player)
            
            # Create game engine
            self.game_engine = GameEngine(self.players)
            
            # Setup game (this should not block now)
            setup_results = self.game_engine.setup_new_game()
            
            # Start auto-play thread
            if not self.game_running:
                self.game_running = True
                self.game_thread = threading.Thread(target=self._auto_play_loop, daemon=True)
                self.game_thread.start()
            
            return {
                'success': True,
                'message': 'Game initialized successfully',
                'setup_results': setup_results,
                'players': len(self.players),
                'human_player': self.human_player.name if self.human_player else None
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_game_state(self):
        """Get current game state for frontend"""
        if not self.game_engine:
            return {
                'error': 'Game not initialized'
            }
        
        try:
            current_player = self.game_engine.get_current_player()
            
            # Check if waiting for human action
            is_human_turn = current_player == self.human_player if self.human_player else False
            waiting_for_human = (is_human_turn and 
                               isinstance(current_player, APIHumanPlayer) and 
                               current_player.waiting_for_action)
            
            # Game state
            game_state = {
                'turn_count': getattr(self.game_engine, 'turn_count', 0),
                'current_player': current_player.name if current_player else '',
                'dutch_called': getattr(self.game_engine, 'dutch_called', False),
                'deck_size': len(getattr(self.game_engine, 'deck', [])),
                'top_discard': str(self.game_engine.discard_pile[-1]) if (hasattr(self.game_engine, 'discard_pile') and self.game_engine.discard_pile) else None,
                'game_status': 'ended' if getattr(self.game_engine, 'game_over', False) else 'playing',
                'is_human_turn': is_human_turn,
                'waiting_for_human': waiting_for_human,
                'pending_action': self._serialize_pending_action(getattr(current_player, 'pending_action', None)) if is_human_turn else None
            }
            
            # Players data
            players_data = []
            for player in self.players:
                # Safely convert hand to strings
                hand_strings = []
                for card in player.hand:
                    if card is None:
                        hand_strings.append(None)
                    else:
                        hand_strings.append(str(card))
                
                player_data = {
                    'name': player.name,
                    'hand': hand_strings,
                    'known_cards': getattr(player, 'known_cards', [False] * len(player.hand)),
                    'score': player.get_score(),
                    'hand_size': player.get_hand_size(),
                    'is_gym_player': getattr(player, 'is_gym_player', False),
                    'is_human': getattr(player, 'is_human', False)
                }
                players_data.append(player_data)
            
            return {
                'game_state': game_state,
                'players': players_data
            }
            
        except Exception as e:
            return {
                'error': f'Failed to get game state: {str(e)}'
            }
    
    def _auto_play_loop(self):
        """Auto-play loop for AI turns, pause for human turns"""
        while self.game_running and self.game_engine and not getattr(self.game_engine, 'game_over', False):
            try:
                current_player = self.game_engine.get_current_player()
                
                # If it's human turn and they're waiting for action, skip this iteration
                if (current_player == self.human_player and 
                    isinstance(current_player, APIHumanPlayer) and 
                    current_player.waiting_for_action):
                    time.sleep(0.1)
                    continue
                
                # Play one turn
                turn_result = self.game_engine.play_turn()
                
                # Check if game ended
                if turn_result.get("game_ended") or getattr(self.game_engine, 'game_over', False):
                    self.game_running = False
                    break
                
                # Wait before next turn (shorter for better responsiveness)
                time.sleep(self.turn_delay)
                
            except Exception as e:
                print(f"Error in auto-play loop: {e}")
                break
        
        self.game_running = False
    
    def _serialize_pending_action(self, pending_action):
        """Serialize pending action to ensure JSON compatibility"""
        if pending_action is None:
            return None
        
        # Create a copy and ensure all values are JSON serializable
        serialized = {}
        for key, value in pending_action.items():
            if hasattr(value, '__str__'):
                serialized[key] = str(value)
            else:
                serialized[key] = value
        
        return serialized
    
    def handle_human_action(self, action_data):
        """Handle human player action"""
        if not self.human_player or not hasattr(self.human_player, 'waiting_for_action'):
            return {'error': 'No human player or not waiting for action'}
        
        if not self.human_player.waiting_for_action:
            return {'error': 'Not waiting for human action'}
        
        try:
            action = action_data.get('action')
            
            if action == 'discard':
                # Human chooses to discard the drawn card
                result = {"action": "discard", "position": None}
                self.human_player.set_action_result(result)
                return {'success': True, 'message': 'Discarded drawn card'}
                
            elif action == 'replace':
                # Human chooses to replace a card
                position = action_data.get('position', 0)
                result = {"action": "replace", "position": position}
                self.human_player.set_action_result(result)
                return {'success': True, 'message': f'Replaced card at position {position}'}
                
            elif action == 'call_dutch':
                # Human calls Dutch
                result = {"action": "call_dutch", "position": None}
                self.human_player.set_action_result(result)
                return {'success': True, 'message': 'Called DUTCH!'}
                
            else:
                return {'error': f'Unknown action: {action}'}
                
        except Exception as e:
            return {'error': f'Action failed: {str(e)}'}
    
    def handle_action(self, action_data):
        """Handle action from frontend"""
        if not self.game_engine:
            return {'error': 'Game not initialized'}
        
        try:
            action = action_data.get('action')
            
            # Check if it's a human action
            if action in ['discard', 'replace', 'call_dutch']:
                return self.handle_human_action(action_data)
            
            elif action == 'card_click':
                # Handle card click (for future interactivity)
                card_type = action_data.get('card_type')
                return {'success': True, 'message': f'Clicked on {card_type}'}
            
            elif action == 'reset_game':
                # Reset the game
                self.game_running = False
                if self.game_thread:
                    self.game_thread.join(timeout=1)
                
                self.game_engine = None
                self.players = []
                self.human_player = None
                
                return {'success': True, 'message': 'Game reset'}
            
            else:
                return {'error': f'Unknown action: {action}'}
                
        except Exception as e:
            return {'error': f'Action failed: {str(e)}'}


# Global game server instance
game_server = GameAPIServer()


def create_app():
    """Create Flask app with API routes"""
    app = Flask(__name__)
    CORS(app)  # Enable CORS for React frontend
    
    @app.route('/api/game/init', methods=['POST'])
    def init_game():
        """Initialize new game"""
        data = request.get_json() or {}
        player_configs = data.get('players', [
            {'name': 'Human Player', 'type': 'human'},
            {'name': 'SmartBayes AI', 'type': 'ai', 'is_gym_player': True}
        ])
        
        result = game_server.initialize_game(player_configs)
        return jsonify(result)
    
    @app.route('/api/game/state', methods=['GET'])
    def get_state():
        """Get current game state"""
        result = game_server.get_game_state()
        return jsonify(result)
    
    @app.route('/api/game/action', methods=['POST'])
    def handle_action():
        """Handle game action"""
        data = request.get_json() or {}
        result = game_server.handle_action(data)
        return jsonify(result)
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'game_initialized': game_server.game_engine is not None,
            'game_running': game_server.game_running,
            'has_human_player': game_server.human_player is not None
        })
    
    @app.route('/', methods=['GET'])
    def index():
        """API info"""
        return jsonify({
            'name': 'Dutch Cabo API',
            'version': '1.0.0',
            'description': 'Backend API for Dutch Cabo advanced GUI',
            'endpoints': {
                'POST /api/game/init': 'Initialize new game',
                'GET /api/game/state': 'Get current game state',
                'POST /api/game/action': 'Handle game action',
                'GET /api/health': 'Health check'
            }
        })
    
    return app


def run_server(host='localhost', port=5001, debug=False):
    """Run the Flask server"""
    app = create_app()
    
    print(f"🚀 Starting Dutch Cabo API server...")
    print(f"📡 Server will run on http://{host}:{port}")
    print(f"🎮 React app should connect to this URL")
    print(f"📊 Health check: http://{host}:{port}/api/health")
    print("=" * 50)
    
    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")


if __name__ == '__main__':
    run_server(debug=True) 