"""
============================================
Web Based Smart Waste Management System
for Municipal Services
============================================
BCA Major Project - Flask Backend
============================================
This file contains the main Flask application
that handles all routes and database operations.
============================================
"""

# ============================================
# IMPORT REQUIRED LIBRARIES
# ============================================
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import mysql.connector  # Library to connect Python with MySQL database
import os  # For file and folder operations
from werkzeug.utils import secure_filename  # For secure file uploads
import time  # For generating unique filenames

# ============================================
# FLASK APP CONFIGURATION
# ============================================
app = Flask(__name__)

# Secret key for session management and flash messages
app.secret_key = 'waste_management_secret_key_2024'

# Configure upload folder for garbage images
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allowed file extensions for image upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# ============================================
# DATABASE CONFIGURATION
# ============================================
# MySQL connection settings - Uses Railway environment variables if available
# Falls back to local settings for development
DB_CONFIG = {
    'host': os.environ.get('MYSQLHOST', 'localhost'),
    'user': os.environ.get('MYSQLUSER', 'root'),
    'password': os.environ.get('MYSQLPASSWORD', 'aman'),
    'database': os.environ.get('MYSQLDATABASE', 'waste_management'),
    'port': int(os.environ.get('MYSQLPORT', 3306))
}   


# ============================================
# HELPER FUNCTIONS
# ============================================

def init_database():
    """
    Initialize the database and table if they don't exist.
    This runs automatically when the app starts.
    """
    try:
        # First connect without database to create it
        conn = mysql.connector.connect(
            host=os.environ.get('MYSQLHOST', 'localhost'),
            user=os.environ.get('MYSQLUSER', 'root'),
            password=os.environ.get('MYSQLPASSWORD', 'aman'),
            port=int(os.environ.get('MYSQLPORT', 3306))
        )
        cursor = conn.cursor()
        
        # Create database if not exists (Railway creates DB automatically)
        db_name = os.environ.get('MYSQLDATABASE', 'waste_management')
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
        cursor.execute(f"USE {db_name}")
        
        # Create complaints table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS complaints (
                id INT PRIMARY KEY AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                area VARCHAR(100) NOT NULL,
                description TEXT,
                latitude VARCHAR(50),
                longitude VARCHAR(50),
                image_path VARCHAR(255),
                status VARCHAR(50) DEFAULT 'Pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database initialized successfully!")
        return True
    except mysql.connector.Error as err:
        print(f"❌ Database initialization error: {err}")
        return False


def get_db_connection():
    """
    Create and return a database connection.
    This function is called whenever we need to interact with MySQL.
    """
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None


