import json
import logging
import multiprocessing
import os

from src.utils.logger import ColoredFormatter, _level_from_string

workers_per_core_str = os.getenv("WORKERS_PER_CORE", "1")
max_workers_str = os.getenv("MAX_WORKERS", "10")
use_max_workers = None

if max_workers_str:
    use_max_workers = int(max_workers_str)

web_concurrency_str = os.getenv("WEB_CONCURRENCY", None)
host = os.getenv("HOST", "0.0.0.0")
port = os.getenv("PORT", "8000")
bind_env = os.getenv("BIND", None)
use_loglevel = os.getenv("LOG_LEVEL", "info")

# Configure Gunicorn logger with colored output
gunicorn_logger = logging.getLogger("gunicorn")
if not gunicorn_logger.handlers:
    lvl = _level_from_string(use_loglevel)
    gunicorn_logger.setLevel(lvl)
    handler = logging.StreamHandler()
    handler.setLevel(lvl)
    handler.setFormatter(
        ColoredFormatter(
            fmt="[GUNICORN] %(levelname)s %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    gunicorn_logger.addHandler(handler)

# Configure access and error loggers
access_logger = logging.getLogger("gunicorn.access")
if not access_logger.handlers:
    access_logger.setLevel(logging.INFO)
    access_handler = logging.StreamHandler()
    access_handler.setFormatter(
        ColoredFormatter(
            fmt="[ACCESS] %(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )
    access_logger.addHandler(access_handler)

error_logger = logging.getLogger("gunicorn.error")
if not error_logger.handlers:
    error_logger.setLevel(_level_from_string(use_loglevel))
    error_handler = logging.StreamHandler()
    error_handler.setFormatter(
        ColoredFormatter(
            fmt="[ERROR] %(levelname)s %(asctime)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    error_logger.addHandler(error_handler)

if bind_env:
    use_bind = bind_env
else:
    use_bind = f"{host}:{port}"

cores = multiprocessing.cpu_count()
workers_per_core = float(workers_per_core_str)
default_web_concurrency = workers_per_core * cores

if web_concurrency_str:
    web_concurrency = int(web_concurrency_str)
    assert web_concurrency > 0
else:
    web_concurrency = max(int(default_web_concurrency), 2)
    if use_max_workers:
        web_concurrency = min(web_concurrency, use_max_workers)

accesslog_var = os.getenv("ACCESS_LOG", "-")
use_accesslog = accesslog_var or None
errorlog_var = os.getenv("ERROR_LOG", "-")
use_errorlog = errorlog_var or None
graceful_timeout_str = os.getenv("GRACEFUL_TIMEOUT", "60")
timeout_str = os.getenv("TIMEOUT", "60")
keepalive_str = os.getenv("KEEP_ALIVE", "5")

# Gunicorn config variables
worker_class = "uvicorn.workers.UvicornWorker"
loglevel = use_loglevel
workers = web_concurrency
bind = use_bind
errorlog = use_errorlog
worker_tmp_dir = "/dev/shm"
accesslog = use_accesslog
graceful_timeout = int(graceful_timeout_str)
timeout = int(timeout_str)
keepalive = int(keepalive_str)

# For debugging and testing
log_data = {
    "loglevel": loglevel,
    "workers": workers,
    "bind": bind,
    "graceful_timeout": graceful_timeout,
    "timeout": timeout,
    "keepalive": keepalive,
    "errorlog": errorlog,
    "accesslog": accesslog,
    # Additional, non-gunicorn variables
    "workers_per_core": workers_per_core,
    "use_max_workers": use_max_workers,
    "host": host,
    "port": port,
}

print(json.dumps(log_data))