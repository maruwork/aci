# CI-20 fixture part 3/3: same hardcoded endpoint (3 occurrences triggers CI-20)
DATABASE_URL = "postgresql://prod.example.com/appdb"

def health_check():
    return DATABASE_URL
