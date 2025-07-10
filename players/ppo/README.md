# Dutch Cabo PPO Training System

Bu klasör Dutch Cabo oyunu için PPO (Proximal Policy Optimization) reinforcement learning sistemi içermektedir.

## 🎯 Özellikler

### ✅ **Tamamlanan Sistemler**

1. **Training Pipeline** 
   - Stable Baselines3 ile PPO implementation
   - Paralel environment support (4-16 env)
   - Advanced callback sistemi
   - Early stopping ve checkpointing

2. **Dashboard & Monitoring**
   - **Tensorboard**: Gerçek zamanlı training metrics
   - **Wandb**: Gelişmiş dashboard ve experiment tracking
   - Custom metrics: win rate, episode length, reward tracking
   - Real-time progress updates

3. **Configuration System**
   - **fast_training.json**: Hızlı test için (100K steps, 2 env)
   - **production_training.json**: Ciddi training için (2M steps, 8 env)  
   - **extreme_training.json**: Maximum performance için (5M steps, 16 env)

4. **Model Evaluation**
   - Farklı opponent type'lara karşı test
   - Detaylı performance metrics
   - Win rate, score distribution, position analysis
   - JSON export ile results tracking

5. **PPO Player Class**
   - Trained model'i oyunda kullanma
   - Action validation ve fallback strategies
   - Game state observation conversion
   - Strategic decision making for special abilities

## 📁 Klasör Yapısı

```
players/ppo/
├── __init__.py                    # Module initialization
├── train_ppo.py                   # 🚀 ANA TRAINING SCRIPT
├── ppo_player.py                  # 🤖 Trained model player
├── evaluate_model.py              # 📊 Model evaluation
├── configs/                       # ⚙️ Training configurations
│   ├── fast_training.json         #   Hızlı test (100K steps)
│   ├── production_training.json   #   Production (2M steps) 
│   └── extreme_training.json      #   Extreme (5M steps)
├── logs/                          # 📈 Training logs (auto-created)
└── evaluations/                   # 📋 Evaluation results (auto-created)
```

## 🚀 Kullanım

### 1. **Hızlı Training Başlatma**

```bash
# Temel training (default config)
cd players/ppo
python train_ppo.py

# Fast training config ile
python train_ppo.py --config configs/fast_training.json

# Wandb dashboard ile
python train_ppo.py --wandb

# GPU kullanarak
python train_ppo.py --device cuda --envs 8
```

### 2. **Advanced Training Options**

```bash
# Production-level training
python train_ppo.py \
    --config configs/production_training.json \
    --wandb \
    --device cuda

# Custom parametreler
python train_ppo.py \
    --timesteps 500000 \
    --envs 6 \
    --lr 2e-4 \
    --wandb

# CPU-only training (multiprocessing disable)
python train_ppo.py \
    --no-multiprocessing \
    --envs 2 \
    --device cpu
```

### 3. **Model Evaluation**

```bash
# Basit evaluation
python evaluate_model.py path/to/model.zip

# Detaylı evaluation 
python evaluate_model.py path/to/model.zip \
    --games 200 \
    --detailed

# Quiet mode
python evaluate_model.py path/to/model.zip \
    --games 50 \
    --quiet \
    --output my_eval_results.json
```

### 4. **Trained Model Kullanma**

```python
from players.ppo import PPOPlayer

# Model load etme
ppo_agent = PPOPlayer("MyPPO", "path/to/trained_model.zip")

# Oyunda kullanma
players = [ppo_agent, SimpleAI("AI1"), BayesPlayer("AI2")]
# ... game setup
```

## 📊 Dashboard Kullanımı

### **Tensorboard**
```bash
# Training sırasında başka terminal'de:
tensorboard --logdir players/ppo/logs

# Browser'da: http://localhost:6006
```

**Tensorboard Metrics:**
- `custom/mean_episode_reward`: Ortalama episode reward
- `custom/win_rate`: Win rate (son 100 episode)
- `custom/mean_episode_length`: Ortalama oyun uzunluğu
- `custom/episode_count`: Toplam episode sayısı
- `train/learning_rate`: Learning rate
- `train/loss`: Policy ve value loss'lar

### **Wandb Dashboard**
```bash
# Training ile başlatma
python train_ppo.py --wandb

# Otomatik olarak browser'da açılır veya:
# https://wandb.ai/your-username/dutch-cabo-ppo
```

**Wandb Features:**
- Real-time metric plotting
- Hyperparameter comparison
- Model artifacts tracking
- Experiment comparison
- Team collaboration

## ⚙️ Configuration Açıklaması

### **Training Parameters**
- `learning_rate`: Neural network learning rate (3e-4 optimal)
- `n_steps`: Steps per environment per update (2048 default)
- `batch_size`: Mini-batch size (64 default)
- `n_epochs`: Training epochs per update (10 default)
- `total_timesteps`: Total training steps (1M+ recommended)
- `n_envs`: Parallel environments (4-16 optimal)

