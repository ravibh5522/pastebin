# Pastebin Application - Deployment Guide

## Overview
A secure pastebin application with user authentication, file uploads, and auto-cleanup features.

## Quick Start (Development)

1. **Clone and Setup**:
   ```bash
   git clone <repository>
   cd pastebin
   cp .env.example .env
   # Edit .env with your configuration
   ```

2. **Start with Docker**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Open http://localhost:8000
   - Create an account and start pasting!

## Production Deployment

### Option 1: Simple Docker Deployment
```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with production values

# 2. Deploy
docker-compose up -d

# 3. Enable nginx (optional)
docker-compose --profile production up -d
```

### Option 2: Full Production with PostgreSQL
```bash
# 1. Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# 2. Configure SSL certificates (recommended)
# Place SSL certificates in ./ssl/ directory
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | (required) | JWT signing key - make it long and random |
| `DATABASE_URL` | `sqlite:///./data/pastes.db` | Database connection string |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `43200` | JWT token expiration (30 days) |
| `AUTO_DELETE_DAYS` | `5` | Auto-delete pastes after N days |
| `MAX_FILES` | `5` | Maximum files per paste |
| `MAX_FILE_SIZE_MB` | `10` | Maximum file size in MB |
| `HOST` | `0.0.0.0` | Server host |
| `PORT` | `8000` | Server port |

### Database Support

**SQLite (Default)**:
```bash
DATABASE_URL=sqlite:///./data/pastes.db
```

**PostgreSQL**:
```bash
DATABASE_URL=postgresql://username:password@localhost:5432/pastebin
```

**MySQL**:
```bash
DATABASE_URL=mysql+pymysql://username:password@localhost:3306/pastebin
```

## Features

✅ **Authentication System**
- User registration and login
- JWT tokens with HTTP-only cookies
- Session management with localStorage backup

✅ **Paste Management**
- Create public/private pastes
- Save/unsave pastes for logged-in users
- Syntax highlighting and expiration options

✅ **File Uploads**
- Multi-file uploads per paste
- Configurable size limits
- Secure file handling

✅ **User Dashboard**
- View all created pastes
- Manage saved pastes
- Auto-cleanup notifications

✅ **Security Features**
- Password hashing with bcrypt
- CORS protection
- Rate limiting ready
- Auto-logout on session expiry

## API Endpoints

### Authentication
- `POST /register` - User registration
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /session-status` - Check session status

### Pastes
- `GET /` - Home page
- `POST /` - Create paste
- `GET /{paste_id}` - View paste
- `POST /{paste_id}/save` - Save paste
- `DELETE /{paste_id}/save` - Unsave paste

### Dashboard
- `GET /dashboard` - User dashboard

## Health Checks

The application provides health endpoints:
- `GET /session-status` - Application health and session status

## Monitoring

### Logs
Application logs are available in the container:
```bash
docker-compose logs -f pastebin
```

### Database
Monitor database size and performance:
```bash
# SQLite
sqlite3 data/pastes.db "SELECT count(*) FROM pastes;"

# PostgreSQL
docker-compose exec db psql -U pastebin_user -d pastebin -c "SELECT count(*) FROM pastes;"
```

## Security Recommendations

1. **Change default SECRET_KEY** - Use a long, random string
2. **Use HTTPS** - Configure SSL certificates in nginx
3. **Firewall** - Restrict access to database ports
4. **Backups** - Regular database backups
5. **Updates** - Keep containers updated

## Troubleshooting

### Common Issues

**Database connection errors**:
```bash
# Check database service
docker-compose logs db

# Reinitialize database
docker-compose down
docker volume rm pastebin_postgres_data
docker-compose up -d
```

**File upload issues**:
```bash
# Check upload directory permissions
docker-compose exec pastebin ls -la /app/uploads
```

**Authentication issues**:
```bash
# Clear browser localStorage
# Check SECRET_KEY configuration
# Verify token expiration settings
```

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Adding Features
The application is built with FastAPI and follows a modular structure:
- `app/main.py` - Main application and routes
- `app/database.py` - Database models and configuration
- `app/auth.py` - Authentication utilities
- `app/crud.py` - Database operations
- `app/schemas.py` - Pydantic models

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Verify configuration: Review `.env` file
3. Check database connectivity
4. Ensure proper file permissions

## License

[Add your license information here]
