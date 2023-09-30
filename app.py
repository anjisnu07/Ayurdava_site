from flask import Flask, request, render_template, send_file, redirect, url_for
import os
import cv2
import tempfile
from YOLOv6 import YOLOv6
import pymysql
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import io



app = Flask(__name__)


# /Redirect if not logged in


class_names =  ['Aloevera','Amla',
'Bamboo','Betel','Curry','Amruthaballi',
'Arali','Ashoka','Astma_weed','Badipala',
'Ballon_Vine','Beans','Bharmi','Bringaraja'
,'Camphor']

# =======================>Login Start<====================================================================================
# MySQL database configuration
db = pymysql.connect(
    host='dpg-ckas9jvs0fgc739mluig-a',
    user='ayurdava_user_user',
    password='puqmC7NyBsP6kg3Bm9u4vx2z804Ith8x',
    database='postgres://ayurdava_user_user:puqmC7NyBsP6kg3Bm9u4vx2z804Ith8x@dpg-ckas9jvs0fgc739mluig-a/ayurdava_user'
)
# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" 
# Set the secret key
app.secret_key = 'af6367fb7f72e1f1d7d7ab752578a53a26ab7a7ebe718c4d'

class User(UserMixin):
    def __init__(self, user_id, full_name=None, email=None, is_business_person=None):
        self.id = user_id
        self.full_name = full_name
        self.email = email
        self.is_business_person = is_business_person

