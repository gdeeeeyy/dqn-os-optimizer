use std::fs::File;
use std::io::BufRead;
use std::io::BufReader;

pub fn get_cpu_count() -> usize {
    std::thread::available_parallelism()
        .map(|n| n.get())
        .unwrap_or(1)
}

pub fn read_proc_stat() -> std::io::Result<Vec<String>> {
    let file = File::open("/proc/stat")?;
    let reader = BufReader::new(file);
    Ok(reader.lines().filter_map(Result::ok).collect())
}
