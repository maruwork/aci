# CI-20 fixture part 2/3: same hardcoded endpoint
DATABASE_URL = "postgresql://prod.example.com/appdb"

def create_engine():
    return DATABASE_URL
