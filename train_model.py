import numpy as np
import pandas as pd
import gym
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
import logging
import os
import argparse
from datetime import datetime

from trading_env import TradingEnv
from utils import fetch_historical_data, preprocess_data, normalize_data, split_data_train_test, calculate_sharpe_ratio
from config import WINDOW_SIZE, INITIAL_BALANCE, MODEL_PATH

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def train_model(data, model_path=MODEL_PATH, timesteps=100000, eval_freq=10000):
    """Train a PPO model on the provided data"""
    # Create the environment
    env = TradingEnv(data=data, initial_balance=INITIAL_BALANCE, window_size=WINDOW_SIZE)
    
    # Vectorize the environment
    env = DummyVecEnv([lambda: env])
    
    # Create the model
    model = PPO(
        "MlpPolicy", 
        env, 
        verbose=1,
        learning_rate=3e-4,
        n_steps=2048,
        batch_size=64,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        clip_range_vf=None,
        ent_coef=0.01,
        vf_coef=0.5,
        max_grad_norm=0.5,
        tensorboard_log="./tensorboard_logs/"
    )
    
    logger.info(f"Starting model training for {timesteps} timesteps...")
    
    # Train the model
    model.learn(total_timesteps=timesteps)
    
    # Save the model
    model.save(model_path)
    logger.info(f"Model saved to {model_path}")
    
    return model

def evaluate_model(model, env, episodes=10):
    """Evaluate the trained model on test data"""
    returns = []
    sharpe_ratios = []
    
    for episode in range(episodes):
        obs = env.reset()
        done = False
        episode_return = 0
        episode_rewards = []
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            episode_return += reward
            episode_rewards.append(reward)
        
        returns.append(episode_return)
        
        # Calculate Sharpe ratio for this episode
        if len(episode_rewards) > 0:
            episode_sharpe = calculate_sharpe_ratio(np.array(episode_rewards))
            sharpe_ratios.append(episode_sharpe)
        
        logger.info(f"Episode {episode+1}/{episodes} - Return: {episode_return:.2f}")
    
    avg_return = sum(returns) / len(returns) if returns else 0
    avg_sharpe = sum(sharpe_ratios) / len(sharpe_ratios) if sharpe_ratios else 0
    
    logger.info(f"Average return: {avg_return:.2f}")
    logger.info(f"Average Sharpe ratio: {avg_sharpe:.2f}")
    
    return avg_return, avg_sharpe

def main():
    """Main function to train and evaluate the model"""
    parser = argparse.ArgumentParser(description='Train a RL trading bot')
    parser.add_argument('--symbol', type=str, default='BTC-USD', help='Symbol to train on (default: BTC-USD)')
    parser.add_argument('--period', type=str, default='3mo', help='Data period (default: 3mo)')
    parser.add_argument('--interval', type=str, default='5m', help='Data interval (default: 5m)')
    parser.add_argument('--timesteps', type=int, default=100000, help='Training timesteps (default: 100000)')
    parser.add_argument('--model-path', type=str, default=MODEL_PATH, help='Path to save model')
    args = parser.parse_args()
    
    # Create a unique model path with timestamp if not specified
    if args.model_path == MODEL_PATH:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.model_path = f"{MODEL_PATH}_{timestamp}"
    
    # Fetch and preprocess data
    logger.info(f"Fetching historical data for {args.symbol}...")
    data = fetch_historical_data(args.symbol, args.period, args.interval)
    
    if data.empty:
        logger.error("Failed to fetch data. Exiting.")
        return
    
    logger.info("Preprocessing data...")
    data = preprocess_data(data)
    data = normalize_data(data)
    
    # Split data for training and testing
    train_data, test_data = split_data_train_test(data)
    
    if train_data is None or test_data is None:
        logger.error("Failed to split data. Exiting.")
        return
    
    # Train the model
    model = train_model(train_data, args.model_path, args.timesteps)
    
    # Evaluate the model
    env = TradingEnv(data=test_data, initial_balance=INITIAL_BALANCE, window_size=WINDOW_SIZE)
    env = DummyVecEnv([lambda: env])
    
    logger.info("Evaluating model on test data...")
    evaluate_model(model, env)
    
    logger.info("Training and evaluation complete!")

if __name__ == "__main__":
    main()
