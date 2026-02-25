# Deploying Speed Test PWA on Oracle Cloud Free Tier

A complete guide to hosting your app on a free cloud VM.

---

## Part 1: Create Oracle Cloud Account

### Step 1: Sign Up

1. Go to: https://www.oracle.com/cloud/free/
2. Click **"Start for free"**
3. Fill in your details:
   - Use your real name and address (they verify it)
   - You'll need a credit card for verification (you WON'T be charged)
   - Select your **Home Region** (pick one closest to you - this cannot be changed later)

4. Wait for account approval (usually instant, sometimes a few hours)

### Step 2: Access Cloud Console

1. Go to: https://cloud.oracle.com/
2. Enter your **Cloud Account Name** (from signup email)
3. Sign in with your credentials

---

## Part 2: Create a Virtual Machine

### Step 1: Navigate to Compute

1. In the Oracle Cloud Console, click the **hamburger menu** (☰) top-left
2. Go to: **Compute** → **Instances**
3. Click **"Create instance"**

### Step 2: Configure the Instance

**Name:** `speedtest-server` (or whatever you like)

**Placement:** Leave default

**Image and shape:**
1. Click **"Edit"** in the Image and shape section
2. For **Image**: Keep "Oracle Linux" OR click **"Change image"** and select **"Canonical Ubuntu"** → **"22.04 Minimal"** (Ubuntu is easier for beginners)
3. For **Shape**: Click **"Change shape"**
   - Select **"Ampere"** (ARM processor)
   - Choose **"VM.Standard.A1.Flex"**
   - Set **OCPUs: 2** and **Memory: 12 GB** (free tier allows up to 4 OCPU / 24GB total)

**Networking:**
- Keep defaults (new VCN will be created)
- Make sure **"Assign a public IPv4 address"** is selected

**SSH Keys (IMPORTANT):**
1. Select **"Generate a key pair for me"**
2. Click **"Save private key"** - download this file!
3. Also click **"Save public key"** for backup
4. **SAVE THESE FILES SECURELY** - you cannot download them again!

### Step 3: Create the Instance

1. Click **"Create"**
2. Wait for the instance to show **"RUNNING"** (takes 1-2 minutes)
3. Note down the **Public IP address** shown on the instance details page

---

## Part 3: Configure Firewall Rules

Oracle Cloud blocks most ports by default. We need to open ports 80 (HTTP) and 443 (HTTPS).

### Step 1: Find Your VCN

1. On your instance details page, under **"Primary VNIC"**, click the **Subnet** link
2. Click on the **Security Lists** link (usually named "Default Security List for...")

### Step 2: Add Ingress Rules

1. Click **"Add Ingress Rules"**

2. Add rule for HTTP:
   - Source CIDR: `0.0.0.0/0`
   - Destination Port Range: `80`
   - Description: `HTTP`
   - Click **"Add Ingress Rules"**

3. Click **"Add Ingress Rules"** again for HTTPS:
   - Source CIDR: `0.0.0.0/0`
   - Destination Port Range: `443`
   - Description: `HTTPS`
   - Click **"Add Ingress Rules"**

---

## Part 4: Connect to Your VM

### On Windows (using PowerShell or Command Prompt)

1. Open PowerShell
2. Navigate to where you saved your private key:
   ```
   cd Downloads
   ```

3. Connect via SSH:
   ```
   ssh -i ssh-key-*.key ubuntu@YOUR_PUBLIC_IP
   ```
   Replace `YOUR_PUBLIC_IP` with your instance's IP address.

   If using Oracle Linux instead of Ubuntu, use `opc` instead of `ubuntu`:
   ```
   ssh -i ssh-key-*.key opc@YOUR_PUBLIC_IP
   ```

4. If asked about fingerprint, type `yes`

### Alternative: Use PuTTY (Windows)

1. Download PuTTY: https://www.putty.org/
2. You'll need to convert the key to PuTTY format using PuTTYgen:
   - Open PuTTYgen
   - Click "Load" and select your .key file
   - Click "Save private key" to save as .ppk
3. In PuTTY:
   - Host Name: `ubuntu@YOUR_PUBLIC_IP`
   - Go to Connection → SSH → Auth → Credentials
   - Browse for your .ppk file
   - Click "Open"

---

## Part 5: Set Up the Server

Once connected via SSH, run these commands:

### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Required Software

```bash
# Install Python, pip, nginx, and certbot
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx git
```

### Step 3: Configure Ubuntu Firewall

