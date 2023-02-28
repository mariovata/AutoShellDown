# AutoShellDown

```
             __         __
 /\    |_ _ (_ |_  _ |||  \ _      _
/--\|_||_(_)__)| )(-`|||__/(_)\/\/| )
    
    Version: 1.0.0
    Listener, File Hosting, and Exfiltration
    Author: Mario Vata
    
    
usage: asd.py [-h] [-p PORT] [-lp LPORT] [-i INTERFACE] [-d DPORT] [-o OS] [-v] [-q]

options:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Listen port for the reverse shell
  -lp LPORT, --lport LPORT
                        Local port for the file server
  -i INTERFACE, --interface INTERFACE
                        The interface to use
  -d DPORT, --dport DPORT
                        The port to use for data exfiltration
  -o OS, --os OS        Currently not used
  -v, --verbose         Verbose output
  -q, --quiet           Quiet output

```

AutoShellDown is my attempt at making an automated reverse shell that automates some basic boring stuff like: 

* Setting up a server to host files 

* Uploading and running linpeas.sh

I made this so to speed up enumeration during privilege escalation on HackTheBox machines. This is very much a work in progress and I currently don't recommend using the experimental version of this script.

# Requirements

* Python 3.11
* pip3
* python3.11-venv (recommended)
* git
* Kali Linux

# Installation

## One-liner

### Venv (recommended, needs python3.11-venv) 
```
git clone https://github.com/mariovata/AutoShellDown.git && cd AutoShellDown && python3 -m venv asd-env && source asd-env/bin/activate && pip3 install -r requirements.txt && chmod +x asd.py
```

### Pip
```
git clone https://github.com/mariovata/AutoShellDown.git && cd AutoShellDown && pip3 install -r requirements.txt && chmod +x asd.py
```


## Using venv (recommended)

1. `sudo apt install python3.11-venv`   (if you don't have venv installed)
2. `python3 -m venv asd-env`            - Creates a virtual environment with the name `asd-env`
3. `source asd-env/bin/activate`        - Activates the virtual environment
4. `pip3 install -r requirements.txt`   - Installs the required packages (in the virtual environment)
5. `chmod +x asd.py`                    - Makes the script executable
6. `python3 asd.py -h`                  - Runs the script (in the virtual environment)

### Deactivating venv
`deactivate`                         - Deactivates the virtual environment

## Using pip

1. `pip3 install -r requirements.txt` - Installs the required packages
2. `chmod +x asd.py`                  - Makes the script executable
3. `python3 asd.py -h`                - Runs the script


# Features:

* Automatically sets up a server to host files
* Automatically uploads and runs linpeas.sh (or other scripts)
* Automatically sets up an FTP server to exfiltrate files
