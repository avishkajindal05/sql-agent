import mysql.connector
import pandas as pd

#python code to connect to sql server
DB_CONFIG = {
    'host' : 'localhost',
    'user' : 'sqlprojectwfour',
    'password' : '05072004'
}

def get_connection():
    config = DB_CONFIG.copy()
    config['database'] = 'sql_teaching'
    return mysql.connector.connect(**config)

def init_db():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()  #cursor helps use traverse the sql database
    
    cursor.execute("CREATE DATABASE IF NOT EXISTS sql_teaching")
    conn.commit()
    
    cursor.close()
    conn.close()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS students(
                       id INT AUTO_INCREMENT PRIMARY KEY,
                       name VARCHAR(255) NOT NULL,
                       age INT
                   )
                   """)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS courses(
                       id INT AUTO_INCREMENT PRIMARY KEY,
                       name VARCHAR(255) NOT NULL
                   )
                   """)
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS enrollments(
                       id INT AUTO_INCREMENT PRIMARY KEY,
                       sid INT,
                       cid INT,
                       MARKS INT,
                       FOREIGN KEY (sid) REFERNECES students(id) ON DELETE CASCADE,
                       FOREIGN KEY (sid) REFERNECES courses(id) ON DELETE CASCADE
                       )
                       """)
    conn.commit()
    cursor.close()
    conn.close()

def add_student(name, age):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO students (name, age) VALUES (%s, %s)", (name, age))
    conn.commit()
    cursor.close()
    conn.close()
    return "Student added"

def add_course(name):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO courses (name) VALUES (%s)", (name))
    conn.commit()
    cursor.close()
    conn.close()
    return "Course added"

def enroll(sid, cid, marks):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO enrollments (sid, cid, marks) VALUES (%s, %s, %s)", (sid, cid, marks))
    conn.commit()
    cursor.close()
    conn.close()
    return "Enrolled Successfully"

def update_student(id, name, age):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE students SET name = %s, age = %s WHERE id = %s", (name, age, id))
    conn.commit()
    cursor.close()
    conn.close()
    return "student updated"

def delete_student(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = %s", (id))
    conn.commit()
    cursor.close()
    conn.close()
    return "student deleted"

def get_join_data():
    query = """
    SELECT s.name as student, c.name as course, e.marks
    FROM students s
    INNER JOIN enrollments e ON s.id = e.id
    INNER JOIN courses c ON e.cid = c.id
    """
    return execute_sql(query)
    
def get_left_join_data():
    query = """
    SELECT s.name as Student, e.amrks
    FROM students s 
    LEFT JOIN enrollments e ON s.id = e.id
    """
    return execute_sql(query)

def get_group_data():
    query = """
    SELECT age, COUNT(*) as Count FROM students GROUP BY age  """
    return execute_sql(query)
def get_subquery_data():
    query = """
    SELECT name FROM students WHERE id IN (SELECT sid FROM enrollments WHERE marks > 80)
    """
    return execute_sql(query)

def get_window_data():
    query ="""
    SELECT sid, marks,
    RANK() OVER (ORDER BY marks DESC) as ranking
    FROM enrollments
    """
    return execute_sql(query)

def execute_sql():
    conn.get_connection()
    try:
        df = pd.read_sql(query, conn)
        return df, "Success"
    except Exception as e:
        return pd.DataFrame(), str(e)
    finally:
        conn.close()


        