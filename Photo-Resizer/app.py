"""
=============================================================================
IMAGE RESIZER AND COMPRESSOR - Flask Web Application
=============================================================================
Purpose: A beginner-friendly web app for resizing and compressing images
         for online form filling (exam forms, government forms, ID uploads)
         
Author: Your Name
Date: 2024
=============================================================================
"""

# =============================================================================
# IMPORTS - Loading required libraries
# =============================================================================
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename  # For secure file handling
from PIL import Image  # Python Imaging Library for image processing
import os  # For file and folder operations
import io  # For handling byte streams
import base64  # For encoding images to display in browser

# =============================================================================
# FLASK APP INITIALIZATION
# =============================================================================
# Create a Flask application instance
# __name__ tells Flask where to look for templates and static files
app = Flask(__name__)

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================
# Maximum upload size: 16 Megabytes (prevents server overload)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# Folder where uploaded files will be temporarily stored
app.config['UPLOAD_FOLDER'] = 'uploads'

# Allowed file extensions (only these image types are accepted)
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

# Secret key for session security (change this in production!)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# =============================================================================
# CREATE UPLOADS FOLDER
# =============================================================================
# Create the uploads directory if it doesn't exist
# exist_ok=True prevents error if folder already exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    
    How it works:
    1. Check if filename contains a dot (.)
    2. Split filename by dot and get the extension (last part)
    3. Convert to lowercase and check if it's in allowed extensions
    
    Args:
        filename (str): Name of the uploaded file
        
    Returns:
        bool: True if file extension is allowed, False otherwise
        
    Example:
        allowed_file('photo.jpg') → True
        allowed_file('document.pdf') → False
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def resize_and_compress_image(image, target_width, target_height, max_size_kb, initial_quality):
    """
    Resize and compress an image to meet the specified requirements.
    
    This function:
    1. Resizes the image to the target dimensions
    2. Compresses the image with the specified quality
    3. If file size exceeds the limit, automatically reduces quality
    4. Preserves image clarity as much as possible
    
    Args:
        image: PIL Image object (the uploaded image)
        target_width (int): Desired width in pixels
        target_height (int): Desired height in pixels
        max_size_kb (float): Maximum file size in kilobytes
        initial_quality (int): Starting quality level (1-100)
    
    Returns:
        tuple: (image_bytes, final_quality, final_size_kb)
            - image_bytes: The processed image as bytes
            - final_quality: The quality level used after auto-adjustment
            - final_size_kb: The final file size in kilobytes
    """
    
    # -------------------------------------------------------------------------
    # STEP 1: Resize the image
    # -------------------------------------------------------------------------
    # Image.LANCZOS is a high-quality resampling filter
    # It produces the best quality when resizing images
    resized_image = image.resize((target_width, target_height), Image.LANCZOS)
    
    # -------------------------------------------------------------------------
    # STEP 2: Handle image mode (transparency, etc.)
    # -------------------------------------------------------------------------
    # JPEG doesn't support transparency, so we need to convert
    # RGBA (has transparency) or P (palette mode) to RGB
    if resized_image.mode in ('RGBA', 'P'):
        # Create a white background
        background = Image.new('RGB', resized_image.size, (255, 255, 255))
        # If image has transparency, paste it on white background
        if resized_image.mode == 'RGBA':
            background.paste(resized_image, mask=resized_image.split()[3])
            resized_image = background
        else:
            resized_image = resized_image.convert('RGB')
    elif resized_image.mode != 'RGB':
        resized_image = resized_image.convert('RGB')
    
    # -------------------------------------------------------------------------
    # STEP 3: Initial compression
    # -------------------------------------------------------------------------
    # BytesIO creates an in-memory file-like object
    # We save the image to this buffer instead of disk
    output_buffer = io.BytesIO()
    
    # Save image as JPEG with specified quality
    # optimize=True enables additional compression optimizations
    resized_image.save(output_buffer, format='JPEG', quality=initial_quality, optimize=True)
    
    # Get current file size in KB (1 KB = 1024 bytes)
    current_size_kb = output_buffer.tell() / 1024
    
    # -------------------------------------------------------------------------
    # STEP 4: Auto-adjust quality if file size exceeds limit
    # -------------------------------------------------------------------------
    current_quality = initial_quality
    
    # Keep reducing quality until file size is within limit
    # Minimum quality is 5 (to maintain some image clarity)
    while current_size_kb > max_size_kb and current_quality > 5:
        # Reduce quality by 5
        current_quality -= 5
        
        # Create new buffer and save with lower quality
        output_buffer = io.BytesIO()
        resized_image.save(output_buffer, format='JPEG', quality=current_quality, optimize=True)
        
        # Recalculate file size
        current_size_kb = output_buffer.tell() / 1024
    
    # -------------------------------------------------------------------------
    # STEP 5: Prepare and return the result
    # -------------------------------------------------------------------------
    # Reset buffer position to beginning for reading
    output_buffer.seek(0)
    
    # Return the image bytes, final quality, and final size
    return output_buffer.getvalue(), current_quality, round(current_size_kb, 2)


