from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Shared limiter instance — init_app(app) called in app.py.
# storage_uri="memory://" is per-process; acceptable for a single-server
# demo. Swap for "redis://..." if you ever run multiple replicas.
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://",
    default_limits=[],
)