```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

### Step 4: Clone Your Project

Option A - If your code is on GitHub:
```bash
cd ~
git clone https://github.com/YOUR_USERNAME/speedtest-pwa.git
cd speedtest-pwa
```

Option B - Create files manually:
```bash
mkdir -p ~/speedtest-pwa/static
cd ~/speedtest-pwa
nano app.py
# Paste your app.py content, then Ctrl+X, Y, Enter to save
# Repeat for other files
```

Option C - Copy from your PC using SCP:
```bash
# Run this from your Windows machine, not the VM:
scp -i ssh-key-*.key -r d:\projects\python\speedtest-pwa ubuntu@YOUR_PUBLIC_IP:~/
```

### Step 5: Set Up Python Environment

```bash
cd ~/speedtest-pwa
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 6: Test the App

```bash
source venv/bin/activate
uvicorn app:app --host 127.0.0.1 --port 8000
```

Open another SSH session and test:
```bash
curl http://localhost:8000
```

You should see HTML. Press `Ctrl+C` to stop.

---

## Part 6: Set Up Nginx Reverse Proxy

### Step 1: Create Nginx Config

```bash
sudo nano /etc/nginx/sites-available/speedtest
```

Paste this content (replace `YOUR_DOMAIN` with your domain, or use your IP for now):

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### Step 2: Enable the Site

```bash
sudo ln -s /etc/nginx/sites-available/speedtest /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## Part 7: Create a Systemd Service

This keeps your app running even after you disconnect.

### Step 1: Create Service File

```bash
sudo nano /etc/systemd/system/speedtest.service
```

Paste this (update paths if needed):

```ini
[Unit]
Description=Speed Test PWA
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/speedtest-pwa
Environment="PATH=/home/ubuntu/speedtest-pwa/venv/bin"
ExecStart=/home/ubuntu/speedtest-pwa/venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Save with `Ctrl+X`, then `Y`, then `Enter`.

### Step 2: Enable and Start Service

```bash
sudo systemctl daemon-reload
sudo systemctl enable speedtest
sudo systemctl start speedtest
```

### Step 3: Check Status

```bash
sudo systemctl status speedtest
```

You should see "active (running)".

---

## Part 8: Test Your App

Open a browser and go to:
```
http://YOUR_PUBLIC_IP
```

You should see your Speed Test app!

---

## Part 9: Add a Free Domain (Optional)

### Option A: Free Subdomain with DuckDNS

1. Go to: https://www.duckdns.org/
2. Sign in with Google/GitHub/etc.
3. Create a subdomain (e.g., `myspeedtest.duckdns.org`)
4. Set the IP to your Oracle Cloud VM's public IP
5. Update your Nginx config with the domain

### Option B: Free Domain with Freenom (if available)

1. Go to: https://www.freenom.com/
2. Search for a free domain (.tk, .ml, .ga, .cf, .gq)
3. Point it to your VM's IP

### Option C: Buy a Cheap Domain

- Namecheap, Porkbun, Cloudflare: ~$8-10/year for a .com

---

## Part 10: Add HTTPS with Let's Encrypt (Requires Domain)

Once you have a domain pointing to your server:

```bash
sudo certbot --nginx -d yourdomain.com
```

Follow the prompts:
- Enter your email
- Agree to terms
- Choose to redirect HTTP to HTTPS (recommended)

Certbot auto-renews certificates. Test renewal with:
```bash
sudo certbot renew --dry-run
```

---

## Useful Commands

### Managing Your App

```bash
# Check app status
sudo systemctl status speedtest

# Restart app
sudo systemctl restart speedtest

# View logs
sudo journalctl -u speedtest -f

# Stop app
sudo systemctl stop speedtest
```

### Updating Your App

```bash
cd ~/speedtest-pwa
git pull  # if using git
sudo systemctl restart speedtest
```

### Server Maintenance

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Check disk space
df -h

# Check memory
free -h

# Check running processes
htop
```

---

## Troubleshooting

### "Connection refused" or site not loading

1. Check if app is running: `sudo systemctl status speedtest`
2. Check Nginx: `sudo systemctl status nginx`
3. Check firewall: `sudo iptables -L -n`
4. Check Oracle Cloud security list has ports 80/443 open

### "502 Bad Gateway"

- App crashed. Check logs: `sudo journalctl -u speedtest -n 50`
- Restart: `sudo systemctl restart speedtest`

### SSH connection timeout

- Check Oracle Cloud security list has port 22 open
- Verify you're using the correct username (ubuntu or opc)

### Can't install packages (ARM architecture issues)

Some Python packages don't have ARM wheels. If you hit issues:
```bash
sudo apt install -y build-essential python3-dev
pip install --no-binary :all: package_name
```

---

## Cost Summary

| Resource | Cost |
|----------|------|
| Oracle Cloud VM | FREE forever |
| DuckDNS domain | FREE |
| Let's Encrypt SSL | FREE |
| **Total** | **$0/month** |

---

## Next Steps

Once your app is running, you could:
- Add a database to store speed test history
- Create user accounts
- Add graphs/charts of speed over time
- Set up automated speed tests
- Add notifications when speed drops

Enjoy your self-hosted app!
