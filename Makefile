PREFIX = /usr/local

.PHONY: install uninstall

install:
	@# Load ec_sys module
	modprobe ec_sys write_support=1
	@# Setup module autoload (if not already configured)
	@grep -q '^ec_sys$$' /etc/modules-load.d/ec_sys.conf 2>/dev/null || echo "ec_sys" > /etc/modules-load.d/ec_sys.conf
	@grep -q 'write_support=1' /etc/modprobe.d/ec_sys.conf 2>/dev/null || echo "options ec_sys write_support=1" > /etc/modprobe.d/ec_sys.conf
	@# Install files
	install -m 755 acer-fan-control.py $(PREFIX)/bin/acer-fan-control
	@test -f /etc/acer-fan-control.conf || install -m 644 acer-fan-control.conf /etc/acer-fan-control.conf
	install -m 644 acer-fan-control.service /etc/systemd/system/
	@# Enable and start service
	systemctl daemon-reload
	systemctl enable --now acer-fan-control
	@echo "Installed. Check status: systemctl status acer-fan-control"

uninstall:
	systemctl disable --now acer-fan-control || true
	rm -f $(PREFIX)/bin/acer-fan-control
	rm -f /etc/systemd/system/acer-fan-control.service
	systemctl daemon-reload
	@echo "Uninstalled. Config left at /etc/acer-fan-control.conf"
