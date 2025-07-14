# Movies API & ETL Project

This project extracts movie data from The Movie Database (TMDb) API, stores it in a SQL Server database, exposes a REST API via Flask, and includes a Power BI dashboard for visualization.

---

## Project Structure

- `api_powerBI.py`  
  Flask API exposing endpoints to query the SQL Server database:
  - `/movies` - returns top 100 movies ordered by release date  
  - `/cast` - returns top 100 cast members  
  - `/crew` - returns top 100 crew members  

- `main_api_pipeline.py`  
  ETL pipeline that:
  - Fetches popular movies and their credits from TMDb API  
  - Creates necessary SQL tables if they don't exist  
  - Inserts and updates data in the SQL Server database  
  - Performs data integrity checks  
  - Runs continuously every 30 minutes (can be stopped with Ctrl+C)  

- `queries.sql`  
  SQL queries for:
  - Data validation and cleaning  
  - Analytical queries on movies, cast, and crew  
  - Popularity analysis by decade and month  
  - Directors' release patterns  

- `dashboard.png`  
  Screenshot of the Power BI dashboard visualizing the movie data.

---

## Requirements

- Python 3.x  
- Packages:
  - `flask`
  - `pyodbc`
  - `requests`  
- SQL Server with ODBC Driver 17 installed  
- TMDb API key (replace `API_KEY` in `main_api_pipeline.py`)  
- Power BI Desktop (to open and modify the dashboard)

---

## Setup Instructions

1. **Database Setup**  
   - Ensure SQL Server is running on your machine (`DESKTOP-LNT219H` or update server name in scripts).  
   - The database `movies_api` should exist (create it if needed).  
   - The ETL script will create tables `Movies`, `MovieCast`, and `MovieCrew` if not present.

2. **Python Environment**  
   - Install required packages:  
     ```bash
     pip install flask pyodbc requests
     ```  
   - Replace `API_KEY` in `main_api_pipeline.py` with your TMDb API key.  
   - Verify your SQL Server connection parameters in both Python scripts.

3. **Running the ETL Pipeline**  
   ```bash
   python main_api_pipeline.py
   ```  
   The pipeline fetches movie data every 30 minutes. Use Ctrl+C to stop.

4. **Running the Flask API**  
   ```bash
   python api_powerBI.py
   ```  
   API will be accessible at `http://127.0.0.1:5000/`

5. **Power BI Dashboard**  
   - Open `dashboard.png` for a snapshot of the dashboard.  
   - To modify or refresh the dashboard, open the corresponding `.pbix` file in Power BI Desktop (if available).

---

## Usage Examples

- Get movies list:  
  `GET http://127.0.0.1:5000/movies`

- Get cast list:  
  `GET http://127.0.0.1:5000/cast`

- Get crew list:  
  `GET http://127.0.0.1:5000/crew`

---

## Notes

- The ETL pipeline handles duplicate movies by comparing cast and crew data.  
- Extensive SQL queries in `queries.sql` enable detailed analysis and data quality checks.  
- Customize the dashboard with Power BI for richer visual insights.

---
