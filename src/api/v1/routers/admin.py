from __future__ import annotations

import asyncio
import logging
import subprocess
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/admin",
    tags=["admin"]
)


class MigrateRequest(BaseModel):
    target_revision: Optional[str] = "head"


class MigrateResponse(BaseModel):
    success: bool
    message: str
    output: str
    error: Optional[str] = None


@router.post("/migrate/upgrade", response_model=MigrateResponse)
async def migrate_upgrade(request: MigrateRequest) -> MigrateResponse:
    """
    Execute Alembic database migration upgrade.

    Args:
        request: Migration request with optional target revision

    Returns:
        Migration result with success status, message and output

    Raises:
        HTTPException: If migration fails
    """
    try:
        logger.info(f"Starting migration upgrade to revision: {request.target_revision}")

        # Prepare alembic command
        cmd = ["alembic", "upgrade", request.target_revision]

        # Execute migration in subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd="."
        )

        stdout, stderr = await process.communicate()

        # Decode output
        stdout_str = stdout.decode() if stdout else ""
        stderr_str = stderr.decode() if stderr else ""

        if process.returncode == 0:
            logger.info(f"Migration completed successfully: {stdout_str}")
            return MigrateResponse(
                success=True,
                message=f"Migration upgrade to {request.target_revision} completed successfully",
                output=stdout_str,
                error=stderr_str if stderr_str else None
            )
        else:
            logger.error(f"Migration failed with code {process.returncode}: {stderr_str}")
            raise HTTPException(
                status_code=500,
                detail=f"Migration failed: {stderr_str or 'Unknown error'}"
            )

    except subprocess.SubprocessError as e:
        error_msg = f"Failed to execute migration command: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during migration: {str(e)}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)