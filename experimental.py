import re
import time
import socket
import json
import subprocess

# Accent MACs (alphabetically ordered)
ACCENT_MACS = {
    "DRESSER": "d8a01165a452",
    "FACES":   "cc40853d9142",
    "HORSE":   "cc4085840e8a",
    "PIG":     "cc40853e5276",
    "SKULLS":  "444f8e1f2fc8",
}

# Overhead MACs (alphabetically ordered)
OVERHEAD_MACS = {
    "ALIEN":    "cc40855a796e",
    "BATHROOM": "cc4085558f40",
    "ENTRANCE": "d8a011671f1a",
    "K_0":      "cc4085558842",
    "K_1":      "cc40855a7c1e",
    "S_0":      "cc4085558c88",
    "S_1":      "d8a01161d568",
    "TV_0":     "cc40855a7e7c",
    "TV_1":     "d8a01162e8da",
}

# Combine all MACs for overall lookups
ALL_MACS = {**ACCENT_MACS, **OVERHEAD_MACS}

# Default command parameters
DIVISOR = 8
DEFAULT_PARAMS = {
    "r": 255/DIVISOR,
    "g": 60/DIVISOR,
    "b": 1,
    "dimming": 10,
    "sceneID": None,
}

DIVISOR = 6
SKIP_LIST = list(OVERHEAD_MACS)
BR = 20

# Overrides:
#  1. GROUP_ACCENT and GROUP_OVERHEAD can apply to all accent/overhead devices if enabled.
#  2. Then each device can have its own override.
OVERRIDES = {
    "GROUP_ACCENT": {
        "enabled": False,
        "params": {"r": 255, "g": 30, "b": 0, "dimming": 40, "sceneID": None},
    },
    "GROUP_OVERHEAD": {
        "enabled": False,
        "params": {"r": 255, "g": 80, "b": 5, "dimming": 60, "sceneID": None},
    },

    "DRESSER": {"enabled": False, "params": {"r": 0, "g": 0, "b": 0, "dimming": 0, "sceneID": None}},
    "FACES": {"enabled": True, "params": {"r": 255, "g": 25, "b": 0, "dimming": 10, "sceneID": None}},
    "HORSE": {"enabled": True, "params": {"r": 255, "g": 25, "b": 0, "dimming": 10, "sceneID": None}},
    "PIG": {"enabled": True, "params": {"r": 255, "g": 25, "b": 0, "dimming": 10, "sceneID": None}},
    "SKULLS": {"enabled": True, "params": {"r": 255, "g": 25, "b": 0, "dimming": 20, "sceneID": None}},

    "ALIEN": {"enabled": False, "params": {"r": 0, "g": 0, "b": 0, "dimming": 0, "sceneID": None}},
    "BATHROOM": {"enabled": False, "params": {"r": 0, "g": 0, "b": 0, "dimming": 0, "sceneID": None}},
    "ENTRANCE": {"enabled": False, "params": {"r": 0, "g": 0, "b": 0, "dimming": 0, "sceneID": None}},
    "K_0": {"enabled": False, "params": {"r": 0, "g": 0, "b": 0, "dimming": 0, "sceneID": None}},
    "K_1": {"enabled": False, "params": {"r": 0, "g": 0, "b": 0, "dimming": 0, "sceneID": None}},
    "S_0": {"enabled": False, "params": {"r": 0, "g": 0, "b": 0, "dimming": 0, "sceneID": None}},
    "S_1": {"enabled": False, "params": {"r": 0, "g": 0, "b": 0, "dimming": 0, "sceneID": None}},
    "TV_1": {"enabled": False, "params": {"r": 0, "g": 0, "b": 0, "dimming": 0, "sceneID": None}},
    "TV_0": {"enabled": False, "params": {"r": 255/DIVISOR, "g": 60/DIVISOR, "b": 2, "dimming": 10, "sceneID": None}}
}


def sort_devices_by_alias(dev_list):
    """
    Sort a list of devices (alias, mac, ip) in place by alias.
    """
    dev_list.sort(key=lambda x: x[0])


