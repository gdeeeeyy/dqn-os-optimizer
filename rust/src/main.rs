// main.rs - Fixed CPU Scheduler Monitor with proper mode handling

use serde::{Deserialize, Serialize};
use serde_json;
use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::Path;
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

const METRICS_FILE: &str = "/tmp/scheduler_metrics.csv";
const STATE_FILE: &str = "/tmp/rl_state.json";
const COLLECT_INTERVAL_MS: u64 = 2000; // 2 seconds
const BASELINE_DURATION_SEC: u64 = 60; // 60 seconds

#[derive(Serialize, Deserialize, Debug)]
struct RLState {
    mode: String,
    episode: i32,
    epsilon: f64,
    timestamp: u64,
}

struct CPUMetrics {
    cpu_usage: f64,
    cpu_variance: f64,
    context_switches: u64,
    load_avg: f64,
}

struct Monitor {
    start_time: SystemTime,
    baseline_start: Option<SystemTime>,
    training_start: Option<SystemTime>,
    mode: String,
}

impl Monitor {
    fn new() -> Self {
        Monitor {
            start_time: SystemTime::now(),
            baseline_start: None,
            training_start: None,
            mode: String::from("baseline"),
        }
    }

    fn get_current_mode(&mut self) -> String {
        // Check if state file exists and read mode from it
        if Path::new(STATE_FILE).exists() {
            if let Ok(file) = File::open(STATE_FILE) {
                if let Ok(state) = serde_json::from_reader::<_, RLState>(file) {
                    self.mode = state.mode.clone();
                    return self.mode.clone();
                }
            }
        }

        // Fallback to time-based mode switching
        let elapsed = self.start_time.elapsed().unwrap_or(Duration::from_secs(0));

        if elapsed.as_secs() < BASELINE_DURATION_SEC {
            self.mode = String::from("baseline");
            if self.baseline_start.is_none() {
                self.baseline_start = Some(SystemTime::now());
                println!(
                    "[Rust Monitor] Starting BASELINE phase ({}s)",
                    BASELINE_DURATION_SEC
                );
            }
        } else {
            self.mode = String::from("rl");
            if self.training_start.is_none() {
                self.training_start = Some(SystemTime::now());
                println!("[Rust Monitor] Switching to RL/TRAINING phase");
            }
        }

        self.mode.clone()
    }

    fn collect_cpu_usage(&self) -> f64 {
        // Read /proc/stat for CPU usage
        if let Ok(file) = File::open("/proc/stat") {
            let reader = BufReader::new(file);
            if let Some(Ok(line)) = reader.lines().next() {
                if line.starts_with("cpu ") {
                    let parts: Vec<&str> = line.split_whitespace().collect();
                    if parts.len() >= 8 {
                        let user: u64 = parts[1].parse().unwrap_or(0);
                        let nice: u64 = parts[2].parse().unwrap_or(0);
                        let system: u64 = parts[3].parse().unwrap_or(0);
                        let idle: u64 = parts[4].parse().unwrap_or(0);
                        let iowait: u64 = parts[5].parse().unwrap_or(0);

                        let total = user + nice + system + idle + iowait;
                        let active = user + nice + system;

                        if total > 0 {
                            return (active as f64 / total as f64) * 100.0;
                        }
                    }
                }
            }
        }
        0.0
    }

    fn collect_cpu_variance(&self) -> f64 {
        // Simple variance approximation based on per-CPU usage
        let mut cpu_usages = Vec::new();

        if let Ok(file) = File::open("/proc/stat") {
            let reader = BufReader::new(file);
            for line_result in reader.lines() {
                if let Ok(line) = line_result {
                    if line.starts_with("cpu") && !line.starts_with("cpu ") {
                        let parts: Vec<&str> = line.split_whitespace().collect();
                        if parts.len() >= 8 {
                            let user: u64 = parts[1].parse().unwrap_or(0);
                            let nice: u64 = parts[2].parse().unwrap_or(0);
                            let system: u64 = parts[3].parse().unwrap_or(0);
                            let idle: u64 = parts[4].parse().unwrap_or(0);

                            let total = user + nice + system + idle;
                            let active = user + nice + system;

                            if total > 0 {
                                cpu_usages.push((active as f64 / total as f64) * 100.0);
                            }
                        }
                    }
                }
            }
        }

        if cpu_usages.is_empty() {
            return 0.0;
        }

        let mean = cpu_usages.iter().sum::<f64>() / cpu_usages.len() as f64;
        let variance =
            cpu_usages.iter().map(|x| (x - mean).powi(2)).sum::<f64>() / cpu_usages.len() as f64;

        variance.sqrt()
    }

