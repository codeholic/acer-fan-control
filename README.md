# Acer Nitro 5 Fan Control for Linux

Temperature-based fan control daemon for Acer Nitro 5 laptops. Replaces the default 100% fan speed on Linux with a quiet, temperature-responsive curve.

**Warning:** This software manipulates EC registers directly. Use at your own risk. If something goes wrong, reboot to restore BIOS control.

## Supported Models

- AN515-55 (tested)
- AN515-57 and similar models may work

## Install

Requires `lm-sensors` (`sudo apt install lm-sensors` on Debian/Ubuntu).

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
| < 50C       | 30%       |
| 50-65C      | 40%       |
| 65-75C      | 55%       |
| 75-85C      | 70%       |
| > 85C       | 100%      |

Edit `/usr/local/etc/acer-fan-control.conf` to customize.

## Uninstall

```bash
sudo make uninstall
```

## How It Works

The daemon reads CPU/GPU temperatures every 2 seconds and writes fan speeds to the laptop's Embedded Controller (EC) via `/sys/kernel/debug/ec/ec0/io`.

| Register | Address | Purpose |
|----------|---------|---------|
| 34 | 0x22 | CPU fan control mode (`0x0c` = manual) |
| 33 | 0x21 | GPU fan control mode (`0x30` = manual) |
| 55 | 0x37 | CPU fan speed (0-100%) |
| 58 | 0x3a | GPU fan speed (0-100%) |

The `ec_sys` kernel module with `write_support=1` exposes these registers to userspace.

## License

MIT
