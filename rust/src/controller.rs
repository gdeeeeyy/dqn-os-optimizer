// controller.rs - Scheduler control module for CPU Scheduler Optimizer

use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs::{File, OpenOptions};
use std::io::Write;
use std::process::Command;
use std::time::{SystemTime, UNIX_EPOCH};

/// Scheduler policies supported by Linux
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SchedulerPolicy {
    SchedOther, // CFS (Completely Fair Scheduler)
    SchedFifo,  // Real-time FIFO
    SchedRr,    // Real-time Round Robin
    SchedBatch, // Batch processing
    SchedIdle,  // Very low priority
}

impl SchedulerPolicy {
    pub fn as_str(&self) -> &str {
        match self {
            SchedulerPolicy::SchedOther => "SCHED_OTHER",
            SchedulerPolicy::SchedFifo => "SCHED_FIFO",
            SchedulerPolicy::SchedRr => "SCHED_RR",
            SchedulerPolicy::SchedBatch => "SCHED_BATCH",
            SchedulerPolicy::SchedIdle => "SCHED_IDLE",
        }
    }

    pub fn chrt_flag(&self) -> &str {
        match self {
            SchedulerPolicy::SchedOther => "--other",
            SchedulerPolicy::SchedFifo => "--fifo",
            SchedulerPolicy::SchedRr => "--rr",
            SchedulerPolicy::SchedBatch => "--batch",
            SchedulerPolicy::SchedIdle => "--idle",
        }
    }

    pub fn from_string(s: &str) -> Option<Self> {
        match s {
            "SCHED_OTHER" => Some(SchedulerPolicy::SchedOther),
            "SCHED_FIFO" => Some(SchedulerPolicy::SchedFifo),
            "SCHED_RR" => Some(SchedulerPolicy::SchedRr),
            "SCHED_BATCH" => Some(SchedulerPolicy::SchedBatch),
            "SCHED_IDLE" => Some(SchedulerPolicy::SchedIdle),
            _ => None,
        }
    }
}

/// Scheduler action to be applied
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SchedulerAction {
    pub timestamp: u64,
    pub action_type: String,
    pub target_pid: Option<u32>,
    pub nice_value: Option<i32>,
    pub scheduler_policy: Option<String>,
    pub cpu_weight: Option<u32>,
}

/// Controller for managing scheduler operations
pub struct SchedulerController {
    action_log: File,
    action_count: u64,
    last_action_time: u64,
    min_action_interval: u64, // seconds
    max_actions_per_minute: u32,
    recent_actions: Vec<u64>,
    dry_run: bool,
}

impl SchedulerController {
    /// Create new scheduler controller
    pub fn new(log_path: &str, min_interval: u64, max_per_minute: u32) -> Result<Self, String> {
        let action_log = OpenOptions::new()
            .create(true)
            .write(true)
            .append(true)
            .open(log_path)
            .map_err(|e| format!("Failed to create action log: {}", e))?;

        Ok(SchedulerController {
            action_log,
            action_count: 0,
            last_action_time: 0,
            min_action_interval: min_interval,
            max_actions_per_minute: max_per_minute,
            recent_actions: Vec::new(),
            dry_run: false,
        })
    }

    /// Enable dry-run mode (don't actually apply actions)
    pub fn set_dry_run(&mut self, enabled: bool) {
        self.dry_run = enabled;
    }

    /// Check if we can apply an action based on rate limits
    fn can_apply_action(&mut self) -> bool {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        // Check minimum interval
        if now - self.last_action_time < self.min_action_interval {
            return false;
        }

        // Check actions per minute
        self.recent_actions.retain(|&t| now - t < 60);
        if self.recent_actions.len() >= self.max_actions_per_minute as usize {
            return false;
        }

        true
    }

