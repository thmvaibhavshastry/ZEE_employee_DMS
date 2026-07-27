import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'emp-mgmt-secret-key-2026')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///emp_mgmt.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
