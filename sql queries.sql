SELECT TOP (1000) [id]
      ,[title]
      ,[release_date]
      ,[popularity]
      ,[vote_average]
      ,[vote_count]
  FROM [movies_api].[dbo].[Movies]

  -- שאילתה הבודקת את הפרשי הזמנים בין הפקות שונות של אותו במאי
  WITH directors AS (
    -- שליפה של כל הבמאים והסרטים שלהם
    SELECT 
        c.name AS director_name,
        m.id AS movie_id,
        m.title,
        m.release_date,
        m.vote_average
    FROM MovieCrew c
    JOIN Movies m ON c.movie_id = m.id
    WHERE c.job = 'Director'
      AND m.release_date IS NOT NULL
      AND m.vote_average IS NOT NULL
),

ranked_directors AS (
    -- מיון הסרטים של כל במאי לפי תאריך
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY director_name ORDER BY release_date) AS movie_rank
    FROM directors
),

director_with_previous AS (
    -- מציאת הסרט הקודם של כל במאי
    SELECT 
        curr.director_name,
        curr.title,
        curr.release_date,
        curr.vote_average,
        prev.release_date AS prev_release_date,
        DATEDIFF(DAY, prev.release_date, curr.release_date) AS days_since_last
    FROM ranked_directors curr
    JOIN ranked_directors prev
      ON curr.director_name = prev.director_name
     AND curr.movie_rank = prev.movie_rank + 1
)

SELECT *
FROM director_with_previous
ORDER BY director_name, release_date;

 -- שאילתא הבודקת ממוצע פופולריות של כל סהרטים שיצאו לפני הסרט המסוים בתקופות זמן
SELECT 
    m1.id,
    m1.title,
    m1.release_date,
    m1.popularity AS movie_popularity,

    -- ממוצע הפופולריות של סרטים חודש לפני
    (
        SELECT AVG(m2.popularity)
        FROM movies m2
        WHERE 
            m2.release_date >= DATEADD(DAY, -30, m1.release_date)
            AND m2.release_date < m1.release_date
            AND m2.popularity IS NOT NULL
    ) AS avg_popularity_last_1_month,

    -- ממוצע הפופולריות של סרטים 3 חודשים לפני
    (
        SELECT AVG(m2.popularity)
        FROM movies m2
        WHERE 
            m2.release_date >= DATEADD(DAY, -90, m1.release_date)
            AND m2.release_date < m1.release_date
            AND m2.popularity IS NOT NULL
    ) AS avg_popularity_last_3_months,

    -- ממוצע הפופולריות של סרטים חצי שנה לפני
    (
        SELECT AVG(m2.popularity)
        FROM movies m2
        WHERE 
            m2.release_date >= DATEADD(DAY, -180, m1.release_date)
            AND m2.release_date < m1.release_date
            AND m2.popularity IS NOT NULL
    ) AS avg_popularity_last_6_months

FROM 
    movies m1
WHERE 
    m1.popularity IS NOT NULL
    AND m1.release_date IS NOT NULL
ORDER BY 
    m1.release_date;
--ניקיון הדאטה
select * from Movies
select * from MovieCast
select * from MovieCrew

--בדיקת תקינות שמות הסרטים
select title 
from Movies
where title like '%[^ a-zA-Z0-9]'

SELECT title
FROM Movies
WHERE title LIKE '%&%';

select *
from Movies
where title='Lilo & Stitch'

--בדיקת תקינות טבלת השחקנים
select * from MovieCast
where [id] is null or [movie_id] is null or [cast_id] is null or [name] is null or [character] is null or [order] is null;

--בדיקת תקינות בטבלת הצוות
select * from MovieCrew
where [id] is null or [movie_id] is null or department is null or job is null or [name] is  null;

--בדיקת תקינות פורמט התאריכים: בודק אם יש תאריך ריק או שיש תאריך שלא יכול להיות מומר לסוג תאריך ואם הוא לא יכול הוא יחזיר ערך ריק
SELECT release_date
FROM Movies
WHERE release_date IS NULL
   OR TRY_CONVERT(date, release_date) IS NULL;
--בדיקת סבירות שנים
SELECT *
FROM Movies
WHERE release_date > GETDATE()  -- תאריכים מהעתיד
   OR release_date < '1900-01-01';  -- תאריכים קדומים מדי (לדוגמה)
--בדיקת נכונות מחרוזת התאריכים
SELECT release_date
FROM Movies
WHERE release_date NOT LIKE '[0-9][0-9][0-9][0-9]-%'  -- פורמט לא תקין של שנה
   OR SUBSTRING(release_date, 6, 2) = '00'            -- חודש = 00
   OR SUBSTRING(release_date, 9, 2) = '00'            -- יום = 00
--בדיקת ייחודיות למזהה השחקן 
select distinct id from MovieCast
--בדיקת ייחודיות למזהה הסרט
select distinct movie_id from MovieCast

SELECT cast_id,
       COUNT(*) AS total_rows,
       COUNT(DISTINCT movie_id) AS unique_movies
FROM MovieCast
GROUP BY cast_id
HAVING COUNT(*) != COUNT(DISTINCT movie_id);

SELECT cast_id, movie_id, COUNT(*) as cnt
FROM MovieCast
GROUP BY cast_id, movie_id
HAVING COUNT(*) > 1;

SELECT *
FROM MovieCast mc
WHERE EXISTS (
    SELECT 1
    FROM MovieCast mc2
    WHERE mc.cast_id = mc2.cast_id
      AND mc.movie_id = mc2.movie_id
    GROUP BY cast_id, movie_id
    HAVING COUNT(*) > 1
)
ORDER BY movie_id, cast_id;

