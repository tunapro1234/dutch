from typing import List, Optional, Tuple, Dict, Any
import random
from copy import deepcopy

from .card import Card, create_deck
from .player_base import PlayerBase


class GameEngine:
    """Pure game engine - no UI, just game logic for AI players"""
    
    def __init__(self, players: List[PlayerBase]):
        """
        Initialize a new game engine.
        
        Args:
            players: List of PlayerBase objects (must be 2-4 players)
        """
        if not 2 <= len(players) <= 4:
            raise ValueError("Game must have 2-4 players")
        
        self.players = players
        self.deck: List[Card] = []
        self.discard_pile: List[Card] = []
        self.current_player_index = 0
        self.game_over = False
        self.winner: Optional[PlayerBase] = None
        self.turn_count = 0
        self.dutch_called = False
        self.dutch_caller: Optional[PlayerBase] = None
        self.final_round = False
        self.turns_after_dutch = 0
        
        # Game settings
        self.max_rounds = 1
        
    def setup_new_game(self) -> Dict[str, Any]:
        """Set up a new game by shuffling deck and dealing cards"""
        # Reset game state
        self.deck = create_deck()
        random.shuffle(self.deck)
        self.discard_pile = []
        self.game_over = False
        self.winner = None
        self.turn_count = 0
        self.dutch_called = False
        self.dutch_caller = None
        self.final_round = False
        self.turns_after_dutch = 0
        
        # Reset all players
        for player in self.players:
            player.reset_for_new_game()
        
        # Deal 4 cards to each player
        for player in self.players:
            for position in range(4):
                card = self.deck.pop()
                player.receive_card(card, position)
        
        # Start discard pile with one card
        self.discard_pile.append(self.deck.pop())
        
        # Each player peeks at one card initially
        initial_peeks = {}
        for player in self.players:
            position = player.choose_initial_peek()
            peeked_card = player.peek_at_own_card(position)
            initial_peeks[player.name] = {"position": position, "card": str(peeked_card)}
        
        # Randomly choose starting player
        self.current_player_index = random.randint(0, len(self.players) - 1)
        
        return {
            "initial_peeks": initial_peeks,
            "starting_player": self.players[self.current_player_index].name,
            "deck_size": len(self.deck),
            "discard_top": str(self.discard_pile[-1]) if self.discard_pile else None
        }
    
    def get_current_player(self) -> PlayerBase:
        """Get the current player"""
        return self.players[self.current_player_index]
    
    def get_other_players(self, exclude_player: PlayerBase) -> List[PlayerBase]:
        """Get all players except the specified one"""
        return [p for p in self.players if p != exclude_player]
    
    def next_turn(self):
        """Move to the next player's turn"""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.turn_count += 1
        
        # Track turns after Dutch call (only count non-Dutch caller turns)
        if self.final_round:
            current_player = self.get_current_player()
            if current_player != self.dutch_caller:
                self.turns_after_dutch += 1
    
    def draw_card(self) -> Card:
        """Draw a card from the deck"""
        if not self.deck:
            # Reshuffle discard pile if deck is empty (keep top card)
            if len(self.discard_pile) <= 1:
                raise RuntimeError("No cards available to draw")
            
            top_card = self.discard_pile.pop()
            self.deck = self.discard_pile.copy()
            random.shuffle(self.deck)
            self.discard_pile = [top_card]
            
            # Update BayesPlayer deck composition after reshuffle
            for player in self.players:
                if hasattr(player, '_initialize_deck_tracking'):
                    # Reset deck tracking since deck was reshuffled
                    player.deck_composition = player._initialize_deck_tracking()
                    # Remove known discarded cards
                    if hasattr(player, 'discarded_cards'):
                        for discarded_card in player.discarded_cards:
                            value = discarded_card.get_score_value()
                            if value in player.deck_composition and player.deck_composition[value] > 0:
                                player.deck_composition[value] -= 1
        
        drawn_card = self.deck.pop()
        
        # Notify BayesPlayer about drawn card (they can observe it)
        for player in self.players:
            if hasattr(player, 'observe_card'):
                player.observe_card(drawn_card)
        
        return drawn_card
    
    def discard_card(self, card: Card):
        """Add a card to the discard pile"""
        self.discard_pile.append(card)
        
        # Notify BayesPlayer about discarded card
        for player in self.players:
            if hasattr(player, 'observe_discard'):
                player.observe_discard(card)
    
    def get_game_state(self) -> Dict[str, Any]:
        """Get current game state information (for AI decision making)"""
        return {
            "turn_count": self.turn_count,
            "current_player": self.get_current_player().name,
            "player_hand_sizes": {p.name: p.get_hand_size() for p in self.players},
            "top_discard": self.discard_pile[-1] if self.discard_pile else None,
            "deck_size": len(self.deck),
            "players": [{"name": p.name, "hand_size": p.get_hand_size(), "known_cards": sum(p.known_cards)} 
                       for p in self.players],
            "dutch_called": self.dutch_called,
            "dutch_caller": self.dutch_caller.name if self.dutch_caller else None,
            "final_round": self.final_round
        }
    
    def handle_matching_cards_opportunity(self, player: PlayerBase, timing: str) -> List[Card]:
        """Handle the opportunity to discard cards matching the top discard card"""
        discarded_cards = []
        
        # Only check for discard pile matches - NO MORE HAND DOUBLES
        if len(self.discard_pile) > 0:
            top_discard = self.discard_pile[-1]
            matches_available = player.get_discard_pile_matches(top_discard)
            
            if matches_available:
                positions_to_discard = player.want_to_discard_pile_matches(
                    matches_available, top_discard, timing, self.get_game_state()
                )
                
                if positions_to_discard:
                    # Sort positions in reverse order to avoid index issues
                    for pos in sorted(positions_to_discard, reverse=True):
                        if pos < len(player.hand) and player.hand[pos] is not None:
                            card = player.hand[pos]
                            discarded_cards.append(card)
                            player.hand[pos] = None
                            player.known_cards[pos] = False
                            self.discard_card(card)
                    
                    # Update BayesPlayer knowledge if present
                    for p in self.players:
                        if hasattr(p, 'observe_discard'):
                            for card in discarded_cards:
                                p.observe_discard(card)
        
        return discarded_cards
    
    def handle_card_draw(self, player: PlayerBase) -> Tuple[Card, bool]:
        """Handle the card drawing phase of a turn. Returns (card, drawn_from_discard)"""        
        # Check if drawing from discard is allowed
        can_draw_from_discard = (
            len(self.discard_pile) > 0 and 
            not self.discard_pile[-1].has_special_ability()
        )
        
        drawn_from_discard = False
        
        if can_draw_from_discard and hasattr(player, 'choose_draw_source'):
            # AI can choose if implemented
            draw_choice = player.choose_draw_source(self.discard_pile[-1], self.get_game_state())
            if draw_choice == "discard":
                drawn_card = self.discard_pile.pop()
                drawn_from_discard = True
            else:
                drawn_card = self.draw_card()
                drawn_from_discard = False
        else:
            # Default: draw from deck
            drawn_card = self.draw_card()
            drawn_from_discard = False
        
        return drawn_card, drawn_from_discard
    
    def handle_drawn_card_action(self, player: PlayerBase, drawn_card: Card, action: dict, drawn_from_discard: bool) -> Dict[str, Any]:
        """
        Handle the player's chosen action with the drawn card.
        
        Returns:
            Dictionary with action results and any errors
        """
        action_type = action["action"]
        result = {"action": action_type, "success": True, "error": None}
        
        if action_type == "discard":
            # Check if trying to discard a card drawn from discard pile
            if drawn_from_discard:
                result["success"] = False
                result["error"] = "Cannot discard card drawn from discard pile"
                return result
            else:
                # Normal discard from deck draw
                self.discard_card(drawn_card)
                result["discarded_card"] = str(drawn_card)
            
        elif action_type == "swap":
            # Swap drawn card with one in hand
            position = action["position"]
            old_card = player.swap_card(position, drawn_card)
            result["swapped_card"] = str(old_card)
            result["position"] = position
            
            # Update BayesPlayer knowledge about opponent actions
            for p in self.players:
                if hasattr(p, 'infer_from_opponent_action') and p != player:
                    p.infer_from_opponent_action(player.name, action)
            
            # Check if the swapped-out card has special abilities
            if old_card.has_special_ability():
                special_result = self.offer_special_ability_after_swap(player, old_card)
                result["special_ability_used"] = special_result
            else:
                self.discard_card(old_card)
            
        elif action_type == "use_ability":
            # Use special card ability
            if drawn_card.is_jack():
                ability_result = self.handle_jack_ability(player, drawn_card)
                result["jack_result"] = ability_result
            elif drawn_card.is_queen():
                ability_result = self.handle_queen_ability(player, drawn_card)
                result["queen_result"] = ability_result
            # Discard the special card after use
            self.discard_card(drawn_card)
            
        elif action_type == "call_dutch":
            # Player calls Dutch - finish the game after everyone else gets one more turn
            self.discard_card(drawn_card)
            self.dutch_called = True
            self.dutch_caller = player
            self.final_round = True
            self.turns_after_dutch = 0  # Reset counter
            remaining_players = len(self.players) - 1  # Everyone except Dutch caller
            result["dutch_called"] = True
            result["remaining_turns"] = remaining_players
        
        else:
            result["success"] = False
            result["error"] = f"Unknown action type: {action_type}"
        
        return result
    
    def offer_special_ability_after_swap(self, player: PlayerBase, special_card: Card) -> Dict[str, Any]:
        """Offer to use special ability of a card that was swapped out"""
        # Ask player if they want to use the special ability
        wants_to_use = player.want_to_use_special_ability_after_swap(special_card, self.get_game_state())
        
        if wants_to_use:
            if special_card.is_jack():
                ability_result = self.handle_jack_ability(player, special_card)
                ability_result["ability_used"] = True
                # Always discard after use
                self.discard_card(special_card)
                return ability_result
            elif special_card.is_queen():
                ability_result = self.handle_queen_ability(player, special_card)
                ability_result["ability_used"] = True
                # Always discard after use
                self.discard_card(special_card)
                return ability_result
        
        # Player chose not to use ability or no ability available
        self.discard_card(special_card)
        return {"ability_used": False}
    
    def handle_jack_ability(self, player: PlayerBase, jack_card: Card) -> Dict[str, Any]:
        """Handle Jack's swap ability"""
        opponents = self.get_other_players(player)
        if not opponents:
            return {"error": "No opponents to swap with"}
        
        # Choose which of your own cards to give away
        valid_positions = player.get_valid_positions()
        if not valid_positions:
            return {"error": "No cards to swap"}
        
        own_position = player.choose_own_swap_position(self.get_game_state())
        
        # Choose which opponent card to take
        target_player, target_position = player.choose_swap_target(opponents, self.get_game_state())
        
        # Perform the swap
        player_card = player.hand[own_position]
        opponent_card = target_player.hand[target_position]
        
        player.hand[own_position] = opponent_card
        target_player.hand[target_position] = player_card
        
        # Update known cards properly:
        # - The active player (who used Jack) always knows what they received
        player.known_cards[own_position] = True
        
        # - The target player loses knowledge of both cards
        target_player.known_cards[target_position] = False
        
        return {
            "swap_performed": True,
            "player_card": str(player_card),
            "opponent_card": str(opponent_card),
            "target_player": target_player.name,
            "own_position": own_position,
            "target_position": target_position
        }
    
    def handle_queen_ability(self, player: PlayerBase, queen_card: Card) -> Dict[str, Any]:
        """Handle Queen's peek ability"""
        opponents = self.get_other_players(player)
        target_player, target_position = player.choose_peek_target(opponents, self.get_game_state())
        
        if target_player is None:
            # Peek at own card
            peeked_card = player.peek_at_own_card(target_position)
            
            # Update BayesPlayer knowledge about opponent learning their own card
            for p in self.players:
                if hasattr(p, 'update_opponent_knowledge') and p != player:
                    p.update_opponent_knowledge(player.name, target_position, "peek")
                    
            return {
                "peek_performed": True,
                "target": "self",
                "position": target_position,
                "peeked_card": str(peeked_card)
            }
        else:
            # Peek at opponent's card
            peeked_card = target_player.hand[target_position]
            
            # Update BayesPlayer knowledge - player now knows opponent's card at position
            for p in self.players:
                if hasattr(p, 'update_opponent_knowledge') and p != player:
                    p.update_opponent_knowledge(player.name, target_position, "peek_opponent")
                    
            return {
                "peek_performed": True,
                "target": target_player.name,
                "position": target_position,
                "peeked_card": str(peeked_card) if peeked_card else None
            }
    
    def check_win_condition(self) -> Tuple[bool, Optional[PlayerBase]]:
        """
        Check if any player has won.
        Returns (game_ended, winner)
        """
        # Immediate win: empty hand
        for player in self.players:
            if player.is_hand_empty():
                self.winner = player
                self.game_over = True
                return True, player
        
        # Dutch call win condition
        if self.dutch_called and self.final_round:
            # Find player with lowest score
            lowest_score = float('inf')
            for player in self.players:
                score = player.get_score()
                if score < lowest_score:
                    lowest_score = score
                    self.winner = player
            
            self.game_over = True
            return True, self.winner
        
        # Fallback: turn limit reached
        if self.turn_count >= len(self.players) * 20:
            lowest_score = float('inf')
            for player in self.players:
                score = player.get_score()
                if score < lowest_score:
                    lowest_score = score
                    self.winner = player
            self.game_over = True
            return True, self.winner
        
        return False, None
    
    def play_turn(self) -> Dict[str, Any]:
        """Execute one player's turn and return turn results"""
        current_player = self.get_current_player()
        
        # Check if final round is complete
        if (self.dutch_called and self.final_round and 
            self.turns_after_dutch >= len(self.players) - 1):
            game_ended, winner = self.check_win_condition()
            return {"turn_completed": False, "game_ended": game_ended, "winner": winner.name if winner else None}
        
        # Skip Dutch caller's turn in final round
        if (self.dutch_called and self.final_round and current_player == self.dutch_caller):
            self.next_turn()
            return {"turn_completed": False, "skipped": True, "reason": "Dutch caller doesn't get another turn"}
        
        turn_result = {
            "player": current_player.name,
            "turn_number": self.turn_count + 1,
            "turn_completed": True
        }
        
        # FIRST OPPORTUNITY: Discard matching cards before drawing
        before_draw_discards = self.handle_matching_cards_opportunity(current_player, "before_draw")
        turn_result["before_draw_discards"] = [str(card) for card in before_draw_discards]
        
        # Choose where to draw from and draw a card
        drawn_card, drawn_from_discard = self.handle_card_draw(current_player)
        turn_result["drawn_card"] = str(drawn_card)
        turn_result["drawn_from_discard"] = drawn_from_discard
        
        # Player chooses action
        action = current_player.choose_action(drawn_card, self.get_game_state())
        
        # Handle the action
        action_result = self.handle_drawn_card_action(current_player, drawn_card, action, drawn_from_discard)
        turn_result["action_result"] = action_result
        
        # SECOND OPPORTUNITY: Discard matching cards after turn actions
        after_turn_discards = self.handle_matching_cards_opportunity(current_player, "after_turn")
        turn_result["after_turn_discards"] = [str(card) for card in after_turn_discards]
        
        # Check win conditions
        game_ended, winner = self.check_win_condition()
        turn_result["game_ended"] = game_ended
        if winner:
            turn_result["winner"] = winner.name
        
        # Move to next turn if game continues
        if not game_ended:
            self.next_turn()
            
        return turn_result
    
    def get_final_results(self) -> Dict[str, Any]:
        """Get final game results"""
        results = {
            "game_over": self.game_over,
            "winner": self.winner.name if self.winner else None,
            "final_scores": {},
            "player_hands": {}
        }
        
        scores = []
        for player in self.players:
            score = player.get_score()
            scores.append((player.name, score))
            results["final_scores"][player.name] = score
            results["player_hands"][player.name] = player.display_hand(reveal_all=True)
        
        # Sort by score (lowest wins)
        scores.sort(key=lambda x: x[1])
        results["ranking"] = scores
        
        return results 