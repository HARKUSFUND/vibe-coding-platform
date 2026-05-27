"""Database migrations utilities."""

import subprocess
from pathlib import Path
from loguru import logger


def run_migrations() -> bool:
    """Run Alembic migrations."""
    try:
        # Get the directory containing alembic.ini
        alembic_dir = Path(__file__).parent.parent.parent.parent
        alembic_ini = alembic_dir / "alembic.ini"

        if not alembic_ini.exists():
            logger.error("alembic.ini not found")
            return False

        # Run upgrade
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info("Migrations completed successfully")
            return True
        else:
            logger.error(f"Migration failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False


def create_migration(message: str) -> bool:
    """Create a new migration."""
    try:
        alembic_dir = Path(__file__).parent.parent.parent.parent

        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", message],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            logger.info(f"Migration created: {message}")
            return True
        else:
            logger.error(f"Migration creation failed: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Migration creation error: {e}")
        return False


def check_current_version() -> str:
    """Get current migration version."""
    try:
        alembic_dir = Path(__file__).parent.parent.parent.parent

        result = subprocess.run(
            ["alembic", "current"],
            cwd=alembic_dir,
            capture_output=True,
            text=True,
        )

        return result.stdout.strip() if result.returncode == 0 else "unknown"

    except Exception as e:
        logger.error(f"Version check error: {e}")
        return "error"
