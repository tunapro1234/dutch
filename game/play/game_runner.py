from typing import List, Optional

from ..engine.game_engine import GameEngine
from ..engine.player_base import PlayerBase
from .game_interface import GameInterface
from .human_player import HumanPlayer
from players.simple_ai import SimpleAI
from players.bayes_player import BayesPlayer
from players.bayes.smart_bayes import SmartBayesPlayer


class GameRunner:
    """Complete game runner with 3 core modes: Single-player, Agent Battle, Real Life"""
    
    def __init__(self, players: Optional[List[PlayerBase]] = None):
        """
        Initialize the game runner.
        
        Args:
            players: Optional list of PlayerBase objects. If None, will be set per mode.
        """
        self.players = players
        self.engine = None
        self.interface = None
        
    def run_single_player(self, debug_mode=False):
        """Single-player mode: Human vs AI"""
        print("🎯 SINGLE-PLAYER MODE")
        print("-" * 40)
        print("You will play against a smart AI opponent!")
        print()
        
        # Choose AI difficulty
        print("Choose AI difficulty:")
        print("1. 🟢 Easy (SimpleAI)")
        print("2. 🟡 Medium (BayesPlayer)")
        print("3. 🔴 Hard (SmartBayes)")
        
        while True:
            try:
                choice = input("Enter choice (1-3): ").strip()
                if choice == "1":
                    ai_player = SimpleAI("AI Opponent")
                    difficulty = "Easy"
                    break
                elif choice == "2":
                    ai_player = BayesPlayer("AI Opponent")
                    difficulty = "Medium"
                    break
                elif choice == "3":
                    ai_player = SmartBayesPlayer("AI Opponent")
                    difficulty = "Hard"
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-3.")
            except (ValueError, EOFError, KeyboardInterrupt):
                print("\n👋 Returning to main menu...")
                return
        
        print(f"\n🎯 Playing against {difficulty} AI")
        print("-" * 30)
        
        # Setup players
        human_player = HumanPlayer("You")
        self.players = [human_player, ai_player]
        
        # Run the game
        self._setup_and_play(debug_mode=debug_mode)
        
    def run_agent_battle(self, player1_ai=None, player2_ai=None, num_games=1, interactive=True):
        """Agent Battle mode: AI vs AI with player selection"""
        print("🤖 AGENT BATTLE MODE")
        print("-" * 40)
        
        if interactive:
            print("Watch AI agents compete against each other!")
            print()
            
            # Available AI types
            ai_types = [
                (SimpleAI, "SimpleAI", "🟢 Basic strategy"),
                (BayesPlayer, "BayesPlayer", "🟡 Probabilistic reasoning"),
                (SmartBayesPlayer, "SmartBayes", "🔴 Advanced analytics")
            ]
            
            print("Available AI Agents:")
            for i, (ai_class, name, description) in enumerate(ai_types, 1):
                print(f"{i}. {name} - {description}")
            print()
            
            # Select agents
            agents = []
            for player_num in [1, 2]:
                while True:
                    try:
                        choice = input(f"Choose AI for Player {player_num} (1-3): ").strip()
                        if choice in ["1", "2", "3"]:
                            ai_class, ai_name, _ = ai_types[int(choice) - 1]
                            agent = ai_class(f"{ai_name} {player_num}")
                            agents.append(agent)
                            print(f"✅ Player {player_num}: {agent.name}")
                            break
                        else:
                            print("❌ Invalid choice. Please enter 1-3.")
                    except (ValueError, EOFError, KeyboardInterrupt):
                        print("\n👋 Returning to main menu...")
                        return
            
            print(f"\n🤖 Battle: {agents[0].name} vs {agents[1].name}")
            print("-" * 30)
            
            # Setup players and run single game
            self.players = agents
            self._setup_and_play()
            
        else:
            # Non-interactive mode with specified parameters
            if not player1_ai or not player2_ai:
                raise ValueError("player1_ai and player2_ai must be specified for non-interactive mode")
                
            print(f"Non-interactive battle: {player1_ai} vs {player2_ai} ({num_games} games)")
            print()
            
            # Map AI type strings to classes
            ai_mapping = {
                'simple': (SimpleAI, "SimpleAI"),
                'bayes': (BayesPlayer, "BayesPlayer"),
                'smart': (SmartBayesPlayer, "SmartBayesPlayer")
            }
            
            # Create AI agents
            ai1_class, ai1_name = ai_mapping[player1_ai]
            ai2_class, ai2_name = ai_mapping[player2_ai]
            
            agent1 = ai1_class(f"{ai1_name}_1")
            agent2 = ai2_class(f"{ai2_name}_2")
            
            print(f"🤖 Battle: {agent1.name} vs {agent2.name}")
            print(f"📊 Playing {num_games} game(s)")
            print("-" * 30)
            
            # Track results across games
            results = []
            for game_num in range(num_games):
                print(f"\n🎮 Game {game_num + 1}/{num_games}")
                print("-" * 20)
                
                # Setup players for this game
                self.players = [agent1, agent2]
                
                # Run the game
                self._setup_and_play()
                
                # Get and store results
                if self.engine:
                    final_results = self.engine.get_final_results()
                    results.append(final_results)
                else:
                    print("❌ Error: Game engine not properly initialized")
                    return
                
                # Display quick summary
                winner = final_results.get('winner', 'Unknown')
                winner_score = final_results.get('winner_score', 'Unknown')
                print(f"🏆 Game {game_num + 1} Winner: {winner} (Score: {winner_score})")
            
            # Display overall results summary
            if num_games > 1:
                self._display_battle_summary(results, agent1.name, agent2.name)
                
    def run_real_life_mode(self, interactive=True):
        """Real Life mode: AI assistant for physical card game"""
        print("🎮 REAL LIFE MODE")
        print("-" * 40)
        print("AI will assist you with strategy for your physical card game!")
        print()
        print("Instructions:")
        print("• Use real cards with friends")
        print("• AI will suggest moves and analyze the game")
        print("• Enter game state manually when prompted")
        print("• Follow AI recommendations in your physical game")
        print()
        
        if interactive:
            input("Press Enter when ready to start...")
        
        # Create human player with AI assistant
        print("\n🤖 AI Assistant activated!")
        print("AI will help you analyze the game and suggest optimal moves.")
        print("-" * 30)
        
        # For real life mode, create a special setup
        human_player = HumanPlayer("You (Real Life)")
        ai_assistant = SmartBayesPlayer("AI Assistant")
        
        # Mark the AI as assistant mode
        setattr(ai_assistant, 'assistant_mode', True)
        
        self.players = [human_player, ai_assistant]
        
        # Run the game with special real-life interface
        self._setup_and_play(real_life_mode=True)
        
    def _setup_and_play(self, real_life_mode=False, debug_mode=False):
        """Setup game engine and interface, then play"""
        # Ensure players are set
        if not self.players:
            raise ValueError("No players configured for the game")
            
        # Create engine and interface
        self.engine = GameEngine(self.players)
        self.interface = GameInterface(self.engine)
        
        if real_life_mode:
            setattr(self.interface, 'real_life_mode', True)
        if debug_mode:
            setattr(self.interface, 'debug_mode', True)
        
        # Setup game
        setup_results = self.engine.setup_new_game()
        self.interface.display_game_start(setup_results)
        
        # Main game loop
        while not self.engine.game_over:
            current_player = self.engine.get_current_player()
            
            # Display game state for human players
            if isinstance(current_player, HumanPlayer):
                self.interface.display_game_state(current_player)
            
            # Display final round progress
            self.interface.display_final_round_progress()
            
            # Play one turn
            turn_result = self.engine.play_turn()
            
            # Display turn results if turn was completed
            if turn_result.get("turn_completed"):
                self._display_turn_results(turn_result)
            elif turn_result.get("skipped"):
                reason = turn_result.get("reason", "Unknown reason")
                player_name = turn_result.get("player", "Unknown player")
                self.interface.display_turn_skipped(player_name, reason)
            
            # Check if game ended
            if turn_result.get("game_ended"):
                break
        
        # Display final results
        final_results = self.engine.get_final_results()
        self.interface.display_game_end(final_results)
    
    def _display_turn_results(self, turn_result):
        """Display the results of a completed turn"""
        if not self.interface or not self.engine:
            return
            
        player_name = turn_result.get("player", "Unknown")
        
        # Display matching cards discarded before drawing
        before_draw_discards = turn_result.get("before_draw_discards", [])
        self.interface.display_matching_cards_opportunity(
            player_name, before_draw_discards, "before_draw"
        )
        
        # Display card draw
        drawn_card = turn_result.get("drawn_card", "Unknown")
        drawn_from_discard = turn_result.get("drawn_from_discard", False)
        self.interface.display_card_draw(player_name, drawn_card, drawn_from_discard)
        
        # Display action result
        action_result = turn_result.get("action_result", {})
        self.interface.display_action_result(player_name, action_result)
        
        # Display matching cards discarded after turn
        after_turn_discards = turn_result.get("after_turn_discards", [])
        self.interface.display_matching_cards_opportunity(
            player_name, after_turn_discards, "after_turn"
        )
        
        # Brief pause for readability if human players are involved
        if any(isinstance(p, HumanPlayer) for p in self.engine.players):
            import time
            time.sleep(0.5)  # Small pause for readability 

    def _display_battle_summary(self, results, agent1_name, agent2_name):
        """Display summary of multiple agent battle games"""
        print(f"\n{'='*50}")
        print("🏆 BATTLE SUMMARY")
        print("="*50)
        
        agent1_wins = 0
        agent2_wins = 0
        total_games = len(results)
        
        for result in results:
            winner = result.get('winner', '')
            if agent1_name in winner:
                agent1_wins += 1
            elif agent2_name in winner:
                agent2_wins += 1
        
        print(f"📊 Total Games: {total_games}")
        print(f"🔥 {agent1_name}: {agent1_wins} wins ({agent1_wins/total_games*100:.1f}%)")
        print(f"🔥 {agent2_name}: {agent2_wins} wins ({agent2_wins/total_games*100:.1f}%)")
        
        if agent1_wins > agent2_wins:
            print(f"\n🏆 Overall Winner: {agent1_name}")
        elif agent2_wins > agent1_wins:
            print(f"\n🏆 Overall Winner: {agent2_name}")
        else:
            print(f"\n🤝 Result: Tie!")
        
        print("="*50) 