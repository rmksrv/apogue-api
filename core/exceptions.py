from fastapi import HTTPException


class FileNotSupportedException(HTTPException):
    pass


class FileNotFoundException(HTTPException):
    pass


class NoFilesToProcessException(HTTPException):
    pass
