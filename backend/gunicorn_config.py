import os

workers = 4
bind = f"0.0.0.0:{os.environ.get('PORT', '7860')}"
timeout = 300
accesslog = "-"
errorlog = "-"
loglevel = "info"


def post_worker_init(worker):
    """Pre-load all expensive resources after each worker forks so the first
    real request pays no cold-start cost."""
    try:
        from services.nlp import preprocess
        preprocess("warmup")
    except Exception:
        pass
    try:
        from services.tools.search_tool import search_fragrance_db
        search_fragrance_db("warmup")
    except Exception:
        pass
