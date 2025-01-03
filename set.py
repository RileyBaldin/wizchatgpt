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
    # SceneID is prioritized
    "sceneID": None,
}

SET = {
    "method": "setPilot",
}.update(DEFAULT_PARAMS)

ON = {
    "method": "setState",
    "state": True
}

OFF = {
    "method": "setState",
    "state": False
}

COMMANDS = {
    # GROUPS
    "ACCENT": OFF,
    "OVERHEAD": None,

    # ACCENT
    "DRESSER":  None,
    "FACES":    None,
    "HORSE":    None,
    "PIG":      None,
    "SKULLS":   None,

    # OVERHEAD
    "ALIEN":    None,
    "BATHROOM": None,
    "ENTRANCE": None,
    "K_0":      None,
    "K_1":      None,
    "S_0":      None,
    "S_1":      None,
    "TV_0":     SET.update(DEFAULT_PARAMS),
    "TV_1":     None,
}

def send_command(ip, command):
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

def arp():
    pattern = re.compile(r"\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})")
    cmd = 'arp -a'
    output = subprocess.check_output(cmd,shell=True,stderr=subprocess.STDOUT, text=True)
    matches = pattern.findall(output)
    macs_to_ips = {re.sub(r":", "", mac): ip for ip, mac in matches}
    names_to_ips = {DEVICES[mac]: ip for mac, ip in macs_to_ips.items() if mac in DEVICES}
    return names_to_ips

def run_commands():
    names_to_ips = arp()
    for name, command in COMMANDS:
        if not command:
            break
        if name not in names_to_ips:
            break
        ip = names_to_ips[name]
        send_command(ip, command)



if __name__ == "__main__":
    run()
