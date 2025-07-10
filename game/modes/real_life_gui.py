"""
Real Life GUI Mode - AI vs Human with physical cards and GUI display
"""

import sys
import os
import threading
import time
from typing import List, Optional, Dict, Any
from collections import defaultdict

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from game.engine import Card, Suit
from game.gui.simple_gui import SimpleGameGUI
from players.bayes.smart_bayes import SmartBayesPlayer


class RealLifeGUITracker:
    """Gerçek kart takibi + GUI görselleştirme"""
    
    def __init__(self):
        self.used_cards = defaultdict(int)
        self.max_per_card = 1
        
    def track_card(self, card: Card) -> bool:
        """Kart kullanımını takip et"""
        card_key = (card.suit, card.value)
        self.used_cards[card_key] += 1
        
        if self.used_cards[card_key] > self.max_per_card:
            print(f"ERROR: {card} already used!")
            self.used_cards[card_key] -= 1
            return False
        return True
    
    def remove_card(self, card: Card):
        """Kartı geri çıkar"""
        card_key = (card.suit, card.value)
        if self.used_cards[card_key] > 0:
            self.used_cards[card_key] -= 1


def parse_card_simple(card_input: str, tracker: RealLifeGUITracker) -> Optional[Card]:
    """Basit kart parse"""
    card_input = card_input.lower().strip()
    
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
    
    print(f"ERROR: '{card_input}' not recognized!")
    print("Examples: 2h, 7d, 10c, 9s, ah, jd, qc, ks")
    print("Suits: h=Hearts, d=Diamonds, c=Clubs, s=Spades")
    return None


