# Paste Shaver - Enhanced Pastebin Application

An advanced pastebin application built with FastAPI, featuring user authentication, file uploads, auto-deletion, and a clean dark theme interface.

## 🌟 Features

### Core Features
- **Text & File Sharing**: Create pastes with text content and/or file attachments
- **File Support**: Upload multiple files (up to 5 files, 10MB each)
- **Syntax Highlighting**: Automatic code detection and highlighting
- **File Viewer**: In-browser code editor for supported file types
- **Responsive Design**: Clean, modern dark theme interface

### 🔐 User Authentication & Management
- **User Registration**: Sign up with username, email, and password
- **Secure Login**: Password hashing with bcrypt
- **Session Management**: JWT-based authentication with HTTP-only cookies
- **Dashboard**: Personal dashboard showing user's pastes and saved items

### 💾 Save & Organization
- **Save Pastes**: Logged-in users can save any paste for later access
- **Personal Collection**: View all your created and saved pastes
- **User Attribution**: See who created each paste
- **Anonymous Support**: Non-registered users can still create pastes

### 🧹 Auto-Cleanup System
- **Automatic Deletion**: Pastes older than 5 days are automatically deleted
- **File Cleanup**: Associated uploaded files are also removed
- **Startup Cleanup**: Cleanup runs on application startup
- **Manual Cleanup**: Endpoint for manual cleanup operations
- **Scheduled Tasks**: Batch script for Windows Task Scheduler

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone or download the project**
   ```bash
   cd pastebin
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python -m uvicorn app.main:app --reload
   ```

4. **Open in browser**
   Navigate to `http://127.0.0.1:8000`

## 📁 Project Structure

```
pastebin/
├── app/
│   ├── main.py          # FastAPI application and routes
│   ├── database.py      # Database models and configuration
│   ├── schemas.py       # Pydantic schemas
│   ├── crud.py          # Database operations
│   ├── auth.py          # Authentication utilities
│   ├── static/          # CSS and static files
│   ├── templates/       # Jinja2 HTML templates
│   └── pastes.db        # SQLite database (auto-created)
├── uploads/             # User uploaded files (auto-created)
├── requirements.txt     # Python dependencies
├── cleanup.py          # Cleanup script
└── cleanup.bat         # Windows batch file for scheduling
```

## 🎨 User Interface

### Home Page
- Clean form for creating new pastes
- File upload with drag-and-drop support
- User authentication status display

### Paste View
- Syntax-highlighted code display
- File attachment viewer with image previews
- In-browser code editor for text files
- Save/unsave functionality for logged-in users

### User Dashboard
- **My Pastes**: All pastes created by the user
- **Saved Pastes**: Collection of saved pastes from any user
- User management and logout options

### Authentication
- Registration with email validation
- Secure login with error handling
- Password requirements and validation

## 🔧 API Endpoints

### Public Endpoints
- `GET /` - Home page with paste creation form
- `POST /create` - Create a new paste
- `GET /{slug}` - View a specific paste
- `GET /raw/{slug}` - Download paste content as text
- `GET /uploads/{slug}/{filename}` - Serve uploaded files

### Authentication Endpoints
- `GET /login` - Login form
- `POST /login` - Process login
- `GET /signup` - Registration form  
- `POST /signup` - Process registration
- `POST /logout` - Logout user

### User Endpoints
- `GET /dashboard` - User dashboard (requires auth)
- `POST /save-paste/{paste_id}` - Toggle save status (requires auth)

### Admin Endpoints
- `POST /cleanup` - Manual cleanup of old pastes

## 🗄️ Database Schema

### Users Table
- `id` (Primary Key)
- `username` (Unique)
- `email` (Unique)
- `hashed_password`
- `created_at`
- `is_active`

### Pastes Table
- `id` (Primary Key)
- `slug` (Unique, URL identifier)
- `content` (Text content, optional)
- `filenames` (Comma-separated file list)
- `created_at`
- `user_id` (Foreign Key, optional for anonymous pastes)

### Saved Pastes Table
- `id` (Primary Key)
- `user_id` (Foreign Key)
- `paste_id` (Foreign Key)
- `saved_at`

## 🔄 Auto-Deletion System

### How it Works
1. **Startup Cleanup**: Runs when the application starts
2. **Scheduled Cleanup**: Use the provided batch script with Windows Task Scheduler
3. **Manual Cleanup**: Call the `/cleanup` endpoint

### Setting up Scheduled Cleanup (Windows)
1. Open Windows Task Scheduler
2. Create Basic Task → "Pastebin Cleanup"
3. Set trigger to "Daily"
4. Action: Start a program → Browse to `cleanup.bat`
5. Finish

### Cleanup Process
- Identifies pastes older than 5 days
- Removes associated files from `uploads/` directory
- Deletes saved paste entries
- Removes paste records from database

## 🔒 Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: Secure authentication tokens
- **HTTP-only Cookies**: Prevent XSS attacks
- **File Upload Validation**: Size and type restrictions
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **Path Traversal Prevention**: Secure file serving

## ⚙️ Configuration

### Environment Variables
You can customize these settings by modifying the constants in `app/main.py`:

- `MAX_FILES`: Maximum files per paste (default: 5)
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (default: 10)
- `SECRET_KEY`: JWT secret key (change in production!)

### Database
- Uses SQLite by default (`app/pastes.db`)
- Can be easily changed to PostgreSQL or MySQL by updating the connection string

## 🤝 Usage Examples

### Creating a Paste
1. Visit the home page
2. Enter text content and/or upload files
3. Click "Create Paste"
4. Share the generated URL

### User Registration
1. Click "Sign Up" 
2. Enter username, email, and password
3. Automatically logged in after registration

### Saving Pastes
1. Login to your account
2. View any paste
3. Click the "Save" button (heart icon)
4. Access saved pastes from your dashboard

## 📝 Notes

- Anonymous pastes are supported but cannot be saved
- Files are stored in the `uploads/` directory organized by paste slug
- Database is automatically created on first run
- Image files display previews in the paste view
- Text files can be viewed and copied using the in-browser editor

## 🛠️ Development

To run in development mode:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

The `--reload` flag enables auto-restart on code changes.

## 📄 License

This project is open source and available under the MIT License.
