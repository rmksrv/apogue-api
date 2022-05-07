from core.exceptions import NoSuchPlayerInLobby, LobbyOverflownException, NotEnoughPlayersInLobbyException
from core.models.lobby import Lobby, NEED_PLAYERS, LobbyState

_lobbies: set[Lobby] = set()


def _busy_lobby_ids() -> set[int]:
    return {lobby.id for lobby in _lobbies}


def lobby_by_id(lobby_id: int) -> Lobby:
    for lobby in _lobbies:
        if lobby.id == lobby_id:
            return lobby
    else:
        return Lobby(lobby_id, state=LobbyState.NotExists)


def new_lobby() -> Lobby:
    randint = Lobby.random_id()
    if randint in _busy_lobby_ids():
        return new_lobby()
    _new_lobby = Lobby(id=randint)
    _lobbies.add(_new_lobby)
    return _new_lobby


def add_player(lobby: Lobby, player: str):
    if len(lobby) >= NEED_PLAYERS:
        raise LobbyOverflownException(status_code=400, detail="Lobby is full")
    lobby.players.append(player)

    if not lobby.leader:
        lobby.state = LobbyState.AwaitingPlayers
        lobby.assign_random_leader()

    if len(lobby) == NEED_PLAYERS:
        lobby.state = LobbyState.ReadyToPlay


def remove_player(lobby: Lobby, player: str):
    if player not in lobby.players:
        raise NoSuchPlayerInLobby(status_code=400, detail=f'No player "{player}" in lobby {lobby.id}')
    lobby.players.remove(player)
    lobby.state = LobbyState.AwaitingPlayers

    if lobby.leader == player:
        lobby.assign_random_leader()

    if len(lobby) <= 0:
        lobby.state = LobbyState.NotExists
        _lobbies.remove(lobby)
        del lobby


def clear_lobbies():
    _lobbies.clear()


def start_game(lobby: Lobby):
    if lobby.state != LobbyState.ReadyToPlay:
        raise NotEnoughPlayersInLobbyException(
            status_code=400,
            detail=f"Not enough players in lobby to start game. Waiting for {NEED_PLAYERS - len(lobby.players)}",
        )
    lobby.state = LobbyState.GameStarted
    # TODO: а чё делать дальше-то, если я хочу каждому игроку отдать разный ответ?
