import time
import subprocess


def get_speeds(interface):
    """
    Gets an approximate tx/rx speed for the given interface, in bytes per second.
    """
    # Get the current values
    now_time = time.time()
    with open("/sys/class/net/%s/statistics/rx_bytes" % interface) as fh:
        rx_bytes = int(fh.read().strip())
    with open("/sys/class/net/%s/statistics/tx_bytes" % interface) as fh:
        tx_bytes = int(fh.read().strip())
    # See if there's old values to compare against
    write_new = True
    try:
        with open("/tmp/rdash-%s-speeds" % interface) as fh:
            old_time, old_rx, old_tx = fh.read().strip().split()
        delta = now_time - float(old_time)
        rx_delta = rx_bytes - int(old_rx)
        tx_delta = tx_bytes - int(old_tx)
        rx_speed = rx_delta / delta
        tx_speed = tx_delta / delta
    except IOError:
        rx_speed = None
        tx_speed = None
    # Write to temp file if we need to
    if write_new:
        with open("/tmp/rdash-%s-speeds" % interface, "w") as fh:
            fh.write("%s %s %s\n" % (now_time, rx_bytes, tx_bytes))
    # Return speeds
    return rx_speed, tx_speed


def get_devices(interface):
    """
    Returns the current set of devices on the local network, as a list
    of dicts.

    Will also include wireless info if it can be found.
    """
    # Use the ARP table to find "active" devices
    devices = {}
    with open("/proc/net/arp") as fh:
        for line in fh:
            if line.startswith("IP address"):
                continue
            ip, hw, flags, mac, mask, this_interface = line.split()
            mac = mac.lower()
            if interface == this_interface:
                devices[mac] = {
                    "mac": mac,
                    "name": get_name(mac),
                }
    # Run get_stations and add in any wireless info
    stations = get_stations("wlan0")
    for mac, device in devices.items():
        if mac in stations:
            device['wireless'] = stations[mac]
    return devices


def get_stations(interface):
    """
    Returns current WiFi stations seen in the given interface,
    with some stats.
    """
    output = subprocess.check_output(["iw", interface, "station", "dump"])
    stations = []
    station = {}
    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("Station "):
            if station:
                stations[station['mac']] = station
            mac = line.split()[1].lower()
            station = {
                "mac": mac,
            }
        elif line.startswith("signal avg:"):
            station['signal'] = line.split()[1]
    if station:
        stations[station['mac']] = station
    return stations


def get_name(mac):
    """
    Tries to look up a friendly name for a MAC address.
    """
    if mac == "70:18:8b:ce:6b:a7":
        return "charmander"
    return "unknown"
