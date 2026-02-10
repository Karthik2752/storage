import os
import cv2
import imutils
from PIL import Image
import io
import torch
from flask import Flask, request, jsonify, render_template, redirect,url_for
from torchvision import models, transforms
from skimage.metrics import structural_similarity

app = Flask(__name__)
UPLOAD_FOLDER = 'uploaded_images'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load the CNN model once globally
model = models.resnet18(pretrained=False)
model.fc = torch.nn.Linear(model.fc.in_features, 1)
model.load_state_dict(torch.load('cnn_model.pth', map_location=torch.device('cpu')))
model.eval()

# ---------- Image Processing Functions ----------

def process_images(original_image_path, tampered_image_path):
    original = Image.open(original_image_path).resize((250, 160))
    tampered = Image.open(tampered_image_path).resize((250, 160))
    
    original.save(os.path.join(UPLOAD_FOLDER, 'original_resized.png'))
    tampered.save(os.path.join(UPLOAD_FOLDER, 'tampered_resized.png'))

    original_cv = cv2.imread(os.path.join(UPLOAD_FOLDER, 'original_resized.png'))
    tampered_cv = cv2.imread(os.path.join(UPLOAD_FOLDER, 'tampered_resized.png'))

    original_gray = cv2.cvtColor(original_cv, cv2.COLOR_BGR2GRAY)
    tampered_gray = cv2.cvtColor(tampered_cv, cv2.COLOR_BGR2GRAY)

    score, diff = structural_similarity(original_gray, tampered_gray, full=True)
    diff = (diff * 255).astype("uint8")
    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    cnts = imutils.grab_contours(cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE))

    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(original_cv, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.rectangle(tampered_cv, (x, y), (x + w, y + h), (0, 0, 255), 2)

    cv2.imwrite(os.path.join(UPLOAD_FOLDER, 'original_with_contours.png'), original_cv)
    cv2.imwrite(os.path.join(UPLOAD_FOLDER, 'tampered_with_contours.png'), tampered_cv)

    return score

def transform_image(image_bytes):
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    return transform(image).unsqueeze(0)

def predict_image(image_bytes):
    input_tensor = transform_image(image_bytes)
    with torch.no_grad():
        output = model(input_tensor)
    prob = torch.sigmoid(output)
    label = 'Real' if output.item() >= 0 else 'Fake'
    return label, prob.item()

# ---------- Routes ----------

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/home') 
def home():
    return render_template('index.html')

@app.route('/about') 
def about():
    return render_template('about.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'original_image' not in request.files or 'tampered_image' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    original_image_path = os.path.join(UPLOAD_FOLDER, 'original_image.png')
    tampered_image_path = os.path.join(UPLOAD_FOLDER, 'tampered_image.png')

    request.files['original_image'].save(original_image_path)
    request.files['tampered_image'].save(tampered_image_path)

    ssim_score = process_images(original_image_path, tampered_image_path)

    if ssim_score < 0.35:
        status = "⚠️ The document is likely FAKE or TAMPERED."
    elif ssim_score < 0.50:
        status = "⚠️ The document may be suspicious. Needs further verification."
    else:
        status = "✅ The document is likely GENUINE."

    return jsonify({'status': status, 'ssim_score': round(ssim_score, 4)})


@app.route('/p_m', methods=['GET', 'POST'])
def p_m():
    if request.method == 'POST':
        if 'tampered_image' not in request.files:
            return {'status': 'No image file provided.'}, 400

        file = request.files['tampered_image']
        if file.filename == '':
            return {'status': 'No selected file.'}, 400

        try:
            image_bytes = file.read()
            label, probability = predict_image(image_bytes)  # your prediction logic
            return jsonify({'status': label, 'probability': round(probability, 4)})  # Corrected line
        except Exception as e:
            return {'status': f'Error: {str(e)}'}, 500
    else:
        return render_template('pred_upload.html')

import pymysql
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',      # change this
        password='root',  # change this
        database='fake_doc_detection',
        cursorclass=pymysql.cursors.DictCursor
    )
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                # Optional: check if username or email already exists
                check_query = "SELECT * FROM users WHERE username = %s OR email = %s"
                cursor.execute(check_query, (username, email))
                existing_user = cursor.fetchone()
                if existing_user:
                    return "Username or email already taken."

                # Insert new user with plain password (NOT recommended in production)
                sql = "INSERT INTO users (username, email, password) VALUES (%s, %s, %s)"
                cursor.execute(sql, (username, email, password))
                connection.commit()
                return redirect(url_for('login'))
        finally:
            connection.close()

    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        connection = get_db_connection()
        try:
            with connection.cursor() as cursor:
                sql = "SELECT * FROM users WHERE username = %s AND password = %s"
                cursor.execute(sql, (username, password))
                user = cursor.fetchone()

                if user:
                    return redirect(url_for('home'))
                else:
                    return "Invalid username or password."
        finally:
            connection.close()

    return render_template('login.html')



# ---------- Run App ----------

if __name__ == '__main__':
    app.run(debug=True)
