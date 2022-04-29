import math
from typing import Iterable

import ffmpeg
from pathlib import Path

from core.exceptions import FileNotFoundException, NoFilesToProcessException
from core.utils import ffmpeg_segment

SUPPORTED_CONTENT_TYPE = ("audio/wav", "audio/x-wav")
SOURCE_FILE_NAME = "source"
PLAYER_FILE_NAME = "player"
REVERSED_SUFFIX = "reversed"
PART_SUFFIX = "part"
PART_TIME = 5

MEDIA_DIR = Path(".") / "media"
SOURCE_AUDIO_NAME = f"{SOURCE_FILE_NAME}.wav"
PLAYER_AUDIO_NAME = f"{PLAYER_FILE_NAME}.wav"
SOURCE_REVERSED_AUDIO_NAME = f"{SOURCE_FILE_NAME}_{REVERSED_SUFFIX}.wav"
PLAYER_REVERSED_AUDIO_NAME = f"{PLAYER_FILE_NAME}_{REVERSED_SUFFIX}.wav"
SOURCE_REVERSED_PARTED_AUDIO_TEMPLATE = f"{SOURCE_FILE_NAME}_{REVERSED_SUFFIX}_{PART_SUFFIX}_{{}}.wav"
PLAYER_REVERSED_PARTED_AUDIO_TEMPLATE = f"{PLAYER_FILE_NAME}_{REVERSED_SUFFIX}_{PART_SUFFIX}_{{}}.wav"


def lobby_path(lobby_id: int) -> Path:
    """
    :param lobby_id:
    :return: path containing resources of lobby
    """
    lobby_dir = MEDIA_DIR / "game" / str(lobby_id)
    lobby_dir.mkdir(parents=True, exist_ok=True)
    return lobby_dir


def source_audio(lobby_id: int) -> Path:
    """
    :param lobby_id:
    :return: path of source audio, if it uploaded
    """
    source_path = lobby_path(lobby_id) / SOURCE_AUDIO_NAME
    if not source_path.exists():
        raise FileNotFoundException(status_code=400, detail=f"No source audio found for lobby {lobby_id}")
    return source_path


def reversed_source_audio(lobby_id: int) -> Path:
    """
    Reverses source audio of lobby
    :param lobby_id:
    :return: path of reversed audio, if source audio is uploaded
    """
    source_path = source_audio(lobby_id)
    reverse_path = lobby_path(lobby_id) / SOURCE_REVERSED_AUDIO_NAME
    parts_template = lobby_path(lobby_id) / SOURCE_REVERSED_PARTED_AUDIO_TEMPLATE
    _reverse_audio(source_path, reverse_path)
    _split_audio_to_parts(reverse_path, naming_template=parts_template)
    return reverse_path


def part_of_reversed_source_audio(lobby_id: int, num: int) -> Path:
    segment_path = lobby_path(lobby_id) / SOURCE_REVERSED_PARTED_AUDIO_TEMPLATE.format(str(num).zfill(3))
    if not segment_path.exists():
        raise FileNotFoundException(
            status_code=400, detail=f"No segment {num} of source audio found for lobby {lobby_id}"
        )
    return segment_path


def _reverse_audio(source: str | Path, dest: str | Path):
    if isinstance(dest, Path):
        dest = str(dest)
    stream = ffmpeg.input(source).filter("areverse").output(dest).overwrite_output()
    stream.run()


def _split_audio_to_parts(audio: str | Path, naming_template: str | Path = MEDIA_DIR / "out%03d.wav"):
    if isinstance(naming_template, Path):
        naming_template = str(naming_template)
    if isinstance(audio, Path):
        audio = str(audio)

    # By some reasons it can't recognize `segment_time` param
    # ffmpeg-python uses -filter-complex always and when you set `segment_time` param, ffmpeg can't see it

    # stream = (
    #     ffmpeg.input(audio)
    #     .filter("segment", f"segment_time {PART_TIME}")
    #     .output(naming_template, codec="copy")
    #     .overwrite_output()
    # )
    # stream.run()

    # I'm tired to solving it furthermore, so I do it with subprocess
    # ffmpeg -i "media\game\1\source.wav" -f segment -segment_time 5 -c copy "test_out%03d.wav"
    naming_template = naming_template.format("%03d")
    ffmpeg_segment(audio, naming_template, PART_TIME)


def _concat_audios(audios: Iterable[str | Path], dest: str | Path):
    if isinstance(dest, Path):
        dest = str(dest)
    inputs = [ffmpeg.input(str(audio)) for audio in audios]
    stream = ffmpeg.concat(*inputs, v=0, a=1).output(dest).overwrite_output()
    stream.run()


def parts_amount(audio: str | Path) -> int:
    """
    :param audio:
    :return: amount of parts to split song
    """
    probe = ffmpeg.probe(audio)
    duration = float(probe.get("format").get("duration"))
    return math.ceil(duration / PART_TIME)


def next_player_part_num(lobby_id: int) -> int:
    lobby_dir = lobby_path(lobby_id)
    search_pattern = "_".join(PLAYER_REVERSED_PARTED_AUDIO_TEMPLATE.format("").split("_")[:-1]) + "*"
    found_parts = sorted(list(lobby_dir.rglob(search_pattern)), reverse=True)
    next_num = 0 if not found_parts else int(found_parts[0].stem[-3:]) + 1
    return next_num


def part_of_player_audio_path(lobby_id: int, num: int) -> Path:
    segment_path = lobby_path(lobby_id) / PLAYER_REVERSED_PARTED_AUDIO_TEMPLATE.format(str(num).zfill(3))
    # if not segment_path.exists():
    #     raise FileNotFoundException(
    #         status_code=400, detail=f"No segment {num} of player audio found for lobby {lobby_id}"
    #     )
    return segment_path


def concated_reversed_player_audio(lobby_id: int) -> Path:
    lobby_dir = lobby_path(lobby_id)
    search_pattern = "_".join(PLAYER_REVERSED_PARTED_AUDIO_TEMPLATE.format("").split("_")[:-1]) + "*"
    found_parts = sorted(list(lobby_dir.rglob(search_pattern)))
    if not found_parts:
        raise NoFilesToProcessException(status_code=400, detail="No player parts found to process")

    concated_path = lobby_dir / PLAYER_REVERSED_AUDIO_NAME
    _concat_audios(found_parts, concated_path)

    concated_reversed_path = lobby_dir / PLAYER_AUDIO_NAME
    _reverse_audio(concated_path, concated_reversed_path)

    return concated_reversed_path
