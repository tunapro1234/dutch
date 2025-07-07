from typing import List, Optional, Tuple
from abc import ABC, abstractmethod
import random

from .card import Card


class Player(ABC):
    """Abstract base class for all players (human and AI)"""
    
    def __init__(self, name: str):
        """
        Initialize a player.
        
        Args:
            name: The player's name/identifier
        """
        self.name = name
        self.hand: List[Optional[Card]] = [None] * 4  # 4 face-down cards
        self.known_cards: List[bool] = [False] * 4     # Track which cards the player knows
        self.initial_peek_used = False
        
    def reset_for_new_game(self):
        """Reset player state for a new game"""
        self.hand = [None] * 4
        self.known_cards = [False] * 4
        self.initial_peek_used = False
    
    def receive_card(self, card: Card, position: int):
        """
        Place a card in the player's hand at the specified position.
        
        Args:
            card: The card to place
            position: Position in hand (0-3)
        """
        if not 0 <= position <= 3:
            raise ValueError("Position must be between 0 and 3")
        self.hand[position] = card
    
    def peek_at_own_card(self, position: int) -> Card:
        """
        Peek at one of the player's own cards.
        
        Args:
            position: Position to peek at (0-3)
            
        Returns:
            The card at that position
        """
        if not 0 <= position <= 3:
            raise ValueError("Position must be between 0 and 3")
        if self.hand[position] is None:
            raise ValueError("No card at that position")
        
        self.known_cards[position] = True
        return self.hand[position]
    
    def swap_card(self, position: int, new_card: Card) -> Card:
        """
        Swap a card in the player's hand with a new card.
        
        Args:
            position: Position to swap (0-3)
            new_card: The new card to place
            
        Returns:
            The old card that was replaced
        """
        if not 0 <= position <= 3:
            raise ValueError("Position must be between 0 and 3")
        if self.hand[position] is None:
            raise ValueError("No card at that position")
            
        old_card = self.hand[position]
        self.hand[position] = new_card
        self.known_cards[position] = True  # Player now knows this card
        return old_card
    

    
    def get_score(self) -> int:
        """Calculate the player's current score (sum of card values)"""
        score = 0
        for card in self.hand:
            if card is not None:
                score += card.get_score_value()
        return score
    
    def get_hand_size(self) -> int:
        """Get the current number of cards in hand"""
        return sum(1 for card in self.hand if card is not None)
    
    def is_hand_empty(self) -> bool:
        """Check if the player has no cards left"""
        return self.get_hand_size() == 0
    
    def get_valid_positions(self) -> List[int]:
        """Get list of positions that have cards"""
        return [i for i in range(4) if self.hand[i] is not None]
    
    def get_known_doubles(self) -> List[Tuple[int, int, Card]]:
        """
        Get pairs of known cards with the same value.
        
        Returns:
            List of (pos1, pos2, card) tuples representing double cards
        """
        doubles = []
        for i in range(4):
            if self.hand[i] is not None and self.known_cards[i]:
                for j in range(i + 1, 4):
                    if (self.hand[j] is not None and 
                        self.known_cards[j] and 
                        self.hand[i].value == self.hand[j].value):
                        doubles.append((i, j, self.hand[i]))
        return doubles
    
    def get_discard_pile_matches(self, top_discard_card: 'Card') -> List[Tuple[int, 'Card']]:
        """
        Get known cards that match the top discard card.
        
        Args:
            top_discard_card: The card on top of discard pile
            
        Returns:
            List of (position, card) tuples for matching cards
        """
        matches = []
        if top_discard_card is None:
            return matches
            
        for i in range(4):
            if (self.hand[i] is not None and 
                self.known_cards[i] and 
                self.hand[i].value == top_discard_card.value):
                matches.append((i, self.hand[i]))
        return matches
    
    def discard_doubles(self, pos1: int, pos2: int) -> Tuple[Card, Card]:
        """
        Discard a pair of cards with the same value.
        
        Args:
            pos1, pos2: Positions of the cards to discard
            
        Returns:
            Tuple of the two discarded cards
        """
        if (pos1 < 0 or pos1 >= 4 or pos2 < 0 or pos2 >= 4 or
            self.hand[pos1] is None or self.hand[pos2] is None):
            raise ValueError("Invalid positions for double discard")
        
        if self.hand[pos1].value != self.hand[pos2].value:
            raise ValueError("Cards must have the same value to discard as doubles")
        
        card1 = self.hand[pos1]
        card2 = self.hand[pos2]
        
        self.hand[pos1] = None
        self.hand[pos2] = None
        self.known_cards[pos1] = False
        self.known_cards[pos2] = False
        
        return card1, card2
    
    def display_hand(self, reveal_all: bool = False) -> str:
        """
        Display the player's hand.
        
        Args:
            reveal_all: If True, show all cards. If False, only show known cards.
            
        Returns:
            String representation of the hand
        """
        hand_str = []
        for i, card in enumerate(self.hand):
            if card is None:
                hand_str.append("[ ]")
            elif reveal_all or self.known_cards[i]:
                hand_str.append(f"[{card}]")
            else:
                hand_str.append("[?]")
        return " ".join(hand_str)
    
    @abstractmethod
    def choose_initial_peek(self) -> int:
        """Choose which card to peek at initially (0-3)"""
        pass
    
    @abstractmethod
    def choose_action(self, drawn_card: Card, game_state: dict) -> dict:
        """
        Choose what action to take with a drawn card.
        
        Args:
            drawn_card: The card that was drawn
            game_state: Current game state information
            
        Returns:
            Dictionary describing the chosen action
        """
        pass
    
    @abstractmethod
    def choose_swap_target(self, opponents: List['Player'], game_state: dict) -> Tuple['Player', int]:
        """
        Choose which opponent and position to swap with (when using Jack).
        
        Args:
            opponents: List of other players
            game_state: Current game state information
            
        Returns:
            Tuple of (target_player, target_position)
        """
        pass
    
    @abstractmethod
    def choose_peek_target(self, opponents: List['Player'], game_state: dict) -> Tuple[Optional['Player'], int]:
        """
        Choose which card to peek at (when using Queen).
        
        Args:
            opponents: List of other players
            game_state: Current game state information
            
        Returns:
            Tuple of (target_player, target_position). If target_player is None, peek at own card.
        """
        pass
    
    def choose_draw_source(self, top_discard_card: 'Card', game_state: dict) -> str:
        """
        Choose whether to draw from deck or discard pile.
        
        Args:
            top_discard_card: The card on top of discard pile
            game_state: Current game state information
            
        Returns:
            "deck" or "discard"
        """
        # Default implementation: always draw from deck
        return "deck"
    
    def want_to_discard_doubles(self, doubles_available: List[Tuple[int, int, 'Card']], 
                               timing: str, game_state: dict) -> Optional[Tuple[int, int]]:
        """
        Choose whether to discard a pair of doubles.
        
        Args:
            doubles_available: List of (pos1, pos2, card) tuples for available doubles
            timing: "before_draw" or "after_turn"
            game_state: Current game state
            
        Returns:
            (pos1, pos2) tuple if want to discard, None otherwise
        """
        # Default implementation: never discard doubles
        return None
    
    def want_to_discard_pile_matches(self, matches_available: List[Tuple[int, 'Card']], 
                                   top_discard_card: 'Card', timing: str, game_state: dict) -> Optional[List[int]]:
        """
        Choose whether to discard cards that match the top discard card.
        
        Args:
            matches_available: List of (position, card) tuples for matching cards
            top_discard_card: The card on top of discard pile
            timing: "before_draw" or "after_turn"
            game_state: Current game state
            
        Returns:
            List of positions to discard, None otherwise
        """
        # Default implementation: never discard matches
        return None


