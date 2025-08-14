# 🚀 AWS EC2 Deployment Guide with HTTPS & Custom Domain

This guide will help you deploy your Pastebin application on AWS EC2 with SSL/HTTPS and your custom domain.

## 📋 Prerequisites

- AWS Account with EC2 access
- Domain name (registered with any provider)
- SSH key pair for EC2 access
- Basic knowledge of Linux commands

## 🏗️ Part 1: EC2 Instance Setup

### 1.1 Launch EC2 Instance

1. **Go to AWS EC2 Console**
   - Choose "Launch Instance"
   - Select **Ubuntu Server 22.04 LTS** (Free tier eligible)

2. **Instance Configuration**:
   ```
   Instance Type: t3.micro (or t3.small for better performance)
   Key Pair: Create new or use existing
   Security Groups: Create new with these rules:
   ```

3. **Security Group Rules**:
   ```
   Type        Protocol    Port Range    Source
   SSH         TCP         22           Your IP (0.0.0.0/0 for anywhere)
   HTTP        TCP         80           0.0.0.0/0
   HTTPS       TCP         443          0.0.0.0/0
   Custom      TCP         8000         0.0.0.0/0 (temporary for testing)
   ```

4. **Storage**: 20 GB gp3 (free tier: 30GB)

### 1.2 Connect to Your Instance

```bash
# Replace with your key file and instance public DNS
ssh -i "your-key.pem" ubuntu@ec2-xx-xx-xx-xx.compute-1.amazonaws.com

# Update the system
sudo apt update && sudo apt upgrade -y
```

## 🐳 Part 2: Install Docker & Dependencies

### 2.1 Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker ubuntu

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Logout and login again for group changes
exit
# SSH back in
```

### 2.2 Install Additional Tools

```bash
# Install nginx and certbot for SSL
sudo apt install -y nginx certbot python3-certbot-nginx git curl

# Install AWS CLI (optional, for backups)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

## 📁 Part 3: Deploy Your Application

### 3.1 Upload Your Code

**Option A: Using Git (Recommended)**
```bash
# Clone your repository
git clone <your-repository-url>
cd pastebin

# Or if you don't have a repo, create the project directory
mkdir pastebin && cd pastebin
```

**Option B: Using SCP**
```bash
# From your local machine
scp -i "your-key.pem" -r c:/Users/ravibh/Desktop/pastebin ubuntu@your-ec2-instance:/home/ubuntu/
```

### 3.2 Configure Environment

```bash
# Create production environment file
cp .env.example .env

# Edit with production values
nano .env
```

**Production .env Configuration:**
```env
# IMPORTANT: Generate a strong secret key
SECRET_KEY=your-super-long-random-production-secret-key-at-least-32-characters

# Database (Use PostgreSQL for production)
DATABASE_URL=postgresql://pastebin_user:your_secure_db_password@db:5432/pastebin

# Security
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 1 week
AUTO_DELETE_DAYS=5

# File limits
MAX_FILES=5
MAX_FILE_SIZE_MB=10

# Server config
HOST=0.0.0.0
PORT=8000
WORKERS=2

# Production settings
DEBUG=false
```

### 3.3 Generate Strong Secret Key

```bash
# Generate a secure secret key
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))"
# Copy this output to your .env file
```

## 🔒 Part 4: SSL Certificate & Domain Setup

### 4.1 Configure DNS

**In your domain provider's control panel:**
```
Type    Name    Value
A       @       YOUR_EC2_PUBLIC_IP
A       www     YOUR_EC2_PUBLIC_IP
```

**Wait for DNS propagation (5-30 minutes)**
```bash
# Test DNS resolution
nslookup yourdomain.com
dig yourdomain.com
```

### 4.2 Get SSL Certificate

```bash
# Stop nginx if running
sudo systemctl stop nginx

# Get SSL certificate (replace yourdomain.com)
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Start nginx
sudo systemctl start nginx
```

## 🌐 Part 5: Nginx Configuration

### 5.1 Create Nginx Configuration

```bash
# Remove default config
sudo rm /etc/nginx/sites-enabled/default

# Create your app config
sudo nano /etc/nginx/sites-available/pastebin
```

**Nginx Configuration (`/etc/nginx/sites-available/pastebin`):**
```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL Security Headers
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options DENY always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # File upload size
    client_max_body_size 50M;

    # Logging
    access_log /var/log/nginx/pastebin_access.log;
    error_log /var/log/nginx/pastebin_error.log;

    # Rate limiting for sensitive endpoints
    location ~ ^/(register|login) {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /home/ubuntu/pastebin/app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Upload files
    location /uploads/ {
        alias /home/ubuntu/pastebin/uploads/;
        expires 30d;
        add_header Cache-Control "public";
    }

    # Main application
    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }
}
```

### 5.2 Enable Configuration

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/pastebin /etc/nginx/sites-enabled/

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

## 🚀 Part 6: Deploy with Docker

### 6.1 Start the Application

```bash
# Navigate to your app directory
cd /home/ubuntu/pastebin

# Start with production compose file
docker-compose -f docker-compose.prod.yml up -d

# Check if everything is running
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f app
```

