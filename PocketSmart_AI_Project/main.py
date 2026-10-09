from fastapi import FastAPI, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
from pathlib import Path
from typing import Optional
import json, os, secrets

from database import init_db, create_user, authenticate_user, save_history, get_history
from gemini_utils import generate_home, generate_party, generate_jewelry

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

app = FastAPI(title="PocketSmart AI", version="1.0.0")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", secrets.token_urlsafe(32)),
    max_age=60 * 60 * 24 * 7
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.on_event("startup")
def startup():
    init_db()

def current_user(request: Request):
    return request.session.get("user")

def require_user(request: Request):
    user = current_user(request)
    if not user:
        return None
    return user

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="index.html",
    context={"user": current_user(request)}
)
    
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(
    request=request,
    name="register.html",
    context={"user": current_user(request)}
)
@app.post("/register")
async def register(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    if len(password) < 6:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "user": current_user(request),
                "error": "Password must contain at least 6 characters."
            }
        )

    try:
        clean_name = name.strip()
        clean_email = email.strip().lower()

        create_user(clean_name, clean_email, password)

    except ValueError as e:
        return templates.TemplateResponse(
            request=request,
            name="register.html",
            context={
                "user": current_user(request),
                "error": str(e)
            }
        )

    request.session["user"] = {
        "name": clean_name,
        "email": clean_email
    }

    return RedirectResponse("/dashboard", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"user": current_user(request)}
    )

@app.post("/login")
async def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...)
):
    user = authenticate_user(email.strip().lower(), password)

    if not user:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "user": current_user(request),
                "error": "Invalid email or password."
            }
        )

    request.session["user"] = user
    return RedirectResponse("/dashboard", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    user = require_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)

    history = get_history(user["email"], limit=6)

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "user": user,
            "history": history
        }
    )

@app.get("/home-planner", response_class=HTMLResponse)
async def home_planner(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="home_planner.html",
        context={"user": current_user(request)}
    )


@app.get("/party-planner", response_class=HTMLResponse)
async def party_planner(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="party_planner.html",
        context={"user": current_user(request)}
    )


@app.get("/jewelry-planner", response_class=HTMLResponse)
async def jewelry_planner(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="jewelry_planner.html",
        context={"user": current_user(request)}
    )

@app.post("/generate-home")
async def generate_home_route(request: Request):
    user = require_user(request)
    if not user:
        return JSONResponse({"error": "Please login first."}, status_code=401)
    data = await request.json()
    try:
        result = generate_home(data)
        save_history(user["email"], "Home", data, result)
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/generate-party")
async def generate_party_route(request: Request):
    user = require_user(request)
    if not user:
        return JSONResponse({"error": "Please login first."}, status_code=401)
    data = await request.json()
    try:
        result = generate_party(data)
        save_history(user["email"], "Party", data, result)
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/generate-jewelry")
async def generate_jewelry_route(
    request: Request,
    budget: float = Form(...),
    occasion: str = Form(...),
    style: str = Form(...),
    color: str = Form(""),
    image: Optional[UploadFile] = File(None)
):
    user = require_user(request)
    if not user:
        return JSONResponse({"error": "Please login first."}, status_code=401)

    image_bytes = None
    image_name = None
    if image and image.filename:
        image_bytes = await image.read()
        safe_name = f"{secrets.token_hex(8)}_{Path(image.filename).name}"
        target = UPLOAD_DIR / safe_name
        target.write_bytes(image_bytes)
        image_name = safe_name

    data = {
        "budget": budget,
        "occasion": occasion,
        "style": style,
        "color": color,
        "image_uploaded": bool(image_bytes)
    }
    try:
        result = generate_jewelry(data, image_bytes=image_bytes, image_mime=image.content_type if image else None)
        result["image_url"] = f"/uploads/{image_name}" if image_name else None
        save_history(user["email"], "Jewelry", data, result)
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/history", response_class=HTMLResponse)
async def history_page(request: Request):
    user = require_user(request)

    if not user:
        return RedirectResponse("/login", status_code=303)

    history = get_history(user["email"], limit=100)

    return templates.TemplateResponse(
        request=request,
        name="history.html",
        context={
            "user": user,
            "history": history
        }
    )

@app.get("/session-info")
async def session_info(request: Request):
    user = current_user(request)
    return {"logged_in": bool(user), "user": user}

@app.get("/session-data")
async def session_data(request: Request):
    user = require_user(request)
    if not user:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    return {"user": user, "history": get_history(user["email"], limit=20)}

@app.get("/recommendations-details")
async def recommendation_details(request: Request, category: str = "Home"):
    user = require_user(request)
    if not user:
        return JSONResponse({"error": "Not authenticated"}, status_code=401)
    history = get_history(user["email"], limit=1)
    if not history:
        return {"message": "No recommendations yet."}
    return history[0]

@app.get("/health")
async def health():
    return {"status": "ok", "service": "PocketSmart AI"}
