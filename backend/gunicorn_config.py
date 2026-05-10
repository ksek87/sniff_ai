workers = 2
bind = "0.0.0.0:7860"
timeout = 300
accesslog = "-"
errorlog = "-"
loglevel = "info"


def post_worker_init(worker):
    """Load the ChromaDB HNSWLIB index after each worker forks so the first
    real request doesn't pay the 10-30s cold-start cost."""
    try:
        from services.tools.search_tool import search_fragrance_db
        search_fragrance_db("warmup")
    except Exception:
        pass
