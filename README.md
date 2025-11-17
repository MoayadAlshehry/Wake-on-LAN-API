# Wake-on-LAN API

Control and power on your remote computer securely from anywhere using a Raspberry Pi (or any Linux server), Tailscale, and a simple web API.

This guide provides all the scripts and configuration files needed to create a lightweight, secure API endpoint. When you call this endpoint (e.g., from an iPhone Shortcut), it triggers a Wake-on-LAN (WOL) command on your local network, waking up your target computer.

## How It Works

The flow is simple and secure:

`iPhone Shortcut` → `Tailscale (Secure Tunnel)` → `Raspberry Pi (Linux Server)` → `Flask API` → `wol.sh Script` → `computer Wakes Up`

## Requirements

Before you begin, ensure you have the following:

* **Linux Server:** A Raspberry Pi or any Linux device that can run 24/7.
* **Target PC:** A computer that supports Wake-on-LAN (WOL) and has it enabled.
    * Enable WOL in BIOS/UEFI
    * Enable WOL in Windows
    * Find Your MAC Address
* **Tailscale:** Installed on your Linux server and your client device (e.g., your iPhone). This is how you'll access the API securely from outside your home.
    * [**Tailscale Official Documentation**](https://tailscale.com/kb/)
    * [Getting Started with Tailscale](https://www.youtube.com/watch?v=sPdvyR7bLqI)
      This video provides a great 10-minute overview of how to get started with Tailscale


## Setup Instructions

### Step 1: Install Dependencies
Install Tailscale (Optional)
This command will install Tailscale on your Linux server. This is only needed if you want to access your API from outside your home network.

```bash
curl -s https://tailscale.com/install.sh | sudo sh
```

First, install `wakeonlan` (the utility that sends the magic packet) and `python3-flask` (our web server).

```bash
sudo apt update
sudo apt install wakeonlan python3-flask -y
````

### Step 2: Create the WOL Script

This simple script will execute the `wakeonlan` command.

1.  Create the project folder:

    ```bash
    sudo mkdir -p /opt/wol
    ```

2.  Create the script file:

    ```bash
    sudo nano /opt/wol/wol.sh
    ```

3.  Add the following lines. **Replace `XX:XX:XX:XX:XX:XX` with your target computer's MAC address.**

    ```bash
    #!/bin/bash
    wakeonlan XX:XX:XX:XX:XX:XX
    ```

4.  Make the script executable:

    ```bash
    sudo chmod +x /opt/wol/wol.sh
    ```

### Step 3: Create the Flask API

This Python script creates a simple web server that runs your `wol.sh` script when you visit the `/wol` URL.

1.  Create the server file:

    ```bash
    sudo nano /opt/wol/server.py
    ```

2.  Paste in the following code:

    ```python
    from flask import Flask
    import os

    # Note: It's __name__ (two underscores on each side)
    app = Flask(__name__)

    @app.route('/wol')
    def wol():
        # Executes your shell script
        os.system("/opt/wol/wol.sh")
        return "WOL Packet Sent\n"

    if __name__ == '__main__':
        # Listens on all network interfaces
        app.run(host='0.0.0.0', port=5000)
    ```

### Step 4: Manual Test (Recommended)

Before creating the service, let's test it manually.

1.  Run the server from your terminal:

    ```bash
    sudo python3 /opt/wol/server.py
    ```

2.  From another device (like your phone or PC), open a browser and go to:
    `http://<YOUR-SERVER-IP>:5000/wol`

    > **Note:** Use your server's **Tailscale IP** to test it from outside your network, or its **local IP** (e.g., `192.168.1.10`) to test it from inside.

    Your target computer should power on\! If it works, press `Ctrl+C` in the terminal to stop the server.

### Step 5: Run the API as a Service (systemd)

To make the API run automatically on boot, we'll create a `systemd` service.

1.  Create the service file:

    ```bash
    sudo nano /etc/systemd/system/wol-api.service
    ```

2.  Paste in the following configuration:

    ```ini
    [Unit]
    Description=Wake-on-LAN API
    After=network.target

    [Service]
    User=root
    WorkingDirectory=/opt/wol
    ExecStart=/usr/bin/python3 server.py
    Restart=always
    User=root

    [Install]
    WantedBy=multi-user.target
    ```

3.  Reload `systemd`, enable, and start the new service:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable wol-api
    sudo systemctl restart wol-api
    ```

### Step 6: Verify the Service

Let's check that everything is running correctly.

1.  Check the service status:

    ```bash
    sudo systemctl status wol-api
    ```

    You should see `Active: active (running)` in green.

2.  Check that the port is open and listening:

    ```bash
    sudo netstat -tulpn | grep 5000
    ```

    You should see an output like:
    `tcp    0    0 0.0.0.0:5000    0.0.0.0:* LISTEN    .../python3`

-----

## Usage: Add to iPhone Shortcuts

The easiest way to use your new API is with a one-tap button on your phone's home screen.

1.  Open the **Shortcuts** app on your iPhone.
2.  Tap the **+** icon to create a new Shortcut.
3.  Tap **Add Action** and search for **URL**.
4.  In the URL field, type your API address:

    `http://<YOUR-LOCLE-SERVER-IP>:5000/wol`
    or
    `http://<YOUR-TAILSCALE-SERVER-IP>:5000/wol`
    
5.  Tap **Add Action** again and search for **Get Contents of URL**.
6.  (Optional) Rename the shortcut to something clear, like "Wake PC".
7.  (Optional)**Add to Home Screen** to create a one-tap button.

<!-- end list -->