def allowed_file(filename):
    """
    Check if the uploaded file has an allowed extension.
    Returns True if file extension is valid (png, jpg, jpeg, gif).
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Flag to track if database is initialized
_db_initialized = False

def ensure_db_initialized():
    """Initialize database on first use (not during build)"""
    global _db_initialized
    if not _db_initialized:
        try:
            init_database()
            _db_initialized = True
        except Exception as e:
            print(f"Database init error: {e}")


# ============================================
# ROUTE 1: HOME PAGE - User Complaint Form
# ============================================
@app.route('/')
def index():
    """
    Display the garbage reporting page for citizens.
    Users can submit complaints about garbage through this page.
    """
    ensure_db_initialized()
    return render_template('report.html')


# ============================================
# ROUTE 2: SUBMIT COMPLAINT
# ============================================
@app.route('/submit_complaint', methods=['POST'])
def submit_complaint():
    """
    Handle complaint submission from both web form and mobile app.
    Accepts: name, area, description, latitude, longitude, image
    Saves image to uploads folder and data to MySQL database.
    """
    try:
        # Get form data from the request
        name = request.form.get('name')
        area = request.form.get('area')
        description = request.form.get('description')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        
        # Handle image upload
        image_path = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '' and allowed_file(file.filename):
                # Secure the filename to prevent security issues
                filename = secure_filename(file.filename)
                # Create unique filename using timestamp
                import time
                unique_filename = f"{int(time.time())}_{filename}"
                # Save file to uploads folder
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                file.save(file_path)
                image_path = unique_filename
        
        # Connect to database
        connection = get_db_connection()
        if connection is None:
            flash('Database connection failed!', 'error')
            return redirect(url_for('index'))
        
        cursor = connection.cursor()
        
        # SQL query to insert complaint data
        insert_query = """
            INSERT INTO complaints (name, area, description, latitude, longitude, image_path, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
        """
        
        # Execute the query with complaint data
        cursor.execute(insert_query, (name, area, description, latitude, longitude, image_path))
        
        # Commit the transaction to save changes
        connection.commit()
        
        # Close database connection
        cursor.close()
        connection.close()
        
        flash('Complaint submitted successfully!', 'success')
        return redirect(url_for('index'))
        
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        flash('Error submitting complaint. Please try again.', 'error')
        return redirect(url_for('index'))
    except Exception as e:
        print(f"Error: {e}")
        flash('An unexpected error occurred.', 'error')
        return redirect(url_for('index'))


# ============================================
# ROUTE 3: ADMIN DASHBOARD
# ============================================
@app.route('/admin')
def admin():
    """
    Display the municipality dashboard.
    Shows all complaints with images, location, and status.
    Municipality staff can update complaint status from here.
    """
    ensure_db_initialized()
    try:
        connection = get_db_connection()
        if connection is None:
            return render_template('admin.html', complaints=[], error="Database connection failed")
        
        cursor = connection.cursor(dictionary=True)  # Return results as dictionary
        
        # Fetch all complaints ordered by newest first
        cursor.execute("SELECT * FROM complaints ORDER BY created_at DESC")
        complaints = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        return render_template('admin.html', complaints=complaints)
        
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return render_template('admin.html', complaints=[], error="Database error occurred")


# ============================================
# ROUTE 4: UPDATE COMPLAINT STATUS
# ============================================
@app.route('/update_status', methods=['POST'])
def update_status():
    """
    Update the status of a complaint (Pending / Cleaned).
    Called when municipality staff marks a complaint as resolved.
    """
    try:
        # Get complaint ID and new status from form or JSON
        if request.is_json:
            # For API calls (Flutter app)
            data = request.get_json()
            complaint_id = data.get('id')
            new_status = data.get('status')
        else:
            # For web form submission
            complaint_id = request.form.get('id')
            new_status = request.form.get('status')
        
        connection = get_db_connection()
        if connection is None:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Database connection failed'}), 500
            flash('Database connection failed!', 'error')
            return redirect(url_for('admin'))
        
        cursor = connection.cursor()
        
        # Update query
        update_query = "UPDATE complaints SET status = %s WHERE id = %s"
        cursor.execute(update_query, (new_status, complaint_id))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        
        flash('Status updated successfully!', 'success')
        return redirect(url_for('admin'))
        
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        if request.is_json:
            return jsonify({'success': False, 'message': str(err)}), 500
        flash('Error updating status.', 'error')
        return redirect(url_for('admin'))


# ============================================
# ROUTE 5: API - GET ALL COMPLAINTS (JSON)
# ============================================
@app.route('/complaints', methods=['GET'])
def get_complaints():
    """
    REST API endpoint to get all complaints in JSON format.
    This API is designed to be used by Flutter mobile app (Android & iOS).
    Returns: JSON array of all complaints
    """
    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor(dictionary=True)
        
        # Fetch all complaints
        cursor.execute("SELECT * FROM complaints ORDER BY created_at DESC")
        complaints = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        # Convert datetime objects to string for JSON serialization
        for complaint in complaints:
            if complaint.get('created_at'):
                complaint['created_at'] = complaint['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify({
            'success': True,
            'data': complaints,
            'count': len(complaints)
        })
        
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        return jsonify({'success': False, 'message': str(err)}), 500


# ============================================
# ROUTE 6: API - SUBMIT COMPLAINT (JSON)
# ============================================
@app.route('/api/submit_complaint', methods=['POST'])
def api_submit_complaint():
    """
    REST API endpoint for submitting complaints from Flutter app.
    Accepts JSON data or multipart/form-data.
    Returns: JSON response with success status.
    """
    try:
        # Check if request is JSON or form data
        if request.is_json:
            data = request.get_json()
            name = data.get('name')
            area = data.get('area')
            description = data.get('description')
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            image_path = data.get('image_path')  # For JSON, image should be pre-uploaded
        else:
            # Handle form data (for image upload)
            name = request.form.get('name')
            area = request.form.get('area')
            description = request.form.get('description')
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            
            # Handle image upload
            image_path = None
            if 'image' in request.files:
                file = request.files['image']
                if file and file.filename != '' and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    import time
                    unique_filename = f"{int(time.time())}_{filename}"
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    image_path = unique_filename
        
        connection = get_db_connection()
        if connection is None:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = connection.cursor()
        
        insert_query = """
            INSERT INTO complaints (name, area, description, latitude, longitude, image_path, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
        """
        
        cursor.execute(insert_query, (name, area, description, latitude, longitude, image_path))
        connection.commit()
        
        # Get the ID of the inserted complaint
        complaint_id = cursor.lastrowid
        
        cursor.close()
        connection.close()
        
        return jsonify({
            'success': True,
            'message': 'Complaint submitted successfully',
            'complaint_id': complaint_id
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# ROUTE 7: SERVE UPLOADED IMAGES
# ============================================
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    Serve uploaded images from the uploads folder.
    This allows displaying garbage images in the admin dashboard.
    """
    from flask import send_from_directory
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ============================================
# MAIN ENTRY POINT
# ============================================
if __name__ == '__main__':
    """
    Run the Flask development server.
    Debug mode is enabled for development (shows detailed errors).
    Host '0.0.0.0' allows access from other devices on the network.
    """
    print("=" * 50)
    print("Web Based Smart Waste Management System")
    print("for Municipal Services")
    print("=" * 50)
    
    # Initialize database on startup (local development)
    init_database()
    
    # Get port from environment variable (Railway sets this)
    port = int(os.environ.get('PORT', 5000))
    
    print("Server starting...")
    print(f"User Page: http://localhost:{port}/")
    print(f"Admin Dashboard: http://localhost:{port}/admin")
    print(f"API Endpoint: http://localhost:{port}/complaints")
    print("=" * 50)
    
    app.run(debug=False, host='0.0.0.0', port=port)
