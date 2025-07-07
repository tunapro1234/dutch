# Dutch Cabo Card Game 🎮

A reinforcement learning project implementing a Cabo-like hidden-information card game with PyTorch. This project focuses on building a complete game environment first, then training RL agents to play optimally.

## 🎯 Game Rules

**Objective**: Minimize the total value of cards in your hand when the game ends.

### Setup
- Each player starts with 4 face-down cards
- Players peek at 1 of their own cards initially
- A draw pile and discard pile are created

### Gameplay
On each turn, a player:
1. Draws a card from the deck
2. Chooses one action:
   - **Discard** the drawn card
   - **Swap** the drawn card with one of their face-down cards
   - **Use special ability** (if the card is a Jack or Queen)
   - **Discard matches** (if they have cards matching the drawn card's value)

### Special Cards
- **Red Kings** (♥K, ♦K): Worth 0 points
- **Black Kings** (♠K, ♣K): Worth 10 points  
- **Jacks**: Allow swapping cards with opponents
- **Queens**: Allow peeking at any card (yours or opponent's)
- **Face cards**: Worth 10 points (except red Kings)
- **Aces**: Worth 1 point

### Winning
- Game ends when a player has no cards left OR after a set number of turns
- Player with the **lowest total score** wins

## 🛠️ Setup Instructions

### Option 1: Using Conda (Recommended)
```bash
# Create and activate conda environment
conda env create -f environment.yml
conda activate dutch

# Test the setup
python test_setup.py

# Run the game
python main.py
```

### Option 2: Using System Python
```bash
# Install dependencies
pip install torch numpy pytest black

# Test the setup  
python test_setup.py

# Run the game
python main.py
```

## 🎮 How to Play

### Starting a Game

**Quick 2-Player Game** (Recommended):
```bash
python quick_game.py
```
- Simple interface for human vs AI
- Choose from 3 different AI opponents
- Streamlined setup for fast gameplay

**Full Game Setup**:
```bash
python main.py
```
- Choose number of players (2-4)
- Select player types (Human or AI) for each player
- Enter names for each player

### Game Interface
- Your hand shows known cards and `[?]` for unknown cards
- Positions are numbered 0-3 from left to right
- Follow the prompts to make decisions each turn

### Example Turn
```
============================================================
Turn 5 - Alice's Turn
============================================================
YOUR HAND: [3♥] [?] [?] [K♦]
Bob: [?] [?] [?] [?] (4 cards)
AI_Charlie: [?] [?] [?] [ ] (3 cards)

Top discard: 7♠
Cards left in deck: 31

Alice draws a card...
You drew: J♣
This Jack allows you to swap cards with an opponent!

Choose an action:
1. Discard the drawn card
2. Swap with one of your cards  
3. Use special ability
Enter choice: 3
```

## 📁 Project Structure

```
dutch/
├── .gitignore             # Git ignore patterns
├── environment.yml        # Conda environment specification
├── main.py               # Main game entry point (2-4 players)
├── quick_game.py         # Quick 2-player game launcher
├── test_setup.py         # Environment and functionality tests
├── README.md             # This file
├── src/                  # Core game engine
│   ├── __init__.py       # Package initialization
│   ├── card.py           # Card class and deck creation
│   ├── player.py         # Base player classes (Human, Player)
│   └── game.py           # Main game engine
└── players/              # AI player implementations
    ├── __init__.py       # Player package initialization
    ├── basic_ai.py       # RandomPlayer and RandomAI
    └── simple_ai.py      # SimpleAI (more strategic)
```

## 🧠 AI Players

The `players/` folder contains different AI implementations:

### RandomPlayer (basic_ai.py)
- Makes logical but simple decisions
- Always discards matches (optimal)
- Uses special abilities when beneficial
- Simple value-based card evaluation (keep low, discard high)
- Good for learning the game mechanics

### RandomAI (basic_ai.py)
- Makes completely random valid moves
- 70% chance to discard matches
- Random choice between discard/swap/ability
- Useful for testing edge cases

### SimpleAI (simple_ai.py)
- More strategic than RandomPlayer
- Advanced heuristics for decision making
- Prefers opponent information gathering
- Better at evaluating card value trades

## 🚀 Next Steps (RL Development)

This project is designed to support reinforcement learning development:

1. **Environment API**: Game state can be extracted for RL agents
2. **Action Space**: Well-defined action dictionaries for agent decisions
3. **Observation Space**: Game state includes partial information about opponents
4. **Reward Structure**: Score-based rewards with hidden information challenges

Future RL components will include:
- PyTorch neural network agents
- Deep Q-Learning (DQN) implementation
- Policy gradient methods for partial observability
- Multi-agent training scenarios

## 🧪 Testing

Run the test suite to verify everything works:
```bash
python test_setup.py
```

This tests:
- ✅ Dependencies (torch, numpy)
- ✅ Module imports
- ✅ Card creation and special rules
- ✅ Player functionality  
- ✅ Game initialization

## 🎯 Features

- ✅ Complete CLI interface
- ✅ Human vs AI gameplay
- ✅ All special card rules implemented
- ✅ Modular, clean OOP design
- ✅ Ready for RL agent integration
- ✅ Comprehensive test coverage

---

**Ready to play?** Run `python quick_game.py` for a quick 2-player game! 🎉 