import random
import shutil
import os
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta


from fastapi import (FastAPI, Request, Form, Depends, HTTPException, status,
                     UploadFile, File, Response) # Added Response
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import text
from werkzeug.utils import secure_filename

from . import crud, schemas
from .database import SessionLocal, engine, create_db_and_tables
from .auth import (create_access_token, get_current_user_from_request, 
                   require_user, get_db)

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
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_from_request)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user_pastes = crud.get_user_pastes(db, current_user.id)
    saved_pastes = crud.get_user_saved_pastes(db, current_user.id)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": current_user,
        "user_pastes": user_pastes,
        "saved_pastes": saved_pastes
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