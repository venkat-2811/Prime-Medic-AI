document.addEventListener('DOMContentLoaded', () => {
    const webcamPreview = document.getElementById('webcamPreview');
    const startRecordingBtn = document.getElementById('startRecording');
    const stopRecordingBtn = document.getElementById('stopRecording');
    const uploadVideoBtn = document.getElementById('uploadVideo');
    const uploadedVideo = document.getElementById('uploadedVideo');
    const statusDiv = document.getElementById('status');

    let mediaRecorder;
    let recordedChunks = [];
    let stream;

    // Comprehensive browser compatibility check
    function checkBrowserCompatibility() {
        // Check for core APIs needed for webcam and recording
        const hasUserMedia = !!(
            navigator.mediaDevices && 
            navigator.mediaDevices.getUserMedia
        );
        
        const hasMediaRecorder = !!(window.MediaRecorder);
        
        const hasBlobSupport = !!(window.Blob);
        
        const hasFormDataSupport = !!(window.FormData);

        if (!hasUserMedia) {
            console.error('getUserMedia is not supported in this browser');
            statusDiv.textContent = 'Your browser does not support webcam access. Please try a modern browser like Chrome, Firefox, or Edge.';
            startRecordingBtn.disabled = true;
            return false;
        }

        if (!hasMediaRecorder) {
            console.error('MediaRecorder is not supported');
            statusDiv.textContent = 'Media recording is not supported in your browser.';
            startRecordingBtn.disabled = true;
            return false;
        }

        if (!hasBlobSupport) {
            console.error('Blob is not supported');
            statusDiv.textContent = 'File handling is not supported in your browser.';
            startRecordingBtn.disabled = true;
            return false;
        }

        if (!hasFormDataSupport) {
            console.error('FormData is not supported');
            statusDiv.textContent = 'File upload is not supported in your browser.';
            startRecordingBtn.disabled = true;
            return false;
        }

        return true;
    }

    // Request webcam access with extensive error handling
    async function startWebcam() {
        // First, check browser compatibility
        if (!checkBrowserCompatibility()) {
            return;
        }

        try {
            // Specify detailed constraints
            const constraints = {
                video: {
                    width: { ideal: 640, max: 1280 },
                    height: { ideal: 480, max: 720 },
                    aspectRatio: { ideal: 1.333 },
                    facingMode: 'user' // Prefer front camera
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            };

            stream = await navigator.mediaDevices.getUserMedia(constraints);
            
            // Additional checks after getting the stream
            if (!stream) {
                throw new Error('No stream obtained from getUserMedia');
            }

            // Set video source and play
            webcamPreview.srcObject = stream;
            
            // Ensure video plays
            webcamPreview.onloadedmetadata = (e) => {
                webcamPreview.play().catch(err => {
                    console.error('Error playing video:', err);
                    statusDiv.textContent = 'Could not play webcam stream: ' + err.message;
                });
            };

            // Enable recording button
            startRecordingBtn.disabled = false;
            statusDiv.textContent = 'Webcam access granted. Ready to record.';

        } catch (err) {
            console.error('Comprehensive webcam access error:', err);
            
            // Detailed error messaging
            let errorMessage = 'Error accessing webcam: ';
            switch(err.name) {
                case 'NotAllowedError':
                    errorMessage += 'Permission denied. Please grant webcam access.';
                    break;
                case 'NotFoundError':
                    errorMessage += 'No webcam found on this device.';
                    break;
                case 'NotReadableError':
                    errorMessage += 'Webcam is already in use or blocked.';
                    break;
                case 'OverconstrainedError':
                    errorMessage += 'No camera meets the specified constraints.';
                    break;
                default:
                    errorMessage += err.message || 'Unknown error occurred.';
            }

            statusDiv.textContent = errorMessage;
            startRecordingBtn.disabled = true;
        }
    }

    // Start video recording
    function startRecording() {
        if (!stream) {
            statusDiv.textContent = 'No webcam stream available. Please check webcam access.';
            return;
        }

        recordedChunks = [];
        
        try {
            // Use the most compatible MIME type
            const mimeTypes = [
                'video/webm;codecs=vp9,opus',
                'video/webm;codecs=vp8,vorbis',
                'video/webm'
            ];

            let supportedType = mimeTypes.find(type => 
                MediaRecorder.isTypeSupported(type)
            );

            if (!supportedType) {
                throw new Error('No supported video MIME type found');
            }

            mediaRecorder = new MediaRecorder(stream, {
                mimeType: supportedType
            });

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    recordedChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                const blob = new Blob(recordedChunks, { 
                    type: supportedType 
                });
                
                uploadVideoBtn.disabled = false;
                uploadedVideo.src = URL.createObjectURL(blob);
            };

            mediaRecorder.start();
            startRecordingBtn.disabled = true;
            stopRecordingBtn.disabled = false;
            statusDiv.textContent = 'Recording started...';

        } catch (err) {
            console.error('Recording start error:', err);
            statusDiv.textContent = 'Could not start recording: ' + err.message;
        }
    }

    // Stop video recording
    function stopRecording() {
        if (!mediaRecorder) {
            statusDiv.textContent = 'No active recording to stop.';
            return;
        }

        try {
            mediaRecorder.stop();
            startRecordingBtn.disabled = false;
            stopRecordingBtn.disabled = true;
            statusDiv.textContent = 'Recording stopped.';
        } catch (err) {
            console.error('Recording stop error:', err);
            statusDiv.textContent = 'Error stopping recording: ' + err.message;
        }
    }

    // Upload video to server
    async function uploadVideo() {
        if (recordedChunks.length === 0) {
            statusDiv.textContent = 'No recorded video to upload.';
            return;
        }

        const blob = new Blob(recordedChunks, { 
            type: 'video/webm' 
        });
        
        const formData = new FormData();
        formData.append('video', blob, 'recorded_video.mp4');

        try {
            statusDiv.textContent = 'Uploading video...';
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            if (result.audio_url) {
                uploadedVideo.src = result.audio_url;
                statusDiv.textContent = 'Video uploaded and processed successfully!';
            }
            console.log('Server response:', result);
        } catch (err) {
            console.error('Upload error:', err);
            statusDiv.textContent = 'Upload failed: ' + err.message;
        }
    }

    // Event Listeners
    startRecordingBtn.addEventListener('click', startRecording);
    stopRecordingBtn.addEventListener('click', stopRecording);
    uploadVideoBtn.addEventListener('click', uploadVideo);

    // Initialize webcam on page load
    startWebcam();
});