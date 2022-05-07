from fastapi import FastAPI

from api.v1.game import game_router
from api.v1.lobby import lobby_router

app = FastAPI(title="Apogue Game")


app.include_router(game_router)
app.include_router(lobby_router)
