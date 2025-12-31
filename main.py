"""
Entrypoint shim to make deployment platforms detect the app at repository root.
Imports the FastAPI `app` instance from the existing archive.api.main module.
"""
from archive.api.main import app
