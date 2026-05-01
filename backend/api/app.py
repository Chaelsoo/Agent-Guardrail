from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from ..config import settings
from .routes import router

DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


def create_app() -> FastAPI:
    app = FastAPI(title="Aegis", docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, prefix="/v1")

    if DIST.exists():
        app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="assets")

    @app.get("/dashboard")
    @app.get("/")
    def serve_dashboard():
        return FileResponse(str(DIST / "index.html"))

    @app.on_event("startup")
    async def startup():
        from ..core.classifier import classifier
        from ..core.embedder import embedder
        from ..core.toolcall_verifier import toolcall_verifier
        print("[Aegis] Loading classifier (qualifire/prompt-injection-sentinel)...")
        classifier.load()
        print("[Aegis] Loading embedder (all-MiniLM-L6-v2)...")
        embedder.load()
        print("[Aegis] Loading tool call verifier (llm-semantic-router/toolcall-verifier)...")
        toolcall_verifier.load()
        print("[Aegis] All models ready")
        print_startup_summary()

    return app


app = create_app()


def print_startup_summary() -> None:
    print(f"[Aegis] threshold:   {settings.aegis_threshold}")
    print(f"[Aegis] ready:       http://127.0.0.1:8765/")
