import shutil
import subprocess

from fastapi import UploadFile


def write_file(file_name: str, uploading_file: UploadFile):
    with open(file_name, "wb") as buf:
        shutil.copyfileobj(uploading_file.file, buf)


def ffmpeg_segment(file_input: str, file_output_template: str, segment_time: int):
    cmd = f'ffmpeg -i "{file_input}" -f segment -segment_time {segment_time} -c copy "{file_output_template}"'
    subprocess.call(cmd, shell=True)
