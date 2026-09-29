import json
import re
from typing import List
from app.schemas.monitoring import NetworkMetrics, NetworkInterface


def parse_network_interfaces(raw_network_output: str) -> NetworkMetrics:
    """Parses network interfaces from 'ip -j addr' or standard 'ip addr' / 'ifconfig' output."""
    try:
        cleaned = raw_network_output.strip()
        if not cleaned:
            return NetworkMetrics(interfaces=[], error="Output network kosong.")

        # Attempt JSON parse from 'ip -j addr'
        if cleaned.startswith("[") and cleaned.endswith("]"):
            try:
                data = json.loads(cleaned)
                interfaces: List[NetworkInterface] = []
                for item in data:
                    ifname = item.get("ifname", "")
                    addr_info = item.get("addr_info", [])
                    addrs = []
                    for addr in addr_info:
                        if addr.get("family") == "inet":
                            ip = addr.get("local")
                            if ip and ip != "127.0.0.1":
                                addrs.append(ip)
                    if ifname and addrs:
                        interfaces.append(NetworkInterface(name=ifname, addresses=addrs))
                if interfaces:
                    return NetworkMetrics(interfaces=interfaces)
            except Exception:
                pass

        # Text parsing fallback (ip addr or ifconfig)
        interfaces: List[NetworkInterface] = []
        current_iface = None
        current_addrs: List[str] = []

        for line in cleaned.splitlines():
            line_str = line.strip()
            # Check '2: eth0: ...' or 'eth0: flags=...'
            iface_match = re.match(r"^(\d+:\s+)?([a-zA-Z0-9_-]+):", line)
            if iface_match:
                if current_iface and current_addrs:
                    interfaces.append(NetworkInterface(name=current_iface, addresses=current_addrs))
                current_iface = iface_match.group(2)
                current_addrs = []
                continue

            # Check inet address 'inet 192.168.1.10/24' or 'inet addr:192.168.1.10'
            inet_match = re.search(r"inet\s+(?:addr:)?([0-9\.]+)", line_str)
            if inet_match and current_iface:
                ip = inet_match.group(1)
                if ip != "127.0.0.1":
                    current_addrs.append(ip)

        if current_iface and current_addrs:
            interfaces.append(NetworkInterface(name=current_iface, addresses=current_addrs))

        return NetworkMetrics(interfaces=interfaces)

    except Exception as e:
        return NetworkMetrics(interfaces=[], error=f"Gagal memproses metrik network: {str(e)}")
