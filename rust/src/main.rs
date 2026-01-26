// main.rs - CPU Scheduling Optimizer Rust Core (Integrated)
// Main entry point with logger and controller modules

mod controller;
mod logger;

use serde::{Deserialize, Serialize};
use std::collections::VecDeque;
use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

use controller::{SchedulerAction, SchedulerController};
use logger::{LogLevel, Logger};

const METRIC_HISTORY_SIZE: usize = 100;
const MONITOR_INTERVAL_MS: u64 = 1000;
const STATE_FILE_PATH: &str = "/tmp/rl_state.json";
const ACTION_FILE_PATH: &str = "/tmp/rl_action.json";
const METRICS_CSV_PATH: &str = "/tmp/scheduler_metrics.csv";
const LOG_FILE_PATH: &str = "data/logs/rust_monitor.log";
const ACTION_LOG_PATH: &str = "/tmp/scheduler_actions.log";

#[derive(Debug, Clone, Serialize, Deserialize)]
struct CpuMetrics {
    timestamp: u64,
    per_core_util: Vec<f32>,
    avg_util: f32,
    context_switches: u64,
    running_tasks: u32,
    blocked_tasks: u32,
    load_avg_1m: f32,
}

#[derive(Clone)]
struct CpuStat {
    user: u64,
    nice: u64,
    system: u64,
    idle: u64,
    iowait: u64,
    irq: u64,
    softirq: u64,
}

impl CpuStat {
    fn total(&self) -> u64 {
        self.user + self.nice + self.system + self.idle + self.iowait + self.irq + self.softirq
    }
}

struct MetricsCollector {
    prev_cpu_stats: Vec<CpuStat>,
    prev_context_switches: u64,
    history: VecDeque<CpuMetrics>,
    logger: std::sync::Arc<Logger>,
}

impl MetricsCollector {
    fn new(logger: std::sync::Arc<Logger>) -> Self {
        Self {
            prev_cpu_stats: Vec::new(),
            prev_context_switches: 0,
            history: VecDeque::with_capacity(METRIC_HISTORY_SIZE),
            logger,
        }
    }

    fn read_cpu_stats(&self) -> Vec<CpuStat> {
        let file = match File::open("/proc/stat") {
            Ok(f) => f,
            Err(e) => {
                self.logger.log_error_ctx("open /proc/stat", &e.to_string());
                return Vec::new();
            }
        };

        let reader = BufReader::new(file);
        let mut stats = Vec::new();

        for line in reader.lines().flatten() {
            if !line.starts_with("cpu") || line.starts_with("cpu ") {
                continue;
            }

            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() < 8 {
                continue;
            }

            stats.push(CpuStat {
                user: parts[1].parse().unwrap_or(0),
                nice: parts[2].parse().unwrap_or(0),
                system: parts[3].parse().unwrap_or(0),
                idle: parts[4].parse().unwrap_or(0),
                iowait: parts[5].parse().unwrap_or(0),
                irq: parts[6].parse().unwrap_or(0),
                softirq: parts[7].parse().unwrap_or(0),
            });
        }

        stats
    }

    fn read_context_switches(&self) -> u64 {
        let file = match File::open("/proc/stat") {
            Ok(f) => f,
            Err(_) => return 0,
        };

        let reader = BufReader::new(file);

        for line in reader.lines().flatten() {
            if line.starts_with("ctxt") {
                return line
                    .split_whitespace()
                    .nth(1)
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(0);
            }
        }
        0
    }

    fn read_load_avg(&self) -> f32 {
        std::fs::read_to_string("/proc/loadavg")
            .ok()
            .and_then(|content| {
                content
                    .split_whitespace()
                    .next()
                    .and_then(|s| s.parse().ok())
            })
            .unwrap_or(0.0)
    }

