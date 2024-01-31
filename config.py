import os
from dotenv import load_dotenv

load_dotenv()

postgres_aws_database = os.getenv("DATABASE_URL")