def real_life_gui_mode():
    """AI vs Human with physical cards + GUI display"""
    print("=== Real Life GUI Mode ===")
    print("AI plays against human with physical cards")
    print("GUI shows game state visually")
    print("You execute AI moves exactly as instructed")
    print()
    
    # GUI oluştur
    gui = SimpleGameGUI("Dutch Cabo - Real Life Mode")
    
    # Kart tracker
    tracker = RealLifeGUITracker()
    ai_player = SmartBayesPlayer("AI_Player")
    
    # Oyuncuları GUI'ye ekle
    gui.add_player("AI_Player", is_gym_player=True)
    gui.add_player("Human", is_gym_player=False)
    
    # GUI'yi background'da başlat
    gui_thread = threading.Thread(target=gui.start_gui, daemon=True)
    gui_thread.start()
    
    # Oyun durumu
    ai_hand: List[Optional[Card]] = [None] * 4
    ai_known = [False] * 4
    human_hand_size = 4
    discard_pile: List[Card] = []
    turn_count = 0
    dutch_called = False
    current_player = "ai"
    
    # İlk GUI güncellemesi
    update_gui_state(gui, turn_count, current_player, dutch_called, discard_pile, 0)
    
    print("=== Game Setup ===")
    print("Setup your physical cards...")
    
    # AI'ın ilk kartı
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
            
            # GUI'yi güncelle
            update_player_gui(gui, "AI_Player", ai_hand, ai_known, 
                            sum(c.get_score_value() for i, c in enumerate(ai_hand) 
                                if c and ai_known[i]))
            break
    
    # Discard pile
    while True:
        discard_input = input("Initial discard pile card? (e.g. 5d): ")
        discard_card = parse_card_simple(discard_input, tracker)
        if discard_card:
            discard_pile.append(discard_card)
            ai_player.observe_card(discard_card)
            print(f"Discard pile: {discard_card}")
            
            # GUI güncelle
            update_gui_state(gui, turn_count, current_player, dutch_called, discard_pile, 0)
            break
    
    print("Setup complete! Check the GUI window.")
    gui.set_status("Game started! AI vs Human")
    
    # Ana oyun döngüsü
    while True:
        print("\n" + "=" * 50)
        print(f"Turn {turn_count + 1}")
        
        # GUI güncelle
        update_gui_state(gui, turn_count, current_player, dutch_called, discard_pile, 40)
        update_player_gui(gui, "AI_Player", ai_hand, ai_known,
                         sum(c.get_score_value() for i, c in enumerate(ai_hand) 
                             if c and ai_known[i]))
        update_player_gui(gui, "Human", ["?"] * human_hand_size, [False] * human_hand_size, 0, human_hand_size)
        
        if current_player == "ai":
            print("\n=== AI's Turn ===")
            gui.set_status(f"AI's turn (Turn {turn_count + 1})")
            
            # Matching cards check
            if discard_pile and ai_hand:
                top_card = discard_pile[-1]
                matches = []
                
                for i in range(4):
                    card = ai_hand[i]
                    if (card is not None and ai_known[i] and card.value == top_card.value):
                        matches.append((i, card))
                
                if matches:
                    print("AI has matching cards:")
                    for pos, card in matches:
                        print(f"  Position {pos}: {card}")
                    
                    # AI decision
                    sync_ai_state(ai_player, ai_hand, ai_known)
                    game_state = create_game_state(turn_count, human_hand_size, discard_pile, dutch_called)
                    
                    positions_to_discard = ai_player.want_to_discard_pile_matches(
                        matches, top_card, "before_draw", game_state
                    )
                    
                    if positions_to_discard:
                        print(f"INSTRUCTION: Discard cards at positions: {positions_to_discard}")
                        gui.set_status(f"AI discarding matching cards: {positions_to_discard}")
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
            gui.set_status("AI drawing a card...")
            
            while True:
                card_input = input("What card did AI draw? (e.g. 9h): ")
                drawn_card = parse_card_simple(card_input, tracker)
                if drawn_card:
                    ai_player.observe_card(drawn_card)
                    break
            
            # AI decision
            sync_ai_state(ai_player, ai_hand, ai_known)
            game_state = create_game_state(turn_count, human_hand_size, discard_pile, dutch_called)
            action = ai_player.choose_action(drawn_card, game_state)
            
            print(f"\nAI DECISION:")
            if action["action"] == "discard":
                print(f"INSTRUCTION: Discard {drawn_card}")
                gui.set_status(f"AI discards {drawn_card}")
                input("Press Enter when done...")
                tracker.remove_card(drawn_card)
                
            elif action["action"] == "swap":
                pos = action["position"]
                current = ai_hand[pos] if pos < 4 and ai_hand[pos] else None
                print(f"INSTRUCTION: Swap {drawn_card} with position {pos}")
                if current:
                    print(f"(Position {pos} currently has: {current})")
                gui.set_status(f"AI swaps {drawn_card} with position {pos}")
                input("Press Enter when done...")
                
                if current:
                    tracker.remove_card(current)
                ai_hand[pos] = drawn_card
                ai_known[pos] = True
                ai_player.hand[pos] = drawn_card
                ai_player.known_cards[pos] = True
                
            elif action["action"] == "use_ability":
                if drawn_card.is_jack():
                    print(f"INSTRUCTION: Use JACK - swap with opponent")
                    gui.set_status("AI uses JACK ability")
                elif drawn_card.is_queen():
                    print(f"INSTRUCTION: Use QUEEN - peek at a card")
                    gui.set_status("AI uses QUEEN ability")
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
                gui.set_status("AI calls DUTCH!")
                input("Press Enter when done...")
                dutch_called = True
                tracker.remove_card(drawn_card)
            
            current_player = "human"
            
        else:  # human turn
            print("\n=== Human's Turn ===")
            gui.set_status(f"Human's turn (Turn {turn_count + 1})")
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
                    gui.set_status(f"Human discarded {card}")
                    
            elif choice == "2":
                print("Human drew and swapped")
                try:
                    human_hand_size = int(input("Human hand size now? "))
                    gui.set_status("Human swapped a card")
                except ValueError:
                    pass
                    
            elif choice == "3":
                print("Human used special ability")
                gui.set_status("Human used special ability")
                    
            elif choice == "4":
                print("Human called DUTCH!")
                gui.set_status("Human called DUTCH!")
                dutch_called = True
            
            current_player = "ai"
        
        # Win condition check
        ai_cards_left = sum(1 for card in ai_hand if card is not None)
        if ai_cards_left == 0:
            print("AI WINS - no cards left!")
            gui.set_status("AI WINS!")
            break
        elif human_hand_size == 0:
            print("Human wins - no cards left!")
            gui.set_status("Human WINS!")
            break
        elif dutch_called:
            print("Game ending due to DUTCH call...")
            gui.set_status("Game ending - DUTCH called!")
            break
            
        turn_count += 1
        
        choice = input("\nContinue? (y/n): ").lower()
        if choice == "n":
            break
    
    print("Game finished! Check final state in GUI.")
    gui.set_status("Game finished! You can close this window.")
    input("Press Enter to exit...")
    gui.close()


def update_gui_state(gui, turn_count, current_player, dutch_called, discard_pile, deck_size):
    """GUI oyun durumunu güncelle"""
    gui_state = {
        "turn_count": turn_count + 1,
        "current_player": "AI_Player" if current_player == "ai" else "Human",
        "dutch_called": dutch_called,
        "deck_size": deck_size,
        "top_discard": str(discard_pile[-1]) if discard_pile else None
    }
    gui.update_game_state(gui_state)


def update_player_gui(gui, player_name, hand, known_cards, score, hand_size=None):
    """GUI oyuncu durumunu güncelle"""
    if hand_size is None:
        hand_size = sum(1 for card in hand if card is not None)
    
    player_data = {
        "hand": [str(card) if card else None for card in hand],
        "known_cards": known_cards,
        "score": score,
        "hand_size": hand_size
    }
    gui.update_player(player_name, player_data)


def sync_ai_state(ai_player, ai_hand, ai_known):
    """AI player state sync"""
    for i in range(4):
        ai_player.hand[i] = ai_hand[i]
        ai_player.known_cards[i] = ai_known[i]


def create_game_state(turn_count, human_hand_size, discard_pile, dutch_called):
    """Game state for AI"""
    return {
        "turn_count": turn_count,
        "current_player": "AI_Player",
        "dutch_called": dutch_called,
        "top_discard": discard_pile[-1] if discard_pile else None,
        "player_hand_sizes": {"Human": human_hand_size},
        "players": [{"name": "Human", "hand_size": human_hand_size, "known_cards": 0}]
    } 