import random
import shutil
import os
import json
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import (FastAPI, Request, Form, Depends, HTTPException, status,
                     UploadFile, File, Response, WebSocket, WebSocketDisconnect) # Added WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from werkzeug.utils import secure_filename
from pydantic import BaseModel

from . import crud, schemas
from .database import SessionLocal, engine, create_db_and_tables
from .auth import (create_access_token, get_current_user_from_request, 
                   require_user, get_db, get_current_user_from_token, get_user_from_token_string)
from .websocket_manager import manager
from .background_tasks import start_background_tasks

# Request models for admin endpoints
class SetActingLeaderRequest(BaseModel):
    user_id: int

class AddMemberRequest(BaseModel):
    username: str

class RemoveMemberRequest(BaseModel):
    user_id: int

# Chat file uploads directory
CHAT_UPLOADS_DIR = Path("chat_uploads")

# --- Constants ---
MAX_FILES = int(os.getenv("MAX_FILES", "5"))
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
UPLOADS_DIR = Path("uploads")
AUTO_DELETE_DAYS = int(os.getenv("AUTO_DELETE_DAYS", "5"))
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
# VVV NEW: Define which files can be viewed/edited in-browser VVV
EDITABLE_EXTENSIONS = {
    ".txt", ".md", ".json", ".xml", ".html", ".css", ".js", ".py", ".java",
    ".c", ".cpp", ".cs", ".go", ".rs", ".php", ".rb", ".pl", ".sh", ".sql"
}
# ^^^ END OF NEW ^^^
WORD_LIST = [
    "ant", "ape", "asp", "bat", "bee", "boa", "bug", "cat", "cod", "cow", "cub",
    "cup", "dog", "dug", "eel", "egg", "elk", "elf", "emu", "fly", "fog", "fox",
    "fur", "gap", "gas", "gem", "god", "gum", "hen", "hog", "ice", "ink", "jar",
    "jaw", "jet", "jug", "keg", "key", "kit", "koi", "lap", "leg", "lip", "log",
    "map", "mat", "mix", "mud", "mug", "nap", "net", "new", "nut", "oar", "oat",
    "oil", "owl", "pan", "paw", "peg", "pen", "pet", "pig", "pin", "pot", "pug",
    "pun", "ram", "rat", "red", "rib", "rig", "rim", "rod", "rug", "run", "rye",
    "sad", "sap", "saw", "sea", "sew", "sky", "sly", "sod", "son", "sow", "soy",
    "spy", "sun", "tag", "tan", "tap", "tar", "tea", "ten", "tin", "tip", "top",
    "toy", "tub", "tug", "van", "vet", "wag", "war", "was", "wax", "web", "wet",
    "wig", "win", "yak", "yam", "yap", "yen", "yet", "zip", "zoo"
]

# --- App Setup ---
create_db_and_tables()
app = FastAPI(title="Paste Shaver")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Create necessary directories
UPLOADS_DIR.mkdir(exist_ok=True)
CHAT_UPLOADS_DIR.mkdir(exist_ok=True)

# Start background tasks
@app.on_event("startup")
async def startup_event():
    start_background_tasks()

# --- Authentication Endpoints ---
@app.get("/login", response_class=HTMLResponse)
def login_form(
    request: Request, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    # Redirect if already logged in
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = crud.authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {
            "request": request,
            "error": "Incorrect username or password"
        })
    
    access_token_expires = timedelta(days=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=30*24*60*60)
    return response

@app.get("/signup", response_class=HTMLResponse)
def signup_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    # Redirect if already logged in
    if current_user:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def signup(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Validation
    if password != confirm_password:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Passwords do not match"
        })
    
    if len(password) < 6:
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Password must be at least 6 characters long"
        })
    
    # Check if user exists
    if crud.get_user_by_username(db, username):
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Username already exists"
        })
    
    if crud.get_user_by_email(db, email):
        return templates.TemplateResponse("signup.html", {
            "request": request,
            "error": "Email already registered"
        })
    
    # Create user
    user_create = schemas.UserCreate(username=username, email=email, password=password)
    user = crud.create_user(db, user_create)
    
    # Auto-login after signup
    access_token_expires = timedelta(days=30)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=30*24*60*60)
    return response

