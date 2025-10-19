import time
from typing import Any, Callable, TypeVar, Dict
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.utils.logger import logger
from src.auth.routes.auth import router as auth_router
from src.todo.routes.todo import router as todo_router
from src.utils.reminder_scheduler import start_reminder_scheduler


description = """
TODO API
"""

log = logger()

app = FastAPI(
    title="TODO API",
    description=description,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=settings.root_path,
)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=["*"],
)

@app.get("/", tags=["Health"])
async def health_check() -> Dict[str, str]:
    return {"status": "ok", "message": "Todo API is running"}

# NEW: Start reminder scheduler on app startup
@app.on_event("startup")
async def startup_event():
    log.info("Starting Todo API...")
    start_reminder_scheduler()
    log.info("Reminder scheduler initialized")


@app.on_event("shutdown")
async def shutdown_event():
    log.info("Shutting down Todo API...")

app.include_router(auth_router)
app.include_router(todo_router)


F = TypeVar("F", bound=Callable[..., Any])


@app.middleware("http")
async def process_time_log_middleware(
    request: Request, call_next: Callable[[Request], Any]
) -> Response:
    start_time = time.time()
    response: Response = await call_next(request)
    process_time = str(round(time.time() - start_time, 3))
    response.headers["X-Process-Time"] = process_time
    log.info(
        "Method=%s Path=%s StatusCode=%s ProcessTime=%s",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )
    return response


# include routes
# app.include_router(create_todo_router)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level="debug",
        reload=True,
    )