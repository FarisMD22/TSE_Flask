import mysql.connector
from mysql.connector import Error


class Database:
    def __init__(self):
        self.host = 'localhost'
        self.user = 'root'
        self.password = 'password'
        self.database = 'hostel_management'
        self.connection = None

    def connect(self):
        """Create database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print("Database connected successfully!")
            return self.connection
        except Error as e:
            print(f"Error connecting to MySQL: {e}")
            return None

    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()

    def execute_query(self,query,params=None):
        """Execute a query and return results"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()
            cursor.execute(query,params or ())
            result = cursor.fetchall()
            cursor.close()
            return result
        except Error as e:
            print(f"Error executing query: {e}")
            return []

    def execute_insert(self,query,params=None):
        """Execute insert query and return last insert id"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()
            cursor.execute(query,params or ())
            self.connection.commit()
            insert_id = cursor.lastrowid
            cursor.close()
            return insert_id
        except Error as e:
            print(f"Error executing insert: {e}")
            if self.connection:
                self.connection.rollback()
            return None

    def execute_update(self,query,params=None):
        """Execute update/delete query and return affected rows"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()

            cursor = self.connection.cursor()
            cursor.execute(query,params or ())
            self.connection.commit()
            affected_rows = cursor.rowcount
            cursor.close()
            return affected_rows
        except Error as e:
            print(f"Error executing update: {e}")
            if self.connection:
                self.connection.rollback()
            return None


# Create global database instance
db = Database()