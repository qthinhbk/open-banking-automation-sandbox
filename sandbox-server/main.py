import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routes import auth, accounts, transfers, fineract
import os

app = FastAPI(
    title="Apex Bank Sandbox",
    description="Mock Sandbox for Open Banking Automation & Reverse Engineering Lab",
    version="1.0.0"
)

# Wire up route modules
app.include_router(auth.router)
app.include_router(accounts.router)
app.include_router(transfers.router)
app.include_router(fineract.router)

# Mount templates directory
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

@app.get("/", response_class=HTMLResponse)
def get_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

if __name__ == "__main__":
    # Start the server locally
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
