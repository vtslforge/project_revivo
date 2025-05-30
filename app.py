# app.py - Main backend file for Food Calorie Analyzer (simplified version)
from flask import Flask, request, jsonify, render_template
from google_fit import init_google_fit_routes
import os
import numpy as np
from PIL import Image
import io
import tensorflow as tf
from jinja2 import TemplateNotFound

# Setup Flask with correct template and static folders
app = Flask(__name__)
app.secret_key = 'revivower_secret_key_change_this_in_production'

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Load the food database
FOOD_DATABASE = {
    'Bisi Bele Bath':   {'calories': 250, 'protein': 6, 'carbs': 40, 'fat': 7},
    'Chitranna':        {'calories': 220, 'protein': 4, 'carbs': 38, 'fat': 6},
    'Masala Dosa':      {'calories': 180, 'protein': 4, 'carbs': 30, 'fat': 5},
    'Mysore Pak':       {'calories': 400, 'protein': 3, 'carbs': 45, 'fat': 22},
    'Set Dosa':         {'calories': 150, 'protein': 3, 'carbs': 28, 'fat': 3},
    'Udupi Sambar':     {'calories': 90,  'protein': 3, 'carbs': 15, 'fat': 2},
    'biryani':          {'calories': 320, 'protein': 8, 'carbs': 45, 'fat': 10},
    'chicken curry':    {'calories': 210, 'protein': 18, 'carbs': 6, 'fat': 12},
    'idli':             {'calories': 40,  'protein': 1.5, 'carbs': 8, 'fat': 0.2},
    'kesari bath':      {'calories': 180, 'protein': 2, 'carbs': 35, 'fat': 5},
    'ragi mudde':       {'calories': 70,  'protein': 2, 'carbs': 15, 'fat': 0.5}
}

# Global variable to store the model
model = None

def load_model():
    """Load and return the TensorFlow Keras model."""
    global model
    
    try:
        # Path to your converted Keras .h5 model file
        model_path = "model/food_model.h5"  # Path to the .h5 model file
        
        # Load the model using tf.keras.models.load_model
        model = tf.keras.models.load_model(model_path)
        
        print("TensorFlow Keras model loaded successfully")
        return True
    except Exception as e:
        print(f"Error loading model: {e}")
        return False

def preprocess_image(image_bytes, target_size=(224, 224)):
    """Preprocess the image bytes to prepare for model input."""
    try:
        # Open image from bytes
        image = Image.open(io.BytesIO(image_bytes))
        
        # Resize to target size
        image = image.resize(target_size)
        
        # Convert to RGB if it's not
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to numpy array and normalize
        img_array = np.array(image) / 255.0
        
        # Expand dimensions to match model input shape [1, height, width, channels]
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    except Exception as e:
        print(f"Error in image preprocessing: {e}")
        return None

def get_prediction(preprocessed_image):
    """Run inference on the preprocessed image using the loaded model."""
    try:
        # Standard TensorFlow model inference
        return model.predict(preprocessed_image)
    except Exception as e:
        print(f"Error during prediction: {e}")
        return None

def load_class_names():
    """Return the hardcoded class names list in the correct order."""
    return [
        'Bisi Bele Bath', 'Chitranna', 'Masala Dosa', 'Mysore Pak', 'Set Dosa',
        'Udupi Sambar', 'biryani', 'chicken curry', 'idli', 'kesari bath', 'ragi mudde'
    ]

def process_output(output_tensor):
    """Process model output to get the most confident food prediction only."""
    food_classes = load_class_names()
    if output_tensor is not None:
        if len(output_tensor.shape) > 1:
            output_array = output_tensor[0]
        else:
            output_array = output_tensor
        # Get the index of the most confident prediction
        top_idx = int(np.argmax(output_array))
        confidence = float(output_array[top_idx])
        if confidence < 0.10 or top_idx >= len(food_classes):
            return []
        food_name = food_classes[top_idx]
        food_info = FOOD_DATABASE.get(food_name, {
            'calories': 0,
            'protein': 0,
            'carbs': 0,
            'fat': 0
        })
        return [{
            'food': food_name,
            'confidence': confidence,
            'calories': food_info.get('calories', 0),
            'protein': food_info.get('protein', 0),
            'carbs': food_info.get('carbs', 0),
            'fat': food_info.get('fat', 0)
        }]
    # Fallback in case of error - return sample data
    return [{
        'food': 'Bisi Bele Bath',
        'confidence': 0.85,
        'calories': FOOD_DATABASE['Bisi Bele Bath']['calories'],
        'protein': FOOD_DATABASE['Bisi Bele Bath']['protein'],
        'carbs': FOOD_DATABASE['Bisi Bele Bath']['carbs'],
        'fat': FOOD_DATABASE['Bisi Bele Bath']['fat']
    }]

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/food')
def food_page():
    return render_template('food.html')

@app.route('/explore')
def explore_page():
    return render_template('explore.html')

@app.route('/analytics')
def analytics_page():
    return render_template('analytics.html')

@app.route('/workout')
def workout_page():
    return render_template('workout.html')

@app.route('/workoutpages/<page_name>')
def workout_pages(page_name):
    try:
        return render_template(f'workoutpages/{page_name}.html')
    except TemplateNotFound:
        return "Page not found", 404

@app.route('/api/analyze', methods=['POST'])
def analyze_image():
    """API endpoint to analyze food images."""
    # Check if image file was sent
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No image selected'}), 400
    
    try:
        # Read image file
        image_bytes = file.read()
        
        # Validate image by trying to open it with PIL
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.verify()  # Verify that it is, in fact, an image
        except Exception as img_err:
            return jsonify({'error': f'Invalid image file: {str(img_err)}'}), 400
        
        # Save the file (optional)
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        with open(file_path, 'wb') as f:
            f.write(image_bytes)
        
        # Preprocess the image
        preprocessed_image = preprocess_image(image_bytes)
        if preprocessed_image is None:
            return jsonify({'error': 'Failed to process image'}), 500
        
        # Make prediction
        if model is None:
            # For demo/testing without a model
            food_classes = load_class_names()
            output = np.random.rand(1, len(food_classes))
        else:
            try:
                output = get_prediction(preprocessed_image)
                if output is None:
                    return jsonify({'error': 'Model prediction failed'}), 500
            except Exception as pred_err:
                return jsonify({'error': f'Error during prediction: {str(pred_err)}'}), 500
        
        # Process the output to get food predictions
        results = process_output(output)
        
        # Calculate total nutrition
        total_calories = sum(item['calories'] for item in results)
        total_protein = sum(item['protein'] for item in results)
        total_carbs = sum(item['carbs'] for item in results)
        total_fat = sum(item['fat'] for item in results)
        
        response = {
            'results': results,
            'totals': {
                'calories': total_calories,
                'protein': total_protein,
                'carbs': total_carbs,
                'fat': total_fat
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': f'Error processing image: {str(e)}'}), 500

@app.route('/api/foods', methods=['GET'])
def get_food_database():
    """Return the food database."""
    return jsonify(FOOD_DATABASE)

if __name__ == '__main__':
    # Try to load the model
    model_loaded = load_model()
    if not model_loaded:
        print("Warning: Model not loaded, running in demo mode")
    
    # Initialize Google Fit routes
    init_google_fit_routes(app)
    
    # Start the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)