"""
Bayesian Probability Player - Uses Bayesian inference and opponent modeling
"""

import random
from typing import List, Optional, Tuple, Dict, Set
from collections import defaultdict, Counter
import math

from game.engine.player_base import PlayerBase
from game.engine.card import Card, Suit


class BayesPlayer(PlayerBase):
    """Advanced AI using Bayesian probability and opponent modeling"""
    
    def __init__(self, name: str):
        super().__init__(name)
        
        # Card tracking
        self.seen_cards: Set[str] = set()  # All cards we've observed
        self.discarded_cards: List[Card] = []  # All discarded cards in order
        self.deck_composition = self._initialize_deck_tracking()
        
        # Opponent modeling
        self.opponent_known_cards: Dict[str, Set[int]] = {}  # player_name -> {positions they know}
        self.opponent_actions_history: Dict[str, List[dict]] = defaultdict(list)
        
        # Probability calculations
        self.card_probabilities: Dict[int, Dict[int, float]] = {}  # position -> {value -> probability}
        self.expected_values: Dict[int, float] = {}  # position -> expected score value
        
        # Bayesian beliefs about opponent cards
        self.opponent_card_beliefs: Dict[str, Dict[int, Dict[int, float]]] = {}  # player -> pos -> {value -> prob}
        
        # Strategic insights
        self.cards_likely_in_deck: Dict[int, int] = {}  # value -> count likely remaining
        self.turn_count = 0
        
    def _initialize_deck_tracking(self) -> Dict[int, int]:
        """Initialize deck composition tracking"""
        deck_comp = {}
        # Aces = 1 point (4 cards)
        deck_comp[1] = 4
        # 2-9 = face value (4 each)
        for value in range(2, 10):
            deck_comp[value] = 4
        # 10s, Jacks, Queens, Black Kings = 10 points (12 cards total)
        deck_comp[10] = 12
        # Red Kings = 0 points (2 cards)
        deck_comp[0] = 2
        return deck_comp
    
    def register_opponent(self, player_name: str):
        """Register a new opponent for tracking"""
        if player_name not in self.opponent_known_cards:
            self.opponent_known_cards[player_name] = set()
            self.opponent_card_beliefs[player_name] = {i: self._uniform_card_distribution() for i in range(4)}
    
    def _uniform_card_distribution(self) -> Dict[int, float]:
        """Get uniform probability distribution over card values"""
        return {0: 2/52, 1: 4/52, 2: 4/52, 3: 4/52, 4: 4/52, 5: 4/52, 
                6: 4/52, 7: 4/52, 8: 4/52, 9: 4/52, 10: 12/52}
    
    def observe_card(self, card: Card):
        """Update our knowledge when we see a card"""
        self.seen_cards.add(str(card))
        value = card.get_score_value()
        if value in self.deck_composition and self.deck_composition[value] > 0:
            self.deck_composition[value] -= 1
    
    def observe_discard(self, card: Card):
        """Track when a card is discarded"""
        self.discarded_cards.append(card)
        self.observe_card(card)
    
    def update_opponent_knowledge(self, player_name: str, position: int, action_type: str = "peek"):
        """Track when opponent gains knowledge about a card"""
        if player_name not in self.opponent_known_cards:
            self.register_opponent(player_name)
        self.opponent_known_cards[player_name].add(position)
    
    def infer_from_opponent_action(self, player_name: str, action: dict):
        """Use Bayesian inference from opponent actions"""
        if player_name not in self.opponent_known_cards:
            self.register_opponent(player_name)
        
        self.opponent_actions_history[player_name].append(action)
        
        if action.get("action") == "swap" and "position" in action:
            # If they swapped a known card, they likely got something better
            pos = action["position"]
            if pos in self.opponent_known_cards[player_name]:
                # Bayesian update: they likely received a lower-value card
                self._update_opponent_belief_after_beneficial_swap(player_name, pos)
    
    def _update_opponent_belief_after_beneficial_swap(self, player_name: str, position: int):
        """Update belief that opponent got a good card (lower value) after swapping known card"""
        if player_name in self.opponent_card_beliefs:
            beliefs = self.opponent_card_beliefs[player_name][position]
            # Boost probability of lower values, reduce probability of higher values
            for value in beliefs:
                if value <= 3:  # Good cards
                    beliefs[value] *= 1.5
                elif value >= 7:  # Bad cards
                    beliefs[value] *= 0.5
            # Normalize
            total = sum(beliefs.values())
            for value in beliefs:
                beliefs[value] /= total
    
    def calculate_own_card_probabilities(self):
        """Calculate Bayesian probabilities for our unknown cards"""
        remaining_cards = self.deck_composition.copy()
        
        # Account for cards we definitely know
        for i, card in enumerate(self.hand):
            if card is not None and self.known_cards[i]:
                value = card.get_score_value()
                # This card is known, remove from possibilities
                continue
        
        # For each unknown position, calculate probability distribution
        unknown_positions = [i for i in range(4) if self.hand[i] is not None and not self.known_cards[i]]
        
        for pos in unknown_positions:
            total_remaining = sum(remaining_cards.values())
            if total_remaining > 0:
                self.card_probabilities[pos] = {
                    value: count / total_remaining 
                    for value, count in remaining_cards.items()
                }
                # Calculate expected value for this position
                self.expected_values[pos] = sum(
                    value * prob for value, prob in self.card_probabilities[pos].items()
                )
    
    def estimate_deck_draw_value(self) -> float:
        """Estimate expected value of drawing from deck"""
        total_remaining = sum(self.deck_composition.values())
        if total_remaining == 0:
            return 5.0  # Fallback
        
        expected_value = sum(
            value * count / total_remaining 
            for value, count in self.deck_composition.items()
        )
        return expected_value
    
    def has_potential_double_opportunity(self, card_value: int) -> bool:
        """Check if we might have or get another card of this value for doubles"""
        # Check known cards
        for i, card in enumerate(self.hand):
            if card is not None and self.known_cards[i] and card.get_score_value() == card_value:
                return True
        
        # Check probability in unknown cards
        for pos in range(4):
            if not self.known_cards[pos] and pos in self.card_probabilities:
                prob = self.card_probabilities[pos].get(card_value, 0)
                if prob > 0.15:  # 15% chance is worth considering
                    return True
        
        # Check remaining deck
        if self.deck_composition.get(card_value, 0) > 0:
            return True
            
        return False
    
    def choose_initial_peek(self) -> int:
        """Choose initial peek position - random but track it"""
        pos = random.randint(0, 3)
        return pos
    
    def choose_action(self, drawn_card: Card, game_state: dict) -> dict:
        """Bayesian decision making"""
        self.turn_count += 1
        self.observe_card(drawn_card)
        self.calculate_own_card_probabilities()
        
        drawn_value = drawn_card.get_score_value()
        
        # Always use special abilities for information gathering
        if drawn_card.has_special_ability():
            return {"action": "use_ability"}
        
        # PRIORITY 1: Learn unknown cards (Bayesian approach)
        unknown_positions = [i for i in range(4) if self.hand[i] is not None and not self.known_cards[i]]
        if unknown_positions:
            # Choose position with highest uncertainty (entropy)
            best_pos = max(unknown_positions, key=lambda p: self._calculate_entropy(p))
            print(f"{self.name}: Swapping to learn unknown card (Bayesian inference)")
            return {"action": "swap", "position": best_pos}
        
        # PRIORITY 2: All cards known - make probabilistic decisions
        
        # Consider double discard potential
        if self.has_potential_double_opportunity(drawn_value):
            # Even high cards might be worth keeping for doubles
            worst_pos = self._find_worst_known_card_position()
            if worst_pos is not None:
                worst_value = self.hand[worst_pos].get_score_value()
                if worst_value > drawn_value + 2:  # Only if significantly worse
                    return {"action": "swap", "position": worst_pos}
                elif drawn_value >= 8 and self.has_potential_double_opportunity(drawn_value):
                    # Take calculated risk for doubles even on high cards
                    return {"action": "swap", "position": worst_pos}
        
        # Standard value-based decision
        if drawn_value <= 4:  # Good cards
            worst_pos = self._find_worst_known_card_position()
            if worst_pos is not None:
                worst_value = self.hand[worst_pos].get_score_value()
                if worst_value > drawn_value:
                    return {"action": "swap", "position": worst_pos}
        
        # Check if we should call Dutch before discarding
        if self.should_call_dutch(game_state):
            return {"action": "call_dutch"}
        
        # Discard if not beneficial
        return {"action": "discard"}
    
    def _calculate_entropy(self, position: int) -> float:
        """Calculate entropy (uncertainty) for a position"""
        if position not in self.card_probabilities:
            return 1.0  # High uncertainty
        
        entropy = 0.0
        for value, prob in self.card_probabilities[position].items():
            if prob > 0:
                entropy -= prob * math.log2(prob)
        return entropy
    
    def _find_worst_known_card_position(self) -> Optional[int]:
        """Find position with highest known card value"""
        worst_value = -1
        worst_pos = None
        
        for i, card in enumerate(self.hand):
            if card is not None and self.known_cards[i]:
                value = card.get_score_value()
                if value > worst_value:
                    worst_value = value
                    worst_pos = i
        
        return worst_pos
    
    def choose_swap_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[PlayerBase, int]:
        """Bayesian opponent modeling for swap target"""
        # Register opponents
        for opp in opponents:
            self.register_opponent(opp.name)
        
        # Choose opponent and position based on our beliefs
        best_target = None
        best_expected_value = float('inf')
        
        for opponent in opponents:
            opp_name = opponent.name
            if opp_name in self.opponent_card_beliefs:
                for pos in range(4):
                    if pos < len(opponent.hand) and opponent.hand[pos] is not None:
                        # Calculate expected value based on our beliefs
                        expected_val = sum(
                            value * prob 
                            for value, prob in self.opponent_card_beliefs[opp_name][pos].items()
                        )
                        if expected_val < best_expected_value:
                            best_expected_value = expected_val
                            best_target = (opponent, pos)
        
        if best_target:
            return best_target
        
        # Fallback to random
        target_opponent = random.choice(opponents)
        valid_positions = target_opponent.get_valid_positions()
        target_position = random.choice(valid_positions)
        return target_opponent, target_position
    
    def choose_peek_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[Optional[PlayerBase], int]:
        """Information-theoretic peek selection"""
        # Always prioritize own unknown cards for maximum information gain
        unknown_positions = [i for i in range(4) if self.hand[i] is not None and not self.known_cards[i]]
        if unknown_positions:
            # Choose position with highest entropy (most uncertain)
            best_pos = max(unknown_positions, key=lambda p: self._calculate_entropy(p))
            print(f"{self.name}: Peeking at own card for maximum information gain")
            return None, best_pos
        
        # If all own cards known, peek at opponents strategically
        if opponents:
            target_opponent = random.choice(opponents)
            valid_positions = target_opponent.get_valid_positions()
            target_position = random.choice(valid_positions)
            print(f"{self.name}: Gathering intelligence on {target_opponent.name}")
            return target_opponent, target_position
        
        return None, 0
    
    def choose_draw_source(self, top_discard_card: Card, game_state: dict) -> str:
        """Bayesian decision on draw source"""
        discard_value = top_discard_card.get_score_value()
        deck_expected_value = self.estimate_deck_draw_value()
        
        # Factor in double discard potential
        double_potential = self.has_potential_double_opportunity(discard_value)
        
        if double_potential and discard_value <= 8:
            # Worth taking even medium cards for doubles
            return "discard"
        
        if discard_value < deck_expected_value - 1:  # Significantly better than expected
            return "discard"
        
        return "deck"
    

    
    def want_to_discard_pile_matches(self, matches_available: List[Tuple[int, Card]], 
                                   top_discard_card: Card, timing: str, game_state: dict) -> Optional[List[int]]:
        """Bayesian analysis of discard pile matching"""
        if not matches_available:
            return None
        
        # Analyze each matching card's strategic value
        cards_to_discard = []
        
        for pos, card in matches_available:
            card_value = card.get_score_value()
            
            # Calculate strategic value of keeping this card
            keep_value = 0
            
            # Check if this card could be part of a double later
            remaining_same_value = self.deck_composition.get(card_value, 0)
            double_probability = 0
            
            # Check unknown positions for potential doubles
            for unknown_pos in range(4):
                if (unknown_pos != pos and self.hand[unknown_pos] is not None and 
                    not self.known_cards[unknown_pos] and unknown_pos in self.card_probabilities):
                    double_probability += self.card_probabilities[unknown_pos].get(card_value, 0)
            
            # Higher double probability = higher keep value
            if double_probability > 0.2 or remaining_same_value > 0:
                keep_value += 3  # Strategic value for potential doubles
            
            # Lower card values have higher keep value
            if card_value <= 3:
                keep_value += 4
            elif card_value <= 6:
                keep_value += 2
            
            # Decision threshold based on timing
            discard_threshold = 4 if timing == "before_draw" else 2
            
            if card_value >= discard_threshold and keep_value < 6:
                cards_to_discard.append(pos)
        
        if cards_to_discard:
            card_values = [card.get_score_value() for pos, card in matches_available if pos in cards_to_discard]
            print(f"{self.name}: Bayesian analysis - discarding matches (values: {card_values})")
            return cards_to_discard
        
        return None
    
    def should_call_dutch(self, game_state: dict) -> bool:
        """Sophisticated Bayesian decision on calling Dutch"""
        # Don't call Dutch too early in the game (reduced from 8 to 5)
        if self.turn_count < 5:
            return False
        
        # Calculate our score ranges
        my_min_score, my_max_score, my_expected_score = self.calculate_min_max_score()
        
        # Estimate opponent score ranges
        opponent_estimates = {}
        opponent_ranges = {}
        confidence_levels = {}
        
        for player_info in game_state.get("players", []):
            if player_info["name"] != self.name:
                player_name = player_info["name"]
                expected_score, confidence = self.estimate_opponent_score(player_name, player_info)
                min_score, max_score = self.estimate_opponent_min_max_score(player_name, player_info)
                
                opponent_estimates[player_name] = expected_score
                opponent_ranges[player_name] = (min_score, max_score)
                confidence_levels[player_name] = confidence
        
        if not opponent_estimates:
            return False
        
        # Find best opponent (lowest scores)
        min_opponent_expected = min(opponent_estimates.values())
        min_opponent_min = min(min_score for min_score, max_score in opponent_ranges.values())
        max_opponent_max = max(max_score for min_score, max_score in opponent_ranges.values())
        
        avg_confidence = sum(confidence_levels.values()) / len(confidence_levels)
        
        # GUARANTEED WIN: My maximum score < opponent minimum score
        if my_max_score < min_opponent_min:
            print(f"{self.name}: GUARANTEED WIN! My max ({my_max_score}) < opponent min ({min_opponent_min})")
            return True
        
        # ULTRA AGGRESSIVE: Very low score = instant Dutch
        if my_expected_score <= 3:
            print(f"{self.name}: ULTRA AGGRESSIVE Dutch! My score too good to pass up: {my_expected_score:.1f}")
            return True
        elif my_expected_score <= 4 and avg_confidence >= 0.3:
            print(f"{self.name}: VERY AGGRESSIVE Dutch! Excellent score: {my_expected_score:.1f}")
            return True
        
        # VERY HIGH CONFIDENCE: My expected score significantly better
        score_advantage = min_opponent_expected - my_expected_score
        
        # Much more aggressive thresholds
        if score_advantage >= 3 and avg_confidence >= 0.4:  # Reduced from 4 and 0.5
            print(f"{self.name}: High confidence Dutch call (advantage: {score_advantage:.1f}, confidence: {avg_confidence:.2f})")
            return True
        elif score_advantage >= 5 and avg_confidence >= 0.2:  # Reduced from 6 and 0.3
            print(f"{self.name}: Massive advantage Dutch call (advantage: {score_advantage:.1f})")
            return True
        elif self.turn_count >= 10 and score_advantage >= 1.5:  # Much more aggressive late game
            print(f"{self.name}: Late game Dutch call (advantage: {score_advantage:.1f})")
            return True
        elif self.turn_count >= 6 and score_advantage >= 2.5:  # Aggressive mid game
            print(f"{self.name}: Mid game Dutch call (advantage: {score_advantage:.1f})")
            return True
        
        # POSSIBLE WIN: Much more aggressive
        if my_expected_score <= min_opponent_expected and avg_confidence >= 0.3:  # Reduced from 0.4
            print(f"{self.name}: Reasonable Dutch opportunity (my: {my_expected_score:.1f} vs opponent: {min_opponent_expected:.1f})")
            return True
        
        # LAST RESORT: If my score is really good, just go for it
        if my_expected_score <= 6 and self.turn_count >= 6:
            print(f"{self.name}: Good score, taking the Dutch risk: {my_expected_score:.1f}")
            return True
        
        # Debug information for why we didn't call Dutch
        if self.turn_count >= 5:  # Only show debug after early game
            print(f"{self.name} Dutch analysis: My range ({my_min_score:.1f}-{my_max_score:.1f}), "
                  f"Opponent min {min_opponent_min:.1f}, Advantage: {score_advantage:.1f}, "
                  f"Confidence: {avg_confidence:.2f}")
        
        return False
    
    def calculate_expected_score(self) -> float:
        """Calculate our expected score based on known and unknown cards"""
        total_score = 0.0
        
        for i in range(4):
            if self.hand[i] is None:
                continue
            elif self.known_cards[i]:
                # Known card - exact score
                total_score += self.hand[i].get_score_value()
            elif i in self.expected_values:
                # Unknown card - expected value
                total_score += self.expected_values[i]
            else:
                # Fallback - average card value
                total_score += 5.0
        
        return total_score
    
    def calculate_min_max_score(self) -> tuple[float, float, float]:
        """
        Calculate our minimum, maximum, and expected scores.
        
        Returns:
            (min_score, max_score, expected_score)
        """
        min_score = 0.0
        max_score = 0.0
        expected_score = 0.0
        
        for i in range(4):
            if self.hand[i] is None:
                continue
            elif self.known_cards[i]:
                # Known card - exact score
                card_value = self.hand[i].get_score_value()
                min_score += card_value
                max_score += card_value
                expected_score += card_value
            elif i in self.card_probabilities:
                # Unknown card - calculate min/max/expected from probabilities
                probs = self.card_probabilities[i]
                possible_values = [value for value, prob in probs.items() if prob > 0]
                
                if possible_values:
                    min_score += min(possible_values)
                    max_score += max(possible_values)
                    expected_score += sum(value * prob for value, prob in probs.items())
                else:
                    # Fallback
                    min_score += 0  # Best possible (Red King)
                    max_score += 10  # Worst possible
                    expected_score += 5.0
            else:
                # No probability data - use deck composition
                remaining_values = [value for value, count in self.deck_composition.items() if count > 0]
                if remaining_values:
                    min_score += min(remaining_values)
                    max_score += max(remaining_values)
                    # Calculate expected from deck
                    total_cards = sum(self.deck_composition.values())
                    if total_cards > 0:
                        expected_score += sum(value * count / total_cards 
                                            for value, count in self.deck_composition.items())
                    else:
                        expected_score += 5.0
                else:
                    # Complete fallback
                    min_score += 0
                    max_score += 10
                    expected_score += 5.0
        
        return min_score, max_score, expected_score
    
    def estimate_opponent_score(self, player_name: str, player_info: dict) -> tuple[float, float]:
        """
        Estimate opponent's score and confidence level.
        
        Returns:
            (estimated_score, confidence_level)
        """
        hand_size = player_info.get("hand_size", 4)
        known_cards_count = player_info.get("known_cards", 0)
        
        if hand_size == 0:
            return 0.0, 1.0  # Empty hand = 0 score
        
        # Base estimation on discarded cards and behavior
        estimated_score = 0.0
        confidence = 0.5  # Start with medium confidence
        
        # Analyze opponent's action history
        if player_name in self.opponent_actions_history:
            actions = self.opponent_actions_history[player_name]
            
            # Count beneficial actions (swaps, ability uses)
            beneficial_actions = sum(1 for action in actions 
                                   if action.get("action") in ["swap", "use_ability"])
            
            # More beneficial actions suggest they improved their hand
            if beneficial_actions > 0:
                # Each beneficial action suggests they reduced score by ~2 points
                score_reduction = beneficial_actions * 2
                estimated_score = max(0, 6.0 * hand_size - score_reduction)  # Start with average, reduce
                confidence += 0.1 * beneficial_actions
            else:
                # No beneficial actions - likely stuck with bad cards
                estimated_score = 7.0 * hand_size  # Assume slightly above average
        else:
            # No action history - use neutral estimate
            estimated_score = 6.0 * hand_size  # Slightly above average card value
        
        # Factor in discarded cards analysis
        discarded_high_values = 0
        for card in self.discarded_cards[-10:]:  # Recent discards
            if card.get_score_value() >= 7:
                discarded_high_values += 1
        
        if discarded_high_values > 2:
            # Many high cards discarded - opponent likely has better hand
            estimated_score -= 1.5 * discarded_high_values
            confidence += 0.05 * discarded_high_values
        
        # Factor in known information about this opponent
        if player_name in self.opponent_known_cards:
            known_positions = len(self.opponent_known_cards[player_name])
            if known_positions > known_cards_count:
                # They know more than average - suggests strategic play
                estimated_score -= 1.0
                confidence += 0.1
        
        # Confidence adjustments
        confidence = min(confidence, 0.9)  # Cap confidence
        confidence = max(confidence, 0.3)  # Minimum confidence
        
        # Special case: if opponent has very few cards, estimate lower
        if hand_size <= 2:
            estimated_score *= 0.7  # Assume they kept good cards
            confidence += 0.2
        
        return estimated_score, confidence
    
    def estimate_opponent_min_max_score(self, player_name: str, player_info: dict) -> tuple[float, float]:
        """
        Estimate opponent's minimum and maximum possible scores.
        
        Returns:
            (min_score, max_score)
        """
        hand_size = player_info.get("hand_size", 4)
        known_cards_count = player_info.get("known_cards", 0)
        
        if hand_size == 0:
            return 0.0, 0.0  # Empty hand
        
        # Conservative estimates based on what we know
        min_possible_score = 0.0  # Best case: all Red Kings
        max_possible_score = 10.0 * hand_size  # Worst case: all 10s
        
        # Adjust based on opponent behavior and observed patterns
        if player_name in self.opponent_actions_history:
            actions = self.opponent_actions_history[player_name]
            beneficial_actions = sum(1 for action in actions 
                                   if action.get("action") in ["swap", "use_ability"])
            
            if beneficial_actions > 0:
                # Each beneficial action suggests improvement
                # Reduce maximum score (they likely replaced bad cards)
                score_improvement = beneficial_actions * 2.5
                max_possible_score = max(min_possible_score, max_possible_score - score_improvement)
                
                # Also slightly increase minimum (they wouldn't swap for worse)
                min_possible_score += beneficial_actions * 0.5
        
        # Factor in recent discards - high discards suggest better remaining hand
        recent_high_discards = 0
        for card in self.discarded_cards[-8:]:  # Recent discards
            if card.get_score_value() >= 7:
                recent_high_discards += 1
        
        if recent_high_discards > 1:
            # High cards being discarded suggests players have better alternatives
            adjustment = recent_high_discards * 1.0
            max_possible_score = max(min_possible_score, max_possible_score - adjustment)
        
        # Adjust for hand size
        if hand_size <= 2:
            # Few cards usually means they kept the best ones
            max_possible_score *= 0.8
            min_possible_score = max(min_possible_score, hand_size * 0.5)  # Likely not all Red Kings
        elif hand_size >= 4:
            # More cards, harder to optimize all positions
            min_possible_score = max(min_possible_score, hand_size * 1.0)
        
        # Factor in known cards count
        if known_cards_count > hand_size * 0.75:  # Know most cards
            # If they know most cards and still playing, they likely have decent hand
            min_possible_score = max(min_possible_score, hand_size * 1.5)
        
        # Ensure logical bounds
        min_possible_score = max(0.0, min_possible_score)
        max_possible_score = max(min_possible_score, min(max_possible_score, 10.0 * hand_size))
        
        return min_possible_score, max_possible_score 