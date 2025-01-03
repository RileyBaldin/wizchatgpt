import subprocess
import re

def arp():
    pattern = re.compile(r"\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})")
    cmd = 'arp -a'
    output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, text=True)
    matches = pattern.findall(output)
    mac_ip_dict = {re.sub(r":", "", mac): ip for ip, mac in matches}
    return mac_ip_dict

arp()