# Define the user_loader function
@login_manager.user_loader
def load_user(user_id):
    # Load a user from the database using the user_id
    cursor = db.cursor()
    cursor.execute("SELECT id, full_name, email, is_business_person FROM User WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        # Create a User object with user details
        user = User(user_data[0], user_data[1], user_data[2], user_data[3])
        return user
    return None

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Query the database and check the password here
        cursor = db.cursor()
        cursor.execute("SELECT id, email, password FROM User WHERE email = %s", (email,))
        user_data = cursor.fetchone()

        if user_data and check_password_hash(user_data[2], password):
            # Create a User object and log in the user
            user = User(user_data[0], email=user_data[1], is_business_person=False)
            login_user(user)
            return redirect(url_for('upload_image'))
        else:
            return 'Incorrect password. Please try again.'
    
    return render_template('login.html')

# =======================>Login End<====================================================================================
# model init

model_path = "models/best_ckpt_s.onnx"
yolov6_detector = YOLOv6(model_path, conf_thres=0.35, iou_thres=0.5)

@app.route('/', methods=['GET'])
def render_index():
    return render_template('index.html')


@app.route('/whoweare', methods=['GET'])
def render_index2():
    return render_template('whoweare.html')


@app.route('/signup')

def signup_form():
    return render_template('signup.html')

@app.route('/submit', methods=['POST'])
def signup():
    try:
        cursor = db.cursor()

        # Get form data
        full_name = request.form['username']
        email = request.form['mail']
        phone_number = request.form['phone']
        gender = request.form['gender']
        password = request.form['password']  # Add a new field for password

        # Hash the user's password
        hashed_password = generate_password_hash(password, method='sha256')

        # Check if "business" field exists in the form data
        is_business_person = 0  # Default to No
        if 'business' in request.form:
            if request.form['business'] == 'Yes':
                is_business_person = 1  # Set to 1 if "Yes" is selected

        # Insert data into the "User" table, including the hashed password
        sql = "INSERT INTO User (full_name, email, phone_number, gender, password, is_business_person) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (full_name, email, phone_number, gender, hashed_password, is_business_person)
        cursor.execute(sql, values)

        # Commit the transaction
        db.commit()

        registration_successful = True  # Set this flag to True on successful registration
        return render_template('login_after_reg.html', registration_successful=True)
    except Exception as e:
        db.rollback()
        return f'Error: {str(e)}'



# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))




@app.route('/landing', methods=['GET', 'POST'])
@login_required
def upload_image():
    if request.method == 'POST':
        # file upload checking
        if 'image_file' not in request.files:
            return "No file uploaded"

        image_file = request.files['image_file']

        # For filename purpose
        if image_file.filename == '':
            return "No selected file"

        # Saving the image in a folder
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name
            image_file.save(temp_filename)

        # Reading image
        img = cv2.imread(temp_filename)

        # Detect Objects
        boxes, scores, class_ids = yolov6_detector(img)

        # Mapping respective details accord to class
        class_details = {
            'Aloevera': [
        '<strong>1. Anti-inflammatory:</strong> Aloevera leaves contain compounds like bradykinase, which help reduce inflammation when applied topically. It is commonly used for soothing burns, wounds, and skin irritations.',
        '<strong>2.Antimicrobial:</strong> The gel within the leaves has natural antimicrobial properties, making it effective against bacteria, viruses, and fungi.',
        '<strong>3.Moisturizing:</strong> Aloevera leaves are rich in water content and mucilage, making them an excellent natural moisturizer for the skin.',
        ],
            'Amla': [
        '<strong>1. Rich in Vitamin C:</strong> Amla leaves are a great source of vitamin C, which boosts the immune system and helps fight off various infections.',
        '<strong>2. Antioxidant Properties:</strong> The leaves of Amla are packed with antioxidants that protect cells from damage caused by free radicals and help in preventing chronic diseases.',
        '<strong>3. Digestive Aid:</strong> Amla leaves can aid in digestion, as they stimulate the secretion of gastric juices.',
        
        ],
            'Bamboo': [
        '<strong>1. Antibacterial:</strong> Extracts from bamboo leaves have been found to have antibacterial properties, making them useful in traditional medicine for treating infections.',
        '<strong>2. Rich in Silica:</strong> Bamboo leaves are a good source of silica, which is essential for healthy skin, hair, and nails.',
        '<strong>3. Anti-inflammatory:</strong> Compounds in bamboo leaves can have anti-inflammatory effects, potentially aiding in conditions involving inflammation.',
        
        ],
           
            'Betel': [
        '<strong>1. Antimicrobial:</strong> Betel leaves have natural antimicrobial properties and are used traditionally for oral hygiene and treating minor infections.',
        '<strong>2. Digestive Aid:</strong> Chewing betel leaves is believed to aid in digestion and alleviate gastrointestinal issues.',
        '<strong>3. Anti-inflammatory:</strong> The leaves contain compounds that can help reduce inflammation when applied topically.',
        
        ],
            'Curry': [
        '<strong>1. Rich in Antioxidants:</strong> Curry leaves are packed with antioxidants that help in neutralizing harmful free radicals in the body.',
        '<strong>2. Improves Digestion:</strong> The leaves of the curry plant can help improve digestion and treat conditions like indigestion and diarrhea.',
        '<strong>3. Hair Health:</strong> Curry leaves are known for promoting hair health and are often used in hair care remedies.',
        
        ],
            'Amruthaballi': [
        '<strong>1.Immunomodulatory:</strong> Amruthaballi leaves possess immunomodulatory properties, which means they help regulate and strengthen the immune system.',
        '<strong>2. Anti-inflammatory:</strong> The leaves have anti-inflammatory compounds that can help reduce inflammation in the body.',
        '<strong>3. Antioxidant:</strong> Giloy leaves are rich in antioxidants that protect cells from damage and support overall health.',
        
        ],
            'Arali': [
        '<strong>1. Antipyretic:</strong> Arali leaves have been traditionally used as an antipyretic agent, helping to reduce fever.',
        '<strong>2. Analgesic:</strong> They also have analgesic properties, potentially providing pain relief.',
        '<strong>3. Antimicrobial:</strong> Arali leaves may have natural antimicrobial properties useful in treating infections.',
        
        ],
            'Ashoka': [
        '<strong>1. Uterine Tonic:</strong> Ashoka leaves are often used as a uterine tonic, supporting women reproductive health.',
        '<strong>2. Antioxidant:</strong> They contain antioxidants that help protect cells from oxidative damage.',
        '<strong>3. Anti-inflammatory:</strong> Ashoka leaves may possess anti-inflammatory properties, potentially aiding in conditions involving inflammation.',
        
        ],
            'Astma_weed': [
        '<strong>1. Expectorant:</strong> Asthma Weed leaves are known for their expectorant properties, helping to clear mucus from the respiratory system.',
        '<strong>2. Antimicrobial:</strong> They may have natural antimicrobial properties, which can be beneficial in treating infections.',
        '<strong>3. Anti-inflammatory:</strong> Asthma Weed leaves could have anti-inflammatory effects when applied topically.',
        
        ],
            'Badipala': [
        '<strong>1. Digestive Aid:</strong> Badipala leaves are traditionally used to alleviate digestive issues and promote healthy digestion.',
        '<strong>2. Antimicrobial:</strong> They may possess natural antimicrobial properties, aiding in fighting off infections.',
        
        ],
            'Ballon_Vine':[
        '<strong>Anti-inflammatory:</strong> Balloon Vine leaves may have antiinflammatory properties, potentially useful in treating inflammatory conditions.',
        '<strong>Analgesic:</strong> They may provide pain relief when applied topically.',
        '<strong>Antimicrobial:</strong> Balloon Vine leaves could have natural antimicrobial properties useful in treating infections.',

        
        ],
            'Beans': [
        '<strong>1. Rich in Nutrients:</strong> Bean leaves are packed with essential nutrients like vitamins, minerals, and fiber, contributing to overall health.'
        '<strong>2. Antioxidant Properties:</strong> They contain antioxidants that help protect cells from damage caused by free radicals.'
        '<strong>3. Digestive Health:</strong> Bean leaves can aid in digestion due to their fiber content.'
        
        ],
            'Bharmi': [
        '<strong>1. Anti-inflammatory:</strong> Bharmi leaves may possess anti-inflammatory properties, potentially useful in managing inflammatory conditions.',
        '<strong>2. Analgesic:</strong> They may provide pain relief when applied topically.',
        '<strong>3. Antioxidant:</strong> Bharmi leaves could contain antioxidants that help protect cells.',
        
        ],
            'Bringarja': [
        '<strong>1. Hair Health:</strong> Bhringaraja leaves are known for their benefits to hair health, promoting growth and preventing hair loss.',
        '<strong>2. Liver Support:</strong> They are traditionally used to support liver function and detoxification.',
        '<strong>3. Antimicrobial:</strong> Bhringaraja leaves may have natural antimicrobial properties, aiding in treating infections.',
        
        ],
            'camphor': [
        '<strong>1. Topical Analgesic:</strong> Camphor leaves are a source of natural camphor oil which, when applied topically, can provide pain relief and soothe sore muscles.',
        '<strong>2. Respiratory Benefits:</strong> Inhaling the aroma of camphor leaves can help in relieving congestion and is commonly used in decongestant ointments.',
        '<strong>3. Insect Repellent:</strong> Camphor leaves and oil are known to repel insects, making them useful for insect bites and as a natural insecticide.',
        
        ],
           
        }

        # collecting label
        detected_class = class_names[class_ids[0]]

        # mapping deails wrt label
        details = class_details.get(detected_class, ['No details available'])

        details = '<br>'.join(details)

        # Drawing box
        combined_img = yolov6_detector.draw_detections(img)

        # Saving the image + box 
        result_filename = os.path.join("static", "detected_objects.jpg")
        cv2.imwrite(result_filename, combined_img)

        # Remove the temporary file
        os.remove(temp_filename)

        return render_template('result.html', detected_class=detected_class, details=details)

    return render_template('landing.html')

# Your account
from flask import render_template

@app.route('/your_account')
@login_required
def your_account():
    user = current_user  # Get the current logged-in user
    return render_template('youraccount.html', user=user)


@app.route('/get_image')
def get_image():
    image_path = "static/detected_objects.jpg"

 
    img = cv2.imread(image_path)

    # Define the new dimension
    new_width = int(request.args.get('width', 600)) 
    new_height = int(request.args.get('height', 500))  

    # Resize the image
    resized_img = cv2.resize(img, (new_width, new_height))

    # writing back the original image 
    cv2.imwrite(image_path, resized_img)
    return send_file("static/detected_objects.jpg")


if __name__ == '__main__':
    app.run(debug=True)