@app.get("/session-status")
def session_status(current_user = Depends(get_current_user_from_request)):
    """API endpoint to check current authentication status"""
    if current_user:
        return {
            "authenticated": True,
            "username": current_user.username,
            "user_id": current_user.id
        }
    return {"authenticated": False}

@app.get("/health")
def health_check():
    """Health check endpoint for Docker/monitoring"""
    try:
        # Test database connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@app.post("/logout")
def logout():
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="access_token")
    return response

# --- Dashboard ---
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(
    request: Request, 
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Handle search functionality - now searches globally
    if search and search.strip():
        # Global search through all pastes
        all_search_results = crud.search_all_pastes(db, search)
        # Still get user's personal pastes and saved pastes for the dashboard
        user_pastes = crud.search_user_pastes(db, current_user.id, search)
        saved_pastes = crud.search_saved_pastes(db, current_user.id, search)
    else:
        all_search_results = []
        user_pastes = crud.get_user_pastes(db, current_user.id)
        saved_pastes = crud.get_user_saved_pastes(db, current_user.id)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "user_pastes": user_pastes,
        "saved_pastes": saved_pastes,
        "all_search_results": all_search_results,
        "search_query": search or ""
    })

# --- Global Search Endpoint ---
@app.get("/search", response_class=HTMLResponse)
def global_search(
    request: Request,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Global search page for all pastes"""
    search_results = []
    if q and q.strip():
        search_results = crud.search_all_pastes(db, q, limit=100)
    
    return templates.TemplateResponse("search.html", {
        "request": request,
        "current_user": current_user,
        "search_results": search_results,
        "search_query": q or ""
    })

# --- Group Chat Endpoints ---
@app.get("/chat", response_class=HTMLResponse)
def chat_home(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Main chat page showing user's groups"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_groups = crud.get_user_groups(db, current_user.id)
    
    return templates.TemplateResponse("chat/home.html", {
        "request": request,
        "current_user": current_user,
        "groups": user_groups
    })

@app.get("/chat/group/{group_id}", response_class=HTMLResponse)
def chat_group(
    request: Request,
    group_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Individual group chat page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Check if user is member of the group
    if not crud.is_group_member(db, group_id, current_user.id):
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    
    group = crud.get_group_by_id(db, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    members = crud.get_group_members(db, group_id)
    messages = crud.get_group_messages(db, group_id, limit=50)
    messages.reverse()  # Show oldest first
    
    # Check current user's permissions
    user_is_admin = crud.is_group_admin(db, group_id, current_user.id)
    user_is_acting_leader = crud.is_acting_leader(db, group_id, current_user.id)
    
    # Get user's token for WebSocket authentication
    token = request.cookies.get("access_token")
    
    return templates.TemplateResponse("chat/group.html", {
        "request": request,
        "current_user": current_user,
        "group": group,
        "members": members,
        "messages": messages,
        "auth_token": token,
        "user_is_admin": user_is_admin,
        "user_is_acting_leader": user_is_acting_leader
    })

@app.get("/chat/create", response_class=HTMLResponse)
def chat_create_page(
    request: Request,
    current_user = Depends(get_current_user_from_request)
):
    """Create group page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("chat/create.html", {
        "request": request,
        "current_user": current_user
    })

@app.get("/chat/join", response_class=HTMLResponse)
def chat_join_page(
    request: Request,
    current_user = Depends(get_current_user_from_request)
):
    """Join group page"""
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse("chat/join.html", {
        "request": request,
        "current_user": current_user
    })

@app.post("/chat/create-group")
def create_group(
    name: str = Form(...),
    description: str = Form(""),
    is_private: bool = Form(False),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Create a new group"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    group_data = schemas.GroupCreate(
        name=name,
        description=description,
        is_private=is_private
    )
    
    group = crud.create_group(db, group_data, current_user.id)
    return RedirectResponse(url=f"/chat/group/{group.id}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/chat/join-group")
def join_group(
    invite_code: str = Form(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Join a group using invite code"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    group = crud.get_group_by_invite_code(db, invite_code)
    if not group:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    success = crud.join_group(db, group.id, current_user.id)
    if not success:
        raise HTTPException(status_code=400, detail="Already a member of this group")
    
    return RedirectResponse(url=f"/chat/group/{group.id}", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/chat/leave-group/{group_id}")
def leave_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Leave a group"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    crud.leave_group(db, group_id, current_user.id)
    return RedirectResponse(url="/chat", status_code=status.HTTP_303_SEE_OTHER)

@app.post("/chat/admin/set-acting-leader/{group_id}")
def set_acting_leader(
    group_id: int,
    request: SetActingLeaderRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Set or remove acting leader status (admin only)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = request.user_id
    
    # Check if current user is admin of the group
    if not crud.is_group_admin(db, group_id, current_user.id):
        raise HTTPException(status_code=403, detail="Only group admins can manage acting leaders")
    
    # Check if target user is a member
    if not crud.is_group_member(db, group_id, user_id):
        raise HTTPException(status_code=404, detail="User is not a member of this group")
    
    # Toggle acting leader status
    current_status = crud.is_acting_leader(db, group_id, user_id)
    new_status = not current_status
    crud.set_acting_leader(db, group_id, user_id, new_status)
    return {"success": True, "message": f"Acting leader status {'granted' if new_status else 'revoked'}"}

@app.post("/chat/admin/add-member/{group_id}")
def add_member_by_username(
    group_id: int,
    request: AddMemberRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Add a member by username (admin or acting leader only)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    username = request.username
    
    # Check if current user is admin or acting leader
    is_admin = crud.is_group_admin(db, group_id, current_user.id)
    is_acting_leader = crud.is_acting_leader(db, group_id, current_user.id)
    
    if not (is_admin or is_acting_leader):
        raise HTTPException(status_code=403, detail="Only group admins or acting leaders can add members")
    
    result = crud.add_member_by_username(db, group_id, username)
    
    if result is None:
        raise HTTPException(status_code=404, detail="User not found")
    elif result is False:
        raise HTTPException(status_code=400, detail="User is already a member")
    
    return {"success": True, "message": f"User {username} added to the group", "user": {"id": result.id, "username": result.username}}

@app.delete("/chat/admin/remove-member/{group_id}")
def remove_member(
    group_id: int,
    request: RemoveMemberRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Remove a member from the group (admin or acting leader only)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = request.user_id
    
    # Check if current user is admin or acting leader
    is_admin = crud.is_group_admin(db, group_id, current_user.id)
    is_acting_leader = crud.is_acting_leader(db, group_id, current_user.id)
    
    if not (is_admin or is_acting_leader):
        raise HTTPException(status_code=403, detail="Only group admins or acting leaders can remove members")
    
    # Prevent removing group creator
    group = crud.get_group_by_id(db, group_id)
    if user_id == group.creator_id:
        raise HTTPException(status_code=400, detail="Cannot remove group creator")
    
    # Prevent acting leaders from removing admins
    if is_acting_leader and not is_admin and crud.is_group_admin(db, group_id, user_id):
        raise HTTPException(status_code=403, detail="Acting leaders cannot remove group admins")
    
    if not crud.is_group_member(db, group_id, user_id):
        raise HTTPException(status_code=404, detail="User is not a member of this group")
    
    crud.remove_member_from_group(db, group_id, user_id)
    return {"success": True, "message": "Member removed from the group"}

@app.post("/chat/admin/refresh-invite-code/{group_id}")
def refresh_invite_code(
    group_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Manually refresh the group invite code (admin only)"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if current user is admin of the group
    if not crud.is_group_admin(db, group_id, current_user.id):
        raise HTTPException(status_code=403, detail="Only group admins can refresh invite codes")
    
    group = crud.refresh_group_invite_code(db, group_id)
    return {"success": True, "new_invite_code": group.invite_code, "message": "Invite code refreshed"}

@app.post("/chat/upload-file/{group_id}")
async def upload_chat_file(
    group_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Upload a file to group chat"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if user is member of the group
    if not crud.is_group_member(db, group_id, current_user.id):
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    
    # File size check
    if file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE_MB}MB limit")
    
    # Create unique filename
    file_id = str(uuid.uuid4())
    safe_filename = secure_filename(file.filename)
    if not safe_filename:
        safe_filename = f"file_{file_id}"
    
    # Save file
    group_dir = CHAT_UPLOADS_DIR / str(group_id)
    group_dir.mkdir(exist_ok=True)
    file_path = group_dir / f"{file_id}_{safe_filename}"
    
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    finally:
        file.file.close()
    
    # Create file message
    file_message = schemas.MessageFile(
        file_name=safe_filename,
        file_path=str(file_path),
        group_id=group_id
    )
    
    message = crud.create_file_message(db, file_message, current_user.id)
    
    # Broadcast to group members
    message_data = {
        "id": message.id,
        "content": None,
        "message_type": "file",
        "file_name": safe_filename,
        "sender": {"id": current_user.id, "username": current_user.username},
        "created_at": message.created_at.isoformat(),
        "reply_to": None
    }
    
    await manager.send_message_to_group(group_id, message_data)
    
    return {"success": True, "message_id": message.id}

@app.get("/chat/download/{group_id}/{message_id}")
async def download_chat_file(
    group_id: int,
    message_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Download a file from chat"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if user is member of the group
    if not crud.is_group_member(db, group_id, current_user.id):
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    
    message = crud.get_message_by_id(db, message_id)
    if not message or message.message_type != "file" or message.group_id != group_id:
        raise HTTPException(status_code=404, detail="File not found")
    
    file_path = Path(message.file_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(file_path, filename=message.file_name)

@app.get("/chat/messages/{group_id}")
async def get_chat_messages(
    group_id: int,
    before: Optional[int] = None,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    """Get chat messages for infinite scroll"""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if user is member of the group
    if not crud.is_group_member(db, group_id, current_user.id):
        raise HTTPException(status_code=403, detail="You are not a member of this group")
    
    messages = crud.get_group_messages_paginated(db, group_id, before_id=before, limit=limit)
    
    # Format messages for JSON response
    formatted_messages = []
    for message in messages:
        reply_to = None
        if message.reply_to_id:
            reply_msg = crud.get_message_by_id(db, message.reply_to_id)
            if reply_msg:
                reply_to = {
                    "id": reply_msg.id,
                    "content": reply_msg.content,
                    "file_name": reply_msg.file_name,
                    "sender": {"username": reply_msg.sender.username}
                }
        
        formatted_message = {
            "id": message.id,
            "content": message.content,
            "message_type": message.message_type,
            "code_language": message.code_language,
            "file_name": message.file_name,
            "sender": {"id": message.sender.id, "username": message.sender.username},
            "created_at": message.created_at.isoformat(),
            "reply_to": reply_to
        }
        formatted_messages.append(formatted_message)
    
    return {"messages": formatted_messages}

# WebSocket endpoint for real-time chat
@app.websocket("/ws/chat/{group_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    group_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time chat"""
    # Authenticate user
    user = get_user_from_token_string(token, db)
    if not user:
        await websocket.close(code=4001)
        return
    
    # Check if user is member of the group
    if not crud.is_group_member(db, group_id, user.id):
        await websocket.close(code=4003)
        return
    
    # Connect to chat
    await manager.connect(websocket, group_id, user.id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data["type"] == "message":
                # Create new message
                content = message_data.get("content", "").strip()
                message_type = message_data.get("message_type", "text")
                code_language = message_data.get("code_language")
                reply_to_id = message_data.get("reply_to_id")
                
                if content:
                    message_create = schemas.MessageCreate(
                        content=content,
                        message_type=message_type,
                        code_language=code_language,
                        group_id=group_id,
                        reply_to_id=reply_to_id
                    )
                    
                    message = crud.create_message(db, message_create, user.id)
                    
                    # Prepare message data for broadcast
                    reply_to = None
                    if message.reply_to_id:
                        reply_msg = crud.get_message_by_id(db, message.reply_to_id)
                        if reply_msg:
                            reply_to = {
                                "id": reply_msg.id,
                                "content": reply_msg.content,
                                "sender": {"username": reply_msg.sender.username}
                            }
                    
                    broadcast_data = {
                        "id": message.id,
                        "content": message.content,
                        "message_type": message.message_type,
                        "code_language": message.code_language,
                        "sender": {"id": user.id, "username": user.username},
                        "created_at": message.created_at.isoformat(),
                        "reply_to": reply_to
                    }
                    
                    await manager.send_message_to_group(group_id, broadcast_data)
            
            elif message_data["type"] == "typing":
                is_typing = message_data.get("is_typing", False)
                await manager.handle_typing(group_id, user.id, is_typing)
                
    except WebSocketDisconnect:
        manager.disconnect(group_id, user.id)
        await manager.broadcast_to_group(group_id, {
            "type": "user_left",
            "user_id": user.id,
            "timestamp": datetime.utcnow().isoformat()
        })

# --- Save/Unsave Paste ---
@app.post("/save-paste/{paste_id}")
def toggle_save_paste(
    paste_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if paste exists
    paste = db.query(crud.models.Paste).filter(crud.models.Paste.id == paste_id).first()
    if not paste:
        raise HTTPException(status_code=404, detail="Paste not found")
    
    # Toggle save status
    if crud.is_paste_saved_by_user(db, current_user.id, paste_id):
        crud.unsave_paste(db, current_user.id, paste_id)
        return {"saved": False}
    else:
        crud.save_paste(db, current_user.id, paste_id)
        return {"saved": True}

# --- API Endpoints ---
@app.get("/", response_class=HTMLResponse)
def show_create_form(request: Request, current_user = Depends(get_current_user_from_request)):
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "max_files": MAX_FILES, 
        "max_size": MAX_FILE_SIZE_MB,
        "current_user": current_user
    })

@app.post("/create", response_class=RedirectResponse)
async def create_paste_entry(
    db: Session = Depends(get_db),
    content: Optional[str] = Form(None),
    files: List[UploadFile] = File(...),
    current_user = Depends(get_current_user_from_request)
):
    upload_files = [file for file in files if file.filename]
    if not content and not upload_files:
        raise HTTPException(status_code=400, detail="Cannot create an empty paste with no files.")
    if len(upload_files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Cannot upload more than {MAX_FILES} files.")
    while True:
        slug = "-".join(random.sample(WORD_LIST, 3))
        if not crud.get_paste_by_slug(db, slug=slug):
            break
    saved_filenames = []
    if upload_files:
        paste_upload_dir = UPLOADS_DIR / slug
        paste_upload_dir.mkdir(parents=True, exist_ok=True)
        for file in upload_files:
            if file.size > MAX_FILE_SIZE_BYTES:
                shutil.rmtree(paste_upload_dir)
                raise HTTPException(status_code=413, detail=f"File '{file.filename}' exceeds {MAX_FILE_SIZE_MB}MB limit.")
            safe_filename = secure_filename(file.filename)
            if not safe_filename:
                safe_filename = f"unnamed_file_{random.randint(1000, 9999)}"
            file_path = paste_upload_dir / safe_filename
            try:
                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                saved_filenames.append(safe_filename)
            finally:
                file.file.close()
    filenames_str = ",".join(saved_filenames) if saved_filenames else None
    user_id = current_user.id if current_user else None
    paste_data = schemas.PasteCreate(slug=slug, content=content, filenames=filenames_str, user_id=user_id)
    crud.create_paste(db=db, paste=paste_data)
    return RedirectResponse(url=f"/{slug}", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/{slug}", response_class=HTMLResponse)
def view_paste(
    request: Request, 
    slug: str, 
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    db_paste = crud.get_paste_by_slug(db, slug=slug)
    if db_paste is None:
        raise HTTPException(status_code=404, detail="Paste not found")
    
    files_data = []
    if db_paste.filenames:
        for filename in db_paste.filenames.split(','):
            file_extension = Path(filename).suffix.lower()
            files_data.append({
                "name": filename,
                "is_image": file_extension in IMAGE_EXTENSIONS,
                "is_editable": file_extension in EDITABLE_EXTENSIONS # Pass this to the template
            })
    
    # Check if current user has saved this paste
    is_saved = False
    if current_user:
        is_saved = crud.is_paste_saved_by_user(db, current_user.id, db_paste.id)
    
    return templates.TemplateResponse("paste.html", {
        "request": request, 
        "paste": db_paste, 
        "files_data": files_data,
        "current_user": current_user,
        "is_saved": is_saved
    })

# VVV NEW ENDPOINT TO SERVE RAW FILE CONTENT FOR THE EDITOR VVV
@app.get("/content/{slug}/{filename}")
async def get_file_content(slug: str, filename: str):
    """Securely serves the raw text content of a file."""
    # Basic security check to prevent path traversal
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = UPLOADS_DIR / slug / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")

    # Ensure it's an editable file type before reading as text
    if Path(filename).suffix.lower() not in EDITABLE_EXTENSIONS:
        raise HTTPException(status_code=403, detail="File type is not viewable as text.")

    try:
        content = file_path.read_text(encoding="utf-8")
        return Response(content=content, media_type="text/plain")
    except Exception:
        # Fallback for non-utf8 files
        raise HTTPException(status_code=500, detail="Could not read file content.")
# ^^^ END OF NEW ENDPOINT ^^^

@app.get("/raw/{slug}")
def download_paste(slug: str, db: Session = Depends(get_db)):
    db_paste = crud.get_paste_by_slug(db, slug=slug)
    if db_paste is None or not db_paste.content:
        raise HTTPException(status_code=404, detail="Paste or content not found")
    return Response(content=db_paste.content, media_type="text/plain", headers={"Content-Disposition": f"attachment; filename={slug}.txt"})

@app.get("/uploads/{slug}/{filename}")
async def serve_upload(slug: str, filename: str):
    if ".." in filename or "/" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    file_path = UPLOADS_DIR / slug / filename
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found.")
    return FileResponse(file_path, filename=filename)

# Auto-cleanup endpoint (can be called by cron job or scheduled task)
@app.post("/cleanup")
def cleanup_old_pastes(db: Session = Depends(get_db)):
    """Delete pastes older than configured days"""
    deleted_count = crud.delete_old_pastes(db, days=AUTO_DELETE_DAYS)
    return {"deleted": deleted_count, "message": f"Cleaned up {deleted_count} old pastes"}

# Startup event to run cleanup
@app.on_event("startup")
async def startup_event():
    """Run cleanup on startup"""
    db = SessionLocal()
    try:
        deleted_count = crud.delete_old_pastes(db, days=AUTO_DELETE_DAYS)
        print(f"Startup cleanup: deleted {deleted_count} old pastes")
    except Exception as e:
        print(f"Startup cleanup error: {e}")
    finally:
        db.close()
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)