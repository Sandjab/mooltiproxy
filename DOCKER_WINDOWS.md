# Docker Installation and Deployment Guide for Windows 11

This guide provides step-by-step instructions for installing Docker on Windows 11 and deploying Mooltiproxy.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Install WSL2](#install-wsl2)
3. [Install Docker Desktop](#install-docker-desktop)
4. [Verify Installation](#verify-installation)
5. [Clone and Setup Mooltiproxy](#clone-and-setup-mooltiproxy)
6. [Build the Docker Image](#build-the-docker-image)
7. [Deploy with Docker Compose](#deploy-with-docker-compose)
8. [Deploy with Docker Run](#deploy-with-docker-run)
9. [Managing the Container](#managing-the-container)
10. [Troubleshooting](#troubleshooting)
11. [Tips for Windows Users](#tips-for-windows-users)

---

## Prerequisites

Before starting, ensure you have:

- **Windows 11** (64-bit, version 21H2 or later)
- **Administrator access** on your computer
- At least **4 GB of RAM** (8 GB recommended)
- **Virtualization enabled** in BIOS (usually enabled by default)
- **Internet connection** for downloads

### Check Windows Version

1. Press `Win + R`
2. Type `winver` and press Enter
3. Verify you have Windows 11 version 21H2 or later

### Check if Virtualization is Enabled

1. Press `Ctrl + Shift + Esc` to open Task Manager
2. Click on the **Performance** tab
3. Select **CPU**
4. Look for **Virtualization: Enabled**

If virtualization is disabled, you'll need to enable it in your BIOS settings.

---

## Install WSL2

Docker Desktop for Windows requires WSL2 (Windows Subsystem for Linux 2).

### Step 1: Enable WSL

Open **PowerShell** as Administrator:

1. Press `Win + X`
2. Select **Windows PowerShell (Admin)** or **Terminal (Admin)**
3. Run the following command:

```powershell
wsl --install
```

This command will:
- Enable the Windows Subsystem for Linux feature
- Enable the Virtual Machine Platform feature
- Download and install the latest Linux kernel
- Set WSL2 as the default version
- Install Ubuntu (default Linux distribution)

### Step 2: Restart Your Computer

After the installation completes, restart your computer:

```powershell
Restart-Computer
```

### Step 3: Set Up Ubuntu

After restart, Ubuntu will automatically launch:

1. Wait for installation to complete
2. Create a **username** (lowercase, no spaces)
3. Create a **password** (you won't see characters as you type)
4. Confirm your password

Example:
```
Enter new UNIX username: mooltiuser
New password: ********
Retype new password: ********
```

### Step 4: Update WSL2

Open PowerShell as Administrator and run:

```powershell
wsl --update
```

### Step 5: Verify WSL2 Installation

Check your WSL version:

```powershell
wsl --list --verbose
```

You should see something like:
```
  NAME      STATE           VERSION
* Ubuntu    Running         2
```

The VERSION should be **2**.

---

## Install Docker Desktop

### Step 1: Download Docker Desktop

1. Go to [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Click **Download for Windows**
3. Wait for `Docker Desktop Installer.exe` to download

**Direct link:** https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe

### Step 2: Run the Installer

1. Double-click `Docker Desktop Installer.exe`
2. If prompted by User Account Control, click **Yes**
3. In the Configuration window:
   - ✅ **Use WSL 2 instead of Hyper-V** (should be checked by default)
   - ✅ **Add shortcut to desktop** (optional)
4. Click **OK**
5. Wait for installation to complete (this may take several minutes)
6. Click **Close and restart** when prompted

### Step 3: First Launch

After restart:

1. Docker Desktop will launch automatically
2. Accept the **Docker Subscription Service Agreement**
3. You may be asked to sign in (you can skip this for now)
4. Wait for Docker Engine to start (you'll see "Docker Desktop is running" in the system tray)

### Step 4: Configure Docker Desktop

1. Click the Docker icon in the system tray (bottom-right)
2. Select **Settings** (gear icon)
3. Go to **General**:
   - ✅ **Use the WSL 2 based engine** (should be checked)
   - ✅ **Start Docker Desktop when you log in** (recommended)
4. Go to **Resources → WSL Integration**:
   - ✅ **Enable integration with my default WSL distro**
   - ✅ **Ubuntu** (or your WSL distro)
5. Click **Apply & Restart**

---

## Verify Installation

### Open PowerShell or Windows Terminal

Press `Win + X` and select **Windows PowerShell** or **Terminal**.

### Check Docker Version

```powershell
docker --version
```

Expected output:
```
Docker version 24.x.x, build xxxxxxx
```

### Check Docker Compose Version

```powershell
docker compose version
```

Expected output:
```
Docker Compose version v2.x.x
```

### Run Test Container

```powershell
docker run hello-world
```

If successful, you'll see:
```
Hello from Docker!
This message shows that your installation appears to be working correctly.
...
```

---

## Clone and Setup Mooltiproxy

### Step 1: Install Git (if not already installed)

Download and install Git from: https://git-scm.com/download/win

Or install via PowerShell (if you have winget):

```powershell
winget install --id Git.Git -e --source winget
```

### Step 2: Choose a Working Directory

Open PowerShell and navigate to where you want to store the project:

```powershell
# Option 1: Use your Documents folder
cd $HOME\Documents

# Option 2: Create a Projects folder
mkdir $HOME\Projects
cd $HOME\Projects
```

### Step 3: Clone the Repository

```powershell
git clone https://github.com/Sandjab/mooltiproxy.git
cd mooltiproxy
```

### Step 4: Create Configuration File

```powershell
# Copy the template
copy config_template.yaml config.yaml

# Open in Notepad
notepad config.yaml
```

Edit `config.yaml` with your settings. Minimal example:

```yaml
system:
  ssl: false
  debug: true
  port: 8000
  timeout: 30

cerbere:
  max_tries: 5
  whitelist: []
  blacklist: []

targets:
  default: openai

  openai:
    url: https://api.openai.com/v1
    envkey: YOUR_OPENAI_API_KEY
    mapping:
      /:
      /models:
      /completions:
      /chat/completions:
```

Save and close the file.

### Step 5: Create Environment Variables File

```powershell
# Copy the example
copy .env.example .env

# Open in Notepad
notepad .env
```

Edit `.env` with your keys:

```bash
# Required: Master proxy key
MOOLTIPROXY_KEY=your_secure_master_key_here

# Optional: Port (default is 8000)
PROXY_PORT=8000

# Optional: Your API keys
YOUR_OPENAI_API_KEY=sk-your-openai-key-here
```

**Generate a secure key** using PowerShell:

```powershell
# Generate a random 32-character base64 key
[Convert]::ToBase64String((1..24 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

Copy the output and paste it as your `MOOLTIPROXY_KEY`.

Save and close the file.

---

## Build the Docker Image

### Method 1: Using Docker Compose (Recommended)

Docker Compose will automatically build the image when you first run it:

```powershell
docker compose build
```

Expected output:
```
[+] Building 45.2s (12/12) FINISHED
 => [internal] load build definition from Dockerfile
 => => transferring dockerfile: 1.23kB
 => [internal] load .dockerignore
 ...
 => => naming to docker.io/library/mooltiproxy:latest
```

### Method 2: Manual Build

Build the image manually with a specific tag:

```powershell
# Build with 'latest' tag
docker build -t mooltiproxy:latest .

# Build with version tag
docker build -t mooltiproxy:1.0.0 .

# Build without using cache (clean build)
docker build --no-cache -t mooltiproxy:latest .
```

### Verify the Image

Check that the image was created:

```powershell
docker images
```

You should see:
```
REPOSITORY      TAG       IMAGE ID       CREATED          SIZE
mooltiproxy     latest    abc123def456   2 minutes ago    200MB
```

---

## Deploy with Docker Compose

### Start the Container

```powershell
# Start in detached mode (background)
docker compose up -d
```

Expected output:
```
[+] Running 2/2
 ✔ Network mooltiproxy_mooltiproxy-network  Created
 ✔ Container mooltiproxy                    Started
```

### View Logs

```powershell
# View all logs
docker compose logs

# Follow logs in real-time
docker compose logs -f

# View last 50 lines
docker compose logs --tail=50
```

### Check Status

```powershell
docker compose ps
```

Expected output:
```
NAME          IMAGE               STATUS         PORTS
mooltiproxy   mooltiproxy:latest  Up 2 minutes   0.0.0.0:8000->8000/tcp
```

### Test the Deployment

Open a new PowerShell window and test:

```powershell
# Basic test (should return 404 with proper headers)
curl http://localhost:8000/

# Test with authentication
$headers = @{
    "Authorization" = "Bearer your_secure_master_key_here"
}
Invoke-RestMethod -Uri http://localhost:8000/ -Headers $headers
```

Or test in your web browser:
- Open: http://localhost:8000/

---

## Deploy with Docker Run

If you prefer to use `docker run` instead of Docker Compose:

### Basic Deployment

```powershell
docker run -d `
  --name mooltiproxy `
  -p 8000:8000 `
  -e MOOLTIPROXY_KEY="your_secure_master_key_here" `
  -v ${PWD}/config.yaml:/app/config.yaml:ro `
  --restart unless-stopped `
  mooltiproxy:latest
```

**Note:** In PowerShell, use backticks (`` ` ``) for line continuation.

### With All Options

```powershell
docker run -d `
  --name mooltiproxy `
  --restart unless-stopped `
  -p 8000:8000 `
  -e MOOLTIPROXY_KEY="your_secure_master_key_here" `
  -e YOUR_OPENAI_API_KEY="sk-..." `
  -v ${PWD}/config.yaml:/app/config.yaml:ro `
  --health-cmd="curl -f http://localhost:8000/ || exit 1" `
  --health-interval=30s `
  --health-timeout=5s `
  --health-retries=3 `
  mooltiproxy:latest
```

### View Container Logs

```powershell
# View all logs
docker logs mooltiproxy

# Follow logs in real-time
docker logs -f mooltiproxy

# View last 50 lines
docker logs --tail 50 mooltiproxy
```

---

## Managing the Container

### Stop the Container

Using Docker Compose:
```powershell
docker compose stop
```

Using Docker:
```powershell
docker stop mooltiproxy
```

### Start the Container

Using Docker Compose:
```powershell
docker compose start
```

Using Docker:
```powershell
docker start mooltiproxy
```

### Restart the Container

Using Docker Compose:
```powershell
docker compose restart
```

Using Docker:
```powershell
docker restart mooltiproxy
```

### Stop and Remove Everything

Using Docker Compose:
```powershell
# Stop and remove containers
docker compose down

# Stop, remove containers, and remove volumes
docker compose down -v
```

Using Docker:
```powershell
docker stop mooltiproxy
docker rm mooltiproxy
```

### Update the Container

When you make changes to the code:

```powershell
# Rebuild the image
docker compose build

# Stop and remove old container, start new one
docker compose up -d
```

Or in one command:
```powershell
docker compose up -d --build
```

---

## Troubleshooting

### Issue: "Docker is not running"

**Solution:**
1. Open Docker Desktop from Start Menu
2. Wait for Docker Engine to start
3. Look for "Docker Desktop is running" in system tray

### Issue: "WSL 2 installation is incomplete"

**Solution:**
```powershell
# Update WSL
wsl --update

# Restart Docker Desktop
```

### Issue: "Error response from daemon: open \\.\pipe\docker_engine"

**Solution:**
1. Restart Docker Desktop
2. If that doesn't work, restart your computer
3. Ensure Docker Desktop is set to start on login

### Issue: "Cannot connect to the Docker daemon"

**Solution:**
1. Check if Docker Desktop is running
2. Open Docker Desktop manually
3. Check the Docker icon in system tray

### Issue: "Port 8000 is already allocated"

**Solution:**

Check what's using port 8000:
```powershell
netstat -ano | findstr :8000
```

Either:
- Stop the other application using port 8000, or
- Change the port in `.env`:
  ```
  PROXY_PORT=8001
  ```

### Issue: "No such file or directory: config.yaml"

**Solution:**

Verify your current directory:
```powershell
# Check current directory
pwd

# Should be in the mooltiproxy folder
# List files to confirm config.yaml exists
dir
```

If not in the right directory:
```powershell
cd path\to\mooltiproxy
```

### Issue: "Permission denied" when mounting volumes

**Solution:**

In Docker Desktop settings:
1. Go to **Settings → Resources → File Sharing**
2. Add the drive or folder where mooltiproxy is located
3. Click **Apply & Restart**

### Issue: Container starts but immediately stops

**Solution:**

Check the logs:
```powershell
docker compose logs
```

Common causes:
- Missing `MOOLTIPROXY_KEY` environment variable
- Invalid `config.yaml` syntax
- Port already in use

### Issue: "docker: command not found" in PowerShell

**Solution:**

1. Restart PowerShell
2. Ensure Docker Desktop is running
3. Try reopening PowerShell as Administrator
4. Reinstall Docker Desktop if the issue persists

---

## Tips for Windows Users

### Using Windows Terminal

Windows Terminal provides a better experience than PowerShell:

1. Install from Microsoft Store: [Windows Terminal](https://aka.ms/terminal)
2. Open Windows Terminal
3. All commands work the same

### File Paths

In PowerShell, you can use:
- Forward slashes: `/path/to/file`
- Backslashes: `\path\to\file`
- PowerShell variables: `${PWD}` (current directory)

### Viewing Logs in Real-Time

Use Docker Desktop GUI:
1. Click Docker icon in system tray
2. Click **Dashboard**
3. Click on **mooltiproxy** container
4. View logs in the GUI

### Accessing the Container Shell

If you need to access the container's shell:

```powershell
# Using Docker Compose
docker compose exec mooltiproxy /bin/bash

# Using Docker
docker exec -it mooltiproxy /bin/bash
```

Inside the container:
```bash
# Check files
ls -la

# View config
cat config.yaml

# Exit
exit
```

### Using WSL2 (Advanced)

For a more Linux-like experience:

1. Open **Ubuntu** from Start Menu
2. Navigate to your project:
   ```bash
   cd /mnt/c/Users/YourUsername/Documents/mooltiproxy
   ```
3. Run Docker commands as on Linux:
   ```bash
   docker compose up -d
   ```

### Checking Resource Usage

Monitor Docker resource usage:

```powershell
# Check all containers
docker stats

# Check specific container
docker stats mooltiproxy
```

Or use Docker Desktop:
1. Open Docker Desktop
2. Click **Dashboard**
3. View CPU and Memory usage

### Automatic Startup

To make mooltiproxy start automatically:

1. Ensure Docker Desktop is set to start on login
2. Use `restart: unless-stopped` in docker-compose.yml (already configured)
3. The container will auto-start when Docker Desktop starts

### Updating Windows

After Windows updates, you may need to:

1. Restart Docker Desktop
2. Update WSL: `wsl --update`
3. Restart the container: `docker compose restart`

---

## Quick Reference

### Common Commands

| Task | Command |
|------|---------|
| Start container | `docker compose up -d` |
| Stop container | `docker compose stop` |
| View logs | `docker compose logs -f` |
| Restart container | `docker compose restart` |
| Rebuild image | `docker compose build` |
| Remove everything | `docker compose down` |
| Check status | `docker compose ps` |
| Access shell | `docker compose exec mooltiproxy /bin/bash` |

### Useful PowerShell Commands

| Task | Command |
|------|---------|
| Check Docker version | `docker --version` |
| List images | `docker images` |
| List containers | `docker ps -a` |
| Remove unused images | `docker image prune` |
| Remove unused containers | `docker container prune` |
| View disk usage | `docker system df` |
| Clean everything | `docker system prune -a` |

### URLs

- Docker Desktop: http://localhost:8000/ (after deployment)
- Docker Dashboard: Click Docker icon in system tray
- Container logs: Docker Desktop → Dashboard → mooltiproxy

---

## Next Steps

After successful deployment:

1. **Read the main documentation:**
   - [DOCKER.md](DOCKER.md) - Complete Docker guide
   - [README.md](README.md) - Project overview
   - [ARCHITECTURE.md](ARCHITECTURE.md) - How it works

2. **Test the proxy:**
   - Use curl or Postman to test endpoints
   - See [README.md](README.md) for usage examples

3. **Configure targets:**
   - Edit `config.yaml` to add your API endpoints
   - Restart container: `docker compose restart`

4. **Monitor:**
   - Check logs regularly: `docker compose logs -f`
   - Monitor resource usage in Docker Desktop

5. **Secure your deployment:**
   - Use strong random keys
   - Never commit `.env` to version control
   - Consider using HTTPS (see config.yaml)

---

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Read [DOCKER.md](DOCKER.md) for more details
3. Check Docker Desktop logs
4. Open an issue on [GitHub](https://github.com/Sandjab/mooltiproxy/issues)

---

**Last Updated:** 2025-11-22
**Tested on:** Windows 11 22H2
**Docker Desktop:** 4.25+
**WSL2:** 2.0+

---

## Summary Checklist

- [ ] Windows 11 installed and updated
- [ ] Virtualization enabled in BIOS
- [ ] WSL2 installed and updated
- [ ] Docker Desktop installed and running
- [ ] Git installed
- [ ] Repository cloned
- [ ] `config.yaml` created and configured
- [ ] `.env` created with secure keys
- [ ] Docker image built successfully
- [ ] Container deployed and running
- [ ] Tested endpoints responding
- [ ] Logs showing no errors

**Congratulations!** You've successfully deployed Mooltiproxy on Windows 11! 🎉
