#What our scanner will do:
#Find your own local IP address
#Work out the network range to scan (e.g. 192.168.1.1 → 192.168.1.255)
#Ping each address to see if something responds
#Try to get the hostname of anything that responds
#Print the results in a clean list
#
import socket
import subprocess

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip

def get_network_prefix(ip):
    parts = ip.split(".")
    prefix = ".".join(parts[:3])
    return prefix

def ping(ip):
    result = subprocess.run(
        ["ping", "-n", "1", "-w", "500", ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    return result.returncode == 0   # 0 means success

local_ip = get_local_ip()
prefix = get_network_prefix(local_ip)

print(f"Detected IP: {local_ip}")
user_input = input(f"Network prefix to scan [{prefix}]: ").strip()
prefix = user_input if user_input else prefix

print(f"Scanning: {prefix}.1  →  {prefix}.254 ...\n")

for i in range(1, 255):
    ip = f"{prefix}.{i}"
    if ping(ip):
        print(f"  UP  {ip}")