    fn read_task_stats(&self) -> (u32, u32) {
        let file = match File::open("/proc/stat") {
            Ok(f) => f,
            Err(_) => return (0, 0),
        };

        let reader = BufReader::new(file);
        let mut running = 0;
        let mut blocked = 0;

        for line in reader.lines().flatten() {
            if line.starts_with("procs_running") {
                running = line
                    .split_whitespace()
                    .nth(1)
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(0);
            } else if line.starts_with("procs_blocked") {
                blocked = line
                    .split_whitespace()
                    .nth(1)
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(0);
            }
        }

        (running, blocked)
    }

    fn calculate_utilization(&self, prev: &CpuStat, curr: &CpuStat) -> f32 {
        let prev_idle = prev.idle + prev.iowait;
        let curr_idle = curr.idle + curr.iowait;

        let prev_total = prev.total();
        let curr_total = curr.total();

        let total_diff = curr_total.saturating_sub(prev_total) as f32;
        let idle_diff = curr_idle.saturating_sub(prev_idle) as f32;

        if total_diff > 0.0 {
            ((total_diff - idle_diff) / total_diff * 100.0).min(100.0)
        } else {
            0.0
        }
    }

    fn collect(&mut self) -> CpuMetrics {
        let curr_stats = self.read_cpu_stats();
        let curr_context_switches = self.read_context_switches();
        let (running, blocked) = self.read_task_stats();
        let load_avg = self.read_load_avg();

        let mut per_core_util = Vec::new();

        if !self.prev_cpu_stats.is_empty() && self.prev_cpu_stats.len() == curr_stats.len() {
            for (prev, curr) in self.prev_cpu_stats.iter().zip(curr_stats.iter()) {
                per_core_util.push(self.calculate_utilization(prev, curr));
            }
        } else {
            per_core_util = vec![0.0; curr_stats.len()];
        }

        let avg_util = if !per_core_util.is_empty() {
            per_core_util.iter().sum::<f32>() / per_core_util.len() as f32
        } else {
            0.0
        };

        let context_switches_delta =
            curr_context_switches.saturating_sub(self.prev_context_switches);

        self.prev_cpu_stats = curr_stats;
        self.prev_context_switches = curr_context_switches;

        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        let metrics = CpuMetrics {
            timestamp,
            per_core_util,
            avg_util,
            context_switches: context_switches_delta,
            running_tasks: running,
            blocked_tasks: blocked,
            load_avg_1m: load_avg,
        };

        // Log metrics
        self.logger.log_metrics(
            metrics.avg_util,
            metrics.context_switches,
            metrics.load_avg_1m,
        );

        self.history.push_back(metrics.clone());
        if self.history.len() > METRIC_HISTORY_SIZE {
            self.history.pop_front();
        }

        metrics
    }

    fn get_stability_score(&self) -> f32 {
        if self.history.len() < 10 {
            return 0.0;
        }

        let utils: Vec<f32> = self.history.iter().map(|m| m.avg_util).collect();

        let mean = utils.iter().sum::<f32>() / utils.len() as f32;
        let variance = utils.iter().map(|&x| (x - mean).powi(2)).sum::<f32>() / utils.len() as f32;

        (100.0 - variance.sqrt()).max(0.0)
    }
}

fn log_metrics_csv(metrics: &CpuMetrics, mode: &str) {
    let mut file = OpenOptions::new()
        .create(true)
        .write(true)
        .append(true)
        .open(METRICS_CSV_PATH)
        .expect("Failed to open metrics CSV");

    if file.metadata().unwrap().len() == 0 {
        writeln!(
            file,
            "timestamp,mode,avg_util,context_switches,running_tasks,blocked_tasks,load_avg"
        )
        .ok();
    }

    writeln!(
        file,
        "{},{},{:.2},{},{},{},{:.2}",
        metrics.timestamp,
        mode,
        metrics.avg_util,
        metrics.context_switches,
        metrics.running_tasks,
        metrics.blocked_tasks,
        metrics.load_avg_1m
    )
    .ok();
}

