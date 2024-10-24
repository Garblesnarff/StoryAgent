from app import app
import asyncio
from hypercorn.config import Config
from hypercorn.asyncio import serve

if __name__ == "__main__":
    config = Config()
    config.bind = ["0.0.0.0:5000"]
    asyncio.run(serve(app, config))
