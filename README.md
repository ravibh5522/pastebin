# Paste Shaver - Enhanced Pastebin & Chat Application

An advanced pastebin and real-time chat application built with FastAPI, featuring user authentication, file uploads, group chat system, admin management, auto-deletion, and a modern dark theme interface.

## 🌟 Features

### Core Features
- **Text & File Sharing**: Create pastes with text content and/or file attachments
- **File Support**: Upload multiple files (up to 5 files, 10MB each)
- **Syntax Highlighting**: Automatic code detection and highlighting
- **File Viewer**: In-browser code editor for supported file types
- **Responsive Design**: Clean, modern dark theme interface

### 💬 Real-Time Chat System
- **Group Chat**: Create and join chat groups with invite codes
- **Real-Time Messaging**: WebSocket-powered instant messaging
- **File Sharing**: Share files directly in chat conversations
- **Code Sharing**: Auto-detected code blocks with syntax highlighting
- **Message Features**: Copy messages, download code snippets, reply to messages
- **WhatsApp-Style UI**: Variable-width message cards with modern design
- **Infinite Scroll**: Optimized for long conversations
- **Typing Indicators**: See when others are typing

### 👑 Admin Management System
- **Group Administration**: Comprehensive member management
- **Acting Leaders**: Admins can appoint acting leaders with limited permissions
- **Member Management**: Add/remove members by username
- **Role-Based Permissions**: Different access levels for admins and acting leaders
- **Invite Code Management**: Auto-refresh invite codes every hour
- **Manual Code Refresh**: Admins can manually refresh group invite codes

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
- **Background Tasks**: Automated invite code refresh system

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
│   ├── main.py              # FastAPI application and routes
│   ├── database.py          # Database models and configuration
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # Database operations
│   ├── auth.py              # Authentication utilities
│   ├── websocket_manager.py # WebSocket connection management
│   ├── background_tasks.py  # Background task scheduler
│   ├── static/              # CSS, JavaScript and static files
│   │   ├── style.css        # Main stylesheet
│   │   └── session.js       # Session management
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── chat/            # Chat-related templates
│   │   │   ├── group.html   # Group chat interface
│   │   │   ├── create.html  # Create group form
│   │   │   └── join.html    # Join group form
│   │   ├── dashboard.html   # User dashboard
│   │   ├── index.html       # Home page
│   │   ├── login.html       # Login form
│   │   ├── paste.html       # Paste viewer
│   │   └── signup.html      # Registration form
│   └── pastes.db            # SQLite database (auto-created)
├── uploads/                 # User uploaded files (auto-created)
├── chat_uploads/           # Chat file uploads (auto-created)
├── data/                   # Database storage
├── requirements.txt        # Python dependencies
├── cleanup.py             # Cleanup script
├── cleanup.bat            # Windows batch file for scheduling
├── DEPLOYMENT.md          # Deployment instructions
├── EC2_DEPLOYMENT.md      # AWS EC2 deployment guide
└── docker-compose.yml     # Docker configuration
```

## 🎨 User Interface

### Home Page
- Clean form for creating new pastes
- File upload with drag-and-drop support
- User authentication status display
- Navigation to chat groups

### Paste View
- Syntax-highlighted code display
- File attachment viewer with image previews
- In-browser code editor for text files
- Save/unsave functionality for logged-in users

### User Dashboard
- **My Pastes**: All pastes created by the user
- **Saved Pastes**: Collection of saved pastes from any user
- **Chat Groups**: Access to user's chat groups
- User management and logout options

### Chat Interface
- **Modern Design**: WhatsApp-style variable-width message cards
- **Dark Theme**: Matching dark blue theme with the application
- **Message Actions**: Copy, download, reply, and expand functionality
- **File Sharing**: Drag-and-drop file uploads with previews
- **Code Highlighting**: Automatic language detection and syntax highlighting
- **Member Management**: Comprehensive admin controls panel
- **Real-time Updates**: Live typing indicators and message delivery

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

### Chat Endpoints
- `GET /chat/groups` - List user's chat groups
- `GET /chat/create` - Create group form
- `POST /chat/create` - Create new chat group
- `GET /chat/join` - Join group form
- `POST /chat/join` - Join group with invite code
- `GET /chat/group/{group_id}` - Chat group interface
- `POST /chat/upload/{group_id}` - Upload files to chat
- `WebSocket /ws/chat/{group_id}` - Real-time chat connection

### Admin Endpoints
- `POST /cleanup` - Manual cleanup of old pastes
- `POST /chat/admin/set-acting-leader/{group_id}` - Set/remove acting leader
- `POST /chat/admin/add-member/{group_id}` - Add member by username
- `DELETE /chat/admin/remove-member/{group_id}` - Remove group member
- `POST /chat/admin/refresh-invite-code/{group_id}` - Refresh group invite code

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

### Groups Table
- `id` (Primary Key)
- `name` (Group name)
- `description` (Optional description)
- `created_at`
- `creator_id` (Foreign Key to Users)
- `is_private` (Boolean)
- `invite_code` (Unique invite code)
- `invite_code_updated_at` (Last refresh timestamp)

### Group Members Table
- `group_id` (Foreign Key to Groups)
- `user_id` (Foreign Key to Users)
- `joined_at`
- `is_admin` (Boolean)
- `is_acting_leader` (Boolean)

### Messages Table
- `id` (Primary Key)
- `content` (Message text, optional)
- `message_type` (text, code, file, system)
- `code_language` (For code messages)
- `file_path` (For file messages)
- `file_name` (Original filename)
- `created_at`
- `edited_at` (Optional)
- `sender_id` (Foreign Key to Users)
- `group_id` (Foreign Key to Groups)
- `reply_to_id` (Foreign Key to Messages, optional)

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

### Creating a Chat Group
1. Login to your account
2. Navigate to "Chat Groups" from dashboard
3. Click "Create New Group"
4. Enter group name and optional description
5. Share the invite code with others

### Joining a Chat Group
1. Get an invite code from a group admin
2. Click "Join Group" from chat section
3. Enter the invite code
4. Start chatting immediately

### Managing Group Members (Admin/Acting Leader)
1. Open the group chat interface
2. Use the admin controls panel on the right
3. Add members by username
4. Set acting leaders (admin only)
5. Remove members as needed
6. Refresh invite codes when necessary

### Sharing Files in Chat
1. Drag and drop files into the chat input area
2. Or click the upload button to select files
3. Files are shared instantly with all group members
4. Click on files to view or download

## 📝 Notes

- Anonymous pastes are supported but cannot be saved
- Files are stored in the `uploads/` directory organized by paste slug
- Chat files are stored in the `chat_uploads/` directory organized by group ID
- Database is automatically created on first run
- Image files display previews in both paste view and chat
- Text files can be viewed and copied using the in-browser editor
- Group invite codes automatically refresh every hour via background tasks
- WebSocket connections are authenticated using JWT tokens
- Chat messages support markdown-style formatting for code blocks
- Admin permissions cascade (group creators are automatically admins)
- Acting leaders have limited permissions (cannot remove admins or other acting leaders)

## 🛠️ Development

To run in development mode:
```bash
python -m uvicorn app.main:app --reload --port 8000
```

The `--reload` flag enables auto-restart on code changes.

### WebSocket Testing
The chat system uses WebSocket connections for real-time communication. For development:
- WebSocket endpoint: `ws://localhost:8000/ws/chat/{group_id}?token={jwt_token}`
- Authentication is handled via JWT tokens passed as query parameters
- Connection manager handles multiple concurrent connections per group

