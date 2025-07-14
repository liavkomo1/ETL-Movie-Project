import requests
import pyodbc
from datetime import datetime
import time

API_KEY = '7287494199adfa3a86cb0030b38e9744'
SQL_SERVER = 'DESKTOP-LNT219H'
DATABASE = 'movies_api'

def get_db_connection():
    try:
        connection_string = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE};Trusted_Connection=yes'
        conn = pyodbc.connect(connection_string)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def get_popular_movies(page=1):
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={API_KEY}&language=en-US&page={page}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            json_data = response.json()
            if 'results' not in json_data:
                print(f"⚠️ Page {page} does not contain 'results' key. Full response:")
                print(json_data)
                return []
            return json_data.get('results', [])
        else:
            print(f"❌ Error fetching popular movies page {page}: {response.status_code}")
            print(response.text)
            return []
    except Exception as e:
        print(f"❌ Exception fetching movies page {page}: {e}")
        return []

def get_movie_credits(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}/credits?api_key={API_KEY}&language=en-US"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('cast', []), data.get('crew', [])
        else:
            print(f"❌ Failed to get credits for movie {movie_id}: {response.status_code}")
            print(response.text)
            return [], []
    except Exception as e:
        print(f"❌ Exception getting credits for movie {movie_id}: {e}")
        return [], []

def create_tables_if_not_exist(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Movies' AND xtype='U')
        CREATE TABLE Movies (
            id INT PRIMARY KEY,
            title NVARCHAR(255),
            release_date NVARCHAR(50),
            popularity FLOAT,
            vote_average FLOAT,
            vote_count INT
        )
        """)
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='MovieCast' AND xtype='U')
        CREATE TABLE MovieCast (
            id INT IDENTITY(1,1) PRIMARY KEY,
            movie_id INT,
            cast_id INT,
            name NVARCHAR(255),
            character NVARCHAR(255),
            [order] INT,
            FOREIGN KEY (movie_id) REFERENCES Movies(id)
        )
        """)
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='MovieCrew' AND xtype='U')
        CREATE TABLE MovieCrew (
            id INT IDENTITY(1,1) PRIMARY KEY,
            movie_id INT,
            department NVARCHAR(100),
            job NVARCHAR(100),
            name NVARCHAR(255),
            FOREIGN KEY (movie_id) REFERENCES Movies(id)
        )
        """)
        conn.commit()
        print("✅ Tables created or verified")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

def save_movies(movies, conn):
    if not movies:
        print("⚠️ No movies to save")
        return
    try:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO Movies (id, title, release_date, popularity, vote_average, vote_count)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        inserted = 0
        skipped_due_to_duplicate = 0
        for movie in movies:
            try:
                cursor.execute(insert_query, (
                    movie.get('id', 0),
                    movie.get('title', '')[:255] if movie.get('title') else '',
                    movie.get('release_date', ''),
                    movie.get('popularity', 0),
                    movie.get('vote_average', 0),
                    movie.get('vote_count', 0)
                ))
                inserted += 1
            except pyodbc.IntegrityError as e:
                if 'PRIMARY KEY constraint' in str(e):
                    skipped_due_to_duplicate += 1
                else:
                    raise
        conn.commit()
        print(f"✅ Saved {inserted} movies")
        if skipped_due_to_duplicate > 0:
            print(f"⚠️ Skipped {skipped_due_to_duplicate} movies due to duplicate IDs")
    except Exception as e:
        print(f"❌ Error saving movies: {e}")
        conn.rollback()

def save_cast(cast, movie_id, conn):
    if not cast:
        return
    try:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO MovieCast (movie_id, cast_id, name, character, [order])
        VALUES (?, ?, ?, ?, ?)
        """
        cast_data = []
        for member in cast:
            cast_data.append((
                movie_id,
                member.get('cast_id'),
                member.get('name', '')[:255],
                member.get('character', '')[:255],
                member.get('order', 0)
            ))
        cursor.executemany(insert_query, cast_data)
        conn.commit()
        print(f"🎭 Saved {len(cast_data)} cast members for movie {movie_id}")
    except Exception as e:
        print(f"❌ Error saving cast for movie {movie_id}: {e}")
        conn.rollback()

def save_crew(crew, movie_id, conn):
    if not crew:
        return
    try:
        cursor = conn.cursor()
        insert_query = """
        INSERT INTO MovieCrew (movie_id, department, job, name)
        VALUES (?, ?, ?, ?)
        """
        crew_data = []
        for member in crew:
            crew_data.append((
                movie_id,
                member.get('department', '')[:100],
                member.get('job', '')[:100],
                member.get('name', '')[:255]
            ))
        cursor.executemany(insert_query, crew_data)
        conn.commit()
        print(f"🎬 Saved {len(crew_data)} crew members for movie {movie_id}")
    except Exception as e:
        print(f"❌ Error saving crew for movie {movie_id}: {e}")
        conn.rollback()

