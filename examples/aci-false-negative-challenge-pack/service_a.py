# CI-20 fixture part 1/3: hardcoded endpoint repeated across multiple files
DATABASE_URL = "postgresql://prod.example.com/appdb"

def get_connection():
    return DATABASE_URL
