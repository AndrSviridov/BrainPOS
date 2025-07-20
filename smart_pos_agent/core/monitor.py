# smart_pos_agent/core/monitor.py

import logging
import psutil

def run_system_checks():
    logging.debug("Running basic system checks...")
    try:
        check_cpu()
        check_memory()
        check_disks()
        check_usb_devices()
        logging.info("System checks completed successfully.")
    except Exception as e:
        logging.exception("System checks failed: %s", e)

def check_cpu():
    cpu_usage = psutil.cpu_percent(interval=1)
    logging.info(f"CPU Usage: {cpu_usage}%")

def check_memory():
    mem = psutil.virtual_memory()
    logging.info(f"Memory Total: {mem.total}, Available: {mem.available}, Used: {mem.used}, Percent: {mem.percent}%")

def check_disks():
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            logging.info(f"Disk {part.device}: Total: {usage.total}, Used: {usage.used}, Free: {usage.free}, Percent: {usage.percent}%")
        except PermissionError:
            logging.warning(f"Permission denied for disk {part.device}")

def check_usb_devices():
    usb_devices = []
    try:
        for device in psutil.disk_partitions():
            if 'removable' in device.opts or 'cdrom' in device.opts:
                usb_devices.append(device.device)
        logging.info(f"USB Devices: {usb_devices}")
    except Exception as e:
        logging.warning(f"Failed to detect USB devices: {e}")
