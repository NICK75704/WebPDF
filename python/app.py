from flask import Flask, render_template, request, send_from_directory, jsonify
import pdf2image
import os
import base64
from PyPDF2 import PdfWriter, PdfReader
from io import BytesIO
from reportlab.pdfgen import canvas as rl_canvas
from PIL import Image
from pdf2image import convert_from_path
from PIL import Image


app = Flask(__name__)

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'pdf'}

last_uploaded_pdf = ""  # Global variable to track the last uploaded PDF

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    global last_uploaded_pdf
    if request.method == 'POST':
        file = request.files['pdf_file']
        if file and allowed_file(file.filename):
            filename = file.filename
            last_uploaded_pdf = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # Update the path
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            images = pdf2image.convert_from_path(file_path)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename + ".png")
            images[0].save(image_path, 'PNG')
            
            return render_template('index.html', image_path=f"/uploads/{filename}.png")

    return render_template('index.html', image_path=None)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/save', methods=['POST'])
def save_edited_pdf():
    data = request.json
    global last_uploaded_pdf
    if not last_uploaded_pdf or not os.path.exists(last_uploaded_pdf):
        return jsonify({"error": "No PDF file has been uploaded."}), 40
    image_data = data['imageData'].split(",")[1]
    decoded_image_data = base64.b64decode(image_data)

    # Convert image data to Pillow Image
    image = Image.open(BytesIO(decoded_image_data))

    # Save the edited image temporarily
    image_temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_edited_image.png')
    image.save(image_temp_path, "PNG")

    # Use the global variable to get the path of the original PDF
    original_pdf_path = last_uploaded_pdf

    # Add the image to the PDF
    new_pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'edited_pdf.pdf')
    add_image_to_pdf(original_pdf_path, image_temp_path, new_pdf_path)

    # Send the edited PDF to the client
    return send_from_directory(app.config['UPLOAD_FOLDER'], 'edited_pdf.pdf')

def add_image_to_pdf(pdf_path, canvas_image_path, output_path):
    from pdf2image import convert_from_path
    from PIL import Image

    # 1. Convert PDF's specific page to an image
    pdf_images = convert_from_path(pdf_path)
    base_image = pdf_images[0]  # Assuming we're working with the first page; adjust as needed

    # 2. Overlay the transparent canvas image onto this image
    canvas_image = Image.open(canvas_image_path)
    base_image.paste(canvas_image, (0, 0), canvas_image)  # Using canvas_image as mask ensures transparency is respected

    # Save the merged image temporarily
    merged_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_merged_image.png')
    base_image.save(merged_image_path, 'PNG')

    # 3. Convert the combined image back to a PDF
    img_to_pdf = Image.open(merged_image_path)
    img_to_pdf.save(output_path, "PDF")


if __name__ == "__main__":
    app.run(debug=True)
