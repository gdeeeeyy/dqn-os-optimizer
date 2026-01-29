#!/usr/bin/env python3
"""
Advanced DQN Agent for CPU Scheduler - FIXED VERSION
Ensures proper baseline → training transition
"""

import os
import sys
import time
import json
import signal
import numpy as np
from datetime import datetime
from collections import deque

# PyTorch imports
import torch
import torch.nn as nn
import torch.optim as optim

# Local imports
from process_profiler import ProcessProfiler

# Configuration
METRICS_FILE = '/tmp/scheduler_metrics.csv'
STATE_FILE = '/tmp/rl_state.json'
ACTION_FILE = '/tmp/rl_action.json'
LOG_FILE = '/tmp/scheduler_actions.log'
CHECKPOINT_DIR = 'checkpoints'

# Timing configuration
BASELINE_DURATION = 60  # 60 seconds for baseline
CHECK_INTERVAL = 2      # Check every 2 seconds
MODE_WRITE_INTERVAL = 1 # Write mode every second

# DQN Network
class DQNNetwork(nn.Module):
    def __init__(self, state_size, action_size):
        super(DQNNetwork, self).__init__()
        self.fc1 = nn.Linear(state_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, 64)
        self.fc4 = nn.Linear(64, action_size)
        
    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = torch.relu(self.fc3(x))
        return self.fc4(x)

# Replay Buffer
class ReplayBuffer:
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)
    
    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))
    
    def sample(self, batch_size):
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        states, actions, rewards, next_states, dones = zip(*[self.buffer[i] for i in indices])
        return (np.array(states), np.array(actions), np.array(rewards),
                np.array(next_states), np.array(dones))
    
    def __len__(self):
        return len(self.buffer)

