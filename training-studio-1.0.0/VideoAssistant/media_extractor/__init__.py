import tempfile
from pathlib import Path, PurePath
import shutil
import ffmpeg
import datauri
import base64
import mimetypes

def convert_file_to_data_uri(file_path):
    """
    Converts a file to a data URI format.

    Args:
        file_path (str): The path to the file to be converted.

    Returns:
        str: The data URI as a string.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file type cannot be determined.
    """
    # Determine the MIME type of the file
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        raise ValueError(f"Cannot determine MIME type for file: {file_path}")
    
    # Read the file and encode it as a base64 string
    with open(file_path, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode("utf-8")
    
    # Construct the data URI
    data_uri = f"data:{mime_type};base64,{encoded_string}"
    return data_uri


def split_video(video_uri_or_file: str, fps: int = 2) -> tuple[str, list[str]]:
    print(f"Received video file: {video_uri_or_file}")
    if shutil.which("ffmpeg") is None:
        raise FileNotFoundError("ffmpeg not found in PATH")

    if isinstance(video_uri_or_file, str) and video_uri_or_file.startswith("data:"):
        video_uri = video_uri_or_file
    elif isinstance(video_uri_or_file, str):
        video_uri = convert_file_to_data_uri(video_uri_or_file)
        # print(video_uri)
    else:
        raise ValueError("Invalid video input format")

    if video_uri is not None:
        with tempfile.TemporaryDirectory() as outdir:
            audio = PurePath(outdir) / "audio.mp3"
            with datauri.as_tempfile(video_uri) as video_file:
                (
                    ffmpeg.input(video_file)
                    .output(
                        str(audio),
                        loglevel="error",
                        **{
                            # Use 64k bitrate for smaller file
                            "b:a": "64k",
                            # Only output one channel, again for smaller file
                            "ac": "1",
                        },
                    )
                    .run()
                )
                (
                    ffmpeg.input(video_file)
                    .output(
                        str(PurePath(outdir) / "frame-%04d.jpg"),
                        loglevel="error",
                        **{
                            # Use fps as specified, scale image to fit within 512x512
                            "vf": f"fps={fps},scale='if(gt(iw,ih),512,-1)':'if(gt(ih,iw),512,-1)'",
                            "q:v": "20",
                        },
                    )
                    .run()
                )
            images = list(Path(outdir).glob("*.jpg"))
            images.sort()
            return datauri.from_file(audio), [datauri.from_file(image) for image in images]
    else:
        raise ValueError("Invalid video URI")