from quart import Quart
from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio
from app import app

if __name__ == "__main__":
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    asyncio.run(serve(app, config))
