from typing import List, Optional, Tuple
import random
from copy import deepcopy

from .card import Card, create_deck
from .player import Player, HumanPlayer, SimpleAI


class Game:
    """Main game engine for the Dutch/Cabo card game"""
    
    def __init__(self, players: List[Player]):
        """
        Initialize a new game.
        
        Args:
            players: List of Player objects (must be 2-4 players)
        """
        if not 2 <= len(players) <= 4:
            raise ValueError("Game must have 2-4 players")
        
        self.players = players
        self.deck: List[Card] = []
        self.discard_pile: List[Card] = []
        self.current_player_index = 0
        self.game_over = False
        self.winner: Optional[Player] = None
        self.turn_count = 0
        self.round_number = 1
        
        # Game settings
        self.max_rounds = 1  # Can be expanded for multiple rounds
        
    def setup_new_game(self):
        """Set up a new game by shuffling deck and dealing cards"""
        print(f"\n{'='*50}")
        print(f"Starting Round {self.round_number}")
        print(f"{'='*50}")
        
        # Reset game state
        self.deck = create_deck()
        random.shuffle(self.deck)
        self.discard_pile = []
        self.game_over = False
        self.winner = None
        self.turn_count = 0
        
        # Reset all players
        for player in self.players:
            player.reset_for_new_game()
        
        # Deal 4 cards to each player
        for player in self.players:
            for position in range(4):
                card = self.deck.pop()
                player.receive_card(card, position)
        
        # Start discard pile with one card
        self.discard_pile.append(self.deck.pop())
        
        # Each player peeks at one card initially
        for player in self.players:
            position = player.choose_initial_peek()
            peeked_card = player.peek_at_own_card(position)
            print(f"{player.name} peeked at position {position}: {peeked_card}")
        
        # Randomly choose starting player
        self.current_player_index = random.randint(0, len(self.players) - 1)
        print(f"\n{self.players[self.current_player_index].name} goes first!")
    
    def get_current_player(self) -> Player:
        """Get the current player"""
        return self.players[self.current_player_index]
    
    def get_other_players(self, exclude_player: Player) -> List[Player]:
        """Get all players except the specified one"""
        return [p for p in self.players if p != exclude_player]
    
    def next_turn(self):
        """Move to the next player's turn"""
        self.current_player_index = (self.current_player_index + 1) % len(self.players)
        self.turn_count += 1
    
    def draw_card(self) -> Card:
        """Draw a card from the deck"""
        if not self.deck:
            # Reshuffle discard pile if deck is empty (keep top card)
            if len(self.discard_pile) <= 1:
                raise RuntimeError("No cards available to draw")
            
            top_card = self.discard_pile.pop()
            self.deck = self.discard_pile.copy()
            random.shuffle(self.deck)
            self.discard_pile = [top_card]
            print("Deck was empty - reshuffled discard pile!")
        
        return self.deck.pop()
    
    def discard_card(self, card: Card):
        """Add a card to the discard pile"""
        self.discard_pile.append(card)
    
    def get_game_state(self) -> dict:
        """Get current game state information (for AI decision making)"""
        return {
            "turn_count": self.turn_count,
            "current_player": self.get_current_player().name,
            "player_hand_sizes": {p.name: p.get_hand_size() for p in self.players},
            "top_discard": self.discard_pile[-1] if self.discard_pile else None,
            "deck_size": len(self.deck),
            "players": [{"name": p.name, "hand_size": p.get_hand_size(), "known_cards": sum(p.known_cards)} 
                       for p in self.players]
        }
    
    def display_game_state(self, current_player: Player):
        """Display the current game state"""
        print(f"\n{'='*60}")
        print(f"Turn {self.turn_count + 1} - {current_player.name}'s Turn")
        print(f"{'='*60}")
        
        # Show all players' hands (hidden for others)
        for player in self.players:
            if player == current_player:
                print(f"YOUR HAND: {player.display_hand()}")
            else:
                print(f"{player.name}: {player.display_hand()} ({player.get_hand_size()} cards)")
        
        print(f"\nTop discard: {self.discard_pile[-1] if self.discard_pile else 'None'}")
        print(f"Cards left in deck: {len(self.deck)}")
    
    def handle_drawn_card_action(self, player: Player, drawn_card: Card, action: dict):
        """
        Handle the player's chosen action with the drawn card.
        
        Args:
            player: The current player
            drawn_card: The card that was drawn
            action: Dictionary describing the chosen action
        """
        action_type = action["action"]
        
        if action_type == "discard":
            # Simply discard the drawn card
            self.discard_card(drawn_card)
            print(f"{player.name} discarded {drawn_card}")
            
        elif action_type == "swap":
            # Swap drawn card with one in hand
            position = action["position"]
            old_card = player.swap_card(position, drawn_card)
            self.discard_card(old_card)
            print(f"{player.name} swapped {drawn_card} for {old_card} at position {position}")
            
        elif action_type == "discard_matches":
            # Remove matching cards and discard all
            removed_cards = player.remove_matching_cards(drawn_card)
            self.discard_card(drawn_card)
            for pos, card in removed_cards:
                self.discard_card(card)
            print(f"{player.name} discarded {drawn_card} and matching cards: {[card for _, card in removed_cards]}")
            
        elif action_type == "use_ability":
            # Use special card ability
            if drawn_card.is_jack():
                self.handle_jack_ability(player, drawn_card)
            elif drawn_card.is_queen():
                self.handle_queen_ability(player, drawn_card)
            # Discard the special card after use
            self.discard_card(drawn_card)
        
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    def handle_jack_ability(self, player: Player, jack_card: Card):
        """Handle Jack's swap ability"""
        opponents = self.get_other_players(player)
        if not opponents:
            print("No opponents to swap with!")
            return
        
        # Choose swap targets
        target_player, target_position = player.choose_swap_target(opponents, self.get_game_state())
        
        # Choose own card to swap
        valid_positions = player.get_valid_positions()
        if not valid_positions:
            print("No cards to swap!")
            return
        
        if isinstance(player, HumanPlayer):
            print("Choose your card to swap:")
            own_position = player._choose_swap_position()
        else:
            # AI chooses randomly for now
            own_position = random.choice(valid_positions)
        
        # Perform the swap
        player_card = player.hand[own_position]
        opponent_card = target_player.hand[target_position]
        
        player.hand[own_position] = opponent_card
        target_player.hand[target_position] = player_card
        
        # Update known cards (both players now know the swapped cards)
        player.known_cards[own_position] = True
        target_player.known_cards[target_position] = True
        
        print(f"{player.name} swapped cards with {target_player.name}")
        print(f"{player.name} received {opponent_card}, {target_player.name} received {player_card}")
    
    def handle_queen_ability(self, player: Player, queen_card: Card):
        """Handle Queen's peek ability"""
        opponents = self.get_other_players(player)
        target_player, target_position = player.choose_peek_target(opponents, self.get_game_state())
        
        if target_player is None:
            # Peek at own card
            peeked_card = player.peek_at_own_card(target_position)
            print(f"{player.name} peeked at their own card at position {target_position}: {peeked_card}")
        else:
            # Peek at opponent's card
            peeked_card = target_player.hand[target_position]
            print(f"{player.name} peeked at {target_player.name}'s card at position {target_position}: {peeked_card}")
    
    def check_win_condition(self) -> bool:
        """
        Check if any player has won (empty hand or very low score).
        Returns True if game should end.
        """
        for player in self.players:
            if player.is_hand_empty():
                self.winner = player
                self.game_over = True
                return True
        
        # Alternative win condition: if someone has a very low score and calls it
        # For now, we'll end the game after a reasonable number of turns
        if self.turn_count >= len(self.players) * 15:  # Arbitrary limit
            # Find player with lowest score
            lowest_score = float('inf')
            for player in self.players:
                score = player.get_score()
                if score < lowest_score:
                    lowest_score = score
                    self.winner = player
            self.game_over = True
            return True
        
        return False
    
    def play_turn(self):
        """Execute one player's turn"""
        current_player = self.get_current_player()
        
        # Display game state
        self.display_game_state(current_player)
        
        # Draw a card
        drawn_card = self.draw_card()
        print(f"\n{current_player.name} draws a card...")
        
        # Player chooses action
        action = current_player.choose_action(drawn_card, self.get_game_state())
        
        # Handle the action
        self.handle_drawn_card_action(current_player, drawn_card, action)
        
        # Check win condition
        if self.check_win_condition():
            return
        
        # Move to next turn
        self.next_turn()
    
    def play_game(self):
        """Play a complete game"""
        self.setup_new_game()
        
        while not self.game_over:
            try:
                self.play_turn()
            except KeyboardInterrupt:
                print("\nGame interrupted by user.")
                return
            except Exception as e:
                print(f"Error during turn: {e}")
                return
        
        self.display_final_results()
    
    def display_final_results(self):
        """Display final game results"""
        print(f"\n{'='*60}")
        print("GAME OVER!")
        print(f"{'='*60}")
        
        if self.winner:
            print(f"🎉 {self.winner.name} wins!")
        
        print("\nFinal Scores:")
        scores = []
        for player in self.players:
            score = player.get_score()
            scores.append((player.name, score))
            print(f"{player.name}: {score} points")
            print(f"  Final hand: {player.display_hand(reveal_all=True)}")
        
        # Sort by score (lowest wins)
        scores.sort(key=lambda x: x[1])
        print(f"\nRanking:")
        for i, (name, score) in enumerate(scores, 1):
            print(f"{i}. {name} - {score} points")


def create_game_from_setup() -> Game:
    """Create a game with player setup"""
    print("Welcome to Dutch Cabo!")
    print("=" * 40)
    
    # Get number of players
    while True:
        try:
            num_players = int(input("Number of players (2-4): "))
            if 2 <= num_players <= 4:
                break
            else:
                print("Please enter a number between 2 and 4.")
        except ValueError:
            print("Please enter a valid number.")
    
    players = []
    
    # Set up players
    for i in range(num_players):
        print(f"\nPlayer {i+1}:")
        print("1. Human player")
        print("2. AI player")
        
        while True:
            try:
                player_type = int(input("Choose player type: "))
                if player_type in [1, 2]:
                    break
                else:
                    print("Please choose 1 or 2.")
            except ValueError:
                print("Please enter a valid number.")
        
        name = input(f"Enter name for player {i+1}: ").strip()
        if not name:
            name = f"Player {i+1}"
        
        if player_type == 1:
            players.append(HumanPlayer(name))
        else:
            players.append(SimpleAI(name))
    
    return Game(players) 