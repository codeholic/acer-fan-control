# Acer Nitro 5 Fan Control for Linux

Fan control daemon for Acer Nitro 5 on Linux. Fixes fans running at 100% and loud fan noise at idle. A lightweight NitroSense alternative.

## The Problem

Acer Nitro 5 laptops have no fan control on Linux - the OS cannot access BIOS thermal controls, so the fans run at full speed constantly. This makes the laptop unusably loud, even when idle or just browsing.

This daemon fixes it by controlling fan speeds through the EC (Embedded Controller) based on CPU/GPU temperatures.

**Warning:** This software manipulates EC registers directly. Use at your own risk. If something goes wrong, reboot to restore BIOS control.

## Supported Models

Check your model: `cat /sys/class/dmi/id/product_name`

**Confirmed working:**
- AN515-55 (tested by maintainer)

**Should work** (same EC registers):
- AN515-54, AN515-56, AN515-57
- AN517-51, AN517-52

If it works on your model, please open a PR to add it to the confirmed list.

## Install

Requires `lm-sensors`. On Ubuntu/Debian: `sudo apt install lm-sensors`.

For NVIDIA GPU temperature support, `nvidia-smi` must be available (comes with NVIDIA drivers). Without it, GPU fan speed is based on CPU temperature.

```bash
sudo make install
```

## Usage

Check status:
```bash
systemctl status acer-fan-control
journalctl -u acer-fan-control -f
```

Test without writing to hardware:
```bash
sudo python3 acer-fan-control.py --dry-run
```

## Fan Curve

| Temperature | Fan Speed |
|-------------|-----------|
| < 45C       | 10%       |
| 45-50C      | 15%       |
| 50-55C      | 20%       |
| 55-60C      | 25%       |
| 60-65C      | 30%       |
| 65-70C      | 35%       |
| 70-75C      | 40%       |
| 75-80C      | 50%       |
| 80-85C      | 75%       |
| > 85C       | 100%      |

Edit `/etc/acer-fan-control.conf` to customize.

## Uninstall

```bash
sudo make uninstall
```

## How It Works

The daemon reads CPU/GPU temperatures every 2 seconds and writes fan speeds to the EC via `/sys/kernel/debug/ec/ec0/io` using the `ec_sys` kernel module.

| Register | Address | Purpose |
|----------|---------|---------|
| 34 | 0x22 | CPU fan control mode (`0x0c` = manual) |
| 33 | 0x21 | GPU fan control mode (`0x30` = manual) |
| 55 | 0x37 | CPU fan speed (0-100%) |
| 58 | 0x3a | GPU fan speed (0-100%) |

## Why Not nbfc-linux?

[nbfc-linux](https://github.com/nbfc-linux/nbfc-linux) is a popular fan control tool, but it has issues with Acer Nitro 5:

- No official config for Nitro 5 - you have to try configs from similar models
- Only "guides" fan speeds - BIOS can override, so fans may still run full speed
- Some Nitro models have locked EC registers that nbfc can't access

This daemon uses direct EC register writes, giving full control over fan speeds on supported models.

## Support

If this helped you, consider [buying me a coffee](https://buymeacoffee.com/codeholic).

## License

MIT