def parse_devices(data):
    """
    Parse the ARP table output and extract IP and MAC addresses.
    Returns a list of tuples: (IP, MAC).
    """
    pattern = r"\S+\s+\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9A-Fa-f:]+)"
    devices = []
    for match in re.findall(pattern, data):
        ip = match[0]
        mac = ''.join(segment.zfill(2) for segment in match[1].split(":")).lower()
        devices.append((ip, mac))
    return devices


def get_override_name(mac):
    """
    Check if there's a device-specific override for this mac.
    Return the override key if found and enabled, otherwise None.
    """
    for device_key, device_mac in ALL_MACS.items():
        if mac == device_mac and OVERRIDES[device_key]["enabled"]:
            return device_key
    return None


def get_group_override_name(mac):
    """
    Determine if we should apply a group override:
      - GROUP_ACCENT if the device is in ACCENT_MACS and GROUP_ACCENT is enabled
      - GROUP_OVERHEAD if the device is in OVERHEAD_MACS and GROUP_OVERHEAD is enabled
    Return the group key if found, else None.
    """
    # Check accent group
    if mac in ACCENT_MACS.values() and OVERRIDES["GROUP_ACCENT"]["enabled"]:
        return "GROUP_ACCENT"
    # Check overhead group
    if mac in OVERHEAD_MACS.values() and OVERRIDES["GROUP_OVERHEAD"]["enabled"]:
        return "GROUP_OVERHEAD"
    return None


def get_command_params(mac):
    """
    Determine the final command parameters based on the device's MAC address.
    1. Start with DEFAULT_PARAMS.
    2. If there's a relevant group override (accent/overhead) and it's enabled, apply it.
    3. If there's a device-specific override that's enabled, apply that last.
    Returns a dict of r, g, b, dimming, etc.
    """
    params = DEFAULT_PARAMS.copy()

    # 1) Check group override
    group_override_key = get_group_override_name(mac)
    if group_override_key:
        params.update(OVERRIDES[group_override_key]["params"])

    # 2) Check device-specific override
    device_override_key = get_override_name(mac)
    if device_override_key:
        params.update(OVERRIDES[device_override_key]["params"])

    return params


def build_command_json(params):
    """
    Build a JSON command for Wiz lights from the given params.
    Returns the JSON string.
    """
    return json.dumps({
        "id": 1,
        "method": "setPilot",
        "params": {k: v for k, v in params.items() if v is not None},
    })


