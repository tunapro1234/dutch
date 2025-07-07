from typing import Optional
from enum import Enum


class Suit(Enum):
    """Card suits"""
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


class Card:
    """Represents a playing card with suit and value"""
    
    def __init__(self, suit: Suit, value: int):
        """
        Initialize a card.
        
        Args:
            suit: The card's suit
            value: The card's value (1-13, where 1=Ace, 11=Jack, 12=Queen, 13=King)
        """
        if not isinstance(suit, Suit):
            raise ValueError("suit must be a Suit enum")
        if not 1 <= value <= 13:
            raise ValueError("value must be between 1 and 13")
            
        self.suit = suit
        self.value = value
    
    def __str__(self) -> str:
        """String representation of the card"""
        if self.value == 1:
            value_str = "A"
        elif self.value == 11:
            value_str = "J"
        elif self.value == 12:
            value_str = "Q"
        elif self.value == 13:
            value_str = "K"
        else:
            value_str = str(self.value)
        return f"{value_str}{self.suit.value}"
    
    def __repr__(self) -> str:
        return f"Card({self.suit}, {self.value})"
    
    def __eq__(self, other) -> bool:
        """Check if two cards are equal (same value, ignoring suit for game logic)"""
        if not isinstance(other, Card):
            return False
        return self.value == other.value
    
    def __hash__(self) -> int:
        return hash((self.suit, self.value))
    
    def get_score_value(self) -> int:
        """
        Get the card's value for scoring purposes.
        Special rules:
        - Red Kings (Hearts/Diamonds) are worth 0 points
        - Black Kings are worth 10 points
        - Jacks and Queens are worth 10 points
        - Aces are worth 1 point
        """
        if self.value == 13:  # King
            if self.suit in [Suit.HEARTS, Suit.DIAMONDS]:  # Red King
                return 0
            else:  # Black King
                return 10
        elif self.value >= 11:  # Jack, Queen
            return 10
        return self.value
    
    def is_jack(self) -> bool:
        """Check if this card is a Jack (allows swapping with opponents)"""
        return self.value == 11
    
    def is_queen(self) -> bool:
        """Check if this card is a Queen (allows peeking at cards)"""
        return self.value == 12
    
    def is_red_king(self) -> bool:
        """Check if this card is a red King (worth 0 points)"""
        return self.value == 13 and self.suit in [Suit.HEARTS, Suit.DIAMONDS]
    
    def has_special_ability(self) -> bool:
        """Check if this card has a special ability when drawn"""
        return self.is_jack() or self.is_queen()


def create_deck() -> list[Card]:
    """Create a standard 52-card deck"""
    deck = []
    for suit in Suit:
        for value in range(1, 14):  # 1-13
            deck.append(Card(suit, value))
    return deck 