### Background Tasks
The application includes automated background tasks:
- Invite code refresh runs every hour
- Database cleanup can be scheduled
- File cleanup for orphaned uploads

## 🐳 Deployment

Multiple deployment options are available:

### Docker Deployment
```bash
docker-compose up -d
```

### AWS EC2 Deployment
See `EC2_DEPLOYMENT.md` for detailed instructions.

### Manual Deployment
See `DEPLOYMENT.md` for step-by-step deployment guide.

## 🔒 Security Features

- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: Secure authentication tokens with expiration
- **HTTP-only Cookies**: Prevent XSS attacks
- **WebSocket Authentication**: JWT-based WebSocket authentication
- **File Upload Validation**: Size, type, and path restrictions
- **SQL Injection Prevention**: SQLAlchemy ORM protection
- **Path Traversal Prevention**: Secure file serving
- **Role-Based Access Control**: Admin and acting leader permissions
- **Input Sanitization**: XSS prevention in chat messages

## ⚙️ Configuration

### Environment Variables
You can customize these settings using environment variables:

- `DATABASE_URL`: Database connection string (default: SQLite)
- `SECRET_KEY`: JWT secret key (change in production!)
- `MAX_FILES`: Maximum files per paste (default: 5)
- `MAX_FILE_SIZE_MB`: Maximum file size in MB (default: 10)
- `AUTO_DELETE_DAYS`: Days before auto-deletion (default: 5)

### Database
- Uses SQLite by default (`./data/pastes.db`)
- Can be easily changed to PostgreSQL or MySQL by updating `DATABASE_URL`
- Automatic migration support for schema changes

## 📄 License

This project is open source and available under the MIT License.
