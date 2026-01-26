// logger.rs - Logging utilities for CPU Scheduler Optimizer

use chrono::Local;
use std::fs::{File, OpenOptions};
use std::io::Write;
use std::sync::Mutex;

/// Log levels for different types of messages
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum LogLevel {
    Debug,
    Info,
    Warning,
    Error,
}

impl LogLevel {
    fn as_str(&self) -> &str {
        match self {
            LogLevel::Debug => "DEBUG",
            LogLevel::Info => "INFO",
            LogLevel::Warning => "WARN",
            LogLevel::Error => "ERROR",
        }
    }

    fn color_code(&self) -> &str {
        match self {
            LogLevel::Debug => "\x1b[36m",   // Cyan
            LogLevel::Info => "\x1b[32m",    // Green
            LogLevel::Warning => "\x1b[33m", // Yellow
            LogLevel::Error => "\x1b[31m",   // Red
        }
    }
}

/// Main logger structure
pub struct Logger {
    file: Mutex<File>,
    min_level: LogLevel,
    console_enabled: bool,
}

impl Logger {
    /// Create a new logger instance
    pub fn new(log_path: &str, min_level: LogLevel, console_enabled: bool) -> Result<Self, String> {
        let file = OpenOptions::new()
            .create(true)
            .write(true)
            .append(true)
            .open(log_path)
            .map_err(|e| format!("Failed to open log file: {}", e))?;

        Ok(Logger {
            file: Mutex::new(file),
            min_level,
            console_enabled,
        })
    }

    /// Log a message with specified level
    pub fn log(&self, level: LogLevel, message: &str) {
        if !self.should_log(level) {
            return;
        }

        let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S%.3f");
        let level_str = level.as_str();
        let formatted = format!("[{}] [{}] {}", timestamp, level_str, message);

        // Write to file
        if let Ok(mut file) = self.file.lock() {
            writeln!(file, "{}", formatted).ok();
            file.flush().ok();
        }

        // Write to console if enabled
        if self.console_enabled {
            let color = level.color_code();
            let reset = "\x1b[0m";
            println!("{}{}{}", color, formatted, reset);
        }
    }

    /// Check if message should be logged based on level
    fn should_log(&self, level: LogLevel) -> bool {
        let level_value = level as u8;
        let min_value = self.min_level as u8;
        level_value >= min_value
    }

    /// Debug level logging
    pub fn debug(&self, message: &str) {
        self.log(LogLevel::Debug, message);
    }

    /// Info level logging
    pub fn info(&self, message: &str) {
        self.log(LogLevel::Info, message);
    }

    /// Warning level logging
    pub fn warn(&self, message: &str) {
        self.log(LogLevel::Warning, message);
    }

    /// Error level logging
    pub fn error(&self, message: &str) {
        self.log(LogLevel::Error, message);
    }

    /// Log with formatted string
    pub fn log_fmt(&self, level: LogLevel, message: String) {
        self.log(level, &message);
    }

    /// Log system metrics
    pub fn log_metrics(&self, cpu_util: f32, context_switches: u64, load_avg: f32) {
        let message = format!(
            "CPU: {:.2}% | CS: {} | Load: {:.2}",
            cpu_util, context_switches, load_avg
        );
        self.info(&message);
    }

    /// Log scheduler action
    pub fn log_action(&self, action_type: &str, details: &str) {
        let message = format!("Action: {} - {}", action_type, details);
        self.info(&message);
    }

    /// Log error with context
    pub fn log_error_ctx(&self, operation: &str, error: &str) {
        let message = format!("Failed to {}: {}", operation, error);
        self.error(&message);
    }

    /// Log performance metrics
    pub fn log_performance(&self, metric_name: &str, value: f64, unit: &str) {
        let message = format!("Performance: {} = {:.2} {}", metric_name, value, unit);
        self.info(&message);
    }
}

/// Global logger instance for easy access
pub struct GlobalLogger;

impl GlobalLogger {
    /// Initialize global logger
    pub fn init(log_path: &str) -> Result<Logger, String> {
        Logger::new(log_path, LogLevel::Info, true)
    }
}

/// Macro for convenient logging
#[macro_export]
macro_rules! log_info {
    ($logger:expr, $($arg:tt)*) => {
        $logger.info(&format!($($arg)*))
    };
}

#[macro_export]
macro_rules! log_warn {
    ($logger:expr, $($arg:tt)*) => {
        $logger.warn(&format!($($arg)*))
    };
}

#[macro_export]
macro_rules! log_error {
    ($logger:expr, $($arg:tt)*) => {
        $logger.error(&format!($($arg)*))
    };
}

#[macro_export]
macro_rules! log_debug {
    ($logger:expr, $($arg:tt)*) => {
        $logger.debug(&format!($($arg)*))
    };
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_logger_creation() {
        let logger = Logger::new("/tmp/test_logger.log", LogLevel::Info, false);
        assert!(logger.is_ok());
    }

    #[test]
    fn test_log_levels() {
        assert_eq!(LogLevel::Debug.as_str(), "DEBUG");
        assert_eq!(LogLevel::Info.as_str(), "INFO");
        assert_eq!(LogLevel::Warning.as_str(), "WARN");
        assert_eq!(LogLevel::Error.as_str(), "ERROR");
    }

    #[test]
    fn test_should_log() {
        let logger = Logger::new("/tmp/test_logger.log", LogLevel::Warning, false).unwrap();
        assert!(!logger.should_log(LogLevel::Debug));
        assert!(!logger.should_log(LogLevel::Info));
        assert!(logger.should_log(LogLevel::Warning));
        assert!(logger.should_log(LogLevel::Error));
    }
}
