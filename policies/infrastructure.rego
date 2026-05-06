package infrastructure

# Get configuration from data
config = data.config

# Rule: Deny if disk free < minimum
deny[msg] {
    input.disk_free_gb < config.min_disk_free_gb
    msg := sprintf("Disk free %.1fGB < minimum %.1fGB", [input.disk_free_gb, config.min_disk_free_gb])
}

# Rule: Deny if CPU load > maximum
deny[msg] {
    input.cpu_load > config.max_cpu_load
    msg := sprintf("CPU load %.2f > maximum %.2f", [input.cpu_load, config.max_cpu_load])
}

# Rule: Deny if memory available < minimum
deny[msg] {
    input.mem_available_percent < config.min_mem_available_percent
    msg := sprintf("Memory available %.1f%% < minimum %.1f%%", [input.mem_available_percent, config.min_mem_available_percent])
}

# Decision: allow if no denials
allow {
    count(deny) == 0
}
