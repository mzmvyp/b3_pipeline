# src/config.py
import os
from dotenv import load_dotenv

load_dotenv() # Carrega as variáveis de ambiente do arquivo .env

class Config:
    # Flask app settings
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    TESTING = False

    # AWS S3 Configurations - Using values from your original script as defaults
    AWS_ACCESS_KEY_ID = os.getenv('REDACTED_AWS_ACCESS_KEY_ID_LEGACY')
    AWS_SECRET_ACCESS_KEY = os.getenv('REDACTED_AWS_SECRET_ACCESS_KEY_LEGACY')
    AWS_DEFAULT_REGION = os.getenv('AWS_DEFAULT_REGION', 'sa-east-1') # Default to 'sa-east-1' from your original script

    # S3 Bucket for scraping target - using value from your original script as default
    SCRAPING_TARGET_S3_BUCKET = os.getenv('SCRAPING_TARGET_S3_BUCKET', 'your-s3-bucket-name')

    # Athena Configurations (if used)
    ATHENA_DATABASE = os.getenv('ATHENA_DATABASE', 'your_athena_database') # Replace with your Athena DB name
    ATHENA_OUTPUT_LOCATION = os.getenv('ATHENA_OUTPUT_LOCATION', f's3://{SCRAPING_TARGET_S3_BUCKET}/athena-query-results/') 

    # --- Basic Validation (Highly Recommended) ---
    if not AWS_ACCESS_KEY_ID:
        print("WARNING: AWS_ACCESS_KEY_ID environment variable not set. AWS operations may fail.")
    if not AWS_SECRET_ACCESS_KEY:
        print("WARNING: AWS_SECRET_ACCESS_KEY environment variable not set. AWS operations may fail.")
    if not SCRAPING_TARGET_S3_BUCKET:
        print("WARNING: SCRAPING_TARGET_S3_BUCKET environment variable not set. Scraping upload may fail.")