# 🚀 Quick Start Guide

## Get Started in 3 Steps

### 1. Configure Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit the configuration (IMPORTANT: Change the SECRET_KEY!)
# Use a text editor to modify .env:
SECRET_KEY=your-super-secret-production-key-make-it-long-and-random
DATABASE_URL=sqlite:///./data/pastes.db  # or PostgreSQL/MySQL
AUTO_DELETE_DAYS=5
```

### 2. Start the Application
```bash
# Using Docker Compose (recommended)
docker-compose up -d

# The application will be available at:
# http://localhost:8000
```

### 3. Verify Everything Works
```bash
# Check application health
curl http://localhost:8000/health
# Should return: {"status":"healthy","database":"connected","timestamp":"..."}

# Check logs
docker-compose logs -f pastebin
```

## 🎯 What You Get

✅ **Full-Featured Pastebin**
- Text paste creation with syntax highlighting
- Multi-file uploads (up to 5 files, 10MB each)
- Expiration options (1 hour to 1 year, or never)

✅ **User Authentication**
- Register and login system
- Personal dashboard
- Save/unsave pastes
- Session management

✅ **Auto-Cleanup**
- Automatic deletion of old pastes (configurable)
- File cleanup included
- Database maintenance

## 🔧 Production Setup

For production deployment:

1. **Use strong SECRET_KEY**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Use PostgreSQL** (recommended):
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Configure reverse proxy** (nginx):
   - SSL certificates
   - Domain configuration
   - Rate limiting

## 📝 Usage Examples

### Creating Your First Paste
1. Visit http://localhost:8000
2. Enter some text or code
3. Optionally upload files
4. Set expiration (or leave as "Never")
5. Click "Create Paste"

### User Features
1. Click "Sign Up" to create an account
2. Login to access the dashboard
3. Save interesting pastes for later
4. Manage all your pastes from the dashboard

## 🆘 Troubleshooting

**Application won't start?**
```bash
# Check logs
docker-compose logs pastebin

# Common issues:
# - SECRET_KEY not set in .env
# - Port 8000 already in use
# - Insufficient disk space
```

**Database errors?**
```bash
# Reset database
docker-compose down
rm -rf data/
docker-compose up -d
```

**File upload issues?**
```bash
# Check upload directory permissions
docker-compose exec pastebin ls -la /app/uploads
```

## 🔗 Next Steps

- Read the full [README.md](README.md) for detailed information
- Check [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment
- Explore the API at http://localhost:8000/docs

---

🎉 **You're all set!** Your pastebin application is ready to use.
