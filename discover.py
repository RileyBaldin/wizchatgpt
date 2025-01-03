import re
import time
import socket
import json
import subprocess

DEVICES = {
    "d8a01165a452": {"name": "DRESSER", "group": "accent"},
    "cc40853d9142": {"name": "FACES", "group": "accent"},
    "cc4085840e8a": {"name": "HORSE", "group": "accent"},
    "cc40853e5276": {"name": "PIG", "group": "accent"},
    "444f8e1f2fc8": {"name": "SKULLS", "group": "accent"},

    "cc40855a796e": {"name": "ALIEN", "group": "overhead"},
    "cc4085558f40": {"name": "BATHROOM", "group": "overhead"},
    "d8a011671f1a": {"name": "ENTRANCE", "group": "overhead"},
    "cc4085558842": {"name": "K_0", "group": "overhead"},
    "cc40855a7c1e": {"name": "K_1", "group": "overhead"},
    "cc4085558c88": {"name": "S_0", "group": "overhead"},
    "d8a01161d568": {"name": "S_1", "group": "overhead"},
    "cc40855a7e7c": {"name": "TV_0", "group": "overhead"},
    "d8a01162e8da": {"name": "TV_1", "group": "overhead"},
}

DEFAULT_PARAMS = {
    "r": 255,
    "g": 70,
    "b": 10,
    "dimming": 60,
    "sceneID": None,
}

OVERRIDES = {
    # GROUPS
    "ACCENT": False,
    "OVERHEAD": False,

    # ACCENT
    "DRESSER":  False,
    "FACES":    False,
    "HORSE":    False,
    "PIG":      False,
    "SKULLS":   False,

    # OVERHEAD
    "ALIEN":    False,
    "BATHROOM": False,
    "ENTRANCE": False,
    "K_0":  False,
    "K_1":  False,
    "S_0":  False,
    "S_1":  False,
    "TV_0": False,
    "TV_1": False,
}

def send_command(command):
    terminal_command = ["echo", "{}".format(command)]  # Replace with the actual command split into a list
    socat = ["socat", "-", "UDP-DATAGRAM:255.255.255.255:38899,broadcast"]
    process1 = subprocess.Popen(terminal_command, stdout=subprocess.PIPE, text=True)
    process2 = subprocess.run(socat, stdin=process1.stdout, capture_output=True, text=True, check=True)
    results = process2.stdout
    return results

def build_command(method, params={}):
    command = json.dumps({
        "method": method,
        "params": {k: v for k, v in params.items() if v is not None},
    })
    return command

def format_output(device_details):
    formatted = (
        f"{device_details['name']:<10} "  # Name column, 10 characters wide
        f"MAC={device_details['mac']:<17} "  # MAC column, 17 characters wide
        f"STATE={str(device_details.get('state', '')):<8} "  # STATE column, 8 characters
        f"SCENEID={str(device_details.get('sceneId', '')):<10} "  # SCENEID column, 10 characters
        f"RED={str(device_details.get('r', '')):<8} "  # RED column, 8 characters
        f"GREEN={str(device_details.get('g', '')):<8} "  # GREEN column, 8 characters
        f"BLUE={str(device_details.get('b', '')):<8} "  # BLUE column, 8 characters
        f"COOL={str(device_details.get('c', '')):<8} "  # COOL column, 8 characters
        f"WARM={str(device_details.get('w', '')):<8} "  # WARM column, 8 characters
        f"DIMMING={str(device_details.get('dimming', '')):<8}"  # DIMMING column, 8 characters
    )
    return formatted

def discover_devices():
    command = build_command("getPilot")
    results = send_command(command)
    devices = results.split('}{')
    devices = [device + '}' if not device.endswith('}}') else device for device in devices]
    devices = ['{' + device if not device.startswith('{') else device for device in devices]

    grouped_devices = {"accent": [], "overhead": []}

    for device in devices:
        try:
            device_details = json.loads(device)["result"]
            device_mac = device_details["mac"]
            # Ensure all parameters exist; use `` if not present
            for param in DEFAULT_PARAMS.keys():
                if param not in device_details:
                    device_details[param] = ""
            if device_mac in DEVICES:
                device_details["name"] = DEVICES[device_mac]["name"]
                group = DEVICES[device_mac]["group"]
                grouped_devices[group].append(device_details)
            else:
                device_details["name"] = "UNKNOWN"
        except Exception as e:
            print(f"Error processing device: {device}. Error: {e}")

    # Sort and display devices by group
    for group_name, devices in grouped_devices.items():
        print(group_name.upper())
        for device in sorted(devices, key=lambda x: x["name"]):
            print(format_output(device))
        print()  # Add a blank line between groups

def run():
    discover_devices()

if __name__ == "__main__":
    run()