def send_command(ip, command):
    """
    Send a command to the specified device via UDP and parse success from the response.
    Returns True if the device responded with success; otherwise False.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(1)
        sock.sendto(command.encode(), (ip, 38899))
        response, _ = sock.recvfrom(1024)
        decoded = response.decode()
        data = json.loads(decoded)
        return True if data.get("success") == True else False
    except Exception:
        return False
    finally:
        time.sleep(1)
        sock.close()


def print_section(header, data_list, max_alias_length):
    """
    Print a header and each device in `data_list` with aligned columns:
    alias, mac, ip
    """
    if not data_list:
        return
    print(header)
    for alias, mac, ip in data_list:
        print(f"{alias:<{max_alias_length}}  {mac:<12}  {ip:<15}")
    print()  # Blank line after each section


def print_and_send_section(header, data_list, max_alias_length):
    """
    Print a header and, for each device, build and send commands,
    then print a single-line output with success/override info.
    """
    if not data_list:
        return
    print(header)
    for alias, mac, ip in data_list:
        if alias in SKIP_LIST:
            continue
        params = get_command_params(mac)
        command_json = build_command_json(params)
        success = send_command(ip, command_json)
        success_str = "TRUE" if success else "FALSE"
        
        # Check group override
        group_override_key = get_group_override_name(mac)
        group_override_str = "  GROUP_OVERRIDE" if group_override_key else ""
        
        # Check device override
        device_override_key = get_override_name(mac)
        device_override_str = "  OVERRIDE" if device_override_key else ""

        # Combine the possible override notes
        # e.g. "  GROUP_OVERRIDE  OVERRIDE" if both apply
        # or just "  OVERRIDE" or ""
        combined_override_str = f"{group_override_str}{device_override_str}"

        print(
            f"{alias:<{max_alias_length}}  "
            f"{mac:<12}  "
            f"{ip:<15}  "
            f"SUCCESS={success_str:<5}  "
            f"RED={int(params.get('r', 0)):<3}  "
            f"GREEN={int(params.get('g', 0)):<3}  "
            f"BLUE={int(params.get('b', 0)):<3}  "
            f"DIMMING={int(params.get('dimming', 0))}"
            f"{combined_override_str}"
        )
    print()


def discover_devices():
    """
    Discover devices on the network using ARP, then print them
    in aligned sections by device type (Accent, Overhead, Unknown).
    """
    print("Discovering devices on the network...")
    try:
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
        devices = parse_devices(result.stdout)
        
        if not devices:
            print("No devices found.")
            return result.stdout
        
        # Build a list of (alias, MAC, IP)
        discovered_info = []
        for (ip, mac) in devices:
            alias = next((name for name, stored_mac in ALL_MACS.items() if stored_mac == mac), "UNKNOWN")
            discovered_info.append((alias, mac, ip))
        
        # Separate into three groups: accent, overhead, unknown
        accent_list = []
        overhead_list = []
        unknown_list = []
        for alias, mac, ip in discovered_info:
            if alias in ACCENT_MACS:
                accent_list.append((alias, mac, ip))
            elif alias in OVERHEAD_MACS:
                overhead_list.append((alias, mac, ip))
            else:
                unknown_list.append((alias, mac, ip))
        
        # Sort each list by alias
        sort_devices_by_alias(accent_list)
        sort_devices_by_alias(overhead_list)
        sort_devices_by_alias(unknown_list)
        
        # Calculate max alias length for alignment
        all_aliases = accent_list + overhead_list + unknown_list
        max_alias_length = max(len(item[0]) for item in all_aliases) if all_aliases else 7
        
        # Print sections
        print_section("Accent Devices:", accent_list, max_alias_length)
        print_section("Overhead Devices:", overhead_list, max_alias_length)
        print_section("Unknown Devices:", unknown_list, max_alias_length)

        return result.stdout
    except Exception as e:
        print(f"Error discovering devices: {e}")
        return ""

def main():
    wrap()
    while(OVERRIDES["FACES"]["params"]["dimming"] > 10):
        OVERRIDES["FACES"]["params"]["dimming"] -= 1
        wrap()

def wrap():
    # 1. Discover devices (prints them).
    raw_data = discover_devices()
    # 2. Parse discovered data into a structured list.
    devices = parse_devices(raw_data)
    if not devices:
        return

    # 3. Separate known from unknown so we do NOT send commands to unknown.
    known_devices = []
    for (ip, mac) in devices:
        alias = next((name for name, stored_mac in ALL_MACS.items() if stored_mac == mac), "UNKNOWN")
        if alias != "UNKNOWN":
            known_devices.append((alias, mac, ip))

    # 4. Separate accent vs overhead
    accent_list = []
    overhead_list = []
    for alias, mac, ip in known_devices:
        if alias in ACCENT_MACS:
            accent_list.append((alias, mac, ip))
        else:
            overhead_list.append((alias, mac, ip))
    
    # 5. Sort each list by alias
    sort_devices_by_alias(accent_list)
    sort_devices_by_alias(overhead_list)

    # 6. If there are no known devices at all
    if not (accent_list or overhead_list):
        print("No known devices to send commands to.")
        return

    print("Sending commands to known devices...\n")

    # 7. Determine maximum alias length for alignment within these groups
    all_known = accent_list + overhead_list
    max_alias_length = max(len(item[0]) for item in all_known)

    # 8. Print accent devices first, then overhead
    print_and_send_section("Accent Devices:", accent_list, max_alias_length)
    print_and_send_section("Overhead Devices:", overhead_list, max_alias_length)


if __name__ == "__main__":
    main()
