from typing import List

from ..engine.game_engine import GameEngine
from ..engine.player_base import PlayerBase
from .game_interface import GameInterface
from .human_player import HumanPlayer


class GameRunner:
    """Complete game runner that combines engine and interface"""
    
    def __init__(self, players: List[PlayerBase]):
        """
        Initialize the game runner.
        
        Args:
            players: List of PlayerBase objects (mix of humans and AIs)
        """
        self.engine = GameEngine(players)
        self.interface = GameInterface(self.engine)
        
    def play_game(self):
        """Play a complete game with UI - no error handling, let crashes happen"""
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