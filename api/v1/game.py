from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from starlette.responses import StreamingResponse

from core.exceptions import FileNotSupportedException
from core.services import game
from core.utils import write_file

game_router = APIRouter(prefix="/game", tags=["Game"])


@game_router.post("/upload-source-song")
async def upload_source_song(lobby_id: int, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Загружает песню-оригинал игрока 1, которую будет слышать в перевёрнутом виде по кусочкам игрок 2
    """
    if file.content_type not in game.SUPPORTED_CONTENT_TYPE:
        raise FileNotSupportedException(
            status_code=400,
            detail=f"{file.content_type} is not supported! Expected content: {game.SUPPORTED_CONTENT_TYPE}",
        )
    lobby_dir = game.lobby_path(lobby_id)
    full_path = lobby_dir / game.SOURCE_AUDIO_NAME
    background_tasks.add_task(write_file, full_path, file)
    return {"path": full_path}


@game_router.get("/{lobby_id}/reverse-source-song")
async def reverse_source_song(lobby_id: int, background_tasks: BackgroundTasks = None, run_ffmpeg_task: bool = True):
    """
    Инфо о развёрнутой песне. Разворачивает оригинальную песню.
    Если run_ffmpeg_task=True, разбивает её на куски, равные core.services.game.PART_TIME секунд
    """
    if not background_tasks and run_ffmpeg_task:
        raise Exception(
            '"run_ffmpeg_task" is True, but no "background_tasks" was provided. '
            "If you need to run ffmpeg task, please provide BackgroundTasks instance"
        )
    lobby_dir = game.lobby_path(lobby_id)
    full_path = lobby_dir / game.SOURCE_REVERSED_AUDIO_NAME
    if run_ffmpeg_task:
        background_tasks.add_task(game.reversed_source_audio, lobby_id)
    return {"path": full_path, "parts_amount": game.parts_amount(game.source_audio(lobby_id))}


@game_router.get("/{lobby_id}/get-reversed-source-song")
async def get_reversed_source_song(lobby_id: int) -> StreamingResponse:
    """
    Разворачивает оригинальную песню и разбивает её на куски, равные core.services.game.PART_TIME секунд
    """
    # TODO: нужно не запускать таску на разворот песни а искать существующий файл
    #  и в случае если он не существует, бросать исключение
    reversed_audio = await reverse_source_song(lobby_id, run_ffmpeg_task=False)
    buffer = open(reversed_audio.get("path"), mode="rb")
    return StreamingResponse(buffer, media_type="audio/wav")


@game_router.get("/{lobby_id}/get-part-of-reversed-source-song/{part_num}")
async def get_part_of_reversed_source_song(lobby_id: int, part_num: int) -> StreamingResponse:
    """
    Возвращает кусок развёрнутого оригинала
    """
    if part_num < 0:
        raise ValueError('"part_num" can not be negative')

    part_audio = game.part_of_reversed_source_audio(lobby_id, part_num)
    buffer = open(part_audio, mode="rb")
    return StreamingResponse(buffer, media_type="audio/wav")


@game_router.post("/upload-player-part-song")
async def upload_player_part_song(
    lobby_id: int, background_tasks: BackgroundTasks, part_num: int | None = None, file: UploadFile = File(...)
):
    """
    Загружает кусок part_num песни игрока 2. Если part_num не указан явно, то берется i+1
    """
    part_num = part_num or game.next_player_part_num(lobby_id)
    if part_num < 0:
        raise ValueError('"part_num" can not be negative')
    if file.content_type not in game.SUPPORTED_CONTENT_TYPE:
        raise FileNotSupportedException(
            status_code=400,
            detail=f"{file.content_type} is not supported! Expected content: {game.SUPPORTED_CONTENT_TYPE}",
        )

    full_path = game.part_of_player_audio_path(lobby_id, part_num)
    background_tasks.add_task(write_file, full_path, file)
    return {"path": full_path}


@game_router.post("/finish-player-recording")
async def finish_player_recording(lobby_id: int, background_tasks: BackgroundTasks):
    """
    Запускает таску ffmpeg на склейку кусков и разворот файла
    """
    lobby_dir = game.lobby_path(lobby_id)
    full_path = lobby_dir / game.PLAYER_AUDIO_NAME
    background_tasks.add_task(game.concated_reversed_player_audio, lobby_id)
    return {"path": full_path}