--מחיקת כפילויות
WITH DuplicateRows AS (
    SELECT
        id,
        ROW_NUMBER() OVER (PARTITION BY cast_id, movie_id ORDER BY id) AS rn
    FROM MovieCast
)
DELETE FROM DuplicateRows
WHERE rn > 1;

--בדיקת ערכים ריקים בטבלה
SELECT *
FROM MovieCast
WHERE [character] = '' or [name]='';
--מילוי ערכים ריקים בערך null
UPDATE MovieCast
SET character = 'Unknown'
WHERE character IS NULL OR character = '';

UPDATE MovieCast
SET name = 'Unnamed Actor'
WHERE name IS NULL OR name = '';

SELECT 
    movie_id, cast_id, name, character, [order],
    COUNT(*) AS duplicate_count
FROM MovieCast
GROUP BY 
    movie_id, cast_id, name, character, [order]
HAVING COUNT(*) > 1;


--ניתוח מציאת סרטים עם אחוז הצבעות גבוה בהקשר לשחקן שמשחק בו
SELECT 
    m.title AS MovieTitle,
    m.vote_average,
    c.name AS ActorName,
    c.character,
    c.[order]
FROM (
    SELECT TOP 3 id, title, vote_average
    FROM Movies
    ORDER BY vote_average DESC
) AS m
JOIN MovieCast c ON m.id = c.movie_id
ORDER BY m.vote_average DESC, m.title, c.[order];

--דירוג 10 השחקנים המובילים בדירוג ממוצע הסרטים ששיחקו
SELECT TOP 10
    c.name AS ActorName,
    COUNT(DISTINCT c.movie_id) AS MoviesCount,
    AVG(m.vote_average) AS AverageRating
FROM MovieCast c
JOIN Movies m ON c.movie_id = m.id
WHERE c.name IS NOT NULL AND m.vote_average IS NOT NULL
GROUP BY c.name
HAVING COUNT(DISTINCT c.movie_id) >= 2
ORDER BY AverageRating DESC, MoviesCount DESC;
--אותו דבר לאנשי המקצוע :צוות
SELECT TOP 10
    c.name AS CrewName,
    c.job AS Job,
    COUNT(DISTINCT c.movie_id) AS MoviesCount,
    AVG(m.vote_average) AS AverageRating
FROM MovieCrew c
JOIN Movies m ON c.movie_id = m.id
WHERE c.name IS NOT NULL
  AND c.job IS NOT NULL
  AND m.vote_average IS NOT NULL
GROUP BY c.name, c.job
HAVING COUNT(DISTINCT c.movie_id) >= 2
ORDER BY AverageRating DESC, MoviesCount DESC;
--פופולאריות לפי עשור
SELECT 
    (YEAR(release_date) / 10) * 10 AS decade,
    COUNT(*) AS num_movies,
    AVG(popularity) AS avg_popularity
FROM 
    movies
WHERE 
    release_date IS NOT NULL
    AND popularity IS NOT NULL
GROUP BY 
    (YEAR(release_date) / 10) * 10
ORDER BY 
    avg_popularity DESC;
--פופולאריות לפי חודשים של שנות ה-20
SELECT 
   Datename(MONTH,release_date) AS movies_month,
    COUNT(*) AS num_movies,
    AVG(popularity) AS avg_popularity
FROM 
    movies
WHERE 
    release_date IS NOT NULL
    AND popularity IS NOT NULL
GROUP BY 
     (Datename(MONTH,release_date))
ORDER BY 
    avg_popularity DESC;
--ממוצע הפרשי ימים בין השקות של סרטים לכל במאי
WITH director_movies AS (
    SELECT 
        p.name AS director_name,
        m.id AS movie_id,
        m.title,
        m.release_date,
        m.popularity,
        LAG(m.release_date) OVER (PARTITION BY p.name ORDER BY m.release_date) AS prev_release_date
    FROM 
        MovieCrew p
    JOIN 
        movies m ON p.movie_id = m.id
    WHERE 
        p.department = 'Directing' AND p.job = 'Director'
)

SELECT
    director_name,
    COUNT(movie_id) AS num_movies,
    AVG(popularity) AS avg_popularity,
    AVG(DATEDIFF(DAY, prev_release_date, release_date)) AS avg_days_between_releases
FROM
    director_movies
GROUP BY
    director_name
ORDER BY
    avg_popularity DESC;

	SELECT 
    m1.id,
    m1.title,
    m1.release_date,
    m1.popularity AS movie_popularity,

    -- ממוצע הפופולריות של סרטים חודש לפני
    (
        SELECT AVG(m2.popularity)
        FROM movies m2
        WHERE 
            m2.release_date >= DATEADD(DAY, -30, m1.release_date)
            AND m2.release_date < m1.release_date
            AND m2.popularity IS NOT NULL
    ) AS avg_popularity_last_1_month,

    -- ממוצע הפופולריות של סרטים 3 חודשים לפני
    (
        SELECT AVG(m2.popularity)
        FROM movies m2
        WHERE 
            m2.release_date >= DATEADD(DAY, -90, m1.release_date)
            AND m2.release_date < m1.release_date
            AND m2.popularity IS NOT NULL
    ) AS avg_popularity_last_3_months,

    -- ממוצע הפופולריות של סרטים חצי שנה לפני
    (
        SELECT AVG(m2.popularity)
        FROM movies m2
        WHERE 
            m2.release_date >= DATEADD(DAY, -180, m1.release_date)
            AND m2.release_date < m1.release_date
            AND m2.popularity IS NOT NULL
    ) AS avg_popularity_last_6_months

FROM 
    movies m1
WHERE 
    m1.popularity IS NOT NULL
    AND m1.release_date IS NOT NULL
ORDER BY 
    m1.release_date;

	select * from MovieCast