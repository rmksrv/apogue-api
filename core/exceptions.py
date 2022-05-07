from fastapi import HTTPException


class FileNotSupportedException(HTTPException):
    pass


class FileNotFoundException(HTTPException):
    pass


class NoFilesToProcessException(HTTPException):
    pass


class LobbyIsEmptyException(HTTPException):
    pass


class LobbyOverflownException(HTTPException):
    pass


class NotEnoughPlayersInLobbyException(HTTPException):
    pass


class NoSuchLobby(HTTPException):
    pass


class NoSuchPlayerInLobby(HTTPException):
    pass