class HumanPlayer(Player):
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
    
    def choose_swap_target(self, opponents: List[Player], game_state: dict) -> Tuple[Player, int]:
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
    
    def choose_peek_target(self, opponents: List[Player], game_state: dict) -> Tuple[Optional[Player], int]:
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
    
    def want_to_discard_doubles(self, doubles_available: List[Tuple[int, int, Card]], 
                               timing: str, game_state: dict) -> Optional[Tuple[int, int]]:
        """Let human choose whether to discard doubles"""
        if not doubles_available:
            return None
        
        timing_msg = "before drawing" if timing == "before_draw" else "after your turn"
        print(f"\n🎲 You have doubles available to discard {timing_msg}:")
        
        for i, (pos1, pos2, card) in enumerate(doubles_available):
            print(f"{i+1}. Discard {card} at positions {pos1} and {pos2} (value: {card.get_score_value()})")
        
        print("0. Keep all doubles (don't discard)")
        
        while True:
            try:
                choice = int(input("Choose doubles to discard (0 to skip): "))
                if choice == 0:
                    return None
                elif 1 <= choice <= len(doubles_available):
                    pos1, pos2, card = doubles_available[choice - 1]
                    return (pos1, pos2)
                else:
                    print(f"Please choose 0-{len(doubles_available)}")
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


class SimpleAI(Player):
    """Simple rule-based AI player"""
    
    def choose_initial_peek(self) -> int:
        """Randomly choose a card to peek at"""
        return random.randint(0, 3)
    
    def choose_action(self, drawn_card: Card, game_state: dict) -> dict:
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