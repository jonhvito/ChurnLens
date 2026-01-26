#!/usr/bin/env python
"""Application entrypoint."""
from __future__ import annotations

from app import create_app, config

if __name__ == "__main__":
    app = create_app()
    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
