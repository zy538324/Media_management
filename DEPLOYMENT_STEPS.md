# Deployment Steps for Raspberry Pi

## Execute These Commands via SSH

```bash
# 1. SSH into the Raspberry Pi
ssh pmadmin@10.252.0.66

# 2. Verify extraction was successful
cd /var/www/media_manager
ls -la

# 3. Run the installation script with sudo
sudo bash setup.sh

# Wait for it to complete (takes a few minutes)
# It will:
# - Create mediauser:mediauser
# - Set up virtual environment
# - Install Python dependencies
# - Create systemd service: media-management.service
# - Set up log rotation
# - Create management command: media-mgmt

# 5. Verify the service is running
sudo systemctl status media-management

# 6. Check the application logs
media-mgmt app-logs

# 7. Create required directories for Nginx/SSL
sudo mkdir -p /var/www/certbot
sudo chown -R www-data:www-data /var/www/certbot

# 8. Install Nginx
sudo apt update
sudo apt install -y nginx

# 9. Create the Nginx configuration file
sudo nano /etc/nginx/sites-available/media-management

# (Paste the full HTTPS config from nginx_setup.md Step 3)

# 10. Create temporary HTTP config for initial cert generation
sudo nano /etc/nginx/sites-available/media-management-temp

# (Paste the temporary config from nginx_setup.md - HTTP only for Certbot)

# 11. Enable temporary config and test
sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -s /etc/nginx/sites-available/media-management-temp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 12. Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# 13. Obtain SSL certificate
# IMPORTANT: Ensure DNS for media.tamsilcms.com points to 10.252.0.66 first!
sudo certbot certonly --webroot \
  -w /var/www/certbot \
  -d media.tamsilcms.com \
  --email your-email@example.com \
  --agree-tos \
  --no-eff-email

# 14. Switch to full HTTPS config
sudo rm /etc/nginx/sites-enabled/media-management-temp
sudo ln -s /etc/nginx/sites-available/media-management /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 15. Setup firewall (if not already done)
sudo ufw allow 'Nginx Full'
sudo ufw allow 22/tcp  # SSH
sudo ufw enable

# 16. Verify everything is running
sudo systemctl status media-management
sudo systemctl status nginx
sudo certbot certificates

# 17. Test the application
# Open browser and navigate to: https://media.tamsilcms.com
# Login with default credentials:
#   Username: admin
#   Password: changeme123
# CHANGE PASSWORD IMMEDIATELY AFTER LOGIN!

# 18. Check logs if needed
media-mgmt app-logs
sudo tail -f /var/log/nginx/media-management-access.log
sudo tail -f /var/log/nginx/media-management-error.log
```

---

## Quick Reference: Management Commands

After deployment, you can manage the application using:

```bash
# Service management
sudo systemctl start media-management
sudo systemctl stop media-management
sudo systemctl restart media-management
sudo systemctl status media-management

# Logs
media-mgmt app-logs          # Application logs
media-mgmt error-logs        # Error logs
media-mgmt access-logs       # Gunicorn access logs
media-mgmt logs              # All logs combined

# Nginx
sudo systemctl restart nginx
sudo systemctl reload nginx
sudo nginx -t                # Test configuration

# SSL Certificate
sudo certbot certificates
sudo certbot renew --dry-run  # Test renewal
sudo certbot renew            # Manual renewal
```

---

## Troubleshooting

### Service won't start
```bash
media-mgmt app-logs
sudo systemctl status media-management
```
Check for PostgreSQL connectivity issues or missing dependencies.

### Nginx won't start
```bash
sudo nginx -t
sudo tail -f /var/log/nginx/media-management-error.log
```
Usually SSL certificate path issue.

### Can't reach the application
```bash
# Verify service is listening
sudo netstat -tlnp | grep :5000

# Verify Nginx is listening
sudo netstat -tlnp | grep :80
sudo netstat -tlnp | grep :443

# Test connection locally
curl http://localhost:5000
curl http://localhost
```

### SSL certificate not installing
- Verify DNS points to 10.252.0.66
- Verify port 80 is accessible externally
- Check Certbot logs: `sudo tail -f /var/log/letsencrypt/letsencrypt.log`

---

## Verification Checklist

After deployment:

- [ ] SSH into Pi and extract tar.gz
- [ ] Run setup.sh successfully
- [ ] media-management service running (`sudo systemctl status media-management`)
- [ ] Nginx installed
- [ ] SSL certificate obtained
- [ ] DNS configured for media.tamsilcms.com → 10.252.0.66
- [ ] Can access https://media.tamsilcms.com
- [ ] Login works with credentials
- [ ] Changed default admin password
- [ ] Can add a test movie/TV/music request
- [ ] Requests appear in Radarr/Sonarr/Lidarr
- [ ] Application logs show no errors

---

## Post-Deployment Testing

```bash
# Test database connection
media-mgmt test

# Check PostgreSQL connection
psql -h 10.252.0.25 -U media_user -d media_management -c "SELECT COUNT(*) FROM users;"
# Password: 1772BigHorridTurkeyChews!

# Check *arr service connectivity
curl http://10.252.0.2:7878/api/v3/system/status -H "X-Api-Key: YOUR_RADARR_KEY" | jq .
curl http://10.252.0.2:8989/api/v3/system/status -H "X-Api-Key: YOUR_SONARR_KEY" | jq .
curl http://10.252.0.2:8686/api/v1/system/status -H "X-Api-Key: YOUR_LIDARR_KEY" | jq .
```

---

## Success!

Once all verification steps pass, your Media Management application is fully deployed with:

✅ Systemd service for automatic startup
✅ Reverse proxy via Nginx
✅ HTTPS with Let's Encrypt SSL
✅ Auto-renewal of certificates
✅ PostgreSQL backend on 10.252.0.25
✅ Integration with Radarr, Sonarr, Lidarr at 10.252.0.2
✅ Jellyfin library integration
✅ Full media request and recommendation system

Access it at: **https://media.tamsilcms.com**
