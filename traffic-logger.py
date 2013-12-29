#!/usr/bin/env python
"""
Traffic logger which analyses all packets passing through the given
interface and keeps summary traffic stats.
"""

import time
import subprocess
import sys


class Logger():

    def __init__(self, outfile, interface, network_prefix="192.168.1."):
        self.interface = interface
        self.network_prefix = network_prefix
        self.stats = {}
        self.last_flush = time.time()
        self.flush_interval = 1
        self.gc_delay = 30
        self.outfile = outfile

    def record_data(self, ip, direction, size):
        if ip not in self.stats:
            self.stats[ip] = {
                "rx_remote": 0,
                "rx_local": 0,
                "tx_remote": 0,
                "tx_local": 0,
                "seen": 0.
            }
        self.stats[ip][direction] += size
        self.stats[ip]['seen'] = time.time()

    def main(self):
        # Open tcpdump
        proc = subprocess.Popen(["tcpdump", "-n", "-i", self.interface], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)
        for line in iter(proc.stdout.readline, ''):
            try:
                when, proto, source, gt, dest, tail = line.split(" ", 5)
                length = int(tail.split()[-1])
                int(source.split(".")[3])
                int(dest.split(".")[3])
                source = ".".join(source.split(".")[:4])
                dest = ".".join(dest.split(".")[:4])
            except (ValueError, IndexError):
                continue
            if source.startswith(self.network_prefix):
                self.record_data(source, "rx_local" if dest.startswith(self.network_prefix) else "rx_remote", length)
            if dest.startswith(self.network_prefix):
                self.record_data(dest, "tx_local" if source.startswith(self.network_prefix) else "tx_remote", length)
            # Flush if we need to
            if time.time() - self.last_flush > self.flush_interval:
                self.flush()
                self.last_flush = time.time()

    def flush(self):
        # Clear out outdated entries
        for ip, stats in list(self.stats.items()):
            if time.time() - stats['seen'] > self.gc_delay:
                del self.stats[ip]
        # Write out data
        with open(self.outfile, "w") as fh:
            fh.write("ip rx_local rx_remote tx_local tx_remote last_seen\n")
            for ip, stats in self.stats.items():
                fh.write(
                    "%s %s %s %s %s %i\n" % (
                        ip,
                        stats['rx_local'],
                        stats['rx_remote'],
                        stats['tx_local'],
                        stats['tx_remote'],
                        stats['seen'],
                    ),
                )

if __name__ == "__main__":
    try:
        Logger(sys.argv[1], sys.argv[2]).main()
    except IndexError:
        print "Usage: %s <outfile> <interface>" % sys.argv[0]
