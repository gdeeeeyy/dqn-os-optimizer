# CPU Scheduler Optimizer using Deep Reinforcement Learning

Vanakkam guys. So this CPU Scheduler Optimizer using Deep Reinforcement Learning proj can be considered very ambitious(?). But before diving into what the project is, let me give you a context of what got me into this.

So, one day, I had a dream of creating my own operating system. Even though I knew how an OS works, I didn't have enough knowledge to build an OS from scratch. I could've learnt how to, but I decided to Jugaad my way through.

The Jugaad I'm referring to is Archiso; it helps you build Arch Linux ISO images, and if you think about it a bit, you can just (kinda) create your own Distro with your own packages as well. But what can I do to make it different from the basic Arch distros? So the CPU scheduler seemed like a way to start, and since it is an integral function of the kernel, I thought, why not?

Let's break this down. Not that the scheduling was bad per se, but I wanted to play around. So, naturally, I went back to my trusted friend Ubuntu, and I worked on creating a CPU scheduler using an RL algorithm. With the help of my trusted 'fiend' ChatGPT, I decided to use DQN for the RL model. Also, since meddling with the kernel could break my laptop, I thought running it in the user space using nice, chrt, and other packages would be a much safer option.

Thus was born this half-cooked DQN-based CPU scheduler, which can definitely be used as a base level learning tool to traverse through this CPU scheduling + AI road. Sure, this would be a long road to tread down, but I'm ready to do it. Future goals would be to ensure the model works with the kernel as well to perform REAL scheduling (hopefully without crashing my system), and also to extend this scheduling to the GPU as well; and finally, to package this as a Distro. Right now, this might not seem like a lot, but I certainly am proud of this :)

Let me stop yapping and scroll down to see what this project is and how to run it

**P.S:** Props to Priyanka for sitting through with this and trusting me with our final-year project.

---

---

## Tech Stack

### The Languages

- **Rust**
- **Python**
- **Shell**

### The ML Magic

- Deep Q-Network (DQN) with experience replay
- ε-greedy exploration (sometimes you gotta try random stuff)
- Reward shaping that actually makes sense
- Baseline comparison mode (to prove we're not making things worse)

### The System Wizardry

- `/proc/stat` and `/proc/loadavg` for metrics
- `nice` and `chrt` for priority control
- File-based IPC via `/tmp` (old school but it works)
- Optional cgroup integration (for the ambitious)

---

## 🎮 How It Works (The Simple Version)

```
1. Rust monitor: "Hey, CPU is doing this thing..."
2. Python DQN: "Interesting... let me think... *neural network noises*"
3. Python DQN: "Try making this process nicer!"
4. Rust monitor: "You got it boss!" *adjusts scheduling*
5. Repeat forever (or until Ctrl+C)
```

---

## 🚀 Getting Started (The Easy Way)

### Prerequisites

You'll need:

- Linux
- Python 3.8+
- Rust 1.70+
- Trust in me that I won't crash or permanently damage your system(optional)

### Installation

```bash
# Clone this beauty
git clone <your-repo-url>
cd cpu-scheduler-optimizer

# Make the magic script executable
chmod +x run.sh

# Set everything up (one time only)
./run.sh setup
```

This will:

- Build the Rust binary (fast compilation, I promise)
- Create a Python virtual environment
- Install all the ML goodies
- Set up directories for data and logs

### Running It

```bash
# Start the whole system
./run.sh run
```

**What happens next:**

1. System starts in baseline mode (collecting normal behavior)
2. Automatically switches to training mode
3. The DQN starts making scheduling decisions
4. You watch the magic happen in the dashboard

### Stopping It

```bash
# Just hit Ctrl+C in the dashboard
# Or if you're fancy:
./run.sh stop
```

---

## 🎯 The Architecture (For the Nerds)

```
┌─────────────────────────────────────────────┐
│              USER SPACE MAGIC               │
│                                             │
│  ┌──────────────┐      ┌─────────────────┐ │
│  │ Rust Monitor │◄────►│ Python DQN Agent│ │
│  │  - Collects  │ JSON │  - Learns       │ │
│  │  - Controls  │ IPC  │  - Decides      │ │
│  └──────────────┘      └─────────────────┘ │
│         │                      │            │
│         ▼                      ▼            │
│  /tmp/metrics.csv        /tmp/rl_*.json    │
└─────────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────┐
│         KERNEL (untouched, safe)            │
│  • /proc/stat, /proc/loadavg                │
│  • nice, chrt interfaces                    │
│  • cgroups (optional)                       │
└─────────────────────────────────────────────┘
```

---

## 🛠️ What Can Go Wrong (And How to Fix It)

### "CPU usage shows 0.0%"

Your system is too chill. Generate some load:

```bash
python3 -c "while True: pass" &
# Don't forget to kill it later!
```

### "Permission denied everywhere"

```bash
sudo rm -f /tmp/scheduler_*
chmod +x run.sh
./run.sh setup
```

### "Where's my Rust binary?"

```bash
./run.sh setup
# It'll rebuild everything
```

---

## 🔮 The Future (aka The Dream)

This is just the beginning. Sure, it might seem like "just" a user-space scheduler optimizer right now, but here's the vision:

**Short-term goals:**

- Make the DQN even smarter (more layers? transformer architecture? who knows!)
- Better reward functions (currently it's good, but it could be _great_)
- More extensive testing on different workloads

**Medium-term goals:**

- Get this working with actual kernel modifications (safely, with VMs)
- Extend to GPU scheduling (because why stop at CPUs?)
- Multi-agent setups for NUMA systems

**Long-term goals:**

- Package this as a full Arch-based distro
- Call it something cool like "QuantumArch" or "SchedML Linux"
- Maybe, just maybe, contribute something useful to the kernel community

---

## 🎓 What This Actually Is

Look, I'm not going to claim this replaces CFS or makes Linux 500% faster. But it's:

✅ A **learning tool** to understand CPU scheduling + AI  
✅ A **proof of concept** that RL can optimize OS behavior  
✅ A **safe playground** for experimenting without kernel crashes  
✅ A **foundation** for more ambitious projects  
✅ **Something I'm genuinely proud of** 😊

Can it be used as a base-level learning tool to traverse the CPU scheduling + AI road? Absolutely. Is it production-ready? God no. But that's not the point, is it?

---

## 🙏 Props Where Props Are Due

**Massive thanks to:**

- **Priyanka** for trusting me with our final-year project and sitting through all my "I think I know what's wrong" moments (spoiler: I usually didn't)
- **ChatGPT** (at times) for being my trusted 'fiend' always
- **The Linux community** for making `/proc` wonderful
- **Everyone who actually read this README** thanks for giving me the attention

---

## 📜 License

MIT License (because sharing is caring)

---

## 🤝 Contributing

Found a bug? Have an idea? Want to make this even cooler? PRs are welcome! Just remember:

- Keep it safe (no kernel-breaking changes without serious testing)
- Document your changes
- Have fun with it

---

## 💬 Final Thoughts

Sure, this might not seem like a lot compared to building a full OS from scratch. But it's _my_ Jugaad, and I'm proud of it. It's a stepping stone on a much longer journey.

The road ahead is long – kernel integration, GPU scheduling, distro packaging – but I'm ready to walk it. One commit at a time.

**TL;DR:** I wanted to build an OS, settled for making a smart CPU scheduler using deep learning, and ended up learning a ton about both systems programming and AI. Not bad for a Jugaad project.

Now if you'll excuse me, I need to go explain to my laptop why I keep making it reschedule processes randomly.

---

\*Built using a laptop and questionable life choices
