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
1. **Optional**: Discard any pairs of known matching cards (before drawing)
2. Draws a card from the deck or discard pile
3. Chooses one action:
   - **Discard** the drawn card
   - **Swap** the drawn card with one of their face-down cards
   - **Use special ability** (if the card is a Jack or Queen)
4. **Optional**: Discard any pairs of known matching cards (after actions)

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

**⚡ Quick 2-Player Game** (Recommended):
```bash
python quick_game.py
```
- Simple command-line interface for human vs AI
- Choose from 3 different AI opponents
- Streamlined setup with **Dutch call** feature
- **Hidden peek** - only you see the cards you peek at

**📝 Full CLI Setup**:
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
├── quick_game.py         # ⚡ Quick 2-player CLI launcher (BEST)
├── main.py               # 📝 Full CLI game (2-4 players)
├── test_setup.py         # Environment and functionality tests
├── test_gpu.py           # 🔧 PyTorch GPU benchmark
├── README.md             # This file
├── src/                  # Core game engine
│   ├── __init__.py       # Package initialization
│   ├── card.py           # Card class and deck creation
│   ├── player.py         # Base player classes (Human, Player)
│   └── game.py           # Main game engine with Dutch calls
└── players/              # AI player implementations
    ├── __init__.py       # Player package initialization
    ├── basic_ai.py       # RandomPlayer and RandomAI
    └── simple_ai.py      # SimpleAI (more strategic)
```

## 🧠 AI Players

The `players/` folder contains AI implementations:

### SimpleAI (simple_ai.py)
- Strategic decision making with min/max score calculation
- Smart double discard timing (prefers high-value doubles)
- Advanced heuristics for card evaluation
- Intelligent draw source selection (deck vs discard)
- Improved Dutch call logic with guaranteed win detection
- 40% more aggressive than before

### BayesPlayer (bayes_player.py)
- **Advanced Bayesian probability analysis**
- **Min/Max score range calculations** for perfect Dutch timing
- **Opponent modeling** - tracks behavior, actions, and card knowledge
- **Guaranteed win detection** - calls Dutch when mathematically certain
- **Confidence-based decisions** with multiple aggression levels
- **Real-time deck composition tracking** and probability updates
- **Strategic opponent estimation** based on observed play patterns

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

- ✅ **Improved CLI interface** with intuitive text-based gameplay
- ✅ **Strategic double discard system** - discard pairs before/after turns
- ✅ **Dutch call system** - end the game when you want!
- ✅ **Hidden peek mechanics** - only you see what you peek at
- ✅ **GPU-accelerated PyTorch** ready for RL training (RTX 3070 tested)  
- ✅ **Human vs AI gameplay** with strategic SimpleAI opponent
- ✅ **All special card rules** implemented (Red Kings, Jack/Queen abilities)
- ✅ **Modular, clean OOP design** ready for RL agent integration
- ✅ **Comprehensive test coverage** for both game logic and GPU performance

---

**Ready to play?** Run `python quick_game.py` and call DUTCH when you're ready! 🎯🚨 