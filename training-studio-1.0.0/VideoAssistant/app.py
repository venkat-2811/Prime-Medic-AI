import os
import cv2
import numpy as np
from flask import Flask, request, jsonify, render_template

from flask_cors import CORS
from werkzeug.utils import secure_filename
from query import chat
from astrapy import DataAPIClient

app = Flask(__name__)


CORS(app)

from groq import Groq


client = Groq(
      api_key=os.environ.get("GROQ_API_KEY"),
)

db_client = DataAPIClient(os.getenv('ASTRADB_TOKEN'))
db = db_client.get_database_by_api_endpoint(
     "https://b4c89db4-bdf7-47fa-9b9c-ce5380480864-us-east-2.apps.astra.datastax.com"
)
collection = db['prime_medic_ai']
# Configuration

UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'webm', 'mp4', 'avi', 'mov'}

# Ensure upload and processed directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
@app.route('/')
def index():
  return render_template('home.html')

def allowed_file(filename):
  """Check if the file extension is allowed."""
  return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_video(input_path):
  """
  Advanced video processing function.
  This function demonstrates several video processing techniques:
  1. Object detection/tracking
  2. Motion analysis
  3. Frame-by-frame processing
  4. Feature extraction
  Args:
    input_path (str): Path to the input video file
  Returns:
    dict: Processing results and metadata
  """
  # Initialize results dictionary
  results = {
    'total_frames': 0,
    'processed_frames': 0,
    'motion_detected': False,
    'motion_frames': 0,
    'object_counts': {},
    'processing_complete': False
  }
  # Open the video
  cap = cv2.VideoCapture(input_path)
  # Check if video opened successfully
  if not cap.isOpened():
    raise ValueError("Error opening video file")
  # Prepare background subtractor for motion detection
  bg_subtractor = cv2.createBackgroundSubtractorMOG2(
    detectShadows=True
  )
  # Frame processing variables
  prev_frame = None
  frame_count = 0
  motion_frame_count = 0
  # Process video frames
  while True:
    ret, frame = cap.read()
    # Break if no more frames
    if not ret:
      break
    frame_count += 1
    results['total_frames'] = frame_count
    # Resize frame for processing efficiency
    frame_resized = cv2.resize(frame, (640, 480))
    # Motion Detection
    fg_mask = bg_subtractor.apply(frame_resized)
    motion_pixels = np.count_nonzero(fg_mask)
    # Threshold for motion detection (adjust as needed)
    if motion_pixels > 500: # Can be tuned based on specific requirements
      motion_frame_count += 1
      results['motion_detected'] = True
    # # Optional: Feature extraction
    # # (e.g., edge detection, color histogram)
    # gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
    # edges = cv2.Canny(gray, 100, 200)
    # # Optional: Save processed frame
    # if frame_count % 30 == 0: # Save every 30th frame
    # output_path = os.path.join(
    # PROCESSED_FOLDER,
    # f'processed_frame_{frame_count}.jpg'
    # )
    # cv2.imwrite(output_path, frame_resized)
    results['processed_frames'] = frame_count
    results['motion_frames'] = motion_frame_count
  # Release video capture
  cap.release()
  # Finalize results
  results['processing_complete'] = True
  results['motion_percentage'] = (
    motion_frame_count / frame_count * 100
    if frame_count > 0 else 0
  )
  return results

@app.route('/upload', methods=['POST'])
def upload_video():
  if 'video' not in request.files:
    return jsonify({'error': 'No video file uploaded', 'status': 'failed'}), 400
  video_file = request.files['video']
  if video_file.filename == '':
    return jsonify({'error': 'No selected file', 'status': 'failed'}), 400
  if not allowed_file(video_file.filename):
    return jsonify({'error': 'File type not allowed', 'status': 'failed'}), 400
  filename = "recorded-video.mp4"
  filepath = os.path.join(UPLOAD_FOLDER, filename)
  video_file.save(filepath)
  try:
    audio = chat(filepath, [])
    return render_template('home.html', audio_url=audio)
  except Exception as e:
    return jsonify({'error': str(e), 'status': 'failed'}), 500
  # try:
  # # Process the video
  # processing_results = process_video(filepath)
  # # Return results
  # return jsonify({
  # 'status': 'success',
  # 'filename': filename,
  # 'processing_results': processing_results
  # })
  # except Exception as e:
  # # Handle processing errors
  # return jsonify({
  # 'status': 'failed',
  # 'error': str(e)
  # }), 500
# @app.route('/processed_frames', methods=['GET'])
# def get_processed_frames():
# """
# Retrieve list of processed frame files.
# Returns:
# JSON list of processed frame filenames
# """
# processed_frames = os.listdir(PROCESSED_FOLDER)
# return jsonify({
# 'processed_frames': processed_frames
# })

@app.route('/chat')
def home():
  return render_template('index.html')

def get_response(message):
  user_vd = collection.find(
  sort={"$vectorize": message},
  limit=2,
  projection={"$vectorize": True},
  include_similarity=True,
  )
  response = client.chat.completions.create(
  messages=[
    {
      "role": "user",
      "content": message,
    },
    {
      'role': 'system',
      'content': f'''You are an AI Doctor (You have no name) Who is Fully Professional in Medicine field
         and have the versatile knowledge of Medicine including the {user_vd},
         ALso You are a genuine and friendly concerning Doctor who takes a great care and comfort ,
         You will Provide the answers for the patients whatever they ask for and here is the user query {message},
         Ignore the asterisk symbols and not allowed to greet the user as patient, address them with friendly titles
         Now Answer it in the Concerning, Genuine and Jovial way of Speaking possible, You need to GIve the answer in the format given below
         "The Name of the Problem,
         The severity of the problem,
        The precautions to be taken,
        The medicines that need to be taken,
         The need and type of doctor to be consulted .",
         You have to give the response consize and strictly warning you don't use any kind of asterisks usage and pointing,numbering, the answer should only one be in
         '''
    }
    ],
    model="llama-3.1-8b-instant",
  )
  return response.choices[0].message.content

@app.route('/send_message', methods=['POST'])
def send_message():
  message = request.json['message']
  response = get_response(message)
  return jsonify({"response": response})

def main():
  # Run the Flask application
  app.run(
    host='0.0.0.0', # Listen on all available interfaces
    port=5000, # Standard Flask development port
    debug=True # Enable debug mode for development
  )

if __name__ == '__main__':
  main()
