"""
╔══════════════════════════════════════════════════════════════╗
║     WEB BASED SMART WASTE MANAGEMENT SYSTEM                  ║
║     FOR MUNICIPAL SERVICES                                   ║
╠══════════════════════════════════════════════════════════════╣
║  Project Type  : BCA Major Project                           ║
║  Developer     : Aman Verma                                  ║
║  College       : [Your College Name]                         ║
║  Session       : 2024-2025                                   ║
║  Guide         : [Your Guide Name]                           ║
╠══════════════════════════════════════════════════════════════╣
║  Technology Stack:                                           ║
║  - Backend    : Python Flask Framework                       ║
║  - Database   : MySQL (via MySQL Workbench)                  ║
║  - Frontend   : HTML5, CSS3 , JavaScript                      ║
║  - Templates  : Jinja2                                       ║
║  - API        : REST JSON APIs for Mobile App                ║
╚══════════════════════════════════════════════════════════════╝
"""

# ============================================
# IMPORT REQUIRED LIBRARIES
# ============================================
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, session
import mysql.connector  # Library to connect Python with MySQL database
import os  # For file and folder operations
from werkzeug.utils import secure_filename  # For secure file uploads
from functools import wraps  # For creating login decorator

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
# MySQL Workbench connection settings
DB_CONFIG = {
    'host': 'localhost',      # Database server (local machine)
    'user': 'root',           # MySQL username
    'password': 'aman',       # MySQL password
    'database': 'waste_management'  # Database name
}

# ============================================
# ADMIN CREDENTIALS (For Municipality Login)
# ============================================
# In production, these should be stored securely in database
ADMIN_CREDENTIALS = {
    'username': 'admin',
    'password': 'admin123'
}


# ============================================
# HELPER FUNCTIONS
# ============================================

def login_required(f):
    """
    Decorator function to protect admin routes.
    Redirects to login page if user is not authenticated.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Please login to access the dashboard.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def init_database():
    """
    Initialize the database and table if they don't exist.
    This runs automatically when the app starts.
    """
    try:
        # First connect without database to create it
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='aman'
        )
        cursor = conn.cursor()
        
        # Create database if not exists
        cursor.execute("CREATE DATABASE IF NOT EXISTS waste_management")
        cursor.execute("USE waste_management")
        
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


# ============================================
# ROUTE 1: HOME PAGE - User Complaint Form
# ============================================
@app.route('/')
def index():
    """
    Display the garbage reporting page for citizens.
    Users can submit complaints about garbage through this page.
    """
    return render_template('report.html')


# ============================================
# ROUTE: ADMIN LOGIN PAGE
# ============================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Admin login page for municipality staff.
    GET: Display login form
    POST: Validate credentials and create session
    """
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Validate credentials
        if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Login successful! Welcome to the dashboard.', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Invalid username or password!', 'error')
            return redirect(url_for('login'))
    
    return render_template('login.html')


# ============================================
# ROUTE: ADMIN LOGOUT
# ============================================
@app.route('/logout')
def logout():
    """
    Logout admin and clear session.
    Redirects to login page after logout.
    """
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('login'))


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
@login_required  # Protect this route - requires login
def admin():
    """
    Display the municipality dashboard.
    Shows all complaints with images, location, and status.
    Municipality staff can update complaint status from here.
    PROTECTED: Requires admin login to access.
    """
    try:
        connection = get_db_connection()
        if connection is None:
            return render_template('admin.html', complaints=[], error="Database connection failed")
        
        cursor = connection.cursor(dictionary=True)  # Return results as dictionary
        
        # Fetch all complaints ordered by newest first
        cursor.execute("SELECT * FROM complaints ORDER BY created_at DESC")
        complaints = cursor.fetchall()
        
        # Get statistics for dashboard
        cursor.execute("SELECT COUNT(*) as total FROM complaints")
        total = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as pending FROM complaints WHERE status='Pending'")
        pending = cursor.fetchone()['pending']
        
        cursor.execute("SELECT COUNT(*) as cleaned FROM complaints WHERE status='Cleaned'")
        cleaned = cursor.fetchone()['cleaned']
        
        stats = {'total': total, 'pending': pending, 'cleaned': cleaned}
        
        cursor.close()
        connection.close()
        
        return render_template('admin.html', complaints=complaints, stats=stats)
        
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
# ROUTE: DELETE COMPLAINT
# ============================================
@app.route('/delete_complaint/<int:complaint_id>', methods=['POST'])
@login_required
def delete_complaint(complaint_id):
    """
    Delete a complaint from the database.
    Also deletes the associated image file.
    PROTECTED: Requires admin login.
    """
    try:
        connection = get_db_connection()
        if connection is None:
            flash('Database connection failed!', 'error')
            return redirect(url_for('admin'))
        
        cursor = connection.cursor(dictionary=True)
        
        # First, get the image path to delete the file
        cursor.execute("SELECT image_path FROM complaints WHERE id = %s", (complaint_id,))
        complaint = cursor.fetchone()
        
        if complaint and complaint['image_path']:
            # Delete the image file
            image_file = os.path.join(app.config['UPLOAD_FOLDER'], complaint['image_path'])
            if os.path.exists(image_file):
                os.remove(image_file)
        
        # Delete from database
        cursor.execute("DELETE FROM complaints WHERE id = %s", (complaint_id,))
        connection.commit()
        
        cursor.close()
        connection.close()
        
        flash('Complaint deleted successfully!', 'success')
        return redirect(url_for('admin'))
        
    except mysql.connector.Error as err:
        print(f"Database Error: {err}")
        flash('Error deleting complaint.', 'error')
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
    
    # Initialize database on startup
    print("Initializing database...")
    init_database()
    
    print("Server starting...")
    print("User Page: http://localhost:5000/")
    print("Admin Dashboard: http://localhost:5000/admin")
    print("API Endpoint: http://localhost:5000/complaints")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
