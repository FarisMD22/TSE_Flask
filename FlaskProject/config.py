class Config:
    SECRET_KEY = 'your-secret-key-change-in-production'

    # Database Configuration - ✅ Using your password
    DB_HOST = 'localhost'
    DB_USER = 'root'
    DB_PASSWORD = 'password'  # ✅ Matches your database setup
    DB_NAME = 'hostel_management'

    # Flask Configuration
    DEBUG = True
    TESTING = False

    # Application Settings
    ITEMS_PER_PAGE = 20
    MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB