"""
AI vs Human Mode - AI plays against human opponent with physical cards
User executes AI moves exactly as instructed
"""

import sys
import os
from typing import List, Optional, Dict, Any
from collections import defaultdict

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from game.engine import Card, Suit
from players.bayes.smart_bayes import SmartBayesPlayer


class CardTracker:
    """Simple card tracking without emojis"""
    
    def __init__(self):
        self.used_cards = defaultdict(int)
        self.max_per_card = 1
        
    def track_card(self, card: Card) -> bool:
        """Track card usage"""
        card_key = (card.suit, card.value)
        self.used_cards[card_key] += 1
        
        if self.used_cards[card_key] > self.max_per_card:
            print(f"ERROR: {card} already used!")
            self.used_cards[card_key] -= 1
            return False
        return True
    
    def remove_card(self, card: Card):
        """Remove card from tracking"""
        card_key = (card.suit, card.value)
        if self.used_cards[card_key] > 0:
            self.used_cards[card_key] -= 1


def parse_card_simple(card_input: str, tracker: CardTracker) -> Optional[Card]:
    """Parse card input without emojis"""
    card_input = card_input.lower().strip()
    
    # Simple mapping
    suits = {"h": Suit.HEARTS, "d": Suit.DIAMONDS, "c": Suit.CLUBS, "s": Suit.SPADES}
    
    if len(card_input) >= 2:
        suit_char = card_input[-1]
        value_part = card_input[:-1]
        
        if suit_char in suits:
            suit = suits[suit_char]
            
            try:
                if value_part in ["a", "ace"]:
                    value = 1
                elif value_part in ["j", "jack"]:
                    value = 11
                elif value_part in ["q", "queen"]:
                    value = 12
                elif value_part in ["k", "king"]:
                    value = 13
                else:
                    value = int(value_part)
                
                if 1 <= value <= 13:
                    card = Card(suit, value)
                    if tracker.track_card(card):
                        return card
                    else:
                        return None
                        
            except ValueError:
                pass
    
    # Show error and examples
    print(f"ERROR: '{card_input}' not recognized!")
    print("Examples: 2h, 7d, 10c, 9s, ah, jd, qc, ks")
    print("Suits: h=Hearts, d=Diamonds, c=Clubs, s=Spades")
    return None


