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
            
        # DEBUG MODE: Show AI knowledge and reasoning
        if hasattr(self, 'debug_mode') and self.debug_mode:
            self._display_debug_info(current_player)
    
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
                
        # DEBUG MODE: Show AI reasoning for this action
        if hasattr(self, 'debug_mode') and self.debug_mode and action_type:
            self._display_action_reasoning(player_name, action_type, action_result)
    
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
    
    def _display_debug_info(self, current_player: PlayerBase):
        """Display debug information about AI knowledge and reasoning"""
        print(f"\n{'🔍 DEBUG INFO':=^60}")
        
        # Find AI and Human players
        ai_players = [p for p in self.engine.players if not isinstance(p, HumanPlayer)]
        human_players = [p for p in self.engine.players if isinstance(p, HumanPlayer)]
        
        if not ai_players or not human_players:
            print("❌ Debug mode requires Human vs AI setup")
            return
            
        ai_player = ai_players[0]
        human_player = human_players[0]
        
        # Show AI's knowledge about its own hand
        print(f"\n🤖 {ai_player.name}'s Knowledge:")
        print("Own hand:")
        for i, card in enumerate(ai_player.hand):
            if card is None:
                print(f"  Position {i}: [ EMPTY ]")
            elif ai_player.known_cards[i]:
                print(f"  Position {i}: {card} ✅ (KNOWN)")
            else:
                print(f"  Position {i}: {card} ❓ (UNKNOWN to AI)")
        
        # Show what AI knows about human's hand
        print(f"\n👤 What {ai_player.name} knows about {human_player.name}'s hand:")
        for i, card in enumerate(human_player.hand):
            if card is None:
                print(f"  Position {i}: [ EMPTY ] ✅")
            else:
                # Check if AI has any knowledge about this card
                ai_knows = False
                known_info = "❓ Unknown"
                
                # For BayesPlayer, check if they have specific knowledge
                if hasattr(ai_player, 'opponent_card_knowledge'):
                    if human_player.name in ai_player.opponent_card_knowledge:
                        if i in ai_player.opponent_card_knowledge[human_player.name]:
                            knowledge = ai_player.opponent_card_knowledge[human_player.name][i]
                            if knowledge.get('known', False):
                                ai_knows = True
                                known_info = f"✅ Knows: {knowledge.get('card', 'Unknown')}"
                
                print(f"  Position {i}: {card} → {known_info}")
        
        # Show AI's strategy reasoning if available
        if hasattr(ai_player, 'get_strategy_info'):
            strategy_info = ai_player.get_strategy_info()
            if strategy_info:
                print(f"\n🧠 {ai_player.name}'s Current Strategy:")
                print(f"  {strategy_info}")
        
        # Show probability calculations for BayesPlayer
        if hasattr(ai_player, 'card_probabilities'):
            print(f"\n📊 {ai_player.name}'s Card Probability Estimates:")
            print("Own hand probabilities:")
            for i, probs in enumerate(ai_player.card_probabilities):
                if ai_player.hand[i] is not None and not ai_player.known_cards[i]:
                    top_values = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:3]
                    prob_str = ", ".join([f"{val}:{prob:.1%}" for val, prob in top_values])
                    print(f"  Position {i}: {prob_str}")
        
        print("="*60) 
    
    def _display_action_reasoning(self, player_name: str, action_type: str, action_result: Dict[str, Any]):
        """Display AI reasoning for their action choice"""
        # Only show for AI players
        ai_player = None
        for player in self.engine.players:
            if player.name == player_name and not isinstance(player, HumanPlayer):
                ai_player = player
                break
                
        if not ai_player:
            return  # Skip for human players
            
        print(f"\n🧠 {player_name}'s Reasoning:")
        
        if action_type == "discard":
            print(f"  💭 Decided to discard instead of swapping")
            print(f"  📝 Likely reasons: Drew high-value card, or satisfied with current hand")
            
        elif action_type == "swap":
            position = action_result.get("position", "?")
            swapped_card = action_result.get("swapped_card", "?")
            print(f"  💭 Swapped at position {position}, removed {swapped_card}")
            
            # Try to get reasoning from AI if available
            if hasattr(ai_player, 'last_decision_reason'):
                print(f"  📝 AI says: {ai_player.last_decision_reason}")
            else:
                print(f"  📝 Likely improved hand value by removing {swapped_card}")
                
        elif action_type == "use_ability":
            print(f"  💭 Used special card ability")
            if "jack_result" in action_result:
                jack_result = action_result["jack_result"]
                if jack_result.get("swap_performed"):
                    target = jack_result.get("target_player", "?")
                    print(f"  📝 Jack swap with {target} to gain information or improve position")
            elif "queen_result" in action_result:
                queen_result = action_result["queen_result"]
                if queen_result.get("peek_performed"):
                    target = queen_result.get("target", "?")
                    print(f"  📝 Queen peek at {target} to gather information")
                    
        elif action_type == "call_dutch":
            print(f"  💭 Called DUTCH to end the game")
            print(f"  📝 AI believes it has the lowest score")
            
        # Show score analysis if available
        if hasattr(ai_player, 'get_score'):
            current_score = ai_player.get_score()
            print(f"  📊 Current estimated score: {current_score}")
            
        print("  " + "-"*40) 