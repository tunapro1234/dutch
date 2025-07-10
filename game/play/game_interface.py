from typing import Dict, Any, List

from ..engine.game_engine import GameEngine
from ..engine.player_base import PlayerBase
from .human_player import HumanPlayer


class GameInterface:
    """Handles all UI and display elements for human players"""
    
    def __init__(self, engine: GameEngine):
        self.engine = engine
    
    def display_game_start(self, setup_results: Dict[str, Any]):
        """Display game start information"""
        print(f"\n{'='*50}")
        print(f"Starting New Game")
        print(f"{'='*50}")
        
        print(f"Starting player: {setup_results['starting_player']}")
        print(f"Deck size: {setup_results['deck_size']}")
        print(f"Top discard: {setup_results['discard_top']}")
        
        print("\nInitial peeks:")
        for player_name, peek_info in setup_results['initial_peeks'].items():
            print(f"{player_name} peeked at position {peek_info['position']}: {peek_info['card']}")
    
    def display_game_state(self, current_player: PlayerBase):
        """Display the current game state"""
        print(f"\n{'='*60}")
        print(f"Turn {self.engine.turn_count + 1} - {current_player.name}'s Turn")
        print(f"{'='*60}")
        
        # Show players' hands (only show known cards for others)
        for player in self.engine.players:
            if player == current_player and isinstance(player, HumanPlayer):
                print(f"YOUR HAND: {player.display_hand()}")
            else:
                # For opponents, only show cards that are publicly known or empty slots
                hidden_hand = []
                for i, card in enumerate(player.hand):
                    if card is None:
                        hidden_hand.append("[ ]")
                    else:
                        hidden_hand.append("[?]")  # Always hidden unless publicly revealed
                hand_display = " ".join(hidden_hand)
                print(f"{player.name}: {hand_display} ({player.get_hand_size()} cards)")
        
        top_discard = self.engine.discard_pile[-1] if self.engine.discard_pile else None
        print(f"\nTop discard: {top_discard}")
        print(f"Cards left in deck: {len(self.engine.deck)}")
        
        # Show Dutch call status
        if self.engine.dutch_called and self.engine.dutch_caller:
            print(f"🚨 DUTCH CALLED by {self.engine.dutch_caller.name}! Final round in progress.")
        elif self.engine.final_round:
            print("🏁 Final round - game ending soon!")
    
    def display_turn_start(self, player_name: str, turn_number: int):
        """Display turn start information"""
        print(f"\n{'='*60}")
        print(f"Turn {turn_number} - {player_name}'s Turn")
        print(f"{'='*60}")
    
    def display_matching_cards_opportunity(self, player_name: str, discarded_cards: List[str], timing: str):
        """Display information about matching cards being discarded"""
        if discarded_cards:
            timing_msg = "before drawing" if timing == "before_draw" else "after turn actions"
            print(f"🎯 {player_name} discarded matching cards {discarded_cards} {timing_msg}")
            print(f"Cards eliminated: {len(discarded_cards)}")
    
    def display_card_draw(self, player_name: str, drawn_card: str, drawn_from_discard: bool):
        """Display card drawing information"""
        if drawn_from_discard:
            print(f"\n{player_name} draws {drawn_card} from discard pile")
        else:
            print(f"\n{player_name} draws from deck...")
            # Only show the card to human players
            for player in self.engine.players:
                if isinstance(player, HumanPlayer) and player.name == player_name:
                    print(f"You drew: {drawn_card}")
    
    def display_action_result(self, player_name: str, action_result: Dict[str, Any]):
        """Display the result of a player's action"""
        action_type = action_result.get("action")
        success = action_result.get("success", True)
        
        if not success:
            error = action_result.get("error", "Unknown error")
            print(f"❌ {player_name}: {error}")
            return
        
        if action_type == "discard":
            discarded_card = action_result.get("discarded_card")
            print(f"{player_name} discarded {discarded_card}")
            
        elif action_type == "swap":
            swapped_card = action_result.get("swapped_card")
            position = action_result.get("position")
            print(f"{player_name} swapped for {swapped_card} at position {position}")
            
            # Handle special ability after swap
            if "special_ability_used" in action_result:
                self.display_special_ability_result(player_name, action_result["special_ability_used"])
                
        elif action_type == "use_ability":
            if "jack_result" in action_result:
                self.display_jack_result(player_name, action_result["jack_result"])
            elif "queen_result" in action_result:
                self.display_queen_result(player_name, action_result["queen_result"])
                
        elif action_type == "call_dutch":
            if action_result.get("dutch_called"):
                remaining_turns = action_result.get("remaining_turns", 0)
                print(f"\n🚨 {player_name} called DUTCH! Final round begins!")
                print(f"All other players ({remaining_turns}) get one more turn.")
    
    def display_special_ability_result(self, player_name: str, ability_result: Dict[str, Any]):
        """Display special ability usage results"""
        if ability_result.get("ability_used"):
            if "jack_result" in ability_result:
                self.display_jack_result(player_name, ability_result["jack_result"])
            elif "queen_result" in ability_result:
                self.display_queen_result(player_name, ability_result["queen_result"])
        else:
            print(f"✨ {player_name} swapped out a special card but didn't use its ability")
    
    def display_jack_result(self, player_name: str, jack_result: Dict[str, Any]):
        """Display Jack ability results"""
        if jack_result.get("error"):
            print(f"❌ Jack ability failed: {jack_result['error']}")
            return
            
        if jack_result.get("swap_performed"):
            target_player = jack_result.get("target_player")
            player_card = jack_result.get("player_card")
            opponent_card = jack_result.get("opponent_card")
            own_position = jack_result.get("own_position")
            target_position = jack_result.get("target_position")
            
            print(f"✨ {player_name} used Jack to swap with {target_player}")
            
            # Show different information to different players
            for player in self.engine.players:
                if isinstance(player, HumanPlayer):
                    if player.name == player_name:
                        print(f"You gave {player_card} and received {opponent_card}")
                    elif player.name == target_player:
                        print(f"{player_name} swapped with you!")
                        print(f"You gave away a card from position {target_position}")
                        print(f"You received a face-down card at position {target_position}")
                        print("(Use Queen to peek at what you received)")
                    else:
                        print(f"{player_name} swapped cards with {target_player}")
    
    def display_queen_result(self, player_name: str, queen_result: Dict[str, Any]):
        """Display Queen ability results"""
        if not queen_result.get("peek_performed"):
            return
            
        target = queen_result.get("target")
        position = queen_result.get("position")
        peeked_card = queen_result.get("peeked_card")
        
        if target == "self":
            # Show peek result only to the player who peeked
            for player in self.engine.players:
                if isinstance(player, HumanPlayer) and player.name == player_name:
                    print(f"\n👁️ You secretly looked at your card at position {position}: {peeked_card}")
                    input("Press Enter to continue (card is now hidden again)...")
                elif player.name != player_name:
                    print(f"{player_name} peeked at their own card at position {position}")
        else:
            # Peeking at opponent's card
            target_player_name = queen_result.get("target")
            for player in self.engine.players:
                if isinstance(player, HumanPlayer) and player.name == player_name:
                    print(f"\n👁️ You secretly looked at {target_player_name}'s card at position {position}: {peeked_card}")
                    input("Press Enter to continue (only you saw this card)...")
                elif player.name != player_name:
                    print(f"{player_name} peeked at {target_player_name}'s card at position {position}")
    
    def display_turn_skipped(self, player_name: str, reason: str):
        """Display information about a skipped turn"""
        print(f"⏭️ Skipping {player_name}'s turn ({reason})")
    
    def display_final_round_progress(self):
        """Display final round progress information"""
        if self.engine.final_round and self.engine.dutch_caller:
            remaining_turns = (len(self.engine.players) - 1) - self.engine.turns_after_dutch
            if remaining_turns > 0:
                print(f"⏳ Final round: {remaining_turns} more turn(s) until game ends")
    
    def display_game_end(self, final_results: Dict[str, Any]):
        """Display final game results"""
        print(f"\n{'='*60}")
        print("GAME OVER!")
        print(f"{'='*60}")
        
        winner = final_results.get("winner")
        if winner:
            print(f"🎉 {winner} wins!")
        
        print("\nFinal Scores:")
        final_scores = final_results.get("final_scores", {})
        player_hands = final_results.get("player_hands", {})
        
        for player_name, score in final_scores.items():
            hand_display = player_hands.get(player_name, "")
            print(f"{player_name}: {score} points")
            print(f"  Final hand: {hand_display}")
        
        # Show ranking
        ranking = final_results.get("ranking", [])
        print(f"\nRanking:")
        for i, (name, score) in enumerate(ranking, 1):
            print(f"{i}. {name} - {score} points")
    
    def display_error(self, error_message: str):
        """Display error messages"""
        print(f"❌ Error: {error_message}")
    
    def display_info(self, info_message: str):
        """Display informational messages"""
        print(f"ℹ️ {info_message}")
    
    def get_user_confirmation(self, message: str) -> bool:
        """Get yes/no confirmation from user"""
        while True:
            response = input(f"{message} (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' or 'n'")
    
    def pause_for_user(self, message: str = "Press Enter to continue..."):
        """Pause execution until user presses Enter"""
        input(message) 