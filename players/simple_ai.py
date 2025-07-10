"""
Simple AI player - more advanced than BasicAI but still straightforward.
"""

import random
from typing import List, Optional, Tuple

from game.engine.player_base import PlayerBase


class SimpleAI(PlayerBase):
    """Simple rule-based AI player with moderate strategy"""
    
    def choose_initial_peek(self) -> int:
        """Randomly choose a card to peek at"""
        return random.randint(0, 3)
    
    def choose_action(self, drawn_card, game_state: dict) -> dict:
        """Information-focused AI decision making"""
        # Always use special abilities for information gathering
        if drawn_card.has_special_ability():
            return {"action": "use_ability"}
        
        # PRIORITY 1: Learn about unknown cards by swapping
        unknown_positions = [i for i in range(4) if self.hand[i] is not None and not self.known_cards[i]]
        if unknown_positions:
            # Prefer swapping with unknown cards to gain information
            target_pos = random.choice(unknown_positions)
            print(f"{self.name}: Swapping to learn about unknown card at position {target_pos}")
            return {"action": "swap", "position": target_pos}
        
        # PRIORITY 2: If all cards are known, make value-based decisions
        if drawn_card.get_score_value() <= 4:  # Accept medium-good cards
            # Find highest known card to swap out
            highest_value = -1
            highest_pos = -1
            for i, card in enumerate(self.hand):
                if card is not None and self.known_cards[i]:
                    if card.get_score_value() > highest_value:
                        highest_value = card.get_score_value()
                        highest_pos = i
            
            if highest_pos >= 0 and highest_value > drawn_card.get_score_value():
                return {"action": "swap", "position": highest_pos}
        
        # Check if we should call Dutch
        if self.should_call_dutch(game_state):
            return {"action": "call_dutch"}
        
        # Otherwise discard
        return {"action": "discard"}
    
    def choose_swap_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[PlayerBase, int]:
        """Choose an opponent and position to swap with"""
        # Simple strategy: pick random opponent and position
        target_opponent = random.choice(opponents)
        valid_positions = target_opponent.get_valid_positions()
        target_position = random.choice(valid_positions)
        return target_opponent, target_position
    
    def choose_own_swap_position(self, game_state: dict) -> int:
        """Choose which of own cards to give away when using Jack"""
        # Simple strategy: give away the highest known card
        valid_positions = self.get_valid_positions()
        
        # Prefer known cards over unknown ones
        known_positions = [pos for pos in valid_positions if self.known_cards[pos]]
        if known_positions:
            # Among known cards, give away the highest value
            highest_value = -1
            best_position = known_positions[0]
            
            for pos in known_positions:
                card = self.hand[pos]
                if card is not None:
                    card_value = card.get_score_value()
                    if card_value > highest_value:
                        highest_value = card_value
                        best_position = pos
            
            return best_position
        else:
            # If no known cards, pick random position
            return random.choice(valid_positions)
    
    def choose_peek_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[Optional[PlayerBase], int]:
        """Choose peek target - prioritize own unknown cards for information"""
        # PRIORITY: Always peek at own unknown cards first for information gathering
        unknown_positions = [i for i in self.get_valid_positions() if not self.known_cards[i]]
        if unknown_positions:
            target_position = random.choice(unknown_positions)
            print(f"{self.name}: Peeking at own unknown card for information")
            return None, target_position
        
        # If all own cards are known, peek at opponents  
        if opponents:
            target_opponent = random.choice(opponents)
            valid_positions = target_opponent.get_valid_positions()
            target_position = random.choice(valid_positions)
            print(f"{self.name}: Peeking at {target_opponent.name}'s card for intel")
            return target_opponent, target_position
        else:
            # Fallback
            return None, 0
    
    def choose_draw_source(self, top_discard_card, game_state: dict) -> str:
        """Strategic decision about draw source"""
        discard_value = top_discard_card.get_score_value()
        
        # Very strategic: only take from discard if it's significantly better than average
        if discard_value <= 2:
            # Excellent cards (0-2 points) are always worth taking
            return "discard"
        
        if discard_value <= 4:
            # Good cards (3-4 points) taken 60% of the time
            if random.random() < 0.6:
                return "discard"
        
        # Otherwise prefer the unknown from deck
        return "deck"
    

    
    def want_to_discard_pile_matches(self, matches_available, top_discard_card, timing: str, game_state: dict):
        """Strategic decision about discarding cards matching discard pile"""
        if not matches_available:
            return None
        
        # SimpleAI strategy: discard high-value matches to reduce score
        # More conservative than doubles since we lose cards individually
        discard_chance = 0.7 if timing == "before_draw" else 0.5
        
        if random.random() < discard_chance:
            # Choose high-value cards to discard
            high_value_matches = [(pos, card) for pos, card in matches_available 
                                if card.get_score_value() >= 6]
            
            if high_value_matches:
                positions_to_discard = [pos for pos, card in high_value_matches]
                print(f"{self.name}: Discarding {len(positions_to_discard)} high-value matches")
                return positions_to_discard
            elif matches_available:
                # If no high values, maybe discard one medium card
                pos, card = matches_available[0]
                if card.get_score_value() >= 4:
                    print(f"{self.name}: Discarding medium-value match {card}")
                    return [pos]
        
        return None
    
    def should_call_dutch(self, game_state: dict) -> bool:
        """Simple but improved Dutch call logic"""
        # Calculate our scores
        my_known_score = sum(card.get_score_value() for i, card in enumerate(self.hand) 
                           if card is not None and self.known_cards[i])
        unknown_cards = sum(1 for i in range(4) if self.hand[i] is not None and not self.known_cards[i])
        hand_size = self.get_hand_size()
        
        # Don't call Dutch too early or if we don't know enough
        if hand_size > 3 or len([i for i in range(4) if self.known_cards[i]]) < 1:
            return False
        
        # Simple min/max estimation
        my_min_score = my_known_score + (unknown_cards * 0)  # Best case: all Red Kings
        my_max_score = my_known_score + (unknown_cards * 10)  # Worst case: all 10s
        my_expected_score = my_known_score + (unknown_cards * 5)  # Average case
        
        # Estimate opponent - assume they have average cards per hand size
        opponent_hand_sizes = [p.get("hand_size", 4) for p in game_state.get("players", []) 
                              if p.get("name") != self.name]
        
        if opponent_hand_sizes:
            min_opponent_size = min(opponent_hand_sizes)
            # Assume opponent has slightly better than average (they made strategic plays)
            opponent_estimated_score = min_opponent_size * 4.5
            
            # GUARANTEED WIN check
            if my_max_score < opponent_estimated_score - 3:
                print(f"{self.name}: Guaranteed win! My max ({my_max_score}) vs opponent (~{opponent_estimated_score:.1f})")
                return True
        
        # Ultra aggressive heuristics to match BayesPlayer
        if my_expected_score <= 4:
            print(f"{self.name}: ULTRA AGGRESSIVE! Score too good: {my_expected_score:.1f}")
            return True
        
        if my_expected_score <= 7 and hand_size <= 3:
            print(f"{self.name}: Calling Dutch with low expected score: {my_expected_score:.1f}")
            return True
        
        if hand_size <= 2 and my_expected_score <= 12:
            print(f"{self.name}: Calling Dutch with few cards and decent score: {my_expected_score:.1f}")
            return True
        
        # Very aggressive late-game Dutch call (60% chance)
        if my_expected_score <= 15 and hand_size <= 3 and random.random() < 0.6:
            print(f"{self.name}: Taking a calculated Dutch risk (score: {my_expected_score:.1f})")
            return True
        
        return False