### **Environment Parameters**
- `reward_shaping`: Additional reward signals (recommended: true)
- `opponent_types`: ["simple", "bayes", "simple"] mix of opponents

### **Example Custom Config**
```json
{
  "learning_rate": 3e-4,
  "n_steps": 2048,
  "batch_size": 64,
  "total_timesteps": 1000000,
  "n_envs": 4,
  "opponent_types": ["simple", "bayes", "simple"],
  "reward_shaping": true
}
```

## 🎮 Action Space (16 discrete actions)

```
0-3:   Draw from deck + swap with position 0-3
4-7:   Draw from discard + swap with position 0-3  
8:     Draw from deck + discard
9:     Use special ability (Jack/Queen)
10:    Call Dutch
11-14: Discard matching cards from positions 0-3
15:    Skip/fallback action
```

## 🔍 Observation Space (36 dimensions)

```
0-15:  Own hand (4 cards × 4 attributes each)
       - Card value, is_known, is_valid, is_revealed
16-23: Game state 
       - Turn count, deck size, discard_top, dutch_called, etc.
24-35: Opponent info (3 opponents × 4 attributes)
       - Hand size, known_cards_ratio, estimated_score, is_current
```

## 🏆 Performance Expectations

### **Training Phases**
1. **Exploration** (0-100K steps): Random play, learning basics
2. **Learning** (100K-500K steps): Strategy development
3. **Optimization** (500K-1M+ steps): Fine-tuning advanced play

### **Expected Win Rates**
- vs **SimpleAI**: 40-60% (after 500K steps)
- vs **BayesPlayer**: 25-40% (after 1M steps)  
- vs **Mixed opponents**: 30-45% (production target)

### **Evaluation Metrics**
- **Win Rate**: Oyunları kazanma oranı
- **Average Score**: Ortalama final score (düşük daha iyi)
- **Position Distribution**: 1st/2nd/3rd/4th finish oranları
- **Game Length**: Ortalama oyun uzunluğu (turn)

## 🐛 Troubleshooting

### **Common Issues**

1. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'stable_baselines3'
   ```
   **Solution**: `conda env update -f environment.yml`

2. **CUDA Out of Memory**
   ```
   RuntimeError: CUDA out of memory
   ```
   **Solution**: `--device cpu` veya `--envs 2` kullanın

3. **Low Win Rate** 
   - Daha uzun training: `--timesteps 2000000`
   - Farklı config: `--config configs/extreme_training.json`
   - Reward shaping check: config'de `"reward_shaping": true`

4. **Training Çok Yavaş**
   - Multiprocessing enable: Remove `--no-multiprocessing`
   - Daha az env: `--envs 2`
   - Smaller config: `--config configs/fast_training.json`

## 🔬 Advanced Features

### **Custom Reward Shaping**
Environment'ta reward fonksiyonu customize edilebilir:
- **Win bonus**: +100 for winning
- **Score penalty**: -0.1 per score point  
- **Learning bonus**: +0.5 per card learned
- **Improvement bonus**: +2.0 per score improvement

### **Hyperparameter Tuning**
Key parameters for tuning:
- `learning_rate`: 1e-4 to 5e-4
- `ent_coef`: 0.005 to 0.02 (exploration)
- `clip_range`: 0.1 to 0.3 (policy updates)
- `gamma`: 0.99 to 0.995 (discount factor)

### **Model Architecture**
- **Policy**: MlpPolicy (Multi-layer perceptron)
- **Input**: 36-dimensional observation
- **Output**: 16-dimensional action space
- **Hidden layers**: 2x64 neurons (SB3 default)

## 📈 Monitoring & Logging

### **File Locations**
- **Training logs**: `players/ppo/logs/ppo_dutch_cabo_YYYYMMDD_HHMMSS/`
- **Model checkpoints**: `logs/.../checkpoints/`
- **Best models**: `logs/.../best_model/`
- **Evaluations**: `players/ppo/evaluations/`

### **Log Files**
- `final_model.zip`: Trained model
- `training_config.json`: Training configuration
- `evaluations.npz`: Evaluation metrics
- `progress.csv`: Training progress

## 🚀 Next Steps

Bu sistem hazır! Şimdi:

1. **İlk training başlat**: `python train_ppo.py --config configs/fast_training.json`
2. **Dashboard aç**: `tensorboard --logdir logs`
3. **Model train et**: En az 100K steps
4. **Evaluate et**: `python evaluate_model.py path/to/model.zip`
5. **Production training**: `configs/production_training.json` kullan

**Production için önerilen workflow:**
```bash
# 1. Fast test
python train_ppo.py --config configs/fast_training.json

# 2. Production training  
python train_ppo.py --config configs/production_training.json --wandb --device cuda

# 3. Evaluation
python evaluate_model.py logs/best_model/best_model.zip --detailed

# 4. Use in game
# PPOPlayer("Agent", "path/to/best_model.zip") 
```

Bu sistem ile Dutch Cabo'da competitive AI agent'lar eğitebilirsin! 🎉 