fn write_state_json(metrics: &CpuMetrics, stability: f32) {
    let state = serde_json::json!({
        "timestamp": metrics.timestamp,
        "cpu_util": metrics.avg_util,
        "context_switches": metrics.context_switches,
        "stability": stability,
        "running_tasks": metrics.running_tasks,
        "blocked_tasks": metrics.blocked_tasks,
        "load_avg": metrics.load_avg_1m,
    });

    std::fs::write(STATE_FILE_PATH, state.to_string()).ok();
}

fn read_action_json() -> Option<SchedulerAction> {
    let content = std::fs::read_to_string(ACTION_FILE_PATH).ok()?;

    if content.trim().is_empty() {
        return None;
    }

    serde_json::from_str(&content).ok()
}

fn main() {
    println!("═══════════════════════════════════════════════════════════");
    println!("  CPU SCHEDULING OPTIMIZER - Rust Core");
    println!("  Deep RL-based System Scheduler");
    println!("═══════════════════════════════════════════════════════════");
    println!();

    // Initialize logger
    let logger = match Logger::new(LOG_FILE_PATH, LogLevel::Info, true) {
        Ok(l) => l,
        Err(e) => {
            eprintln!("Failed to initialize logger: {}", e);
            std::process::exit(1);
        }
    };

    let logger = std::sync::Arc::new(logger);

    logger.info("=== CPU Scheduler Optimizer Started ===");
    logger.info(&format!("Rust version: {}", env!("CARGO_PKG_VERSION")));

    // Initialize metrics collector
    let mut collector = MetricsCollector::new(logger.clone());

    // Initialize controller
    let mut controller = match SchedulerController::new(ACTION_LOG_PATH, 2, 30) {
        Ok(c) => c,
        Err(e) => {
            logger.log_error_ctx("initialize controller", &e);
            std::process::exit(1);
        }
    };

    logger.info("Components initialized successfully");

    // Baseline collection phase
    println!("📊 Collecting baseline metrics for 60 seconds...\n");
    logger.info("Starting baseline collection phase");

    let baseline_start = Instant::now();
    let baseline_duration = Duration::from_secs(60);

    while baseline_start.elapsed() < baseline_duration {
        let metrics = collector.collect();
        let stability = collector.get_stability_score();

        log_metrics_csv(&metrics, "baseline");
        write_state_json(&metrics, stability);

        println!(
            "CPU: {:.1}% | CS: {} | Tasks: R={} B={} | Load: {:.2} | Stability: {:.1}",
            metrics.avg_util,
            metrics.context_switches,
            metrics.running_tasks,
            metrics.blocked_tasks,
            metrics.load_avg_1m,
            stability
        );

        thread::sleep(Duration::from_millis(MONITOR_INTERVAL_MS));
    }

    println!("\n✅ Baseline collection complete!");
    logger.info("Baseline collection phase completed");

    println!("🤖 Starting RL-controlled optimization...\n");
    logger.info("Starting RL-controlled optimization phase");

    // RL-controlled optimization phase
    loop {
        let metrics = collector.collect();
        let stability = collector.get_stability_score();

        log_metrics_csv(&metrics, "rl_controlled");
        write_state_json(&metrics, stability);

        // Check for action from Python RL agent
        if let Some(action) = read_action_json() {
            match controller.apply_action(action) {
                Ok(result) => {
                    logger.log_action("RL", &result);
                    println!("⚡ {}", result);
                }
                Err(e) => {
                    logger.log_error_ctx("apply action", &e);
                    eprintln!("⚠️  Action failed: {}", e);
                }
            }

            // Clear action file
            std::fs::write(ACTION_FILE_PATH, "").ok();
        }

        println!(
            "CPU: {:.1}% | CS: {} | Stability: {:.1} | Tasks: R={} B={} | Load: {:.2}",
            metrics.avg_util,
            metrics.context_switches,
            stability,
            metrics.running_tasks,
            metrics.blocked_tasks,
            metrics.load_avg_1m
        );

        thread::sleep(Duration::from_millis(MONITOR_INTERVAL_MS));
    }
}