def ai_vs_human_mode():
    """AI plays against human with physical cards"""
    print("=== AI vs Human Mode ===")
    print("AI will play against human opponent")
    print("You execute AI moves exactly as instructed")
    print()
    
    # Setup
    tracker = CardTracker()
    ai_player = SmartBayesPlayer("AI_Player")
    
    # Game state
    ai_hand: List[Optional[Card]] = [None] * 4
    ai_known = [False] * 4
    human_hand_size = 4
    discard_pile: List[Card] = []
    turn_count = 0
    dutch_called = False
    current_player = "ai"  # "ai" or "human"
    
    print("=== Game Setup ===")
    
    # AI's initial card
    print("AI's initial setup:")
    print("AI will peek at position 0")
    
    while True:
        card_input = input("What card does AI see at position 0? (e.g. 7h): ")
        card = parse_card_simple(card_input, tracker)
        if card:
            ai_hand[0] = card
            ai_known[0] = True
            ai_player.hand[0] = card
            ai_player.known_cards[0] = True
            print(f"AI saw: {card}")
            break
    
    # Initial discard pile
    while True:
        discard_input = input("Initial discard pile card? (e.g. 5d): ")
        discard_card = parse_card_simple(discard_input, tracker)
        if discard_card:
            discard_pile.append(discard_card)
            ai_player.observe_card(discard_card)
            print(f"Discard pile: {discard_card}")
            break
    
    print("Setup complete!")
    print()
    
    # Main game loop
    while True:
        print("=" * 40)
        print(f"Turn {turn_count + 1}")
        
        # Show game state
        print(f"\nGame State:")
        ai_display = []
        ai_known_score = 0
        
        for i in range(4):
            card = ai_hand[i]
            if card is None:
                ai_display.append("[ ]")
            elif ai_known[i] and card is not None:
                ai_display.append(f"[{card}]")
                ai_known_score += card.get_score_value()
            else:
                ai_display.append("[?]")
        
        print(f"AI hand: {' '.join(ai_display)}")
        print(f"AI known score: {ai_known_score}")
        print(f"Human cards: {human_hand_size}")
        if discard_pile:
            print(f"Discard top: {discard_pile[-1]}")
        if dutch_called:
            print("DUTCH has been called!")
        
        print(f"\nCurrent turn: {current_player.upper()}")
        
        if current_player == "ai":
            print("\n=== AI's Turn ===")
            
            # Check for matching cards first
            if discard_pile and ai_hand:
                top_card = discard_pile[-1]
                matches = []
                
                for i in range(4):
                    card = ai_hand[i]
                    if (card is not None and 
                        ai_known[i] and 
                        card.value == top_card.value):
                        matches.append((i, card))
                
                if matches:
                    print("AI has matching cards:")
                    for pos, card in matches:
                        print(f"  Position {pos}: {card}")
                    
                    # AI decides whether to discard matches
                    sync_ai_state(ai_player, ai_hand, ai_known)
                    game_state = create_game_state(turn_count, human_hand_size, discard_pile, dutch_called)
                    
                    positions_to_discard = ai_player.want_to_discard_pile_matches(
                        matches, top_card, "before_draw", game_state
                    )
                    
                    if positions_to_discard:
                        print(f"INSTRUCTION: Discard cards at positions: {positions_to_discard}")
                        input("Press Enter when done...")
                        
                        for pos in positions_to_discard:
                            if pos < len(ai_hand):
                                card = ai_hand[pos]
                                if card is not None:
                                    tracker.remove_card(card)
                                    ai_hand[pos] = None
                                    ai_known[pos] = False
                                    ai_player.hand[pos] = None
                                    ai_player.known_cards[pos] = False
                                    print(f"AI discarded {card} from position {pos}")
            
            # Draw card
            print("\nAI draws a card...")
            while True:
                card_input = input("What card did AI draw? (e.g. 9h): ")
                drawn_card = parse_card_simple(card_input, tracker)
                if drawn_card:
                    ai_player.observe_card(drawn_card)
                    break
            
            # Get AI decision
            sync_ai_state(ai_player, ai_hand, ai_known)
            game_state = create_game_state(turn_count, human_hand_size, discard_pile, dutch_called)
            action = ai_player.choose_action(drawn_card, game_state)
            
            print(f"\nAI DECISION:")
            if action["action"] == "discard":
                print(f"INSTRUCTION: Discard {drawn_card}")
                input("Press Enter when done...")
                tracker.remove_card(drawn_card)
                
            elif action["action"] == "swap":
                pos = action["position"]
                current = ai_hand[pos] if pos < 4 and ai_hand[pos] else None
                print(f"INSTRUCTION: Swap {drawn_card} with position {pos}")
                if current:
                    print(f"(Position {pos} currently has: {current})")
                input("Press Enter when done...")
                
                # Update AI state
                if current:
                    tracker.remove_card(current)
                ai_hand[pos] = drawn_card
                ai_known[pos] = True
                ai_player.hand[pos] = drawn_card
                ai_player.known_cards[pos] = True
                
            elif action["action"] == "use_ability":
                if drawn_card.is_jack():
                    print(f"INSTRUCTION: Use JACK - swap with opponent")
                elif drawn_card.is_queen():
                    print(f"INSTRUCTION: Use QUEEN - peek at a card")
                    target = input("Peek at (s)elf or (o)pponent? ").lower()
                    if target == "s":
                        pos = int(input("Which AI position? (0-3): "))
                        card_input = input(f"What card at position {pos}? ")
                        card = parse_card_simple(card_input, tracker)
                        if card:
                            ai_hand[pos] = card
                            ai_known[pos] = True
                            ai_player.hand[pos] = card
                            ai_player.known_cards[pos] = True
                
                input("Press Enter when done...")
                tracker.remove_card(drawn_card)
                
            elif action["action"] == "call_dutch":
                print(f"INSTRUCTION: Call DUTCH! Discard {drawn_card}")
                input("Press Enter when done...")
                dutch_called = True
                tracker.remove_card(drawn_card)
            
            # Check for second matching opportunity
            if discard_pile and ai_hand:
                top_card = discard_pile[-1]
                matches = []
                
                for i in range(4):
                    card = ai_hand[i]
                    if (card is not None and 
                        ai_known[i] and 
                        card.value == top_card.value):
                        matches.append((i, card))
                
                if matches:
                    sync_ai_state(ai_player, ai_hand, ai_known)
                    game_state = create_game_state(turn_count, human_hand_size, discard_pile, dutch_called)
                    
                    positions_to_discard = ai_player.want_to_discard_pile_matches(
                        matches, top_card, "after_turn", game_state
                    )
                    
                    if positions_to_discard:
                        print(f"INSTRUCTION: Discard additional cards at positions: {positions_to_discard}")
                        input("Press Enter when done...")
                        
                        for pos in positions_to_discard:
                            if pos < len(ai_hand) and ai_hand[pos] is not None:
                                card = ai_hand[pos]
                                tracker.remove_card(card)
                                ai_hand[pos] = None
                                ai_known[pos] = False
                                ai_player.hand[pos] = None
                                ai_player.known_cards[pos] = False
            
            current_player = "human"
            
        else:  # human turn
            print("\n=== Human's Turn ===")
            print("What did the human do?")
            print("1. Drew and discarded")
            print("2. Drew and swapped")
            print("3. Used special ability") 
            print("4. Called DUTCH")
            
            choice = input("Choose (1-4): ").strip()
            
            if choice == "1":
                print("Human drew and discarded")
                card_input = input("What card did human discard? ")
                card = parse_card_simple(card_input, tracker)
                if card:
                    discard_pile.append(card)
                    ai_player.observe_card(card)
                    
            elif choice == "2":
                print("Human drew and swapped")
                try:
                    human_hand_size = int(input("Human hand size now? "))
                except ValueError:
                    pass
                    
            elif choice == "3":
                print("Human used special ability")
                ability = input("Which ability? (j)ack/(q)ueen: ").lower()
                if ability == "j":
                    print("Human used Jack (swap)")
                elif ability == "q":
                    print("Human used Queen (peek)")
                    
            elif choice == "4":
                print("Human called DUTCH!")
                dutch_called = True
            
            current_player = "ai"
        
        # Check win condition
        ai_cards_left = sum(1 for card in ai_hand if card is not None)
        if ai_cards_left == 0:
            print("AI WINS - no cards left!")
            break
        elif human_hand_size == 0:
            print("Human wins - no cards left!")
            break
        elif dutch_called:
            print("Game ending due to DUTCH call...")
            break
            
        turn_count += 1
        
        choice = input("\nContinue? (y/n): ").lower()
        if choice == "n":
            break


def sync_ai_state(ai_player, ai_hand, ai_known):
    """Sync AI player state"""
    for i in range(4):
        ai_player.hand[i] = ai_hand[i]
        ai_player.known_cards[i] = ai_known[i]


def create_game_state(turn_count, human_hand_size, discard_pile, dutch_called):
    """Create game state for AI"""
    return {
        "turn_count": turn_count,
        "current_player": "AI_Player",
        "dutch_called": dutch_called,
        "top_discard": discard_pile[-1] if discard_pile else None,
        "player_hand_sizes": {"Human": human_hand_size},
        "players": [{"name": "Human", "hand_size": human_hand_size, "known_cards": 0}]
    } 