    /// Apply a scheduler action
    pub fn apply_action(&mut self, action: SchedulerAction) -> Result<String, String> {
        // Rate limiting check
        if !self.can_apply_action() {
            return Err("Rate limit exceeded".to_string());
        }

        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();

        let result = match action.action_type.as_str() {
            "set_nice" => {
                if let (Some(pid), Some(nice)) = (action.target_pid, action.nice_value) {
                    self.set_process_nice(pid, nice)?
                } else {
                    return Err("Missing PID or nice value".to_string());
                }
            }
            "set_scheduler" => {
                if let (Some(pid), Some(policy_str)) =
                    (action.target_pid, action.scheduler_policy.as_ref())
                {
                    let policy = SchedulerPolicy::from_string(policy_str)
                        .ok_or("Invalid scheduler policy".to_string())?;
                    self.set_scheduler_policy(pid, policy)?
                } else {
                    return Err("Missing PID or policy".to_string());
                }
            }
            "adjust_cgroup" => {
                if let Some(weight) = action.cpu_weight {
                    self.adjust_cgroup_weight(weight)?
                } else {
                    return Err("Missing CPU weight".to_string());
                }
            }
            _ => {
                return Err(format!("Unknown action type: {}", action.action_type));
            }
        };

        // Update tracking
        self.last_action_time = now;
        self.recent_actions.push(now);
        self.action_count += 1;

        // Log action
        self.log_action(&action, &result)?;

        Ok(result)
    }

    /// Set process nice value
    fn set_process_nice(&self, pid: u32, nice: i32) -> Result<String, String> {
        // Validate nice value range (-20 to 19)
        if nice < -20 || nice > 19 {
            return Err(format!("Invalid nice value: {} (must be -20 to 19)", nice));
        }

        if self.dry_run {
            return Ok(format!("DRY RUN: Would set PID {} nice to {}", pid, nice));
        }

        // Check if process exists
        if !self.process_exists(pid) {
            return Err(format!("Process {} does not exist", pid));
        }

        let output = Command::new("renice")
            .arg("-n")
            .arg(nice.to_string())
            .arg("-p")
            .arg(pid.to_string())
            .output()
            .map_err(|e| format!("Failed to execute renice: {}", e))?;

        if output.status.success() {
            Ok(format!("Set PID {} nice value to {}", pid, nice))
        } else {
            let stderr = String::from_utf8_lossy(&output.stderr);
            Err(format!("renice failed: {}", stderr))
        }
    }

    /// Set scheduler policy for a process
    fn set_scheduler_policy(&self, pid: u32, policy: SchedulerPolicy) -> Result<String, String> {
        if self.dry_run {
            return Ok(format!(
                "DRY RUN: Would set PID {} scheduler to {}",
                pid,
                policy.as_str()
            ));
        }

        // Check if process exists
        if !self.process_exists(pid) {
            return Err(format!("Process {} does not exist", pid));
        }

        let policy_flag = policy.chrt_flag();

        // For real-time policies (FIFO, RR), we need a priority
        // For other policies, priority is typically 0
        let priority = match policy {
            SchedulerPolicy::SchedFifo | SchedulerPolicy::SchedRr => "1",
            _ => "0",
        };

        let output = Command::new("chrt")
            .arg(policy_flag)
            .arg(priority)
            .arg("-p")
            .arg(pid.to_string())
            .output()
            .map_err(|e| format!("Failed to execute chrt: {}", e))?;

        if output.status.success() {
            Ok(format!("Set PID {} scheduler to {}", pid, policy.as_str()))
        } else {
            let stderr = String::from_utf8_lossy(&output.stderr);
            Err(format!("chrt failed: {}", stderr))
        }
    }

    /// Adjust cgroup CPU weight
    fn adjust_cgroup_weight(&self, weight: u32) -> Result<String, String> {
        // Validate weight range (1-10000 for cgroup v2)
        if weight < 1 || weight > 10000 {
            return Err(format!("Invalid CPU weight: {} (must be 1-10000)", weight));
        }

        if self.dry_run {
            return Ok(format!(
                "DRY RUN: Would set cgroup CPU weight to {}",
                weight
            ));
        }

        // For cgroup v2, the CPU weight file is typically:
        // /sys/fs/cgroup/cpu.weight (for current cgroup)
        // This is a simplified implementation - production would need proper cgroup path handling

        let cgroup_path = "/sys/fs/cgroup/cpu.weight";

        std::fs::write(cgroup_path, weight.to_string())
            .map_err(|e| format!("Failed to write cgroup weight: {}", e))?;

        Ok(format!("Set cgroup CPU weight to {}", weight))
    }

