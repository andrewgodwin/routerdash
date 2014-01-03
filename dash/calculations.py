import os
import json
import time
import subprocess
import urllib2
from django.conf import settings

from .models import BytesRecord


def calc_speed(key, value, period=5):
    """
    Generic function to take a number of bytes as a current total and return
    the rate of change of that total per second.
    """
    # Write a row for now if there's not been data for more than a second
    now_time = time.time()
    if not BytesRecord.objects.filter(key=key, time__gte=(now_time - 1)).exists():
        BytesRecord.objects.create(key=key, time=now_time, value=value)
        if BytesRecord.objects.filter(key=key).count() == 1:
            return None
    # Fetch the oldest row in there and calculate speed from that
    old_record = BytesRecord.objects.filter(key=key).order_by("time")[0]
    speed = (value - old_record.value) / float(now_time - old_record.time)
    # Delete all rows that are too old
    BytesRecord.objects.filter(key=key, time__lt=(now_time - period)).delete()
    return speed


def get_speeds(interface):
    """
    Gets an approximate tx/rx speed for the given interface, in bytes per second.
    """
    # Get the current values
    with open("/sys/class/net/%s/statistics/rx_bytes" % interface) as fh:
        rx_bytes = int(fh.read().strip())
    with open("/sys/class/net/%s/statistics/tx_bytes" % interface) as fh:
        tx_bytes = int(fh.read().strip())
    # Return speeds
    return (
        calc_speed("iface-%s-rx" % interface, rx_bytes),
        calc_speed("iface-%s-tx" % interface, tx_bytes),
    )


def get_devices(interface):
    """
    Returns the current set of devices on the local network, as a list
    of dicts.

    Will also include wireless info if it can be found.
    """
    # Use the ARP table plus the wireless stations list to find "active" devices
    devices = {}
    stations = get_stations(settings.WIRELESS_INTERFACES)
    output = subprocess.check_output(["ip", "neighbour", "show", "dev", interface])
    for line in output.split("\n"):
        if not line.strip():
            continue
        try:
            ip, mac_type, mac, state = line.split(" ")
        except ValueError:
            continue
        mac = mac.lower()
        if mac == "00:00:00:00:00:00":
            continue
        if state.lower() in ("reachable", "delay", "probe") or mac in stations:
            devices[mac] = {
                "mac": mac,
                "ip": ip,
                "name": None,
                "manufacturer": get_manufacturer(mac),
            }
    # Use the leases file to get more info
    with open("/var/lib/misc/dnsmasq.leases") as fh:
        for line in fh:
            if not line.strip():
                continue
            expires, mac, ip, name, client_id = line.split()
            mac = mac.lower()
            if mac in devices:
                devices[mac]['name'] = None if name == "*" else name
                devices[mac]['lease_expires'] = expires
    # Run get_stations and add in any wireless info
    for mac, device in devices.items():
        if mac in stations:
            device['wireless'] = stations[mac]
            device['interface'] = stations[mac]['interface']
    # Use the traffic monitor to add real traffic info, if possible
    if os.path.exists("/tmp/traffic-%s" % interface):
        for device in devices.values():
            device['rx_speed'] = 0
            device['tx_speed'] = 0
        with open("/tmp/traffic-%s" % interface) as fh:
            for line in fh:
                if line.startswith("ip "):
                    continue
                ip, rx_local, rx_remote, tx_local, tx_remote, last_seen = line.split()
                for device in devices.values():
                    if device['ip'] == ip:
                        device['rx_speed'] = calc_speed("ip-%s-rx" % ip, int(rx_remote))
                        device['tx_speed'] = calc_speed("ip-%s-tx" % ip, int(tx_remote))
    # Label interfaces if they have a label
    for mac, device in devices.items():
        interface = device.get("interface", None)
        if interface in settings.INTERFACE_LABELS:
            device["interface_label"] = settings.INTERFACE_LABELS[interface]
    return devices


def get_stations(interfaces):
    """
    Returns current WiFi stations seen in the given interface,
    with some stats.
    """
    stations = {}
    station = {}
    for interface in interfaces:
        output = subprocess.check_output(["iw", interface, "station", "dump"])
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
                    "interface": interface,
                }
            elif line.startswith("signal:"):
                station['signal'] = int(line.split()[1])
            elif line.startswith("rx bytes:"):
                station['rx_speed'] = calc_speed("station-%s-rx" % station['mac'], int(line.split()[2]))
            elif line.startswith("tx bytes:"):
                station['tx_speed'] = calc_speed("station-%s-tx" % station['mac'], int(line.split()[2]))
            elif line.startswith("tx bitrate:"):
                station['tx_bitrate'] = float(line.split()[2])
                station['tx_bitrate_human'] = line.split()[2] + " Mb/s"
        if station:
            stations[station['mac']] = station
    return stations


def get_manufacturer(mac):
    """
    Gets the manufacturer of a mac address, with caching.
    """
    if not getattr(settings, "MAC_API_KEY", None):
        return "Unknown"
    stripped_mac = mac.lower().replace(":","")
    cache_file = "/tmp/mac-manu-%s" % stripped_mac
    try:
        if not os.path.exists(cache_file):
            result = json.loads(urllib2.urlopen("http://www.macvendorlookup.com/api/%s/%s/" % (settings.MAC_API_KEY, stripped_mac)).read())
            manufacturer = result[0]['company']
            with open(cache_file, "w") as fh:
                fh.write(manufacturer + "\n")
        else:
            with open(cache_file) as fh:
                manufacturer = fh.read().strip()
        return manufacturer
    except (IndexError, KeyError, ValueError):
        return "Unknown"
