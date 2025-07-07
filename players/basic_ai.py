"""
Basic AI player implementations for testing and learning.
"""

import random
from typing import List, Optional, Tuple

from src.player import Player


class RandomAI(Player):
    """Completely random AI - makes random valid decisions"""
    
    def choose_initial_peek(self) -> int:
        """Randomly choose a card to peek at"""
        return random.randint(0, 3)
    
    def choose_action(self, drawn_card, game_state: dict) -> dict:
        """Make completely random decisions"""
        # Check for matching cards first
        for i, card in enumerate(self.hand):
            if card is not None and self.known_cards[i] and card == drawn_card:
                if random.random() < 0.7:  # 70% chance to discard matches
                    return {"action": "discard_matches"}
        
        # Random choice between available actions
        actions = ["discard", "swap"]
        if drawn_card.has_special_ability():
            actions.append("use_ability")
        
        action = random.choice(actions)
        
        if action == "swap":
            valid_positions = self.get_valid_positions()
            if valid_positions:
                position = random.choice(valid_positions)
                return {"action": "swap", "position": position}
            else:
                return {"action": "discard"}
        
        return {"action": action}
    
    def choose_swap_target(self, opponents: List[Player], game_state: dict) -> Tuple[Player, int]:
        """Randomly choose swap target"""
        target_opponent = random.choice(opponents)
        valid_positions = target_opponent.get_valid_positions()
        target_position = random.choice(valid_positions)
        return target_opponent, target_position
    
    def choose_peek_target(self, opponents: List[Player], game_state: dict) -> Tuple[Optional[Player], int]:
        """Randomly choose peek target"""
        if random.random() < 0.5 and opponents:
            # Peek at opponent
            target_opponent = random.choice(opponents)
            valid_positions = target_opponent.get_valid_positions()
            target_position = random.choice(valid_positions)
            return target_opponent, target_position
        else:
            # Peek at own card
            unknown_positions = [i for i in self.get_valid_positions() if not self.known_cards[i]]
            if unknown_positions:
                target_position = random.choice(unknown_positions)
                return None, target_position
            elif opponents:
                # Fallback to opponent
                target_opponent = random.choice(opponents)
                valid_positions = target_opponent.get_valid_positions()
                target_position = random.choice(valid_positions)
                return target_opponent, target_position
            else:
                return None, 0


class RandomPlayer(Player):
    """Very basic AI with simple heuristics - good for testing and learning"""
    
    def choose_initial_peek(self) -> int:
        """Always peek at position 0 for consistency"""
        return 0
    
    def choose_action(self, drawn_card, game_state: dict) -> dict:
        """Simple but logical decision making"""
        print(f"{self.name} is thinking... (drawn card value: {drawn_card.get_score_value()})")
        
        # Always discard matches - this is always good
        for i, card in enumerate(self.hand):
            if card is not None and self.known_cards[i] and card == drawn_card:
                print(f"{self.name}: Found matching card, discarding both!")
                return {"action": "discard_matches"}
        
        # Use special abilities - they're usually beneficial
        if drawn_card.has_special_ability():
            if drawn_card.is_jack():
                print(f"{self.name}: Using Jack to swap with opponent!")
            elif drawn_card.is_queen():
                print(f"{self.name}: Using Queen to peek at a card!")
            return {"action": "use_ability"}
        
        # Simple value-based decision
        drawn_value = drawn_card.get_score_value()
        
        # If drawn card is very good (0-2 points), try to keep it
        if drawn_value <= 2:
            # Look for a known high-value card to replace
            for i, card in enumerate(self.hand):
                if card is not None and self.known_cards[i] and card.get_score_value() >= 7:
                    print(f"{self.name}: Swapping low value card ({drawn_value}) for high value card!")
                    return {"action": "swap", "position": i}
        
        # If drawn card is terrible (9+ points), always discard
        if drawn_value >= 9:
            print(f"{self.name}: High value card ({drawn_value}), discarding!")
            return {"action": "discard"}
        
        # For medium cards (3-8), be more cautious
        # Only swap if we know we have something worse
        for i, card in enumerate(self.hand):
            if card is not None and self.known_cards[i] and card.get_score_value() > drawn_value + 2:
                print(f"{self.name}: Swapping medium card for known worse card!")
                return {"action": "swap", "position": i}
        
        # Default: discard if unsure
        print(f"{self.name}: Unsure, discarding to be safe!")
        return {"action": "discard"}
    
    def choose_swap_target(self, opponents: List[Player], game_state: dict) -> Tuple[Player, int]:
        """Choose swap target - prefer opponents with more cards"""
        # Choose opponent with most cards (more chances for high values)
        best_opponent = max(opponents, key=lambda p: p.get_hand_size())
        valid_positions = best_opponent.get_valid_positions()
        
        # Choose random position (we don't know what they have)
        target_position = random.choice(valid_positions)
        
        print(f"{self.name}: Swapping with {best_opponent.name} at position {target_position}")
        return best_opponent, target_position
    
    def choose_peek_target(self, opponents: List[Player], game_state: dict) -> Tuple[Optional[Player], int]:
        """Choose peek target - gather information strategically"""
        # First, check if we have unknown cards of our own
        unknown_positions = [i for i in self.get_valid_positions() if not self.known_cards[i]]
        
        # 60% chance to peek at opponent if we don't have many unknown cards
        if len(unknown_positions) <= 1 and opponents and random.random() < 0.6:
            # Peek at opponent with most cards
            target_opponent = max(opponents, key=lambda p: p.get_hand_size())
            valid_positions = target_opponent.get_valid_positions()
            target_position = random.choice(valid_positions)
            print(f"{self.name}: Peeking at {target_opponent.name}'s card at position {target_position}")
            return target_opponent, target_position
        
        # Otherwise peek at our own unknown card
        if unknown_positions:
            target_position = random.choice(unknown_positions)
            print(f"{self.name}: Peeking at own card at position {target_position}")
            return None, target_position
        
        # Fallback to opponent if no unknown own cards
        if opponents:
            target_opponent = random.choice(opponents)
            valid_positions = target_opponent.get_valid_positions()
            target_position = random.choice(valid_positions)
            print(f"{self.name}: All own cards known, peeking at {target_opponent.name}")
            return target_opponent, target_position
        
        return None, 0 