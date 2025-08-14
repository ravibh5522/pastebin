# 📋 EC2 Deployment Checklist

## Pre-Deployment Preparation

### Local Machine
- [ ] **Code Ready**: All application files tested locally
- [ ] **Environment File**: `.env.example` updated with production settings
- [ ] **Domain Purchased**: Domain name ready and accessible
- [ ] **AWS Account**: EC2 access with appropriate permissions
- [ ] **SSH Key**: Key pair created for EC2 access

### AWS EC2 Instance
- [ ] **Instance Launched**: Ubuntu 22.04 LTS, t3.micro or larger
- [ ] **Security Groups**: Ports 22, 80, 443 open
- [ ] **Elastic IP**: Assigned to instance (optional but recommended)
- [ ] **SSH Access**: Can connect to instance successfully

## Deployment Steps

### 1. DNS Configuration
- [ ] **A Record**: Point your domain to EC2 public IP
- [ ] **WWW Record**: Point www.yourdomain.com to EC2 public IP  
- [ ] **DNS Propagation**: Wait 5-30 minutes, test with `nslookup yourdomain.com`

### 2. Server Setup
- [ ] **Connect to EC2**: SSH into your instance
- [ ] **Run Setup Script**: Upload and execute `deploy.sh`
- [ ] **Docker Group**: Logout and login for Docker permissions
- [ ] **Application Files**: Upload your pastebin application files

### 3. Application Configuration  
- [ ] **Environment File**: Create production `.env` with strong SECRET_KEY
- [ ] **Setup Secrets**: Run `bash setup-secrets.sh`
- [ ] **Directory Permissions**: Ensure proper ownership of directories
- [ ] **Test Docker**: Verify docker and docker-compose work

### 4. SSL Certificate
- [ ] **Stop Nginx**: `sudo systemctl stop nginx`
- [ ] **Get Certificate**: `sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com`
- [ ] **Verify Certificate**: Check `/etc/letsencrypt/live/yourdomain.com/`
- [ ] **Start Nginx**: `sudo systemctl start nginx`

### 5. Nginx Configuration
- [ ] **Remove Default**: `sudo rm /etc/nginx/sites-enabled/default`
- [ ] **Copy Configuration**: Use `nginx-ec2.conf` template
- [ ] **Replace Domain**: Update YOURDOMAIN.COM placeholders
- [ ] **Enable Site**: Create symlink to sites-enabled
- [ ] **Test Config**: `sudo nginx -t`
- [ ] **Restart Nginx**: `sudo systemctl restart nginx`

### 6. Application Deployment
- [ ] **Start Services**: `docker-compose -f docker-compose.ec2.yml up -d`
- [ ] **Check Status**: `docker-compose -f docker-compose.ec2.yml ps`
- [ ] **View Logs**: `docker-compose -f docker-compose.ec2.yml logs -f app`
- [ ] **Test Health**: `curl http://localhost:8000/health`

### 7. SSL and Security Testing
- [ ] **HTTPS Access**: Visit https://yourdomain.com
- [ ] **SSL Rating**: Test at https://www.ssllabs.com/ssltest/
- [ ] **Security Headers**: Check with security header testing tools
- [ ] **Rate Limiting**: Test login attempts and API calls

### 8. Monitoring Setup
- [ ] **Auto-renewal**: SSL certificate auto-renewal crontab
- [ ] **Monitoring Script**: Add monitoring crontab entry
- [ ] **Backup Script**: Add backup crontab entry  
- [ ] **Log Rotation**: Configure log rotation
- [ ] **Disk Space**: Monitor disk usage

### 9. Final Testing
- [ ] **Registration**: Test user registration
- [ ] **Login**: Test user login and session management
- [ ] **Paste Creation**: Test creating pastes with and without files
- [ ] **File Upload**: Test file upload functionality
- [ ] **Dashboard**: Test user dashboard and saved pastes
- [ ] **Auto-redirect**: Test session persistence and redirects

