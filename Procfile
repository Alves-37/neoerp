web: sh -c "export PYTHONPATH=/app && python -m app.scripts.migrate_db && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
