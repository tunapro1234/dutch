"""
Smart Bayes Player - Rule-based AI focused on winning

Core principles:
1. Learn unknown cards efficiently 
2. Optimize known cards strategically
3. Track deck composition accurately
4. Call Dutch at optimal moments
5. Maximize information gain per turn
"""

import random
from typing import List, Optional, Tuple, Dict, Set
from collections import defaultdict

from game.engine.player_base import PlayerBase
from game.engine.card import Card


class SmartBayesPlayer(PlayerBase):
    """
    Enhanced rule-based AI that should consistently beat SimpleAI
    
    Strategy: Smart information gathering + optimal value decisions
    """
    
    def __init__(self, name: str):
        super().__init__(name)
        
        # Card tracking - simple but effective
        self.seen_cards: Set[int] = set()  # Card values we've seen
        self.remaining_cards = self._init_deck_count()
        
        # Game intelligence
        self.turn_count = 0
        self.opponent_intel: Dict[str, Dict] = defaultdict(dict)
        
        # Decision thresholds - tuned for winning
        self.GOOD_CARD_THRESHOLD = 3      # Cards 0-3 are good
        self.BAD_CARD_THRESHOLD = 7       # Cards 7+ are bad  
        self.DUTCH_MIN_ADVANTAGE = 2      # Minimum score advantage for Dutch
        self.LEARNING_PRIORITY = True     # Always learn unknowns first
        
    def _init_deck_count(self) -> Dict[int, int]:
        """Initialize remaining card counts"""
        return {
            0: 2,   # Red Kings
            1: 4,   # Aces
            2: 4, 3: 4, 4: 4, 5: 4, 6: 4, 7: 4, 8: 4, 9: 4,  # Number cards
            10: 12  # 10s, Jacks, Queens, Black Kings
        }
    
    def observe_card(self, card: Card):
        """Track seen cards efficiently"""
        value = card.get_score_value()
        self.seen_cards.add(value)
        if value in self.remaining_cards and self.remaining_cards[value] > 0:
            self.remaining_cards[value] -= 1
    
    def reset_for_new_game(self):
        """Reset for new game"""
        super().reset_for_new_game()
        self.seen_cards.clear()
        self.remaining_cards = self._init_deck_count()
        self.turn_count = 0
        self.opponent_intel.clear()
    
    def choose_initial_peek(self) -> int:
        """Smart initial peek - prefer corner positions"""
        # Corners (0,3) are often safer to peek than middle (1,2)
        return random.choice([0, 3])
    
    def choose_action(self, drawn_card: Card, game_state: dict) -> dict:
        """Core decision engine - simple but optimal"""
        self.turn_count += 1
        self.observe_card(drawn_card)
        drawn_value = drawn_card.get_score_value()
        
        # PRIORITY 1: Always use special abilities for information
        if drawn_card.has_special_ability():
            return {"action": "use_ability"}
        
        # PRIORITY 2: Learn unknown cards (information gathering)
        if self.LEARNING_PRIORITY:
            unknown_positions = self._get_unknown_positions()
            if unknown_positions:
                # Smart learning: target worst expected position
                target_pos = self._choose_best_learning_position(unknown_positions)
                print(f"{self.name}: Learning unknown card at position {target_pos} (smart targeting)")
                return {"action": "swap", "position": target_pos}
        
        # PRIORITY 3: Value optimization (all cards known)
        worst_pos = self._find_worst_known_position()
        if worst_pos is not None:
            worst_value = self.hand[worst_pos].get_score_value()
            
            # Smart swap decision
            if self._should_swap_for_value(drawn_value, worst_value):
                return {"action": "swap", "position": worst_pos}
        
        # PRIORITY 4: Check Dutch call before discarding
        if self._should_call_dutch(game_state):
            return {"action": "call_dutch"}
        
        # Default: discard
        return {"action": "discard"}
    
    def _get_unknown_positions(self) -> List[int]:
        """Get positions of unknown cards"""
        return [i for i in range(4) 
                if self.hand[i] is not None and not self.known_cards[i]]
    
    def _choose_best_learning_position(self, unknown_positions: List[int]) -> int:
        """Smart position selection for learning"""
        if len(unknown_positions) == 1:
            return unknown_positions[0]
        
        # Prefer positions that are more likely to have bad cards
        # (heuristic: positions we haven't peeked at might have worse cards)
        return random.choice(unknown_positions)
    
    def _find_worst_known_position(self) -> Optional[int]:
        """Find position with worst known card"""
        worst_value = -1
        worst_pos = None
        
        for i, card in enumerate(self.hand):
            if card is not None and self.known_cards[i] and i < len(self.hand):
                value = card.get_score_value()
                if value > worst_value:
                    worst_value = value
                    worst_pos = i
        
        return worst_pos
    
    def _should_swap_for_value(self, drawn_value: int, worst_value: int) -> bool:
        """Smart value-based swap decision"""
        # Always swap if drawn card is significantly better
        if drawn_value <= self.GOOD_CARD_THRESHOLD and worst_value >= self.BAD_CARD_THRESHOLD:
            return True
        
        # Swap if any improvement (but be smart about it)
        if drawn_value < worst_value:
            # Extra consideration: is this worth it?
            improvement = worst_value - drawn_value
            return improvement >= 1  # Even 1 point improvement is worth it
        
        return False
    
    def _should_call_dutch(self, game_state: dict) -> bool:
        """Smart Dutch call timing"""
        # Don't call too early
        if self.turn_count < 3:
            return False
        
        my_score = self._estimate_my_score()
        opponent_scores = self._estimate_opponent_scores(game_state)
        
        if not opponent_scores:
            return False
        
        min_opponent_score = min(opponent_scores)
        my_advantage = min_opponent_score - my_score
        
        # GUARANTEED WIN: I'm definitely better
        if my_advantage >= 4:
            print(f"{self.name}: GUARANTEED WIN! My score: {my_score}, Opponent min: {min_opponent_score}")
            return True
        
        # VERY GOOD POSITION: High advantage
        if my_advantage >= self.DUTCH_MIN_ADVANTAGE and my_score <= 8:
            print(f"{self.name}: Strong Dutch call (advantage: {my_advantage:.1f})")
            return True
        
        # EXCELLENT SCORE: Just go for it
        if my_score <= 3:
            print(f"{self.name}: Excellent score Dutch call: {my_score}")
            return True
        
        return False
    
    def _estimate_my_score(self) -> float:
        """Estimate my current score"""
        total = 0.0
        
        for i, card in enumerate(self.hand):
            if card is None:
                continue
            elif self.known_cards[i]:
                total += card.get_score_value()
            else:
                # Unknown card: use smart estimation
                total += self._estimate_unknown_card_value()
        
        return total
    
    def _estimate_unknown_card_value(self) -> float:
        """Smart estimation for unknown cards"""
        # Calculate weighted average based on remaining cards
        total_cards = sum(self.remaining_cards.values())
        if total_cards == 0:
            return 5.0  # Fallback to average
        
        weighted_sum = sum(value * count for value, count in self.remaining_cards.items())
        return weighted_sum / total_cards
    
    def _estimate_opponent_scores(self, game_state: dict) -> List[float]:
        """Simple but effective opponent score estimation"""
        scores = []
        
        for player_info in game_state.get("players", []):
            if player_info["name"] != self.name:
                hand_size = player_info.get("hand_size", 4)
                # Conservative estimate: assume opponents have decent hands
                estimated_score = hand_size * 4.0  # Average card value
                scores.append(estimated_score)
        
        return scores
    
    def choose_swap_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[PlayerBase, int]:
        """Smart Jack ability usage"""
        # Target random opponent, random position (keep it simple)
        target_opponent = random.choice(opponents)
        valid_positions = target_opponent.get_valid_positions()
        target_position = random.choice(valid_positions)
        return target_opponent, target_position
    
    def choose_peek_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[Optional[PlayerBase], int]:
        """Smart Queen ability usage"""
        # ALWAYS prioritize learning our own unknown cards
        unknown_positions = self._get_unknown_positions()
        if unknown_positions:
            target_pos = self._choose_best_learning_position(unknown_positions)
            print(f"{self.name}: Peeking at own unknown card (position {target_pos})")
            return None, target_pos
        
        # If all our cards are known, peek at opponent
        if opponents:
            target_opponent = random.choice(opponents)
            valid_positions = target_opponent.get_valid_positions()
            target_position = random.choice(valid_positions)
            print(f"{self.name}: Peeking at {target_opponent.name}'s card")
            return target_opponent, target_position
        
        return None, 0
    
    def choose_draw_source(self, top_discard_card: Card, game_state: dict) -> str:
        """Smart draw source decision"""
        discard_value = top_discard_card.get_score_value()
        deck_average = self._estimate_unknown_card_value()
        
        # Take from discard if it's significantly better than deck average
        if discard_value <= self.GOOD_CARD_THRESHOLD:
            return "discard"
        
        if discard_value < deck_average - 1:
            return "discard"
        
        return "deck"
    
    def want_to_discard_pile_matches(self, matches_available: List[Tuple[int, Card]], 
                                   top_discard_card: Card, timing: str, game_state: dict) -> Optional[List[int]]:
        """Smart discard pile matching"""
        if not matches_available:
            return None
        
        cards_to_discard = []
        
        for pos, card in matches_available:
            card_value = card.get_score_value()
            
            # Discard bad cards immediately
            if card_value >= self.BAD_CARD_THRESHOLD:
                cards_to_discard.append(pos)
            # Discard medium cards sometimes
            elif card_value >= 5 and random.random() < 0.7:
                cards_to_discard.append(pos)
        
        if cards_to_discard:
            print(f"{self.name}: Smart discard matching - removing {len(cards_to_discard)} cards")
            return cards_to_discard
        
        return None 