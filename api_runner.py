import os
import uvicorn
from src.api.core.configs import settings


def run_api():
    if settings.env == "prod":
        workers = settings.workers or (os.cpu_count() * 2 + 1)
        os.execvp("gunicorn", [
            "gunicorn",
            "src:fastapi_app",
            "--workers", str(workers),
            "--worker-class", "uvicorn.workers.UvicornWorker",
            "--bind", f"{settings.app_host}:{settings.app_port}",
        ])
    else:
        uvicorn.run("src:fastapi_app",
                    host=settings.app_host,
                    port=settings.app_port,
                    reload=settings.is_dev,
                    log_config=None)


if __name__=="__main__":
    run_api()
