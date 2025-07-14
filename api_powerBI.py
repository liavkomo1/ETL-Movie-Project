from flask import Flask, jsonify
import pyodbc

app = Flask(__name__)

# פרטי החיבור ל-SQL Server
SQL_SERVER = 'DESKTOP-LNT219H'  # שנה אם השרת שלך שונה
DATABASE = 'movies_api'

def get_connection():
    conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SQL_SERVER};DATABASE={DATABASE};Trusted_Connection=yes'
    return pyodbc.connect(conn_str)

@app.route("/movies", methods=["GET"])
def get_movies():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 100 * FROM Movies ORDER BY release_date")
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return jsonify(results)

@app.route("/cast", methods=["GET"])
def get_cast():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 100 * FROM MovieCast")
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return jsonify(results)

@app.route("/crew", methods=["GET"])
def get_crew():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT TOP 100 * FROM MovieCrew")
    columns = [column[0] for column in cursor.description]
    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
    conn.close()
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