# =============================================================================
# FLASK ROUTES (URL Endpoints)
# =============================================================================

@app.route('/')
def index():
    """
    Home Route - Serves the main HTML page
    
    When user visits http://localhost:5000/, this function runs
    and returns the index.html template.
    """
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_and_process():
    """
    Upload Route - Handles image upload and processing
    
    This route:
    1. Receives the uploaded image from the frontend
    2. Validates the file and input parameters
    3. Processes the image (resize + compress)
    4. Returns the processed image as base64 for preview
    
    Returns:
        JSON response with processed image or error message
    """
    try:
        # ---------------------------------------------------------------------
        # VALIDATION 1: Check if image file is present in request
        # ---------------------------------------------------------------------
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file was uploaded. Please select an image.'
            }), 400
        
        file = request.files['image']
        
        # ---------------------------------------------------------------------
        # VALIDATION 2: Check if a file was actually selected
        # ---------------------------------------------------------------------
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected. Please choose an image file.'
            }), 400
        
        # ---------------------------------------------------------------------
        # VALIDATION 3: Check file extension
        # ---------------------------------------------------------------------
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Only JPG, JPEG, and PNG files are allowed.'
            }), 400
        
        # ---------------------------------------------------------------------
        # GET PROCESSING PARAMETERS FROM FORM
        # ---------------------------------------------------------------------
        try:
            # Get width (default: 200 pixels)
            width = int(request.form.get('width', 200))
            
            # Get height (default: 200 pixels)
            height = int(request.form.get('height', 200))
            
            # Get max file size in KB (default: 50 KB)
            max_size_kb = float(request.form.get('maxSize', 50))
            
            # Get quality (default: 80%)
            quality = int(request.form.get('quality', 80))
            
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid input values. Please enter valid numbers.'
            }), 400
        
        # ---------------------------------------------------------------------
        # VALIDATION 4: Validate parameter ranges
        # ---------------------------------------------------------------------
        if width <= 0 or height <= 0:
            return jsonify({
                'success': False,
                'error': 'Width and height must be positive numbers.'
            }), 400
        
        if width > 5000 or height > 5000:
            return jsonify({
                'success': False,
                'error': 'Width and height cannot exceed 5000 pixels.'
            }), 400
        
        if max_size_kb <= 0:
            return jsonify({
                'success': False,
                'error': 'Maximum file size must be a positive number.'
            }), 400
        
        if max_size_kb > 10240:  # 10 MB limit
            return jsonify({
                'success': False,
                'error': 'Maximum file size cannot exceed 10240 KB (10 MB).'
            }), 400
        
        if quality < 1 or quality > 100:
            return jsonify({
                'success': False,
                'error': 'Quality must be between 1 and 100.'
            }), 400
        
        # ---------------------------------------------------------------------
        # OPEN AND PROCESS THE IMAGE
        # ---------------------------------------------------------------------
        # Open the image from the file stream (without saving to disk)
        image = Image.open(file.stream)
        
        # Store original dimensions for display
        original_width, original_height = image.size
        
        # Calculate original file size
        file.stream.seek(0, 2)  # Seek to end
        original_size_kb = file.stream.tell() / 1024
        file.stream.seek(0)  # Reset to beginning
        
        # Process the image (resize and compress)
        processed_bytes, final_quality, final_size_kb = resize_and_compress_image(
            image=image,
            target_width=width,
            target_height=height,
            max_size_kb=max_size_kb,
            initial_quality=quality
        )
        
        # ---------------------------------------------------------------------
        # CONVERT TO BASE64 FOR BROWSER DISPLAY
        # ---------------------------------------------------------------------
        # Base64 encoding allows us to embed the image directly in HTML
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        
        # ---------------------------------------------------------------------
        # PREPARE AND SEND RESPONSE
        # ---------------------------------------------------------------------
        # Prepare a message about quality adjustment
        quality_message = ""
        if final_quality < quality:
            quality_message = f" Quality was auto-adjusted from {quality}% to {final_quality}% to meet the file size requirement."
        
        return jsonify({
            'success': True,
            'image': f'data:image/jpeg;base64,{base64_image}',
            'originalWidth': original_width,
            'originalHeight': original_height,
            'originalSize': round(original_size_kb, 2),
            'newWidth': width,
            'newHeight': height,
            'finalQuality': final_quality,
            'finalSize': final_size_kb,
            'message': f'Image processed successfully! Final size: {final_size_kb} KB.{quality_message}'
        })
        
    except Exception as e:
        # Handle any unexpected errors
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }), 500


