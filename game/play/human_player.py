from typing import List, Optional, Tuple

from ..engine.player_base import PlayerBase
from ..engine.card import Card


class HumanPlayer(PlayerBase):
    """Human player that takes input from the command line"""
    
    def choose_initial_peek(self) -> int:
        """Let human choose which card to peek at initially"""
        print(f"\n{self.name}, choose a card to peek at initially:")
        print("Your hand: [0] [1] [2] [3]")
        
        while True:
            try:
                choice = int(input("Enter position (0-3): "))
                if 0 <= choice <= 3:
                    return choice
                else:
                    print("Please enter a number between 0 and 3.")
            except ValueError:
                print("Please enter a valid number.")
    
    def choose_action(self, drawn_card: Card, game_state: dict) -> dict:
        """Let human choose what to do with drawn card"""
        print(f"\nYou drew: {drawn_card}")
        print(f"Your hand: {self.display_hand()}")
        print(f"Current score: {self.get_score()}")
        
        # Handle special abilities
        if drawn_card.has_special_ability():
            if drawn_card.is_jack():
                print("This Jack allows you to swap cards with an opponent!")
            elif drawn_card.is_queen():
                print("This Queen allows you to peek at any card!")
        
        print("\nChoose an action:")
        print("1. Discard the drawn card")
        print("2. Swap with one of your cards")
        if drawn_card.has_special_ability():
            print("3. Use special ability")
        print("4. Call DUTCH (end the game)")
        
        while True:
            try:
                choice = int(input("Enter choice: "))
                if choice == 1:
                    return {"action": "discard"}
                elif choice == 2:
                    position = self._choose_swap_position()
                    return {"action": "swap", "position": position}
                elif choice == 3 and drawn_card.has_special_ability():
                    return {"action": "use_ability"}
                elif choice == 4:
                    return {"action": "call_dutch"}
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a valid number.")
    
    def _choose_swap_position(self) -> int:
        """Helper method for choosing swap position"""
        valid_positions = self.get_valid_positions()
        print(f"Valid positions: {valid_positions}")
        
        while True:
            try:
                pos = int(input("Choose position to swap (0-3): "))
                if pos in valid_positions:
                    return pos
                else:
                    print("Invalid position. Please choose a valid position.")
            except ValueError:
                print("Please enter a valid number.")
    
    def choose_swap_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[PlayerBase, int]:
        """Let human choose swap target for Jack ability"""
        print("\nChoose opponent to swap with:")
        for i, opponent in enumerate(opponents):
            print(f"{i}: {opponent.name} ({opponent.get_hand_size()} cards)")
        
        # Choose opponent
        while True:
            try:
                opp_choice = int(input("Choose opponent: "))
                if 0 <= opp_choice < len(opponents):
                    target_opponent = opponents[opp_choice]
                    break
                else:
                    print("Invalid opponent choice.")
            except ValueError:
                print("Please enter a valid number.")
        
        # Choose position
        valid_positions = target_opponent.get_valid_positions()
        print(f"Opponent's valid positions: {valid_positions}")
        
        while True:
            try:
                pos_choice = int(input("Choose position: "))
                if pos_choice in valid_positions:
                    return target_opponent, pos_choice
                else:
                    print("Invalid position choice.")
            except ValueError:
                print("Please enter a valid number.")
    
    def choose_own_swap_position(self, game_state: dict) -> int:
        """Let human choose which of their own cards to give away when using Jack"""
        print(f"\n👋 Choose which of YOUR cards to give away:")
        print(f"Your hand: {self.display_hand()}")
        
        valid_positions = self.get_valid_positions()
        print(f"Valid positions: {valid_positions}")
        
        while True:
            try:
                pos = int(input("Choose your position to give away (0-3): "))
                if pos in valid_positions:
                    return pos
                else:
                    print("Invalid position. Please choose a valid position.")
            except ValueError:
                print("Please enter a valid number.")
    
    def choose_peek_target(self, opponents: List[PlayerBase], game_state: dict) -> Tuple[Optional[PlayerBase], int]:
        """Let human choose peek target for Queen ability"""
        print("\nChoose what to peek at:")
        print("0: Your own card")
        for i, opponent in enumerate(opponents):
            print(f"{i+1}: {opponent.name}'s card")
        
        while True:
            try:
                choice = int(input("Choose target: "))
                if choice == 0:
                    # Peek at own card
                    valid_positions = self.get_valid_positions()
                    unknown_positions = [i for i in valid_positions if not self.known_cards[i]]
                    if not unknown_positions:
                        print("You already know all your cards!")
                        continue
                    
                    print(f"Unknown positions: {unknown_positions}")
                    pos = int(input("Choose position: "))
                    if pos in unknown_positions:
                        return None, pos
                    else:
                        print("Invalid position.")
                elif 1 <= choice <= len(opponents):
                    target_opponent = opponents[choice - 1]
                    valid_positions = target_opponent.get_valid_positions()
                    print(f"Opponent's valid positions: {valid_positions}")
                    pos = int(input("Choose position: "))
                    if pos in valid_positions:
                        return target_opponent, pos
                    else:
                        print("Invalid position.")
                else:
                    print("Invalid choice.")
            except ValueError:
                print("Please enter a valid number.")
    
    def choose_draw_source(self, top_discard_card: Card, game_state: dict) -> str:
        """Let human choose where to draw from"""
        print(f"\nDraw options:")
        print(f"1. Draw from deck (unknown card)")
        print(f"2. Draw from discard pile: {top_discard_card} (value: {top_discard_card.get_score_value()})")
        
        while True:
            try:
                choice = int(input("Choose where to draw from (1-2): "))
                if choice == 1:
                    return "deck"
                elif choice == 2:
                    return "discard"
                else:
                    print("Please choose 1 or 2.")
            except ValueError:
                print("Please enter a valid number.")
    
    def want_to_discard_pile_matches(self, matches_available: List[Tuple[int, Card]], 
                                   top_discard_card: Card, timing: str, game_state: dict) -> Optional[List[int]]:
        """Let human choose whether to discard cards matching discard pile"""
        if not matches_available:
            return None
        
        timing_msg = "before drawing" if timing == "before_draw" else "after your turn"
        print(f"\n🎯 You have cards matching the discard pile {timing_msg}!")
        print(f"Top discard: {top_discard_card}")
        
        for i, (pos, card) in enumerate(matches_available):
            print(f"{i+1}. Discard {card} at position {pos} (matches top discard)")
        
        print("0. Keep all matching cards")
        print("A. Discard ALL matching cards")
        
        while True:
            try:
                choice = input("Choose cards to discard (0/A/1-{}): ".format(len(matches_available))).strip().upper()
                
                if choice == "0":
                    return None
                elif choice == "A":
                    # Discard all matches
                    return [pos for pos, card in matches_available]
                else:
                    choice_num = int(choice)
                    if 1 <= choice_num <= len(matches_available):
                        pos, card = matches_available[choice_num - 1]
                        return [pos]
                    else:
                        print(f"Please choose 0, A, or 1-{len(matches_available)}")
            except ValueError:
                print("Please enter a valid option.") 
    
    def want_to_use_special_ability_after_swap(self, special_card: Card, game_state: dict) -> bool:
        """Ask human if they want to use special ability of a card that was swapped out"""
        print(f"\n🃏 You swapped out a {special_card}!")
        
        if special_card.is_jack():
            print("⚡ Jack allows you to swap cards with an opponent!")
        elif special_card.is_queen():
            print("⚡ Queen allows you to peek at any card!")
        
        while True:
            try:
                choice = input("Do you want to use this special ability? (y/n): ").strip().lower()
                if choice in ['y', 'yes', '1']:
                    return True
                elif choice in ['n', 'no', '0']:
                    return False
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
            except (ValueError, EOFError, KeyboardInterrupt):
                print("Invalid input. Please try again.")
                return False 