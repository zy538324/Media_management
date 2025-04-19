from werkzeug.security import generate_password_hash
from app import db, create_app  # Ensure create_app is imported
from app.models import User

# Create the Flask application
app = create_app()

# Check if there are any existing users
with app.app_context():
    existing_users = User.query.count()

    if existing_users == 0:
        # Hash the password
        hashed_password = generate_password_hash('', method='pbkdf2:sha256')

        # Create a new admin user
        admin_user = User(
            username='',
            password=hashed_password,
            email='',  # Replace with a valid email as needed
            role='Admin',
            status='Active'
        )

        # Run the database operations within the application context
        with db.session.begin():
            db.session.add(admin_user)
            db.session.commit()

        print("Default admin user created.")
    else:
        print("Users already exist. Skipping first-time setup.")
