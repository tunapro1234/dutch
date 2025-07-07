"""
Simple AI player - more advanced than BasicAI but still straightforward.
"""

import random
from typing import List, Optional, Tuple

from src.player import Player


class SimpleAI(Player):
    """Simple rule-based AI player with moderate strategy"""
    
    def choose_initial_peek(self) -> int:
        """Randomly choose a card to peek at"""
        return random.randint(0, 3)
    
    def choose_action(self, drawn_card, game_state: dict) -> dict:
        """Simple AI decision making"""
        # Always discard matches if possible
        for i, card in enumerate(self.hand):
            if card is not None and self.known_cards[i] and card == drawn_card:
                return {"action": "discard_matches"}
        
        # Use special abilities
        if drawn_card.has_special_ability():
            return {"action": "use_ability"}
        
        # If drawn card is low value, consider swapping
        if drawn_card.get_score_value() <= 3:
            # Find highest known card to swap
            highest_value = -1
            highest_pos = -1
            for i, card in enumerate(self.hand):
                if card is not None and self.known_cards[i]:
                    if card.get_score_value() > highest_value:
                        highest_value = card.get_score_value()
                        highest_pos = i
            
            if highest_pos >= 0 and highest_value > drawn_card.get_score_value():
                return {"action": "swap", "position": highest_pos}
        
        # Otherwise discard
        return {"action": "discard"}
    
    def choose_swap_target(self, opponents: List[Player], game_state: dict) -> Tuple[Player, int]:
        """Randomly choose swap target"""
        target_opponent = random.choice(opponents)
        valid_positions = target_opponent.get_valid_positions()
        target_position = random.choice(valid_positions)
        return target_opponent, target_position
    
    def choose_peek_target(self, opponents: List[Player], game_state: dict) -> Tuple[Optional[Player], int]:
        """Choose peek target - prefer opponent cards"""
        if opponents and random.random() > 0.3:  # 70% chance to peek at opponent
            target_opponent = random.choice(opponents)
            valid_positions = target_opponent.get_valid_positions()
            target_position = random.choice(valid_positions)
            return target_opponent, target_position
        else:
            # Peek at own unknown card
            unknown_positions = [i for i in self.get_valid_positions() if not self.known_cards[i]]
            if unknown_positions:
                target_position = random.choice(unknown_positions)
                return None, target_position
            else:
                # Fallback to opponent if no unknown own cards
                if opponents:
                    target_opponent = random.choice(opponents)
                    valid_positions = target_opponent.get_valid_positions()
                    target_position = random.choice(valid_positions)
                    return target_opponent, target_position
                else:
                    return None, 0 