    fn collect_context_switches(&self) -> u64 {
        // Read /proc/stat for context switches
        if let Ok(file) = File::open("/proc/stat") {
            let reader = BufReader::new(file);
            for line_result in reader.lines() {
                if let Ok(line) = line_result {
                    if line.starts_with("ctxt ") {
                        let parts: Vec<&str> = line.split_whitespace().collect();
                        if parts.len() >= 2 {
                            return parts[1].parse().unwrap_or(0);
                        }
                    }
                }
            }
        }
        0
    }

    fn collect_load_average(&self) -> f64 {
        // Read /proc/loadavg
        if let Ok(file) = File::open("/proc/loadavg") {
            let reader = BufReader::new(file);
            if let Some(Ok(line)) = reader.lines().next() {
                let parts: Vec<&str> = line.split_whitespace().collect();
                if !parts.is_empty() {
                    return parts[0].parse().unwrap_or(0.0);
                }
            }
        }
        0.0
    }

    fn collect_metrics(&self) -> CPUMetrics {
        CPUMetrics {
            cpu_usage: self.collect_cpu_usage(),
            cpu_variance: self.collect_cpu_variance(),
            context_switches: self.collect_context_switches(),
            load_avg: self.collect_load_average(),
        }
    }

    fn write_metrics(&mut self, metrics: &CPUMetrics) {
        let mode = self.get_current_mode();
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        // Create file if doesn't exist, otherwise append
        let file_exists = Path::new(METRICS_FILE).exists();

        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open(METRICS_FILE)
            .expect("Failed to open metrics file");

        // Write header if new file
        if !file_exists {
            writeln!(
                file,
                "timestamp,mode,cpu_usage,cpu_variance,context_switches,load_avg"
            )
            .expect("Failed to write header");
        }

        // Write data
        writeln!(
            file,
            "{},{},{:.2},{:.2},{},{}",
            timestamp,
            mode,
            metrics.cpu_usage,
            metrics.cpu_variance,
            metrics.context_switches,
            metrics.load_avg
        )
        .expect("Failed to write metrics");

        // Print status
        let elapsed = self.start_time.elapsed().unwrap_or(Duration::from_secs(0));
        if mode == "baseline" {
            let remaining = BASELINE_DURATION_SEC.saturating_sub(elapsed.as_secs());
            println!(
                "[{}] Baseline: {}s remaining - CPU: {:.1}%, Var: {:.1}%, Switches: {}, Load: {:.2}",
                timestamp % 10000,
                remaining,
                metrics.cpu_usage,
                metrics.cpu_variance,
                metrics.context_switches,
                metrics.load_avg
            );
        } else {
            println!(
                "[{}] Training: {}s - CPU: {:.1}%, Var: {:.1}%, Switches: {}, Load: {:.2}",
                timestamp % 10000,
                elapsed.as_secs(),
                metrics.cpu_usage,
                metrics.cpu_variance,
                metrics.context_switches,
                metrics.load_avg
            );
        }
    }

    fn run(&mut self) {
        println!("\n============================================================");
        println!("CPU SCHEDULER MONITOR - STARTING");
        println!("============================================================");
        println!("[Rust Monitor] Metrics file: {}", METRICS_FILE);
        println!(
            "[Rust Monitor] Baseline duration: {}s",
            BASELINE_DURATION_SEC
        );
        println!(
            "[Rust Monitor] Collection interval: {}ms\n",
            COLLECT_INTERVAL_MS
        );

        loop {
            let metrics = self.collect_metrics();
            self.write_metrics(&metrics);

            thread::sleep(Duration::from_millis(COLLECT_INTERVAL_MS));
        }
    }
}

fn main() {
    // Clean up old metrics file
    let _ = std::fs::remove_file(METRICS_FILE);

    let mut monitor = Monitor::new();
    monitor.run();
}
