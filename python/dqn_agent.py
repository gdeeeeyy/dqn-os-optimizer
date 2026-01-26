#!/usr/bin/env python3
"""
DQN-based CPU Scheduler Optimizer
Deep Reinforcement Learning agent for OS-level scheduling decisions
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json
import time
import os
from collections import deque
import random

# Hyperparameters
STATE_DIM = 6  # cpu_util, context_switches, stability, running_tasks, load_avg, blocked_tasks
ACTION_DIM = 5  # noop, reduce_nice, increase_nice, set_batch, set_other
HIDDEN_DIM = 128
LEARNING_RATE = 0.001
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_DECAY = 0.995
BATCH_SIZE = 64
MEMORY_SIZE = 10000
TARGET_UPDATE_FREQ = 100
TRAINING_START = 1000


class DQN(nn.Module):
    """Deep Q-Network for scheduling policy learning"""
    
    def __init__(self, state_dim, action_dim, hidden_dim):
        super(DQN, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, action_dim)
        )
    
    def forward(self, state):
        return self.network(state)


class ReplayBuffer:
    """Experience replay buffer for stable learning"""
    
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return (
            torch.FloatTensor(states),
            torch.LongTensor(actions),
            torch.FloatTensor(rewards),
            torch.FloatTensor(next_states),
            torch.FloatTensor(dones)
        )
    
    def __len__(self):
        return len(self.buffer)


class SchedulerDQNAgent:
    """DQN agent for CPU scheduling optimization"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Networks
        self.policy_net = DQN(STATE_DIM, ACTION_DIM, HIDDEN_DIM).to(self.device)
        self.target_net = DQN(STATE_DIM, ACTION_DIM, HIDDEN_DIM).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Optimizer
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=LEARNING_RATE)
        
        # Replay buffer
        self.memory = ReplayBuffer(MEMORY_SIZE)
        
        # Training state
        self.epsilon = EPSILON_START
        self.steps = 0
        self.episode = 0
        self.total_reward = 0
        
        # State tracking
        self.prev_state = None
        self.prev_action = None
        self.prev_metrics = None
        
        # Performance tracking
        self.episode_rewards = []
        self.losses = []
        
        print(f"🤖 DQN Agent initialized on {self.device}")
        print(f"   State dim: {STATE_DIM}, Action dim: {ACTION_DIM}")
    
    def normalize_state(self, raw_state):
        """Normalize state values to [0, 1] range"""
        cpu_util = raw_state.get('cpu_util', 0.0) / 100.0
        context_switches = min(raw_state.get('context_switches', 0) / 10000.0, 1.0)
        stability = raw_state.get('stability', 0.0) / 100.0
        running_tasks = min(raw_state.get('running_tasks', 0) / 100.0, 1.0)
        load_avg = min(raw_state.get('load_avg', 0.0) / 10.0, 1.0)
        blocked_tasks = min(raw_state.get('blocked_tasks', 0) / 20.0, 1.0)
        
        return np.array([
            cpu_util,
            context_switches,
            stability,
            running_tasks,
            load_avg,
            blocked_tasks
        ], dtype=np.float32)
    
    def calculate_reward(self, state, prev_state):
        """
        Multi-objective reward function:
        - Penalize high CPU variance (instability)
        - Reward efficient CPU utilization (40-70% ideal)
        - Penalize excessive context switches
        - Reward low latency (low blocked tasks)
        """
        if prev_state is None:
            return 0.0
        
        # CPU utilization reward (prefer 40-70%)
        cpu_util = state.get('cpu_util', 0.0)
        if 40 <= cpu_util <= 70:
            cpu_reward = 1.0
        elif cpu_util < 40:
            cpu_reward = cpu_util / 40.0
        else:
            cpu_reward = max(0, 1.0 - (cpu_util - 70) / 30.0)
        
        # Stability reward (high stability is good)
        stability = state.get('stability', 0.0) / 100.0
        stability_reward = stability
        
        # Context switch penalty (lower is better)
        cs = state.get('context_switches', 0)
        cs_penalty = -min(cs / 5000.0, 1.0)
        
        # Blocked tasks penalty (lower is better)
        blocked = state.get('blocked_tasks', 0)
        blocked_penalty = -min(blocked / 10.0, 1.0)
        
        # Load average consideration
        load_avg = state.get('load_avg', 0.0)
        load_penalty = -max(0, (load_avg - 2.0) / 5.0)
        
        # Weighted combination
        reward = (
            2.0 * cpu_reward +
            3.0 * stability_reward +
            1.0 * cs_penalty +
            1.0 * blocked_penalty +
            0.5 * load_penalty
        )
        
        return reward
    
    def select_action(self, state):
        """Epsilon-greedy action selection"""
        if random.random() < self.epsilon:
            return random.randrange(ACTION_DIM)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax(1).item()
    
    def action_to_command(self, action, state):
        """Convert action index to scheduler command"""
        timestamp = int(time.time())
        
        # Action space:
        # 0: No-op
        # 1: Reduce nice (increase priority) for high-CPU processes
        # 2: Increase nice (decrease priority) for low-priority tasks
        # 3: Set SCHED_BATCH for background tasks
        # 4: Set SCHED_OTHER (default) for normal tasks
        
        if action == 0:
            return None  # No action
        
        # Find a target PID (simplified - in production, track process list)
        target_pid = os.getpid()  # Use current process as demo
        
        if action == 1:
            return {
                'timestamp': timestamp,
                'action_type': 'set_nice',
                'target_pid': target_pid,
                'nice_value': -5,
                'scheduler_policy': None,
                'cpu_weight': None
            }
        elif action == 2:
            return {
                'timestamp': timestamp,
                'action_type': 'set_nice',
                'target_pid': target_pid,
                'nice_value': 10,
                'scheduler_policy': None,
                'cpu_weight': None
            }
        elif action == 3:
            return {
                'timestamp': timestamp,
                'action_type': 'set_scheduler',
                'target_pid': target_pid,
                'nice_value': None,
                'scheduler_policy': 'SCHED_BATCH',
                'cpu_weight': None
            }
        elif action == 4:
            return {
                'timestamp': timestamp,
                'action_type': 'set_scheduler',
                'target_pid': target_pid,
                'nice_value': None,
                'scheduler_policy': 'SCHED_OTHER',
                'cpu_weight': None
            }
        
        return None
    
    def train_step(self):
        """Perform one training step using experience replay"""
        if len(self.memory) < TRAINING_START:
            return None
        
        # Sample batch
        states, actions, rewards, next_states, dones = self.memory.sample(BATCH_SIZE)
        states = states.to(self.device)
        actions = actions.to(self.device)
        rewards = rewards.to(self.device)
        next_states = next_states.to(self.device)
        dones = dones.to(self.device)
        
        # Current Q values
        current_q_values = self.policy_net(states).gather(1, actions.unsqueeze(1))
        
        # Target Q values
        with torch.no_grad():
            next_q_values = self.target_net(next_states).max(1)[0]
            target_q_values = rewards + (1 - dones) * GAMMA * next_q_values
        
        # Compute loss
        loss = nn.MSELoss()(current_q_values.squeeze(), target_q_values)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        
        return loss.item()
    
    def update_target_network(self):
        """Update target network with policy network weights"""
        self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def step(self, current_state_raw):
        """Process one environment step"""
        current_state = self.normalize_state(current_state_raw)
        
        # Calculate reward from previous transition
        if self.prev_state is not None and self.prev_action is not None:
            reward = self.calculate_reward(current_state_raw, self.prev_metrics)
            self.total_reward += reward
            
            # Store transition
            done = 0  # Continuous task
            self.memory.push(
                self.prev_state,
                self.prev_action,
                reward,
                current_state,
                done
            )
            
            # Train
            loss = self.train_step()
            if loss is not None:
                self.losses.append(loss)
        
        # Select action
        action = self.select_action(current_state)
        
        # Generate command
        command = self.action_to_command(action, current_state_raw)
        if command:
            with open('/tmp/rl_action.json', 'w') as f:
                json.dump(command, f)
        
        # Update state
        self.prev_state = current_state
        self.prev_action = action
        self.prev_metrics = current_state_raw.copy()
        
        # Update counters
        self.steps += 1
        
        # Decay epsilon
        if self.steps % 10 == 0:
            self.epsilon = max(EPSILON_END, self.epsilon * EPSILON_DECAY)
        
        # Update target network
        if self.steps % TARGET_UPDATE_FREQ == 0:
            self.update_target_network()
        
        # Logging
        if self.steps % 100 == 0:
            avg_loss = np.mean(self.losses[-100:]) if self.losses else 0
            print(f"Step {self.steps} | ε={self.epsilon:.3f} | Avg Loss={avg_loss:.4f} | "
                  f"Reward={self.total_reward:.2f} | Action={action}")
        
        return action