    /// Check if a process exists
    fn process_exists(&self, pid: u32) -> bool {
        std::fs::metadata(format!("/proc/{}", pid)).is_ok()
    }

    /// Get list of running processes with high CPU usage
    pub fn get_high_cpu_processes(&self, threshold: f32) -> Vec<u32> {
        // This is a simplified implementation
        // In production, you'd parse /proc/[pid]/stat for CPU usage

        let mut high_cpu_pids = Vec::new();

        if let Ok(entries) = std::fs::read_dir("/proc") {
            for entry in entries.flatten() {
                if let Ok(file_name) = entry.file_name().into_string() {
                    if let Ok(pid) = file_name.parse::<u32>() {
                        // Simplified: just add some PIDs as candidates
                        // Real implementation would calculate CPU%
                        if pid > 1000 && high_cpu_pids.len() < 5 {
                            high_cpu_pids.push(pid);
                        }
                    }
                }
            }
        }

        high_cpu_pids
    }

    /// Get current nice value of a process
    pub fn get_process_nice(&self, pid: u32) -> Result<i32, String> {
        if !self.process_exists(pid) {
            return Err(format!("Process {} does not exist", pid));
        }

        let stat_path = format!("/proc/{}/stat", pid);
        let stat_content = std::fs::read_to_string(stat_path)
            .map_err(|e| format!("Failed to read process stat: {}", e))?;

        // Parse nice value from stat file (field 19)
        let fields: Vec<&str> = stat_content.split_whitespace().collect();
        if fields.len() > 18 {
            fields[18]
                .parse::<i32>()
                .map_err(|e| format!("Failed to parse nice value: {}", e))
        } else {
            Err("Invalid stat file format".to_string())
        }
    }

    /// Log action to file
    fn log_action(&mut self, action: &SchedulerAction, result: &str) -> Result<(), String> {
        let log_line = format!(
            "[{}] {} - {}\n",
            action.timestamp,
            serde_json::to_string(action).unwrap_or_else(|_| "{}".to_string()),
            result
        );

        self.action_log
            .write_all(log_line.as_bytes())
            .map_err(|e| format!("Failed to write action log: {}", e))?;

        self.action_log
            .flush()
            .map_err(|e| format!("Failed to flush action log: {}", e))?;

        Ok(())
    }

    /// Get statistics about applied actions
    pub fn get_stats(&self) -> HashMap<String, u64> {
        let mut stats = HashMap::new();
        stats.insert("total_actions".to_string(), self.action_count);
        stats.insert(
            "recent_actions".to_string(),
            self.recent_actions.len() as u64,
        );
        stats
    }

    /// Reset rate limiting counters
    pub fn reset_rate_limits(&mut self) {
        self.recent_actions.clear();
        self.last_action_time = 0;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scheduler_policy_conversion() {
        assert_eq!(SchedulerPolicy::SchedOther.as_str(), "SCHED_OTHER");
        assert_eq!(SchedulerPolicy::SchedBatch.chrt_flag(), "--batch");
    }

    #[test]
    fn test_scheduler_policy_from_string() {
        assert_eq!(
            SchedulerPolicy::from_string("SCHED_OTHER"),
            Some(SchedulerPolicy::SchedOther)
        );
        assert_eq!(SchedulerPolicy::from_string("INVALID"), None);
    }

    #[test]
    fn test_controller_creation() {
        let controller = SchedulerController::new("/tmp/test_actions.log", 2, 30);
        assert!(controller.is_ok());
    }

    #[test]
    fn test_nice_value_validation() {
        let controller = SchedulerController::new("/tmp/test_actions.log", 0, 100).unwrap();

        // Invalid nice values should fail
        assert!(controller.set_process_nice(1, -21).is_err());
        assert!(controller.set_process_nice(1, 20).is_err());
    }
}