### 10. Performance Optimization
- [ ] **Database Performance**: Monitor query performance
- [ ] **Memory Usage**: Check application memory consumption
- [ ] **CPU Usage**: Monitor CPU under load
- [ ] **Response Times**: Test page load speeds
- [ ] **Caching**: Verify nginx caching headers

## Post-Deployment Maintenance

### Daily
- [ ] **Health Check**: Verify application is responding
- [ ] **Log Review**: Check error logs for issues
- [ ] **Disk Space**: Monitor available disk space
- [ ] **Memory Usage**: Check for memory leaks

### Weekly  
- [ ] **Security Updates**: Update system packages
- [ ] **Backup Verification**: Ensure backups are working
- [ ] **SSL Certificate**: Check certificate expiry (auto-renewal)
- [ ] **Performance Review**: Review access logs and performance

### Monthly
- [ ] **Full Backup**: Complete system backup
- [ ] **Security Audit**: Review access logs for suspicious activity
- [ ] **Dependency Updates**: Update Docker images
- [ ] **Performance Optimization**: Review and optimize based on usage

## Emergency Procedures

### Application Down
```bash
# Check application status
docker-compose -f docker-compose.ec2.yml ps

# Check logs
docker-compose -f docker-compose.ec2.yml logs app

# Restart application
docker-compose -f docker-compose.ec2.yml restart app

# Full restart
docker-compose -f docker-compose.ec2.yml down
docker-compose -f docker-compose.ec2.yml up -d
```

### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Force renewal
sudo certbot renew --force-renewal

# Restart nginx
sudo systemctl restart nginx
```

### Database Issues
```bash
# Check database status
docker-compose -f docker-compose.ec2.yml logs db

# Restart database
docker-compose -f docker-compose.ec2.yml restart db

# Database backup
docker-compose -f docker-compose.ec2.yml exec db pg_dump -U pastebin_user pastebin > backup.sql
```

### High Resource Usage
```bash
# Check system resources
htop
df -h
free -m

# Check container resources
docker stats

# Restart services if needed
sudo systemctl restart nginx
docker-compose -f docker-compose.ec2.yml restart app
```

## Support Commands

### Application Management
```bash
# View all services status
docker-compose -f docker-compose.ec2.yml ps

# Follow logs
docker-compose -f docker-compose.ec2.yml logs -f

# Update application
git pull
docker-compose -f docker-compose.ec2.yml down
docker-compose -f docker-compose.ec2.yml up -d --build

# Database shell
docker-compose -f docker-compose.ec2.yml exec db psql -U pastebin_user pastebin
```

### System Monitoring
```bash
# System status
systemctl status nginx
systemctl status docker

# Resource usage
htop
iostat -x 1
netstat -tlnp

# Disk usage
du -sh /home/ubuntu/pastebin/*
df -h
```

### Nginx Management
```bash
# Test configuration
sudo nginx -t

# Reload configuration
sudo systemctl reload nginx

# View access logs
sudo tail -f /var/log/nginx/pastebin_access.log

# View error logs
sudo tail -f /var/log/nginx/pastebin_error.log
```

---

## ✅ Success Criteria

Your deployment is successful when:

1. ✅ **HTTPS Access**: https://yourdomain.com loads correctly
2. ✅ **Registration**: Users can register new accounts  
3. ✅ **Login**: Users can login and access dashboard
4. ✅ **Paste Creation**: Users can create pastes with text and files
5. ✅ **File Downloads**: Uploaded files can be downloaded
6. ✅ **SSL Rating**: A+ rating on SSL Labs test
7. ✅ **Performance**: Page loads in under 2 seconds
8. ✅ **Monitoring**: Health checks and backups working
9. ✅ **Security**: Rate limiting and security headers active
10. ✅ **Persistence**: Data persists through application restarts

**🎉 Congratulations! Your Pastebin application is now live and production-ready!**
