import json
import pyodbc
from utils.path_helper import resource_path

class DBManager:
    def __init__(self):
        self.conn = None

    # -------------------------
    # Connect to DB
    # -------------------------
    def connect(self, platform):
        config_path = resource_path("config/db_connection.json")

        with open(config_path) as f:
            config = json.load(f)

        conn_str = config[platform]["conn_str"]
        self.conn = pyodbc.connect(conn_str)

    # -------------------------
    # Search customers
    # -------------------------
    def search_customer(self, customer_name):
        cursor = self.conn.cursor()
        query = """
            SELECT TenantId, TenantName, CustomerName, TenantGuid
            FROM Tenants
            WHERE CustomerName LIKE ?
        """
        cursor.execute(query, f"%{customer_name}%")
        return cursor.fetchall()

    # -------------------------
    # Get ALL active refresh tokens (ordered)
    # -------------------------
    def get_refresh_tokens(self, tenant_id):
        cursor = self.conn.cursor()
        query = """
            SELECT RefreshToken
            FROM TenantTokens
            WHERE TenantId = ?
              AND IsActive = 1
            ORDER BY Recordid DESC
        """
        cursor.execute(query, tenant_id)
        rows = cursor.fetchall()

        return [row.RefreshToken for row in rows]

    # -------------------------
    # Close DB
    # -------------------------
    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
