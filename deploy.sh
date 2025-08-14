#!/bin/bash
# 🚀 Pastebin AWS EC2 Deployment Script
# Run this script on your EC2 instance after initial setup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Pastebin EC2 Deployment Script${NC}"
echo "=================================================="

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    echo -e "${RED}❌ Please run this script as ubuntu user${NC}"
    exit 1
fi

# Function to print status
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Update system
echo -e "${YELLOW}📦 Updating system packages...${NC}"
sudo apt update && sudo apt upgrade -y
print_status "System updated"

# Install Docker
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}🐳 Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker ubuntu
    print_status "Docker installed"
else
    print_status "Docker already installed"
fi

# Install Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${YELLOW}🔧 Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    print_status "Docker Compose installed"
else
    print_status "Docker Compose already installed"
fi

# Install Nginx and Certbot
echo -e "${YELLOW}🌐 Installing Nginx and Certbot...${NC}"
sudo apt install -y nginx certbot python3-certbot-nginx git curl unzip htop
print_status "Nginx and Certbot installed"

# Install AWS CLI (optional)
if ! command -v aws &> /dev/null; then
    echo -e "${YELLOW}☁️  Installing AWS CLI...${NC}"
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
    rm -rf awscliv2.zip aws/
    print_status "AWS CLI installed"
else
    print_status "AWS CLI already installed"
fi

# Create application directory
APP_DIR="/home/ubuntu/pastebin"
if [ ! -d "$APP_DIR" ]; then
    echo -e "${YELLOW}📁 Creating application directory...${NC}"
    mkdir -p $APP_DIR
    cd $APP_DIR
    
    # Ask user if they want to clone from git or will upload files manually
    read -p "Do you have a git repository URL to clone? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your git repository URL: " GIT_URL
        git clone $GIT_URL .
        print_status "Repository cloned"
    else
        print_warning "Please upload your application files to $APP_DIR"
        print_warning "You can use: scp -i your-key.pem -r ./pastebin ubuntu@your-ec2:/home/ubuntu/"
    fi
else
    print_status "Application directory exists"
    cd $APP_DIR
fi

# Generate secret key
echo -e "${YELLOW}🔐 Generating secret key...${NC}"
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
print_status "Secret key generated"

# Create environment file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚙️  Creating environment configuration...${NC}"
    
    # Ask for domain name
    read -p "Enter your domain name (e.g., example.com): " DOMAIN_NAME
    
    # Ask for database password
    read -p "Enter a secure database password: " -s DB_PASSWORD
    echo
    
    cat > .env << EOF
# Production Environment Configuration
SECRET_KEY=$SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Database Configuration
DATABASE_URL=postgresql://pastebin_user:$DB_PASSWORD@db:5432/pastebin

# File Configuration
MAX_FILES=5
MAX_FILE_SIZE_MB=10

# Auto-cleanup
AUTO_DELETE_DAYS=5

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=2

# Production Settings
DEBUG=false
DOMAIN_NAME=$DOMAIN_NAME
EOF
    print_status "Environment file created"
else
    print_status "Environment file already exists"
fi

# Create backup directory
mkdir -p /home/ubuntu/backups
print_status "Backup directory created"

# Create monitoring script
cat > /home/ubuntu/monitor.sh << 'EOF'
#!/bin/bash
# Application monitoring script

DOMAIN=$(grep DOMAIN_NAME /home/ubuntu/pastebin/.env | cut -d'=' -f2)
APP_DIR="/home/ubuntu/pastebin"

# Check if application is responding
if curl -f -s https://$DOMAIN/health > /dev/null; then
    echo "$(date): Application is healthy"
else
    echo "$(date): Application is down! Restarting..."
    cd $APP_DIR
    docker-compose -f docker-compose.prod.yml restart app
fi

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 85 ]; then
    echo "$(date): Warning: Disk usage is ${DISK_USAGE}%"
fi
EOF

chmod +x /home/ubuntu/monitor.sh
print_status "Monitoring script created"

# Create backup script
cat > /home/ubuntu/backup.sh << 'EOF'
#!/bin/bash
# Backup script for pastebin

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/backups"
APP_DIR="/home/ubuntu/pastebin"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose -f $APP_DIR/docker-compose.prod.yml exec -T db pg_dump -U pastebin_user pastebin > $BACKUP_DIR/db_backup_$DATE.sql 2>/dev/null || echo "Database backup failed"

# Backup uploads
tar -czf $BACKUP_DIR/uploads_backup_$DATE.tar.gz -C $APP_DIR uploads/ 2>/dev/null || echo "Upload backup failed"

# Backup configuration
cp $APP_DIR/.env $BACKUP_DIR/env_backup_$DATE

# Keep only last 7 backups
find $BACKUP_DIR -name "*backup*" -type f -mtime +7 -delete

echo "$(date): Backup completed - $DATE"
EOF

chmod +x /home/ubuntu/backup.sh
print_status "Backup script created"

# Remove default nginx site
sudo rm -f /etc/nginx/sites-enabled/default
print_status "Default nginx site removed"

echo
echo -e "${GREEN}🎉 Basic setup completed!${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. 🌐 Configure your DNS to point to this server's IP"
echo "2. 🔒 Run SSL setup: sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com"  
echo "3. 📝 Create nginx configuration (see EC2_DEPLOYMENT.md)"
echo "4. 🚀 Start your application: docker-compose -f docker-compose.prod.yml up -d"
echo "5. 📊 Setup monitoring crontabs (see EC2_DEPLOYMENT.md)"
echo
echo -e "${GREEN}🔧 Useful commands:${NC}"
echo "• Check logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "• Restart app: docker-compose -f docker-compose.prod.yml restart app"
echo "• System status: htop"
echo "• Test health: curl https://yourdomain.com/health"
echo
echo -e "${YELLOW}⚠️  Remember to:${NC}"
echo "• Configure your domain's DNS"
echo "• Setup SSL certificate"  
echo "• Configure nginx (template in EC2_DEPLOYMENT.md)"
echo "• Setup monitoring crontabs"
echo "• Test your deployment"

# Show environment file location
echo
echo -e "${GREEN}📁 Your environment file is at: /home/ubuntu/pastebin/.env${NC}"
echo -e "${GREEN}🔐 Your generated secret key has been saved to the .env file${NC}"

print_warning "Please logout and login again for Docker group changes to take effect!"
EOF
