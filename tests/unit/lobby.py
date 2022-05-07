import copy
import uuid

import pytest

from api.v1 import lobby as lobby_api
from core.models.lobby import LobbyState, Lobby
from core import exceptions


@pytest.fixture(autouse=True)
def refresh_service():
    lobby_api.lobby_service.clear_lobbies()


@pytest.mark.parametrize(
    "players, exp_state",
    [
        (["foo"], LobbyState.AwaitingPlayers),
        (["foo", "bar"], LobbyState.ReadyToPlay),
    ],
)
@pytest.mark.anyio
async def test_lobby_info_hp(players: list[str], exp_state: LobbyState):
    _players = copy.copy(players)
    leader = _players.pop(0)
    new_lobby_info: dict = await lobby_api.create_new_lobby(leader)
    lobby_id = new_lobby_info.get("id")
    for p in _players:
        await lobby_api.connect_to_lobby(lobby_id, p)

    info = await lobby_api.lobby_info(lobby_id)
    assert info.get("state") == exp_state
    assert info.get("leader") == leader
    assert info.get("players") == players


@pytest.mark.anyio
async def test_create_new_lobby_hp():
    username = str(uuid.uuid4())
    new_lobby_info: dict = await lobby_api.create_new_lobby(username)
    assert new_lobby_info.get("state") == LobbyState.AwaitingPlayers
    assert username in new_lobby_info.get("players")
    assert new_lobby_info.get("leader") == username


@pytest.mark.anyio
async def test_connect_to_lobby_hp():
    leader = str(uuid.uuid4())
    new_lobby_info: dict = await lobby_api.create_new_lobby(leader)
    lobby_id = new_lobby_info.get("id")

    player = str(uuid.uuid4())
    lobby_info: dict = await lobby_api.connect_to_lobby(lobby_id, player)
    assert lobby_info.get("state") == LobbyState.ReadyToPlay
    assert len(lobby_info.get("players")) == 2
    assert player in lobby_info.get("players")
    assert lobby_info.get("leader") == leader


@pytest.mark.anyio
async def test_connect_to_not_existing_lobby():
    lobby_id = Lobby.random_id()
    player = str(uuid.uuid4())
    try:
        await lobby_api.connect_to_lobby(lobby_id, player)
    except exceptions.NoSuchLobby as e:
        assert e.status_code == 400
        assert e.detail == f"Lobby {lobby_id} not exists"


@pytest.mark.anyio
async def test_connect_to_overflown_lobby():
    leader = str(uuid.uuid4())
    new_lobby_info: dict = await lobby_api.create_new_lobby(leader)
    lobby_id = new_lobby_info.get("id")
    player1 = str(uuid.uuid4())
    await lobby_api.connect_to_lobby(lobby_id, player1)

    player2 = str(uuid.uuid4())
    try:
        await lobby_api.connect_to_lobby(lobby_id, player2)
    except exceptions.LobbyOverflownException as e:
        lobby_state = (await lobby_api.lobby_info(lobby_id)).get("state")
        assert e.status_code == 400
        assert e.detail == f"Lobby {lobby_id} is not wait for new players. Actual state: {lobby_state}"


@pytest.mark.parametrize(
    "players, exp_state",
    [
        (["foo"], LobbyState.NotExists),
        (["foo", "bar"], LobbyState.AwaitingPlayers),
    ],
)
@pytest.mark.anyio
async def test_remove_player_from_lobby(players: list[str], exp_state: LobbyState):
    _players = copy.copy(players)
    leader = _players.pop(0)
    new_lobby_info: dict = await lobby_api.create_new_lobby(leader)
    lobby_id = new_lobby_info.get("id")
    for p in _players:
        await lobby_api.connect_to_lobby(lobby_id, p)

    info = await lobby_api.remove_player_from_lobby(lobby_id, leader)
    assert info.get("state") == exp_state
    assert info.get("leader") != leader
    assert len(info.get("players")) == len(players) - 1
