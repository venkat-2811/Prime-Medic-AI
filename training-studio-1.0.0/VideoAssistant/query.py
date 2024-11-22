# Multimodal demo
# This is an example of how to simulate a video- and audio-aware model using existing LLM vision models (that take text and images as input, and generate text as output).

from io import BytesIO
import os
from pathlib import Path
from typing import Any

import dotenv
from groq import Groq

from media_extractor import split_video
import datauri

from gtts import gTTS

# UPLOAD_FOLDER = 'static/'


# Load OpenAI API key from .env file
dotenv.load_dotenv()
if os.environ.get("GROQ_API_KEY") is None:
    raise ValueError("GROQ_API_KEY not found in .env file")

client = Groq()


# This is the input video that we'll turn into the user prompt.

def chat(video_file: str, messages: list[Any]) -> str:
    # Extract audio and frames from the video
    audio_uri, image_uris = split_video(video_file)

    with datauri.as_tempfile(audio_uri) as audio_file:
        # Transcribe audio to text
        transcription = client.audio.transcriptions.create(
            file=Path(audio_file),
            model="whisper-large-v3-turbo",
            response_format="json"
        )

    user_prompt = transcription.text

    # Add the user's input (text + optional images) to messages
    new_message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": user_prompt,
            }
        ]
    }

    # Append the new message to the messages list
    messages.append(new_message)

    # Append the first image URL if available
    if image_uris:
        first_image_uri = image_uris[0]
        messages.append({
            "role": "user", 
            "content": [
                {
                    "type": "image_url", 
                    "image_url": {
                        "url": first_image_uri
                    }
                }
            ]
        })

    # Get AI-generated response
    try:
        response = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=messages,
        )
        response_text = response.choices[0].message.content
        messages.append({
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": response_text,
            }
        ]
    })
    except Exception as e:
        print(f"Error during API call: {e}")
        return ""

    # Convert AI response to audio
    audio = gTTS(text=response_text, lang='en')
    filepath = "static/response_audio.mp3"
    # Return audio as a data URI
    audio.save(filepath)

    # filename = "response_audio.mp3"
    # filepath = os.path.join(UPLOAD_FOLDER, filename)
    # audio.save(filepath)
    # Read the saved file and create a data URI
    with open(filepath, "rb") as audio_file:
        response_audio_uri = datauri.from_bytes(audio_file.read(), "audio/mpeg")
    print(response_audio_uri)
    return response_audio_uri

    
