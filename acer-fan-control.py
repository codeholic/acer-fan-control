#!/usr/bin/env python3
"""Acer Nitro 5 fan control daemon for Linux."""

import argparse
import configparser
import logging
import re
import subprocess
import sys
import time
from pathlib import Path

EC_PATH = Path("/sys/kernel/debug/ec/ec0/io")
CONFIG_PATH = Path("/etc/acer-fan-control.conf")
REG_CPU_FAN_CONTROL = 34
REG_GPU_FAN_CONTROL = 33
REG_CPU_FAN_SPEED = 55
REG_GPU_FAN_SPEED = 58

DEFAULT_THRESHOLDS = [(85, 100), (75, 70), (65, 55), (50, 40), (0, 30)]

log = logging.getLogger("acer-fan-control")


def load_config(config_path):
    config = configparser.ConfigParser()
    thresholds = DEFAULT_THRESHOLDS
    log_level = "INFO"
    if config_path.exists():
        config.read(config_path)
        if "thresholds" in config:
            thresholds = [(int(temp), int(speed)) for temp, speed in config["thresholds"].items()]
            thresholds = sorted(thresholds, reverse=True)
        if "settings" in config:
            log_level = config["settings"].get("log_level", "INFO").upper()
    return thresholds, log_level


def get_cpu_temp():
    try:
        output = subprocess.check_output(["sensors", "-u"], text=True)
        log.debug("sensors output:\n%s", output)
        for line in output.split("\n"):
            if "Package id 0" in line or "Tctl" in line:
                match = re.search(r"temp\d+_input:\s*([\d.]+)", next(iter(output.split(line)[1:]), ""))
                if not match:
                    for next_line in output.split(line)[1].split("\n")[:3]:
                        match = re.search(r"temp\d+_input:\s*([\d.]+)", next_line)
                        if match:
                            temp = float(match.group(1))
                            log.debug("CPU temp from '%s': %s", line.strip(), temp)
                            return temp
        for match in re.finditer(r"temp\d+_input:\s*([\d.]+)", output):
            temp = float(match.group(1))
            log.debug("CPU temp (fallback): %s", temp)
            return temp
    except Exception as e:
        log.error("Error reading CPU temp: %s", e)
    log.debug("CPU temp: using default 50.0")
    return 50.0


def get_gpu_temp():
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            text=True, stderr=subprocess.DEVNULL
        )
        temp = float(output.strip())
        log.debug("GPU temp from nvidia-smi: %s", temp)
        return temp
    except Exception as e:
        log.debug("nvidia-smi failed (%s), using CPU temp for GPU", e)
        return get_cpu_temp()


def calc_fan_speed(temp, thresholds):
    for threshold, speed in thresholds:
        if temp >= threshold:
            return speed
    return 30


def write_ec(register, value, dry_run=False):
    log.debug("write_ec: reg=%d val=%d (0x%02x) dry_run=%s", register, value, value, dry_run)
    if dry_run:
        return True
    try:
        with open(EC_PATH, "r+b") as f:
            f.seek(register)
            f.write(bytes([value]))
        return True
    except Exception as e:
        log.error("Error writing EC register %d: %s", register, e)
        return False


def enable_manual_control(dry_run=False):
    ok = write_ec(REG_CPU_FAN_CONTROL, 0x0C, dry_run)
    ok &= write_ec(REG_GPU_FAN_CONTROL, 0x30, dry_run)
    return ok


def set_fan_speeds(cpu_speed, gpu_speed, dry_run=False):
    write_ec(REG_CPU_FAN_SPEED, cpu_speed, dry_run)
    write_ec(REG_GPU_FAN_SPEED, gpu_speed, dry_run)


def main():
    parser = argparse.ArgumentParser(description="Acer Nitro 5 Fan Control")
    parser.add_argument("--dry-run", action="store_true", help="Don't write to EC")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Log level")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="Config file path")
    args = parser.parse_args()

    if not args.dry_run and not EC_PATH.exists():
        print(f"Error: {EC_PATH} not found. Run: modprobe ec_sys write_support=1", file=sys.stderr)
        sys.exit(1)

    thresholds, config_log_level = load_config(args.config)
    level = args.log_level or config_log_level
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")

    log.info("Starting (dry_run=%s, log_level=%s, thresholds=%s)", args.dry_run, level, thresholds)

    if not enable_manual_control(args.dry_run):
        log.warning("Failed to enable manual control")

    last_cpu_speed = last_gpu_speed = -1

    while True:
        cpu_temp = get_cpu_temp()
        gpu_temp = get_gpu_temp()

        cpu_speed = calc_fan_speed(cpu_temp, thresholds)
        gpu_speed = calc_fan_speed(gpu_temp, thresholds)

        if cpu_speed != last_cpu_speed or gpu_speed != last_gpu_speed:
            log.info("CPU: %.0fC -> %d%%, GPU: %.0fC -> %d%%", cpu_temp, cpu_speed, gpu_temp, gpu_speed)
            set_fan_speeds(cpu_speed, gpu_speed, args.dry_run)
            last_cpu_speed, last_gpu_speed = cpu_speed, gpu_speed

        time.sleep(2)


if __name__ == "__main__":
    main()
