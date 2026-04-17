import pyodbc

SERVER = "localhost"
DATABASE = "DeltaSupport"
USERNAME = "delta_user"
PASSWORD = "Delta@123456"


def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        f"UID={USERNAME};"
        f"PWD={PASSWORD};"
        "TrustServerCertificate=yes;"
    )