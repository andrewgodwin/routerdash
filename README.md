# RouterDash

This is an experimental Django-based UI for my home router (which is a small Shuttle PC running Ubuntu).

Don't expect this code to work on your system unless you have a surprisingly similar setup to me
(see notes below). This won't do much on normal development computers.

## Network environment

This expects to be installed on a router which has the internet on one interface (mine is eth0)
and the local network on a series of other interfaces all connected to a single bridge (mine is br0).

To get proper traffic info, it also expects the traffic-logger.py script to be running against
the bridge and writing to /tmp/traffic-br0 (or whatever the bridge is called).

## License

The portions of the code which are mine are released under the 3-clause BSD license
(http://opensource.org/licenses/BSD-3-Clause)
