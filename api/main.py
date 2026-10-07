"""Run from the project root: uv run uvicorn api.main:app."""
import os
from pathlib import Path
from speecheval.service import create_app

app = create_app(Path(os.environ.get('SPEECHEVAL_ROOT', Path.cwd())))