def main():
    """Main RL control loop"""
    print("=" * 60)
    print("🧠 CPU Scheduler DQN Agent")
    print("=" * 60)
    
    agent = SchedulerDQNAgent()
    
    print("\n⏳ Waiting for Rust collector to start...")
    time.sleep(5)
    
    print("🎯 Starting RL-based scheduling optimization...\n")
    
    while True:
        try:
            # Read current state from Rust collector
            if os.path.exists('/tmp/rl_state.json'):
                with open('/tmp/rl_state.json', 'r') as f:
                    state = json.load(f)
                
                # Process step
                action = agent.step(state)
                
            time.sleep(1.0)  # 1 second control loop
            
        except KeyboardInterrupt:
            print("\n\n🛑 Training interrupted by user")
            break
        except Exception as e:
            print(f"⚠️  Error: {e}")
            time.sleep(1.0)
    
    # Save final model
    torch.save({
        'policy_net': agent.policy_net.state_dict(),
        'target_net': agent.target_net.state_dict(),
        'optimizer': agent.optimizer.state_dict(),
        'steps': agent.steps,
        'epsilon': agent.epsilon,
    }, 'scheduler_dqn_model.pth')
    
    print("\n✅ Model saved to scheduler_dqn_model.pth")


if __name__ == '__main__':
    main()