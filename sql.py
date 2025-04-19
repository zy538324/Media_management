from sqlalchemy import create_engine, text

# Connect to the database
engine = create_engine("mysql+pymysql://Media_admin:72RedBlueDuckingDorkies!@localhost/Media_management")

# Map invalid values to valid ones
corrections = {
    'TV Show': 'TV',
    'Movies': 'Movie',
    'Songs': 'Music',  # Example corrections
}

# Update invalid values
with engine.connect() as conn:
    for invalid, valid in corrections.items():
        query = text("UPDATE media SET media_type = :valid WHERE media_type = :invalid")
        conn.execute(query, {'valid': valid, 'invalid': invalid})

# Apply ENUM constraint
with engine.connect() as conn:
    conn.execute(text("ALTER TABLE media MODIFY media_type ENUM('Movie', 'TV', 'Music') NOT NULL"))