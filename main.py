from fastapi import FastAPI

from api.v1.game import game_router

app = FastAPI(title="Apogue Game")


app.include_router(game_router)