@app.route('/download', methods=['POST'])
def download_image():
    """
    Download Route - Generates a downloadable image file
    
    This route:
    1. Receives the base64 image data from frontend
    2. Decodes it back to binary
    3. Sends it as a downloadable file
    
    Returns:
        Downloadable JPEG file or error message
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data received'
            }), 400
        
        image_data = data.get('image', '')
        filename = data.get('filename', 'resized_image.jpg')
        
        if not image_data:
            return jsonify({
                'success': False,
                'error': 'No image data provided'
            }), 400
        
        # ---------------------------------------------------------------------
        # DECODE BASE64 IMAGE DATA
        # ---------------------------------------------------------------------
        # Remove the data URL prefix (e.g., "data:image/jpeg;base64,")
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 to bytes
        image_bytes = base64.b64decode(image_data)
        
        # Create a BytesIO object to serve as a file
        output_buffer = io.BytesIO(image_bytes)
        output_buffer.seek(0)
        
        # ---------------------------------------------------------------------
        # SEND FILE FOR DOWNLOAD
        # ---------------------------------------------------------------------
        return send_file(
            output_buffer,
            mimetype='image/jpeg',
            as_attachment=True,  # This makes browser download instead of display
            download_name=secure_filename(filename)  # Secure the filename
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }), 500


@app.route('/health')
def health_check():
    """
    Health Check Route - Verifies the server is running
    
    Useful for monitoring and debugging.
    """
    return jsonify({
        'status': 'healthy',
        'message': 'Image Resizer API is running!'
    })


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(413)
def file_too_large(error):
    """Handle file too large error (exceeds MAX_CONTENT_LENGTH)"""
    return jsonify({
        'success': False,
        'error': 'File is too large. Maximum upload size is 16 MB.'
    }), 413


@app.errorhandler(404)
def not_found(error):
    """Handle page not found error"""
    return jsonify({
        'success': False,
        'error': 'The requested resource was not found.'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle internal server error"""
    return jsonify({
        'success': False,
        'error': 'An internal server error occurred. Please try again.'
    }), 500


# =============================================================================
# RUN THE APPLICATION
# =============================================================================
if __name__ == '__main__':
    """
    This block runs when you execute: python app.py
    
    debug=True enables:
    - Auto-reload when code changes
    - Detailed error messages
    - Interactive debugger
    
    NOTE: Set debug=False in production!
    """
    print("=" * 60)
    print("IMAGE RESIZER AND COMPRESSOR")
    print("=" * 60)
    print("Server starting...")
    print("Open your browser and go to: http://localhost:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)