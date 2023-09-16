from config import BASE_DIR

import os
import uvicorn
from api.router import stream_router
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

ROOT = os.path.dirname(__file__)

app = FastAPI()

app.mount("/static", StaticFiles(directory=BASE_DIR + "/static"), name="static")

app.include_router(stream_router)


def main():
    uvicorn.run(app="main:app", host='0.0.0.0',  port=8000, reload=True,
                # ssl_keyfile='./key.pem',
                # ssl_certfile='./cert.pem'
                )


if __name__ == '__main__':
    main()