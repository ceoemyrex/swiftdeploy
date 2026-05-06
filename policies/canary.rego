package canary

# Get configuration from data
config = data.config

# Rule: Deny if error rate > maximum
deny[msg] {
    input.error_rate > config.max_error_rate
    msg := sprintf("Error rate %.2f%% > maximum %.2f%%", [input.error_rate * 100, config.max_error_rate * 100])
}

# Rule: Deny if P99 latency > maximum
deny[msg] {
    input.p99_latency_ms > config.max_p99_latency_ms
    msg := sprintf("P99 latency %.0fms > maximum %.0fms", [input.p99_latency_ms, config.max_p99_latency_ms])
}

# Rule: Deny if uptime < minimum (just restarted)
deny[msg] {
    input.uptime_seconds < config.min_uptime_before_promote
    msg := sprintf("Uptime %.0fs < minimum %.0fs before canary promotion", [input.uptime_seconds, config.min_uptime_before_promote])
}

# Decision: allow if no denials
allow {
    count(deny) == 0
}
