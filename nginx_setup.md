# Nginx and SSL Setup for Media Management

## Step 1: SSH to Raspberry Pi and Install Application

```bash
ssh pmadmin@10.252.0.66

# Extract the deployment package
cd ~
tar -xzf media_management_deploy.tar.gz -C /tmp/media_management_extract
cd /tmp/media_management_extract

# Run the installation script
sudo bash setup.sh

# Verify service is running
sudo systemctl status media-management
```

---

## Step 2: Install Nginx

```bash
sudo apt update
sudo apt install -y nginx
```

---

## Step 3: Create Nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/media-management
```

Paste the following configuration:

```nginx
# HTTP server - Redirect to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name media.tamsilcms.com;

    # Allow Certbot to validate domain
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    # Redirect all other traffic to HTTPS
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server - Main application
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name media.tamsilcms.com;

    # SSL certificate paths (will be created by Certbot)
    ssl_certificate /etc/letsencrypt/live/media.tamsilcms.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/media.tamsilcms.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/media.tamsilcms.com/chain.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/media-management-access.log;
    error_log /var/log/nginx/media-management-error.log;

    # Max upload size (for potential file uploads)
    client_max_body_size 100M;

    # Proxy to Flask application
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;

        # WebSocket support (if needed in future)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 600;
        proxy_send_timeout 600;
        proxy_read_timeout 600;
        send_timeout 600;
    }

    # Static files (served directly by Nginx for better performance)
    location /static {
        alias /var/www/media_manager/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

Save and exit (Ctrl+X, Y, Enter)

---

## Step 4: Create Certbot Directory

```bash
sudo mkdir -p /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot
```

---

## Step 5: Enable the Site (Without SSL First)

Create a temporary HTTP-only config for initial Certbot validation:

```bash
sudo nano /etc/nginx/sites-available/media-management-temp
```

Paste this temporary configuration:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name media.tamsilcms.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the temporary config:

```bash
# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Enable temporary config
sudo ln -s /etc/nginx/sites-available/media-management-temp /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## Step 6: Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

---

## Step 7: Obtain SSL Certificate

**IMPORTANT**: Make sure DNS for `media.tamsilcms.com` points to `10.252.0.66` before running this!

```bash
sudo certbot certonly --webroot \
  -w /var/www/certbot \
  -d media.tamsilcms.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email
```

Replace `your-email@example.com` with your actual email address.

---

## Step 8: Enable Full HTTPS Configuration

```bash
# Remove temporary config
sudo rm /etc/nginx/sites-enabled/media-management-temp

# Enable full HTTPS config
sudo ln -s /etc/nginx/sites-available/media-management /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## Step 9: Set Up Auto-Renewal

Certbot automatically installs a systemd timer. Verify it:

```bash
# Check if timer is active
sudo systemctl status certbot.timer

# Test renewal (dry run)
sudo certbot renew --dry-run
```

---

## Step 10: Update Flask to Bind to Localhost Only

For security, update the service to only listen on localhost since Nginx is handling external traffic:

```bash
sudo nano /etc/systemd/system/media-management.service
```

Verify the ExecStart line uses `127.0.0.1:5000`:

```ini
ExecStart=/var/www/media_manager/venv/bin/gunicorn \
    --workers 2 \
    --threads 4 \
    --bind 127.0.0.1:5000 \
    --timeout 300 \
    ...
```

Reload and restart if changed:

```bash
sudo systemctl daemon-reload
sudo systemctl restart media-management
```

---

## Step 11: Configure Firewall

```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'

# Remove direct Flask port access (no longer needed)
sudo ufw delete allow 5000/tcp

# Enable firewall if not already
sudo ufw enable

# Check status
sudo ufw status
```

---

## Verification Steps

### 1. Check Service Status
```bash
sudo systemctl status media-management
sudo systemctl status nginx
```

### 2. Check SSL Certificate
```bash
sudo certbot certificates
```

### 3. Test Application
- Open browser: `https://media.tamsilcms.com`
- Verify SSL certificate is valid
- Test login and functionality

### 4. Check Logs
```bash
# Application logs
media-mgmt app-logs

# Nginx logs
sudo tail -f /var/log/nginx/media-management-access.log
sudo tail -f /var/log/nginx/media-management-error.log

# SSL renewal logs
sudo journalctl -u certbot.timer
```

---

## Troubleshooting

### SSL Certificate Fails to Install

**Check DNS:**
```bash
nslookup media.tamsilcms.com
```
Should return `10.252.0.66`

**Check port 80 is accessible externally:**
```bash
sudo netstat -tlnp | grep :80
```

**Check Certbot logs:**
```bash
sudo tail -f /var/log/letsencrypt/letsencrypt.log
```

### Nginx Won't Start After SSL Config

```bash
# Check configuration
sudo nginx -t

# Check if certificates exist
ls -la /etc/letsencrypt/live/media.tamsilcms.com/

# If certificates don't exist, go back to temporary config
sudo rm /etc/nginx/sites-enabled/media-management
sudo ln -s /etc/nginx/sites-available/media-management-temp /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

### Application Not Accessible

```bash
# Check if service is running
media-mgmt status

# Check Nginx is proxying correctly
curl -I http://localhost:5000
curl -I http://localhost

# Check Nginx error logs
sudo tail -f /var/log/nginx/media-management-error.log
```

---

## Certificate Renewal

Certbot will automatically renew certificates. To manually renew:

```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## Maintenance Commands

```bash
# Restart everything
sudo systemctl restart media-management
sudo systemctl restart nginx

# Reload Nginx config (no downtime)
sudo systemctl reload nginx

# View certificate info
sudo certbot certificates

# Revoke certificate (if needed)
sudo certbot revoke --cert-name media.tamsilcms.com

# Delete certificate (if needed)
sudo certbot delete --cert-name media.tamsilcms.com
```

---

## Summary

After following these steps, you'll have:

✅ Media Management app running as a systemd service
✅ Nginx reverse proxy handling external traffic
✅ Valid SSL certificate from Let's Encrypt
✅ Automatic certificate renewal
✅ Secure HTTPS-only access
✅ Application accessible at: `https://media.tamsilcms.com`

**Default credentials** (if not changed):
- Username: `admin`
- Password: `changeme123`

**Remember to change the default admin password after first login!**