### 6.2 Test the Deployment

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test external access
curl https://yourdomain.com/health
```

## 🔧 Part 7: Production Optimizations

### 7.1 Setup Auto-SSL Renewal

```bash
# Add crontab entry for certificate renewal
sudo crontab -e

# Add this line:
0 12 * * * /usr/bin/certbot renew --quiet && systemctl reload nginx
```

### 7.2 Setup Log Rotation

```bash
# Create logrotate config
sudo nano /etc/logrotate.d/pastebin
```

**Logrotate Configuration:**
```
/var/log/nginx/pastebin_*.log {
    daily
    missingok
    rotate 14
    compress
    notifempty
    create 0644 www-data www-data
    postrotate
        systemctl reload nginx
    endscript
}
```

### 7.3 Setup Monitoring

**Create monitoring script:**
```bash
nano ~/monitor.sh
```

```bash
#!/bin/bash
# Simple monitoring script

# Check if application is responding
if curl -f -s https://yourdomain.com/health > /dev/null; then
    echo "$(date): Application is healthy"
else
    echo "$(date): Application is down! Restarting..."
    cd /home/ubuntu/pastebin
    docker-compose -f docker-compose.prod.yml restart app
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "$(date): Warning: Disk usage is ${DISK_USAGE}%"
fi
```

```bash
# Make executable
chmod +x ~/monitor.sh

# Add to crontab (check every 5 minutes)
crontab -e
# Add: */5 * * * * /home/ubuntu/monitor.sh >> /home/ubuntu/monitor.log 2>&1
```

### 7.4 Setup Backups

**Create backup script:**
```bash
nano ~/backup.sh
```

```bash
#!/bin/bash
# Backup script for pastebin

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/backups"
APP_DIR="/home/ubuntu/pastebin"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database (if using PostgreSQL)
docker-compose -f $APP_DIR/docker-compose.prod.yml exec -T db pg_dump -U pastebin_user pastebin > $BACKUP_DIR/db_backup_$DATE.sql

# Backup uploads
tar -czf $BACKUP_DIR/uploads_backup_$DATE.tar.gz -C $APP_DIR uploads/

# Backup configuration
cp $APP_DIR/.env $BACKUP_DIR/env_backup_$DATE

# Keep only last 7 backups
find $BACKUP_DIR -name "*backup*" -type f -mtime +7 -delete

echo "$(date): Backup completed - $DATE"
```

```bash
# Make executable
chmod +x ~/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup.sh >> /home/ubuntu/backup.log 2>&1
```

## 🔍 Part 8: Troubleshooting

### 8.1 Common Issues

**Application won't start:**
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs app

# Check if port is in use
sudo netstat -tlnp | grep :8000

# Restart everything
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

**SSL certificate issues:**
```bash
# Check certificate status
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Test nginx config
sudo nginx -t
```

**Database connection issues:**
```bash
# Check if database is running
docker-compose -f docker-compose.prod.yml ps db

# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Reset database (CAUTION: This deletes all data)
docker-compose -f docker-compose.prod.yml down
docker volume rm pastebin_postgres_data
docker-compose -f docker-compose.prod.yml up -d
```

### 8.2 Performance Tuning

**For higher traffic:**
```yaml
# In docker-compose.prod.yml, increase workers:
environment:
  WORKERS: 4  # Increase based on CPU cores

# Add Redis for caching (future enhancement)
```

**Nginx optimization:**
```nginx
# Add to nginx config for better performance
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}

# Enable gzip compression
gzip on;
gzip_types text/plain application/json application/javascript text/css;
```

## 🎯 Part 9: Final Steps

### 9.1 Security Checklist

- [ ] Strong SECRET_KEY generated and set
- [ ] SSL certificate installed and auto-renewal configured  
- [ ] Security headers configured in Nginx
- [ ] Rate limiting enabled
- [ ] Firewall configured (only necessary ports open)
- [ ] Regular backups scheduled
- [ ] Monitoring set up
- [ ] Default passwords changed
- [ ] SSH key-only authentication (disable password auth)

### 9.2 Post-Deployment Testing

```bash
# Test all endpoints
curl -I https://yourdomain.com
curl -I https://yourdomain.com/health
curl -I https://yourdomain.com/docs

# Test SSL rating
# Visit: https://www.ssllabs.com/ssltest/
# Enter your domain and check the rating
```

## 🎉 Congratulations!

Your Pastebin application is now live at `https://yourdomain.com` with:

✅ **HTTPS/SSL encryption**  
✅ **Custom domain**  
✅ **Production-ready configuration**  
✅ **Automatic backups**  
✅ **Monitoring**  
✅ **Security headers**  
✅ **Rate limiting**  

## 📞 Support Commands

```bash
# View application status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart application
docker-compose -f docker-compose.prod.yml restart app

# Update application
git pull
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d --build

# Check disk space
df -h

# Check memory usage
free -h

# Check running processes
htop
```

---

🚀 **Your Pastebin application is now production-ready on AWS EC2!**
