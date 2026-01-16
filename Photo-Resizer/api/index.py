"""
=============================================================================
IMAGE RESIZER AND COMPRESSOR - Vercel Serverless Deployment
=============================================================================
Modified Flask application for Vercel's serverless environment.
=============================================================================
"""

from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from PIL import Image
import os
import io
import base64

# =============================================================================
# FLASK APP INITIALIZATION
# =============================================================================
app = Flask(__name__, 
            template_folder='../templates',  # Templates are in parent directory
            static_folder='../static')       # Static files are in parent directory

# =============================================================================
# CONFIGURATION
# =============================================================================
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def resize_and_compress_image(image, target_width, target_height, max_size_kb, initial_quality):
    """
    Resize and compress an image to meet the specified requirements.
    """
    # Resize the image using high-quality LANCZOS resampling
    resized_image = image.resize((target_width, target_height), Image.LANCZOS)
    
    # Handle transparency and color modes
    if resized_image.mode in ('RGBA', 'P'):
        background = Image.new('RGB', resized_image.size, (255, 255, 255))
        if resized_image.mode == 'RGBA':
            background.paste(resized_image, mask=resized_image.split()[3])
            resized_image = background
        else:
            resized_image = resized_image.convert('RGB')
    elif resized_image.mode != 'RGB':
        resized_image = resized_image.convert('RGB')
    
    # Initial compression
    output_buffer = io.BytesIO()
    resized_image.save(output_buffer, format='JPEG', quality=initial_quality, optimize=True)
    current_size_kb = output_buffer.tell() / 1024
    
    # Auto-adjust quality if needed
    current_quality = initial_quality
    while current_size_kb > max_size_kb and current_quality > 5:
        current_quality -= 5
        output_buffer = io.BytesIO()
        resized_image.save(output_buffer, format='JPEG', quality=current_quality, optimize=True)
        current_size_kb = output_buffer.tell() / 1024
    
    output_buffer.seek(0)
    return output_buffer.getvalue(), current_quality, round(current_size_kb, 2)


# =============================================================================
# ROUTES
# =============================================================================

@app.route('/')
def index():
    """Serve the main HTML page."""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_and_process():
    """Handle image upload and processing."""
    try:
        # Validate file presence
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file was uploaded. Please select an image.'
            }), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected. Please choose an image file.'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Only JPG, JPEG, and PNG files are allowed.'
            }), 400
        
        # Get processing parameters
        try:
            width = int(request.form.get('width', 200))
            height = int(request.form.get('height', 200))
            max_size_kb = float(request.form.get('maxSize', 50))
            quality = int(request.form.get('quality', 80))
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid input values. Please enter valid numbers.'
            }), 400
        
        # Validate parameters
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
        
        if max_size_kb <= 0 or max_size_kb > 10240:
            return jsonify({
                'success': False,
                'error': 'Maximum file size must be between 1 and 10240 KB.'
            }), 400
        
        if quality < 1 or quality > 100:
            return jsonify({
                'success': False,
                'error': 'Quality must be between 1 and 100.'
            }), 400
        
        # Process the image
        image = Image.open(file.stream)
        original_width, original_height = image.size
        
        file.stream.seek(0, 2)
        original_size_kb = file.stream.tell() / 1024
        file.stream.seek(0)
        
        processed_bytes, final_quality, final_size_kb = resize_and_compress_image(
            image=image,
            target_width=width,
            target_height=height,
            max_size_kb=max_size_kb,
            initial_quality=quality
        )
        
        # Convert to base64
        base64_image = base64.b64encode(processed_bytes).decode('utf-8')
        
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
        return jsonify({
            'success': False,
            'error': f'An unexpected error occurred: {str(e)}'
        }), 500


@app.route('/download', methods=['POST'])
def download_image():
    """Generate a downloadable image file."""
    try:
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
        
        # Decode base64 image
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        output_buffer = io.BytesIO(image_bytes)
        output_buffer.seek(0)
        
        return send_file(
            output_buffer,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=secure_filename(filename)
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Download failed: {str(e)}'
        }), 500


@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'message': 'Image Resizer API is running on Vercel!'
    })


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({
        'success': False,
        'error': 'File is too large. Maximum upload size is 16 MB.'
    }), 413


@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'The requested resource was not found.'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'An internal server error occurred. Please try again.'
    }), 500


# =============================================================================
# VERCEL SERVERLESS HANDLER
# =============================================================================
# Vercel looks for an 'app' variable for WSGI applications
# No need to call app.run() - Vercel handles that

# For local testing only
if __name__ == '__main__':
    app.run(debug=True, port=5000)