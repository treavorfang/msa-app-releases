from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from api.routes import router

app = FastAPI(title="MSA Mobile API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

# Add cache control middleware for static files
from fastapi import Request
@app.middleware("http")
async def add_cache_control_header(request: Request, call_next):
    response = await call_next(request)
    # Never cache index.html or the root to ensure version updates are seen
    path = request.url.path
    if path.endswith("index.html") or path == "/static/" or path == "/" or path == "/static":
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "MSA API is running"}

# Mount photos directory
photo_dir = os.path.join(os.getcwd(), "User_Data", "Ticket_Photos")
if os.path.exists(photo_dir):
    app.mount("/photos", StaticFiles(directory=photo_dir), name="photos")

# Mount mobile UI
api_dir = os.path.dirname(os.path.abspath(__file__))
ui_dir = os.path.join(os.path.dirname(api_dir), "ui_mobile")
if os.path.exists(ui_dir):
    app.mount("/static", StaticFiles(directory=ui_dir), name="static")
    
    from fastapi.responses import RedirectResponse
    @app.get("/")
    async def root():
        return RedirectResponse(url="/static/index.html")

