#!/usr/bin/env python3
"""
Advanced DQN Agent for CPU Scheduling (NO psutil dependency)
Research-grade implementation with:
- Dueling DQN architecture
- Prioritized Experience Replay
- Double DQN
- Multi-objective reward function
- Comprehensive evaluation metrics
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import json
import time
import os
import sys
from collections import deque
from typing import Tuple, List, Dict
import random

# Add python directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from process_profiler import ProcessProfiler


# ============================================================================
# ADVANCED DQN ARCHITECTURE
# ============================================================================

class DuelingDQN(nn.Module):
    """
    Dueling DQN Architecture (Wang et al., 2016)
    Separates value and advantage streams for better learning
    """
    
    def __init__(self, state_dim, action_dim, hidden_dim=256):
        super(DuelingDQN, self).__init__()
        
        # Shared feature layers
        self.feature = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
        )
        
        # Value stream V(s)
        self.value_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1)
        )
        
        # Advantage stream A(s, a)
        self.advantage_stream = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim)
        )
        
        # Initialize weights
        self.apply(self._init_weights)
    
    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            nn.init.orthogonal_(module.weight, gain=np.sqrt(2))
            if module.bias is not None:
                nn.init.constant_(module.bias, 0)
    
    def forward(self, state):
        features = self.feature(state)
        
        value = self.value_stream(features)
        advantages = self.advantage_stream(features)
        
        # Combine: Q(s,a) = V(s) + (A(s,a) - mean(A(s,a)))
        q_values = value + (advantages - advantages.mean(dim=1, keepdim=True))
        
        return q_values


class PrioritizedReplayBuffer:
    """
    Prioritized Experience Replay (Schaul et al., 2016)
    Samples important transitions more frequently
    """
    
    def __init__(self, capacity, alpha=0.6, beta_start=0.4, beta_frames=100000):
        self.capacity = capacity
        self.alpha = alpha  # Priority exponent
        self.beta_start = beta_start  # Importance sampling exponent
        self.beta_frames = beta_frames
        self.frame = 1
        
        self.buffer = []
        self.priorities = np.zeros(capacity, dtype=np.float32)
        self.pos = 0
    
    def beta_by_frame(self):
        """Anneal beta from beta_start to 1"""
        return min(1.0, self.beta_start + self.frame * (1.0 - self.beta_start) / self.beta_frames)
    
    def push(self, state, action, reward, next_state, done):
        """Add experience with maximum priority"""
        max_priority = self.priorities.max() if self.buffer else 1.0
        
        if len(self.buffer) < self.capacity:
            self.buffer.append((state, action, reward, next_state, done))
        else:
            self.buffer[self.pos] = (state, action, reward, next_state, done)
        
        self.priorities[self.pos] = max_priority
        self.pos = (self.pos + 1) % self.capacity
    
    def sample(self, batch_size):
        """Sample batch with priorities"""
        if len(self.buffer) == self.capacity:
            priorities = self.priorities
        else:
            priorities = self.priorities[:self.pos]
        
        # Calculate sampling probabilities
        probabilities = priorities ** self.alpha
        probabilities /= probabilities.sum()
        
        # Sample indices
        indices = np.random.choice(len(self.buffer), batch_size, p=probabilities, replace=False)
        
        # Calculate importance sampling weights
        total = len(self.buffer)
        weights = (total * probabilities[indices]) ** (-self.beta_by_frame())
        weights /= weights.max()
        
        # Get samples
        samples = [self.buffer[idx] for idx in indices]
        
        states, actions, rewards, next_states, dones = zip(*samples)
        
        return (
            np.array(states),
            np.array(actions),
            np.array(rewards, dtype=np.float32),
            np.array(next_states),
            np.array(dones, dtype=np.float32),
            indices,
            weights
        )
    
    def update_priorities(self, indices, priorities):
        """Update priorities based on TD error"""
        for idx, priority in zip(indices, priorities):
            self.priorities[idx] = priority + 1e-5  # Small constant for stability
    
    def __len__(self):
        return len(self.buffer)


# ============================================================================
# MULTI-OBJECTIVE REWARD FUNCTION
# ============================================================================

class RewardCalculator:
    """
    Multi-objective reward function for scheduling optimization
    Considers: efficiency, fairness, latency, stability
    """
    
    def __init__(self):
        self.prev_metrics = None
        self.reward_history = deque(maxlen=100)
        
        # Reward component weights (tunable)
        self.weights = {
            'cpu_efficiency': 2.0,
            'stability': 3.0,
            'fairness': 1.5,
            'latency': 2.0,
            'context_switch': 1.0,
            'load_balance': 1.0
        }
    
    def calculate(self, current_state: np.ndarray, prev_state: np.ndarray, 
                  action: int, profiler: ProcessProfiler) -> float:
        """
        Calculate comprehensive reward signal
        
        State vector indices:
        0: System CPU, 1: Memory, 2: Load avg, 3: Context switches
        4: Avg CPU top, 5: Max CPU top, 6: I/O intensity
        7-9: Workload distribution, 10: Num processes, 11: Total mem
        """
        
        if prev_state is None:
            return 0.0
        
        rewards = {}
        
        # 1. CPU Efficiency Reward
        # Reward: Keep CPU in optimal range (40-75%)
        cpu_util = current_state[0] * 100
        if 40 <= cpu_util <= 75:
            cpu_reward = 1.0
        elif cpu_util < 40:
            cpu_reward = cpu_util / 40.0
        else:
            cpu_reward = max(0, 1.0 - (cpu_util - 75) / 25.0)
        rewards['cpu_efficiency'] = cpu_reward
        
        # 2. Stability Reward
        # Penalize high variance in CPU usage
        cpu_change = abs(current_state[0] - prev_state[0])
        stability_reward = max(0, 1.0 - cpu_change * 10)
        rewards['stability'] = stability_reward
        
        # 3. Fairness Reward
        # Reward balanced CPU distribution (low max/avg ratio)
        avg_cpu = current_state[4]
        max_cpu = current_state[5]
        if avg_cpu > 0.01:
            fairness = 1.0 - min(1.0, (max_cpu - avg_cpu) / avg_cpu)
        else:
            fairness = 1.0
        rewards['fairness'] = fairness
        
        # 4. Latency Reward (based on load average)
        # Penalize high load relative to CPU count
        load_norm = current_state[2]
        latency_reward = max(0, 1.0 - load_norm)
        rewards['latency'] = latency_reward
        
        # 5. Context Switch Penalty
        # Penalize excessive context switching
        ctx_switches = current_state[3]
        ctx_penalty = -min(1.0, ctx_switches)
        rewards['context_switch'] = ctx_penalty
        
        # 6. Load Balance Reward
        # Reward balanced workload distribution
        cpu_intensive = current_state[7]
        io_intensive = current_state[8]
        interactive = current_state[9]
        
        # Ideal: somewhat balanced distribution
        workload_balance = 1.0 - abs(cpu_intensive - io_intensive) - abs(io_intensive - interactive)
        workload_balance = max(0, workload_balance)
        rewards['load_balance'] = workload_balance
        
        # 7. Action-specific bonuses
        action_bonus = 0.0
        if action > 0:  # Non-NO_OP action
            # Small bonus for taking action when system is suboptimal
            if cpu_util > 80 or load_norm > 0.8:
                action_bonus = 0.2
        
        # Combine weighted rewards
        total_reward = sum(
            self.weights[key] * value 
            for key, value in rewards.items()
        ) + action_bonus
        
        # Normalize
        total_weight = sum(self.weights.values())
        normalized_reward = total_reward / total_weight
        
        self.reward_history.append(normalized_reward)
        
        return normalized_reward
    
    def get_reward_breakdown(self) -> Dict[str, float]:
        """Get average reward components for analysis"""
        if not self.reward_history:
            return {}
        
        return {
            'avg_reward': np.mean(self.reward_history),
            'std_reward': np.std(self.reward_history),
            'min_reward': np.min(self.reward_history),
            'max_reward': np.max(self.reward_history)
        }


# ============================================================================
# ADVANCED DQN AGENT
# ============================================================================

class AdvancedDQNAgent:
    """
    Research-grade DQN agent with advanced techniques
    """
    
    def __init__(self, state_dim=12, action_dim=5, hidden_dim=256):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Networks (Dueling DQN)
        self.policy_net = DuelingDQN(state_dim, action_dim, hidden_dim).to(self.device)
        self.target_net = DuelingDQN(state_dim, action_dim, hidden_dim).to(self.device)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()
        
        # Optimizer with gradient clipping
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=1e-4)
        self.scheduler = optim.lr_scheduler.StepLR(self.optimizer, step_size=10000, gamma=0.95)
        
        # Prioritized replay buffer
        self.memory = PrioritizedReplayBuffer(capacity=50000)
        
        # Process profiler
        self.profiler = ProcessProfiler(history_size=100, min_cpu_threshold=2.0)
        
        # Reward calculator
        self.reward_calculator = RewardCalculator()
        
        # Hyperparameters
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.9995
        self.batch_size = 128
        self.target_update_freq = 500
        self.training_start = 1000
        
        # Tracking
        self.steps = 0
        self.episode = 0
        self.total_reward = 0
        self.prev_state = None
        self.prev_action = None
        
        # Metrics
        self.episode_rewards = []
        self.losses = []
        self.q_values = []
        self.td_errors = []
        
        # Evaluation metrics
        self.action_counts = {i: 0 for i in range(action_dim)}
        self.successful_actions = 0
        self.total_actions = 0
        
        print(f"🧠 Advanced DQN Agent initialized")
        print(f"   Device: {self.device}")
        print(f"   Architecture: Dueling DQN")
        print(f"   Replay: Prioritized Experience Replay")
        print(f"   State dim: {state_dim}, Action dim: {action_dim}")
    
    def select_action(self, state: np.ndarray, evaluate=False) -> int:
        """Epsilon-greedy action selection with evaluation mode"""
        if evaluate or random.random() > self.epsilon:
            with torch.no_grad():
                state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
                q_values = self.policy_net(state_tensor)
                action = q_values.argmax(1).item()
                
                # Track Q-values
                self.q_values.append(q_values.max().item())
        else:
            action = random.randrange(self.action_dim)
        
        self.action_counts[action] += 1
        return action
    
    def train_step(self):
        """Perform one training step with Double DQN and PER"""
        if len(self.memory) < self.training_start:
            return None
        
        # Sample from prioritized replay buffer
        states, actions, rewards, next_states, dones, indices, weights = \
            self.memory.sample(self.batch_size)
        
        states = torch.FloatTensor(states).to(self.device)
        actions = torch.LongTensor(actions).to(self.device)
        rewards = torch.FloatTensor(rewards).to(self.device)
        next_states = torch.FloatTensor(next_states).to(self.device)
        dones = torch.FloatTensor(dones).to(self.device)
        weights = torch.FloatTensor(weights).to(self.device)
        
        # Current Q values
        current_q_values = self.policy_net(states).gather(1, actions.unsqueeze(1))
        
        # Double DQN: use policy network to select action, target network to evaluate
        with torch.no_grad():
            next_actions = self.policy_net(next_states).argmax(1, keepdim=True)
            next_q_values = self.target_net(next_states).gather(1, next_actions).squeeze(1)
            target_q_values = rewards + (1 - dones) * self.gamma * next_q_values
        
        # Calculate TD errors for priority update
        td_errors = (current_q_values.squeeze() - target_q_values).detach().cpu().numpy()
        self.td_errors.extend(td_errors.tolist())
        
        # Update priorities in replay buffer
        self.memory.update_priorities(indices, np.abs(td_errors))
        
        # Weighted loss (importance sampling)
        loss = (weights * nn.MSELoss(reduction='none')(
            current_q_values.squeeze(), target_q_values
        )).mean()
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(self.policy_net.parameters(), 1.0)
        self.optimizer.step()
        self.scheduler.step()
        
        self.losses.append(loss.item())
        
        return loss.item()
    
    def update_target_network(self):
        """Soft update of target network"""
        self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def step(self):
        """Execute one environment step"""
        # Get current system state
        current_state = self.profiler.get_system_state_vector()
        
        # Calculate reward from previous transition
        reward = 0.0
        if self.prev_state is not None and self.prev_action is not None:
            reward = self.reward_calculator.calculate(
                current_state, self.prev_state, self.prev_action, self.profiler
            )
            self.total_reward += reward
            
            # Store transition in replay buffer
            done = 0  # Continuous task
            self.memory.push(
                self.prev_state,
                self.prev_action,
                reward,
                current_state,
                done
            )
        
        # Select action
        action = self.select_action(current_state)
        
        # Get intelligent target for action
        target_info = self.profiler.get_action_target(action)
        
        # Generate scheduler command
        if target_info:
            command = self.generate_command(action, target_info)
            if command:
                # Write command for Rust controller
                with open('/tmp/rl_action.json', 'w') as f:
                    json.dump(command, f)
                self.successful_actions += 1
        
        self.total_actions += 1
        
        # Train
        loss = self.train_step()
        
        # Update state
        self.prev_state = current_state
        self.prev_action = action
        
        # Update counters
        self.steps += 1
        self.memory.frame = self.steps
        
        # Decay epsilon
        if self.steps % 10 == 0:
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        
        # Update target network
        if self.steps % self.target_update_freq == 0:
            self.update_target_network()
        
        # Logging
        if self.steps % 100 == 0:
            avg_loss = np.mean(self.losses[-100:]) if self.losses else 0
            avg_q = np.mean(self.q_values[-100:]) if self.q_values else 0
            avg_reward = np.mean(self.reward_calculator.reward_history)
            
            print(f"Step {self.steps} | ε={self.epsilon:.3f} | Loss={avg_loss:.4f} | "
                  f"Q={avg_q:.3f} | R={avg_reward:.3f} | Action={action} | "
                  f"Success Rate={self.successful_actions/max(1,self.total_actions):.2%}")
        
        return action, reward, loss
    
    def generate_command(self, action: int, target_info: Dict) -> Dict:
        """Generate scheduler command from action and target"""
        timestamp = int(time.time())
        
        if action == 0:
            return None
        
        elif action in [1, 2]:  # Nice adjustments
            return {
                'timestamp': timestamp,
                'action_type': 'set_nice',
                'target_pid': target_info['pid'],
                'nice_value': target_info['nice_delta'],
                'scheduler_policy': None,
                'cpu_weight': None
            }
        
        elif action in [3, 4]:  # Policy changes
            return {
                'timestamp': timestamp,
                'action_type': 'set_scheduler',
                'target_pid': target_info['pid'],
                'nice_value': None,
                'scheduler_policy': target_info['policy'],
                'cpu_weight': None
            }
        
        return None
    
    def save_checkpoint(self, path='checkpoints/dqn_latest.pth'):
        """Save model checkpoint"""
        os.makedirs('checkpoints', exist_ok=True)
        torch.save({
            'policy_net': self.policy_net.state_dict(),
            'target_net': self.target_net.state_dict(),
            'optimizer': self.optimizer.state_dict(),
            'steps': self.steps,
            'epsilon': self.epsilon,
            'metrics': {
                'episode_rewards': self.episode_rewards,
                'action_counts': self.action_counts,
                'successful_actions': self.successful_actions,
                'total_actions': self.total_actions
            }
        }, path)
    
    def get_evaluation_metrics(self) -> Dict:
        """Get comprehensive evaluation metrics"""
        return {
            'total_steps': self.steps,
            'epsilon': self.epsilon,
            'avg_reward': np.mean(self.reward_calculator.reward_history) if self.reward_calculator.reward_history else 0,
            'avg_loss': np.mean(self.losses[-1000:]) if self.losses else 0,
            'avg_q_value': np.mean(self.q_values[-1000:]) if self.q_values else 0,
            'avg_td_error': np.mean(np.abs(self.td_errors[-1000:])) if self.td_errors else 0,
            'action_distribution': {k: v/max(1, sum(self.action_counts.values())) 
                                   for k, v in self.action_counts.items()},
            'action_success_rate': self.successful_actions / max(1, self.total_actions),
            'profiler_stats': self.profiler.get_statistics()
        }


def main():
    """Main training loop"""
    print("="*80)
    print("🧠 RESEARCH-GRADE DQN SCHEDULER")
    print("="*80)
    
    agent = AdvancedDQNAgent()
    
    print("\n⏳ Waiting for system initialization...")
    time.sleep(5)
    
    print("🎯 Starting intelligent scheduling optimization...\n")
    
    try:
        while True:
            action, reward, loss = agent.step()
            
            # Save checkpoint periodically
            if agent.steps % 1000 == 0:
                agent.save_checkpoint()
            
            # Print detailed metrics every 500 steps
            if agent.steps % 500 == 0:
                metrics = agent.get_evaluation_metrics()
                print("\n" + "="*80)
                print(f"EVALUATION METRICS (Step {agent.steps})")
                print("="*80)
                for k, v in metrics.items():
                    if isinstance(v, dict):
                        print(f"{k}:")
                        for kk, vv in v.items():
                            print(f"  {kk}: {vv}")
                    else:
                        print(f"{k}: {v}")
                print("="*80 + "\n")
            
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Training interrupted")
        agent.save_checkpoint('checkpoints/dqn_final.pth')
        
        final_metrics = agent.get_evaluation_metrics()
        print("\n📊 Final Metrics:")
        print(json.dumps(final_metrics, indent=2))


if __name__ == '__main__':
    main()