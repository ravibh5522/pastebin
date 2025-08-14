#!/bin/bash
# Setup script for EC2 deployment secrets and final configuration

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🔐 Setting up secrets and final configuration...${NC}"

# Create secrets directory
mkdir -p secrets

# Generate database password if not exists
if [ ! -f "secrets/db_password.txt" ]; then
    echo -e "${YELLOW}Generating secure database password...${NC}"
    openssl rand -base64 32 > secrets/db_password.txt
    echo -e "${GREEN}✅ Database password generated${NC}"
fi

# Set proper permissions
chmod 600 secrets/db_password.txt
chmod 700 secrets/

# Update .env file with the database password
DB_PASSWORD=$(cat secrets/db_password.txt)
if grep -q "DATABASE_URL=postgresql" .env; then
    sed -i "s|postgresql://pastebin_user:.*@db|postgresql://pastebin_user:$DB_PASSWORD@db|" .env
    echo -e "${GREEN}✅ Database URL updated in .env${NC}"
fi

# Create logs directory
mkdir -p logs

# Set proper ownership
sudo chown -R ubuntu:ubuntu uploads/ data/ logs/ secrets/ 2>/dev/null || true

echo -e "${GREEN}🎉 Secrets and directories configured successfully!${NC}"
echo
echo -e "${YELLOW}You can now start the application with:${NC}"
echo "docker-compose -f docker-compose.ec2.yml up -d"
