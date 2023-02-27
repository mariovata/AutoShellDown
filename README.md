# AutoShellDown

AutoShellDown is my attempt at making an automated reverse shell that automates some basic boring stuff like: 

* Setting up a server to host files 

* Uploading and running linpeas.sh

I made this so to speed up enumeration during privilege escalation on HackTheBox machines. This is very much a work in progress and I currently don't recommend using the experimental version of this script.

# Installation

## One-liner

### Venv (recommended, needs python3.11-venv) 
```
git clone https://github.com/mariovata/AutoShellDown.git && cd AutoShellDown && python3 -m venv asd-env && source asd-env/bin/activate && pip3 install -r requirements.txt && chmod +x asd.py && python3 asd.py -d 1337
```

### Pip
```
git clone https://github.com/mariovata/AutoShellDown.git && cd AutoShellDown && pip3 install -r requirements.txt && chmod +x asd.py && python3 asd.py -d 1337
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
