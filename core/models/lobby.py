import random
from dataclasses import dataclass, field
from typing import ClassVar

from core.utils import StringEnum

NEED_PLAYERS = 2


class LobbyState(StringEnum):
    NotExists = "NotExists"
    AwaitingPlayers = "AwaitingPlayers"
    ReadyToPlay = "ReadyToPlay"
    GameStarted = "GameStarted"
    GameFinished = "GameFinished"


@dataclass(eq=False)
class Lobby:
    id: int
    state: LobbyState = LobbyState.NotExists
    players: list[str] = field(default_factory=lambda: [])
    leader: str | None = None

    MIN_ID: ClassVar[int] = 1_000
    MAX_ID: ClassVar[int] = 999_999

    @classmethod
    def random_id(cls) -> int:
        return random.randint(cls.MIN_ID, cls.MAX_ID)

    def can_start_game(self) -> bool:
        return self.state == LobbyState.ReadyToPlay

    def assign_random_leader(self):
        self.leader = random.choice(self.players) if self.players else None

    def __len__(self):
        return len(self.players)
