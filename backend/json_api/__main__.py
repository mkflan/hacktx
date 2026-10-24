"""Local dev server: python -m json_api (run from backend/)."""

import logging
from pathlib import Path

from dotenv import load_dotenv

from .config import Settings
from .main import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    for name in ("env.txt", ".env"):
        load_dotenv(REPO_ROOT / name, override=False)
    logging.basicConfig(level=logging.INFO)
    settings = Settings.from_env()
    app = create_app(settings=settings)
    app.run(host=settings.host, port=settings.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
