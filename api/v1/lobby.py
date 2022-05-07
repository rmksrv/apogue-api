from dataclasses import asdict

from fastapi import APIRouter

from core.exceptions import NoSuchLobby, LobbyOverflownException
from core.models.lobby import LobbyState
from core.services import lobby as lobby_service


lobby_router = APIRouter(prefix="/lobby", tags=["Lobby"])


@lobby_router.get("/{lobby_id}/lobby-info")
async def lobby_info(lobby_id: int):
    searched_lobby = lobby_service.lobby_by_id(lobby_id)
    return asdict(searched_lobby)


@lobby_router.post("/connect-to-lobby")
async def connect_to_lobby(lobby_id: int, username: str):
    searched_lobby = lobby_service.lobby_by_id(lobby_id)
    if searched_lobby.state == LobbyState.NotExists:
        raise NoSuchLobby(status_code=400, detail=f"Lobby {lobby_id} not exists")
    if searched_lobby.state != LobbyState.AwaitingPlayers:
        raise LobbyOverflownException(
            status_code=400,
            detail=f"Lobby {lobby_id} is not wait for new players. Actual state: {searched_lobby.state}",
        )
    lobby_service.add_player(searched_lobby, username)
    return asdict(searched_lobby)


@lobby_router.post("/create-new-lobby")
async def create_new_lobby(username: str):
    lobby = lobby_service.new_lobby()
    lobby_service.add_player(lobby, username)
    return asdict(lobby)


@lobby_router.post("/remove-player-from-lobby")
async def remove_player_from_lobby(lobby_id: int, username: str):
    searched_lobby = lobby_service.lobby_by_id(lobby_id)
    if searched_lobby.state == LobbyState.NotExists:
        raise NoSuchLobby(status_code=400, detail=f"Lobby {lobby_id} not exists")
    lobby_service.remove_player(searched_lobby, username)
    return asdict(searched_lobby)


@lobby_router.post("/start-game")
async def start_game(lobby_id: int):
    lobby = lobby_service.lobby_by_id(lobby_id)
    lobby_service.start_game(lobby)
