from flask import Flask, request, jsonify, send_file
from rembg import remove
from PIL import Image
import cv2
import numpy as np
import requests
import io
import os
import tempfile

app = Flask(__name__)

# Load face detection model
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

def download_image(url):
    """Download image from URL"""
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return Image.open(io.BytesIO(response.content)).convert("RGBA")

def remove_background(img):
    """Remove background using rembg"""
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    result = remove(img_bytes.read())
    return Image.open(io.BytesIO(result)).convert("RGBA")

def detect_and_crop_face(img, output_width=413, output_height=531):
    """
    Detect face and crop to ID photo format (35x45mm = 413x531px at 300dpi)
    Returns cropped image with white background
    """
    # Convert to numpy for OpenCV
    img_np = np.array(img.convert("RGB"))
    gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
    
    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray, 
        scaleFactor=1.1, 
        minNeighbors=5, 
        minSize=(50, 50)
    )
    
    if len(faces) == 0:
        # No face detected — center crop fallback
        w, h = img.size
        ratio = output_width / output_height
        if w / h > ratio:
            new_w = int(h * ratio)
            left = (w - new_w) // 2
            img = img.crop((left, 0, left + new_w, h))
        else:
            new_h = int(w / ratio)
            top = max(0, int(h * 0.15) - (new_h - h) // 4)
            img = img.crop((0, top, w, top + new_h))
        img = img.resize((output_width, output_height), Image.LANCZOS)
    else:
        # Use largest face
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        fx, fy, fw, fh = faces[0]
        
        # Face should be about 60-70% of the width of the final photo
        face_ratio = 0.65
        target_face_width = output_width * face_ratio
        scale = target_face_width / fw
        
        # Calculate crop region
        # Face should be roughly in the upper-center (top 30-70% of image)
        center_x = fx + fw // 2
        center_y = fy + fh // 2
        
        # Shift up slightly so face is in upper portion
        crop_w = int(output_width / scale)
        crop_h = int(output_height / scale)
        
        # Position: face center horizontally, face top third vertically
        left = int(center_x - crop_w // 2)
        top = int(center_y - crop_h * 0.38)
        
        # Bounds check
        w, h = img.size
        left = max(0, min(left, w - crop_w))
        top = max(0, min(top, h - crop_h))
        right = min(w, left + crop_w)
        bottom = min(h, top + crop_h)
        
        img = img.crop((left, top, right, bottom))
        img = img.resize((output_width, output_height), Image.LANCZOS)
    
    return img

def add_white_background(img):
    """Replace transparent background with white"""
    background = Image.new("RGBA", img.size, (255, 255, 255, 255))
    background.paste(img, mask=img.split()[3])
    return background.convert("RGB")


@app.route('/process', methods=['POST'])
def process_photo():
    """
    Main endpoint. Accepts JSON with 'image_url' field.
    Returns processed ID photo (background removed + face cropped).
    """
    try:
        data = request.get_json()
        if not data or 'image_url' not in data:
            return jsonify({"error": "Missing 'image_url' in request body"}), 400
        
        image_url = data['image_url']
        
        # Optional parameters
        width = data.get('width', 413)    # 35mm at 300dpi
        height = data.get('height', 531)  # 45mm at 300dpi
        bg_color = data.get('bg_color', 'white')  # 'white' or 'transparent'
        
        # Step 1: Download
        img = download_image(image_url)
        
        # Step 2: Remove background
        img = remove_background(img)
        
        # Step 3: Detect face and crop
        img = detect_and_crop_face(img, output_width=width, output_height=height)
        
        # Step 4: Add white background (or keep transparent)
        if bg_color == 'white':
            img = add_white_background(img)
            fmt = 'JPEG'
            mimetype = 'image/jpeg'
            ext = 'jpg'
        else:
            fmt = 'PNG'
            mimetype = 'image/png'
            ext = 'png'
        
        # Save to buffer
        buffer = io.BytesIO()
        img.save(buffer, format=fmt, quality=95)
        buffer.seek(0)
        
        return send_file(buffer, mimetype=mimetype, download_name=f'photo_id.{ext}')
    
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to download image: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
