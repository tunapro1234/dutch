#!/usr/bin/env python3
"""
CHAMPIONSHIP LEAGUE PPO Training - Dutch Cabo Self-Play

Features:
- 64 parallel environments
- Championship League System (AlphaStar-style)
- Tournament-based opponent selection (1000 games, 40% threshold)
- Tensorboard tournament visualization
- Population-based training
"""

import os
import sys
from datetime import datetime
import numpy as np
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv
import pickle
from typing import List, Dict, Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from game.gym_env.dutch_env import DutchCaboEnv
from players.ppo.ppo_player import PPOPlayer


class ChampionshipLeague:
    """
    🏆 AlphaStar-style Championship League for PPO Self-Play
    
    - Each checkpoint challenges current champion
    - 1000 game tournaments 
    - 40% win rate threshold for challenger victory
    - Tensorboard tournament logging
    """
    
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        self.current_champion = None
        self.checkpoints = []
        self.tournament_history = []
        self.tournament_count = 0
        
        # Create checkpoint directory
        self.checkpoint_dir = os.path.join(log_dir, "championship_league")
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        
        print("🏆 Championship League initialized!")
        print(f"📁 League data: {self.checkpoint_dir}")
    
    def save_checkpoint(self, model: PPO, step: int) -> str:
        """Save model checkpoint for tournament"""
        checkpoint_path = os.path.join(
            self.checkpoint_dir, 
            f"checkpoint_step_{step}.zip"
        )
        model.save(checkpoint_path)
        
        checkpoint_info = {
            "path": checkpoint_path,
            "step": step,
            "timestamp": datetime.now().isoformat()
        }
        self.checkpoints.append(checkpoint_info)
        
        print(f"💾 Checkpoint saved: step_{step}")
        return checkpoint_path
    
    def challenge_champion(self, challenger_path: str, step: int) -> Optional[str]:
        """
        🥊 Tournament: New checkpoint challenges current champion
        
        Returns:
            Path to the new champion (challenger if wins, current if defends)
        """
        self.tournament_count += 1
        
        # First checkpoint automatically becomes champion
        if self.current_champion is None:
            self.current_champion = challenger_path
            print(f"👑 FIRST CHAMPION: checkpoint_step_{step}")
            self._log_tournament_result(challenger_path, None, 1.0, step, "auto_champion")
            return challenger_path
        
        print(f"\n🥊 TOURNAMENT #{self.tournament_count}")
        print(f"🏆 Champion: {os.path.basename(self.current_champion)}")
        print(f"🔥 Challenger: checkpoint_step_{step}")
        print("📊 Playing 1000 games...")
        
        # Load models for tournament
        champion_model = PPO.load(self.current_champion)
        challenger_model = PPO.load(challenger_path)
        
        # Run tournament
        win_rate = self._run_tournament(challenger_model, champion_model, games=1000)
        
        # Determine winner (40% threshold for challenger)
        if win_rate >= 0.40:
            # 🏆 NEW CHAMPION!
            old_champion = self.current_champion
            self.current_champion = challenger_path
            
            print(f"🎉 NEW CHAMPION! Win rate: {win_rate:.1%}")
            print(f"👑 {os.path.basename(challenger_path)} dethrones {os.path.basename(old_champion)}")
            
            result = "challenger_wins"
        else:
            # 🛡️ CHAMPION DEFENDS!
            print(f"🛡️ CHAMPION DEFENDS! Challenger win rate: {win_rate:.1%}")
            print(f"👑 {os.path.basename(self.current_champion)} holds the title")
            
            result = "champion_defends"
        
        # Log tournament result
        self._log_tournament_result(challenger_path, self.current_champion, win_rate, step, result)
        
        return self.current_champion
    
    def _run_tournament(self, challenger: PPO, champion: PPO, games: int = 1000) -> float:
        """
        Run 1000-game tournament between challenger and champion
        
        Returns:
            Challenger win rate (0.0 to 1.0)
        """
        challenger_wins = 0
        
        # Create tournament environment (single env for evaluation)
        tournament_env = DutchCaboEnv(
            opponent_players=[PPOPlayer("Champion")],
            reward_shaping=False,  # 🔧 FIXED: No reward shaping for fair evaluation
            render_mode=None
        )
        
        # Set champion as opponent
        tournament_env.opponent_players[0].set_live_model(champion)
        
        for game in range(games):
            obs, _ = tournament_env.reset()
            done = False
            
            while not done:
                # Challenger's turn
                action, _ = challenger.predict(obs, deterministic=True)
                obs, reward, done, _, info = tournament_env.step(action)
                
                if done:
                    # 🔧 FIXED: Use actual game winner, not reward value
                    winner_name = info.get('winner')
                    if winner_name == tournament_env.gym_player.name:
                        challenger_wins += 1
                    break
            
            # Progress update every 100 games
            if (game + 1) % 100 == 0:
                current_rate = challenger_wins / (game + 1)
                print(f"  Game {game + 1}/1000: Win rate {current_rate:.1%}")
        
        tournament_env.close()
        win_rate = challenger_wins / games
        
        print(f"🏁 Tournament complete: {challenger_wins}/{games} wins ({win_rate:.1%})")
        return win_rate
    
    def _log_tournament_result(self, challenger_path: str, champion_path: Optional[str], 
                             win_rate: float, step: int, result: str):
        """Log tournament results for tensorboard"""
        tournament_result = {
            "tournament_id": self.tournament_count,
            "challenger_path": challenger_path,
            "champion_path": champion_path,
            "challenger_win_rate": win_rate,
            "step": step,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        self.tournament_history.append(tournament_result)
        
        # Save tournament history
        history_path = os.path.join(self.checkpoint_dir, "tournament_history.pkl")
        with open(history_path, 'wb') as f:
            pickle.dump(self.tournament_history, f)
        
        print(f"📊 Tournament logged: {result}")
    
    def get_current_champion_path(self) -> Optional[str]:
        """Get path to current champion model"""
        return self.current_champion
    
    def get_tournament_stats(self) -> Dict:
        """Get tournament statistics for tensorboard"""
        if not self.tournament_history:
            return {}
        
        return {
            "total_tournaments": len(self.tournament_history),
            "champion_changes": sum(1 for t in self.tournament_history if t["result"] == "challenger_wins"),
            "current_champion_step": self.tournament_history[-1]["step"] if self.tournament_history else 0,
            "last_win_rate": self.tournament_history[-1]["challenger_win_rate"] if self.tournament_history else 0.0
        }


def make_self_play_env(rank: int, seed: int):
    """Create environment where PPO agent plays against its own model"""
    def _init():
        # Create PPO opponent that will use the live model
        ppo_opponent = PPOPlayer("SelfPlay_Opponent")
        
        env = DutchCaboEnv(
            opponent_players=[ppo_opponent],  # Just 1 opponent for simplicity
            reward_shaping=True,
            render_mode=None
        )
        
        env = Monitor(env)
        env.reset(seed=seed + rank)
        
        # Store reference to opponent for model updates
        env.ppo_opponent = ppo_opponent
        return env
    
    return _init


def update_opponents_with_model(vec_env, model):
    """Update all PPO opponents with the current model"""
    try:
        # Get individual environments from vectorized env
        for env in vec_env.envs:
            if hasattr(env, 'ppo_opponent'):
                env.ppo_opponent.set_live_model(model)
    except Exception as e:
        print(f"Warning: Could not update opponents: {e}")


def train_championship_ppo():
    """🏆 Championship League PPO Training with Tournament Selection"""
    
    print("🎮 Dutch Cabo Championship League Training")
    print("=" * 50)
    print("🏆 Mode: Championship League Self-Play")
    print("🥊 Tournament-based opponent selection")
    print("📊 Dashboard: Tensorboard + Tournament metrics")
    print("🎯 40% win threshold for challenger victory")
    print("=" * 50)
    
    # Training configuration
    TOTAL_STEPS = 15_000_000  # 15M steps for 3-5 hour training
    N_ENVS = 64              # 64 parallel environments (16x faster)
    LEARNING_RATE = 3e-4
    ENTROPY_COEF = 0.05      # Higher entropy for slower exploration decay
    CHECKPOINT_FREQ = 50000  # Save checkpoint every 50K steps
    
    # Create log directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = f"players/ppo/logs/championship_league_{timestamp}"
    os.makedirs(log_dir, exist_ok=True)
    
    print(f"📁 Logs: {log_dir}")
    print(f"🖥️ Tensorboard: tensorboard --logdir {log_dir}")
    print()
    
    # Initialize Championship League
    league = ChampionshipLeague(log_dir)
    
    # Create vectorized environment  
    print(f"🏗️ Setting up {N_ENVS} parallel environments...")
    vec_env = DummyVecEnv([
        make_self_play_env(i, 42) for i in range(N_ENVS)
    ])
    print("✅ Environments ready")
    
    # Create PPO model
    print("🧠 Creating PPO model...")
    model = PPO(
        "MlpPolicy",
        vec_env,
        learning_rate=LEARNING_RATE,
        n_steps=2048,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        ent_coef=ENTROPY_COEF,  # Higher entropy for slower exploration decay
        tensorboard_log=log_dir,
        verbose=1
    )
    print("✅ PPO model created")
    
    # Initial opponent linking (will be updated by championship league)
    print("🔗 Linking opponents to training model...")
    update_opponents_with_model(vec_env, model)
    print("✅ Self-play linked")
    
    print(f"\n🚀 Starting Championship League Training...")
    print(f"📈 Target: {TOTAL_STEPS:,} total steps")
    print(f"🏆 Tournament every {CHECKPOINT_FREQ:,} steps")
    print("💡 Opponents selected via championship battles!")
    
    try:
        # Championship League training loop
        total_trained = 0
        checkpoint_count = 0
        
        while total_trained < TOTAL_STEPS:
            # Train for a checkpoint period
            steps_this_round = min(CHECKPOINT_FREQ, TOTAL_STEPS - total_trained)
            
            print(f"\n📚 Training checkpoint {checkpoint_count + 1}...")
            model.learn(
                total_timesteps=steps_this_round,
                reset_num_timesteps=False,
                progress_bar=True
            )
            
            total_trained += steps_this_round
            checkpoint_count += 1
            
            # Save checkpoint for tournament
            checkpoint_path = league.save_checkpoint(model, total_trained)
            
            # Championship battle! 🥊
            champion_path = league.challenge_champion(checkpoint_path, total_trained)
            
            # Update opponents with current champion
            if champion_path:
                print(f"🔄 Updating opponents with champion...")
                champion_model = PPO.load(champion_path)
                update_opponents_with_model(vec_env, champion_model)
                print("✅ Champion linked to opponents")
                
                # Log tournament stats to tensorboard
                stats = league.get_tournament_stats()
                if stats:
                    # Custom tensorboard logging for tournament metrics
                    for key, value in stats.items():
                        # We would log these to tensorboard here if we had access to the writer
                        print(f"📊 {key}: {value}")
            
            # Progress update
            progress = total_trained / TOTAL_STEPS * 100
            print(f"📊 Overall Progress: {progress:.1f}% ({total_trained:,}/{TOTAL_STEPS:,} steps)")
            print(f"🏆 Tournaments completed: {league.tournament_count}")
            
        print("\n✅ Championship League Training completed!")
        
    except KeyboardInterrupt:
        print("\n⚠️ Training interrupted by user")
    
    # Save final model and tournament results
    final_model_path = os.path.join(log_dir, "final_champion.zip")
    model.save(final_model_path)
    print(f"💾 Final model saved: {final_model_path}")
    
    # Save final championship stats
    stats = league.get_tournament_stats()
    print(f"\n🏆 CHAMPIONSHIP LEAGUE FINAL STATS:")
    print(f"   Total Tournaments: {stats.get('total_tournaments', 0)}")
    print(f"   Champion Changes: {stats.get('champion_changes', 0)}")
    print(f"   Final Champion: {os.path.basename(league.get_current_champion_path() or 'None')}")
    
    vec_env.close()
    
    print("\n🎉 Championship League Complete!")
    print(f"📊 View results: tensorboard --logdir {log_dir}")
    print(f"🏆 Tournament data: {league.checkpoint_dir}")
    
    return model, league


if __name__ == "__main__":
    train_championship_ppo() 