def cast_equal(cast1, cast2):
    set1 = set((c.get('cast_id'), c.get('name')) for c in cast1)
    set2 = set((c.get('cast_id'), c.get('name')) for c in cast2)
    return set1 == set2

def crew_equal(crew1, crew2):
    set1 = set((c.get('department'), c.get('job'), c.get('name')) for c in crew1)
    set2 = set((c.get('department'), c.get('job'), c.get('name')) for c in crew2)
    return set1 == set2

def generate_new_movie_id(existing_ids, base_id):
    # כאן אפשר היה להשתמש במזהה ייחודי משולב, אך זה יעמיס על הדאטה בזיכרון
    new_id = base_id + 1000000
    while new_id in existing_ids:
        new_id += 1
    return new_id

def validate_data_integrity(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Movies")
        total_movies = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT movie_id) FROM MovieCast")
        movies_with_cast = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT movie_id) FROM MovieCrew")
        movies_with_crew = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*) FROM Movies
            WHERE id IN (SELECT DISTINCT movie_id FROM MovieCast)
              AND id IN (SELECT DISTINCT movie_id FROM MovieCrew)
        """)
        movies_with_both = cursor.fetchone()[0]

        print("\n----- 🎬 Data Harmony Report -----")
        print(f"🎞️ Total movies: {total_movies}")
        print(f"✅ Movies with both cast & crew: {movies_with_both}")
        print(f"🧍‍♂️ Movies with cast only: {movies_with_cast - movies_with_both}")
        print(f"🎥 Movies with crew only: {movies_with_crew - movies_with_both}")
        print(f"⚠️ Movies with neither: {total_movies - movies_with_cast - movies_with_crew + movies_with_both}")
    except Exception as e:
        print(f"❌ Error in integrity check: {e}")

def run_etl():
    print(f"⚙️ ETL started at {datetime.now()}")
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database, stopping ETL")
        return
    try:
        if not create_tables_if_not_exist(conn):
            return
        all_movies = []
        for page in range(1, 6):
            print(f"📥 Fetching page {page}...")
            movies = get_popular_movies(page)
            if movies:
                all_movies.extend(movies)
            time.sleep(0.5)

        movies_by_id = {}
        for movie in all_movies:
            movie_id = movie.get('id')
            movies_by_id.setdefault(movie_id, []).append(movie)

        cursor = conn.cursor()
        cursor.execute("DELETE FROM MovieCast")
        cursor.execute("DELETE FROM MovieCrew")
        cursor.execute("DELETE FROM Movies")
        conn.commit()
        print("🧹 Cleared tables")

        existing_movie_ids = set()
        skipped = 0
        added_new = 0

        for movie_id, movie_list in movies_by_id.items():
            base_movie = movie_list[0]
            base_cast, base_crew = get_movie_credits(movie_id)

            save_movies([base_movie], conn)
            save_cast(base_cast, movie_id, conn)
            save_crew(base_crew, movie_id, conn)
            existing_movie_ids.add(movie_id)

            for other_movie in movie_list[1:]:
                other_cast, other_crew = get_movie_credits(other_movie['id'])
                if cast_equal(base_cast, other_cast) and crew_equal(base_crew, other_crew):
                    skipped += 1
                    print(f"⚠️ Skipped duplicate movie {other_movie['id']} ({other_movie.get('title')})")
                else:
                    new_id = generate_new_movie_id(existing_movie_ids, other_movie['id'])
                    existing_movie_ids.add(new_id)
                    save_movies([{
                        'id': new_id,
                        'title': other_movie.get('title'),
                        'release_date': other_movie.get('release_date'),
                        'popularity': other_movie.get('popularity'),
                        'vote_average': other_movie.get('vote_average'),
                        'vote_count': other_movie.get('vote_count')
                    }], conn)
                    save_cast(other_cast, new_id, conn)
                    save_crew(other_crew, new_id, conn)
                    added_new += 1

        print(f"\n⚠️ Skipped {skipped} duplicate movies with identical cast & crew")
        print(f"✅ Added {added_new} movies with new IDs due to different cast/crew")
        print(f"✅ ETL finished successfully at {datetime.now()}")
        validate_data_integrity(conn)
    except Exception as e:
        print(f"❌ Error in ETL process: {e}")
    finally:
        conn.close()

def test_connection():
    conn = get_db_connection()
    if conn:
        try:
            conn.cursor().execute("SELECT 1")
            print("✅ Database connection successful")
            conn.close()
            return True
        except:
            return False
    return False

if __name__ == "__main__":
    if not test_connection():
        print("❌ Cannot connect to database, exiting...")
        exit(1)
    while True:
        try:
            run_etl()
        except KeyboardInterrupt:
            print("🛑 ETL stopped by user")
            break
        print("⏲️ Sleeping for 30 minutes...")
        time.sleep(1800)