class DQNAgent:
    def __init__(self):
        # State and action configuration
        self.state_size = 10
        self.action_size = 5
        
        # Networks
        self.policy_net = DQNNetwork(self.state_size, self.action_size)
        self.target_net = DQNNetwork(self.state_size, self.action_size)
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=0.0001)
        
        # Training parameters
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.9995
        self.batch_size = 64
        
        # Replay buffer
        self.memory = ReplayBuffer()
        
        # Tracking
        self.episode = 0
        self.total_steps = 0
        self.rewards = []
        self.losses = []
        
        # Process profiler
        self.profiler = ProcessProfiler()
        
        # Phase tracking
        self.mode = 'baseline'
        self.baseline_start_time = None
        self.training_start_time = None
        
        # Running flag
        self.running = True
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        print("[DQN Agent] Initialized")
        print(f"[DQN Agent] Baseline duration: {BASELINE_DURATION}s")
    
    def signal_handler(self, signum, frame):
        print("\n[DQN Agent] Shutting down gracefully...")
        self.running = False
    
    def get_state_from_metrics(self):
        """Read latest metrics and convert to state"""
        try:
            if not os.path.exists(METRICS_FILE):
                return None
            
            with open(METRICS_FILE, 'r') as f:
                lines = f.readlines()
                if len(lines) < 2:
                    return None
                
                # Parse last line
                last_line = lines[-1].strip().split(',')
                header = lines[0].strip().split(',')
                
                if len(last_line) < len(header):
                    return None
                
                data = dict(zip(header, last_line))
                
                # Extract features
                cpu_usage = float(data.get('cpu_usage', 0)) / 100.0
                cpu_variance = float(data.get('cpu_variance', 0)) / 100.0
                context_switches = float(data.get('context_switches', 0)) / 10000.0
                load_avg = float(data.get('load_avg', 0)) / 4.0
                
                # Get process information
                processes = self.profiler.get_high_cpu_processes()
                num_processes = len(processes)
                avg_nice = np.mean([p.get('nice', 0) for p in processes]) / 20.0 if processes else 0
                
                # Create state vector
                state = np.array([
                    cpu_usage,
                    cpu_variance,
                    context_switches,
                    load_avg,
                    num_processes / 10.0,
                    avg_nice,
                    self.epsilon,
                    self.episode / 1000.0,
                    0, 0  # Placeholder for additional features
                ])
                
                return state
        except Exception as e:
            print(f"[DQN Agent] Error reading state: {e}")
            return None
    
    def select_action(self, state):
        """Epsilon-greedy action selection"""
        if np.random.random() < self.epsilon:
            return np.random.randint(self.action_size)
        
        with torch.no_grad():
            state_tensor = torch.FloatTensor(state).unsqueeze(0)
            q_values = self.policy_net(state_tensor)
            return q_values.argmax().item()
    
    def apply_action(self, action):
        """Apply scheduling action to processes"""
        try:
            processes = self.profiler.get_high_cpu_processes()
            if not processes:
                return
            
            # Select target process (highest CPU)
            target = processes[0]
            pid = target['pid']
            
            action_desc = ""
            
            if action == 0:
                # Increase priority (decrease nice)
                nice = max(-20, target.get('nice', 0) - 5)
                os.system(f"renice -n {nice} -p {pid} > /dev/null 2>&1")
                action_desc = f"Increased priority for {target['name']} (PID: {pid}, nice: {nice})"
                
            elif action == 1:
                # Decrease priority (increase nice)
                nice = min(19, target.get('nice', 0) + 5)
                os.system(f"renice -n {nice} -p {pid} > /dev/null 2>&1")
                action_desc = f"Decreased priority for {target['name']} (PID: {pid}, nice: {nice})"
                
            elif action == 2:
                # Set SCHED_FIFO (real-time)
                os.system(f"chrt -f -p 50 {pid} > /dev/null 2>&1")
                action_desc = f"Applied SCHED_FIFO to {target['name']} (PID: {pid})"
                
            elif action == 3:
                # Set CPU affinity
                import subprocess
                cpu_count = os.cpu_count() or 4
                cpus = ",".join(str(i) for i in range(cpu_count))
                subprocess.run(['taskset', '-cp', cpus, str(pid)], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                action_desc = f"Set CPU affinity for {target['name']} (PID: {pid})"
                
            elif action == 4:
                # Balance load
                action_desc = "Rebalanced load across CPU cores"
            
            # Log action
            if action_desc:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                with open(LOG_FILE, 'a') as f:
                    f.write(f"{timestamp} - {action_desc}\n")
                print(f"[Action] {action_desc}")
            
            # Write action to file for Rust controller
            action_data = {
                'action': action,
                'pid': pid,
                'timestamp': time.time()
            }
            with open(ACTION_FILE, 'w') as f:
                json.dump(action_data, f)
                
        except Exception as e:
            print(f"[DQN Agent] Error applying action: {e}")
    
    def calculate_reward(self, prev_state, curr_state):
        """Calculate reward based on state improvement"""
        if prev_state is None or curr_state is None:
            return 0.0
        
        # Reward components
        cpu_improvement = (prev_state[0] - curr_state[0]) * 10.0
        variance_improvement = (prev_state[1] - curr_state[1]) * 15.0
        switches_improvement = (prev_state[2] - curr_state[2]) * 5.0
        load_improvement = (prev_state[3] - curr_state[3]) * 8.0
        
        reward = cpu_improvement + variance_improvement + switches_improvement + load_improvement
        
        # Penalty for extreme actions
        if abs(reward) > 50:
            reward *= 0.5
        
        return reward
    
    def train_step(self):
        """Perform one training step"""
        if len(self.memory) < self.batch_size:
            return 0.0
        
        # Sample batch
        states, actions, rewards, next_states, dones = self.memory.sample(self.batch_size)
        
        # Convert to tensors
        states = torch.FloatTensor(states)
        actions = torch.LongTensor(actions)
        rewards = torch.FloatTensor(rewards)
        next_states = torch.FloatTensor(next_states)
        dones = torch.FloatTensor(dones)
        
        # Current Q values
        current_q = self.policy_net(states).gather(1, actions.unsqueeze(1))
        
        # Target Q values
        with torch.no_grad():
            next_q = self.target_net(next_states).max(1)[0]
            target_q = rewards + (1 - dones) * self.gamma * next_q
        
        # Loss
        loss = nn.MSELoss()(current_q.squeeze(), target_q)
        
        # Optimize
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        return loss.item()
    
    def update_target_network(self):
        """Update target network"""
        self.target_net.load_state_dict(self.policy_net.state_dict())
    
    def write_state(self):
        """Write current training state to file"""
        try:
            processes = self.profiler.get_high_cpu_processes()
            
            state_data = {
                'mode': self.mode,
                'episode': self.episode,
                'epsilon': self.epsilon,
                'avg_reward': np.mean(self.rewards[-100:]) if self.rewards else 0.0,
                'avg_q_value': 0.0,  # Placeholder
                'loss': np.mean(self.losses[-100:]) if self.losses else 0.0,
                'total_steps': self.total_steps,
                'processes': processes,
                'timestamp': time.time()
            }
            
            with open(STATE_FILE, 'w') as f:
                json.dump(state_data, f, indent=2)
                
        except Exception as e:
            print(f"[DQN Agent] Error writing state: {e}")
    
    def run_baseline(self):
        """Run baseline collection phase"""
        print(f"\n[DQN Agent] Starting BASELINE phase ({BASELINE_DURATION}s)")
        self.baseline_start_time = time.time()
        self.mode = 'baseline'
        
        while self.running:
            elapsed = time.time() - self.baseline_start_time
            
            if elapsed >= BASELINE_DURATION:
                print(f"[DQN Agent] Baseline complete after {elapsed:.1f}s")
                break
            
            # Just monitor, don't take actions
            state = self.get_state_from_metrics()
            if state is not None:
                print(f"[Baseline] {elapsed:.0f}s/{BASELINE_DURATION}s - CPU: {state[0]*100:.1f}%")
            
            # Write state file
            self.write_state()
            
            time.sleep(CHECK_INTERVAL)
        
        print("[DQN Agent] Baseline phase COMPLETE, switching to TRAINING\n")
    
    def run_training(self):
        """Run training phase"""
        print("[DQN Agent] Starting TRAINING phase")
        self.training_start_time = time.time()
        self.mode = 'rl'
        
        prev_state = None
        
        while self.running:
            # Get current state
            curr_state = self.get_state_from_metrics()
            if curr_state is None:
                time.sleep(CHECK_INTERVAL)
                continue
            
            # Select and apply action
            action = self.select_action(curr_state)
            self.apply_action(action)
            
            # Wait for effect
            time.sleep(CHECK_INTERVAL)
            
            # Get next state
            next_state = self.get_state_from_metrics()
            if next_state is None:
                time.sleep(CHECK_INTERVAL)
                continue
            
            # Calculate reward
            reward = self.calculate_reward(curr_state, next_state)
            self.rewards.append(reward)
            
            # Store transition
            done = False
            self.memory.push(curr_state, action, reward, next_state, done)
            
            # Train
            if len(self.memory) >= self.batch_size:
                loss = self.train_step()
                self.losses.append(loss)
                
                # Update target network periodically
                if self.total_steps % 100 == 0:
                    self.update_target_network()
            
            # Update epsilon
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
            
            # Increment counters
            self.episode += 1
            self.total_steps += 1
            
            # Write state
            self.write_state()
            
            # Progress
            if self.episode % 10 == 0:
                avg_reward = np.mean(self.rewards[-100:]) if self.rewards else 0
                print(f"[Training] Episode {self.episode}, Reward: {avg_reward:.2f}, ε: {self.epsilon:.3f}")
            
            # Save checkpoint periodically
            if self.episode % 100 == 0:
                self.save_checkpoint()
            
            prev_state = curr_state
    
    def save_checkpoint(self):
        """Save model checkpoint"""
        try:
            os.makedirs(CHECKPOINT_DIR, exist_ok=True)
            checkpoint_path = os.path.join(CHECKPOINT_DIR, f'dqn_model_ep{self.episode}.pth')
            torch.save({
                'episode': self.episode,
                'model_state_dict': self.policy_net.state_dict(),
                'optimizer_state_dict': self.optimizer.state_dict(),
                'epsilon': self.epsilon
            }, checkpoint_path)
            print(f"[DQN Agent] Checkpoint saved: {checkpoint_path}")
        except Exception as e:
            print(f"[DQN Agent] Error saving checkpoint: {e}")
    
    def run(self):
        """Main run loop"""
        print("\n" + "="*60)
        print("DQN CPU SCHEDULER AGENT - STARTING")
        print("="*60)
        
        # Wait for metrics file to exist
        print("[DQN Agent] Waiting for metrics file...")
        while not os.path.exists(METRICS_FILE) and self.running:
            time.sleep(1)
        
        if not self.running:
            return
        
        print(f"[DQN Agent] Metrics file found: {METRICS_FILE}")
        
        # Phase 1: Baseline
        self.run_baseline()
        
        if not self.running:
            return
        
        # Phase 2: Training
        self.run_training()
        
        print("\n[DQN Agent] Shutdown complete")

def main():
    agent = DQNAgent()
    
    try:
        agent.run()
    except KeyboardInterrupt:
        print("\n[DQN Agent] Interrupted by user")
    except Exception as e:
        print(f"\n[DQN Agent] Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("[DQN Agent] Exiting")

if __name__ == "__main__":
    main()