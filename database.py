import os
import sqlite3
from typing import List, Dict, Any, Optional
from config import DB_PATH

# Detect if we should use PostgreSQL (for cloud deployment)
DATABASE_URL = os.getenv("DATABASE_URL")
IS_POSTGRES = DATABASE_URL is not None and (DATABASE_URL.startswith("postgres://") or DATABASE_URL.startswith("postgresql://"))

if IS_POSTGRES:
    import psycopg2
    from psycopg2.extras import RealDictCursor

def get_db_connection():
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def get_dict_cursor(conn):
    if IS_POSTGRES:
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()

def get_tuple_cursor(conn):
    if IS_POSTGRES:
        return conn.cursor()
    else:
        return conn.cursor()

def execute_query(cursor, query, params=()):
    if IS_POSTGRES:
        # PostgreSQL uses %s placeholders instead of sqlite's ?
        query = query.replace('?', '%s')
    cursor.execute(query, params)

def init_db():
    """Initializes the database schema if it doesn't already exist."""
    conn = get_db_connection()
    cursor = get_tuple_cursor(conn)
    
    if IS_POSTGRES:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                date TEXT NOT NULL,
                amount DOUBLE PRECISION NOT NULL,
                source_account TEXT NOT NULL,
                recipient_or_use TEXT,
                comment TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (date)")
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                source_account TEXT NOT NULL,
                recipient_or_use TEXT,
                comment TEXT
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions (date)")
    
    conn.commit()
    conn.close()

def add_transaction(date: str, amount: float, source_account: str, recipient_or_use: str, comment: str) -> int:
    """Inserts a single transaction and returns its auto-incremented ID."""
    conn = get_db_connection()
    cursor = get_tuple_cursor(conn)
    if IS_POSTGRES:
        cursor.execute("""
            INSERT INTO transactions (date, amount, source_account, recipient_or_use, comment)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (date, amount, source_account, recipient_or_use, comment))
        tx_id = cursor.fetchone()[0]
    else:
        cursor.execute("""
            INSERT INTO transactions (date, amount, source_account, recipient_or_use, comment)
            VALUES (?, ?, ?, ?, ?)
        """, (date, amount, source_account, recipient_or_use, comment))
        tx_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tx_id

def add_transactions(tx_list: List[Dict[str, Any]]) -> List[int]:
    """Inserts a batch of transactions inside a single DB transaction."""
    conn = get_db_connection()
    cursor = get_tuple_cursor(conn)
    ids = []
    try:
        for tx in tx_list:
            if IS_POSTGRES:
                cursor.execute("""
                    INSERT INTO transactions (date, amount, source_account, recipient_or_use, comment)
                    VALUES (%s, %s, %s, %s, %s) RETURNING id
                """, (
                    tx.get("date"),
                    tx.get("amount"),
                    tx.get("source_account"),
                    tx.get("recipient_or_use") or tx.get("recipient"),
                    tx.get("comment")
                ))
                ids.append(cursor.fetchone()[0])
            else:
                cursor.execute("""
                    INSERT INTO transactions (date, amount, source_account, recipient_or_use, comment)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    tx.get("date"),
                    tx.get("amount"),
                    tx.get("source_account"),
                    tx.get("recipient_or_use") or tx.get("recipient"),
                    tx.get("comment")
                ))
                ids.append(cursor.lastrowid)
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
    return ids

def get_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    source_account: Optional[str] = None,
    search: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves list of transactions matching specified filters."""
    conn = get_db_connection()
    cursor = get_dict_cursor(conn)
    
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if source_account:
        query += " AND source_account = ?"
        params.append(source_account)
    if search:
        query += " AND (recipient_or_use LIKE ? OR comment LIKE ?)"
        params.append(f"%{search}%")
        params.append(f"%{search}%")
        
    query += " ORDER BY date DESC, id DESC"
    
    execute_query(cursor, query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def delete_transaction(tx_id: int) -> bool:
    """Deletes a transaction by ID."""
    conn = get_db_connection()
    cursor = get_tuple_cursor(conn)
    execute_query(cursor, "DELETE FROM transactions WHERE id = ?", (tx_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def update_transaction(tx_id: int, updates: Dict[str, Any]) -> bool:
    """Updates a transaction's fields by ID."""
    if not updates:
        return False
    
    conn = get_db_connection()
    cursor = get_tuple_cursor(conn)
    
    fields = []
    params = []
    for key, val in updates.items():
        if key in ["date", "amount", "source_account", "recipient_or_use", "comment"]:
            fields.append(f"{key} = ?")
            params.append(val)
            
    if not fields:
        conn.close()
        return False
        
    params.append(tx_id)
    query = f"UPDATE transactions SET {', '.join(fields)} WHERE id = ?"
    execute_query(cursor, query, params)
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def get_stats() -> Dict[str, Any]:
    """Generates analytics data (totals by account, monthly summaries)."""
    conn = get_db_connection()
    cursor = get_tuple_cursor(conn)
    
    # 1. Total Volume
    cursor.execute("SELECT SUM(amount) FROM transactions")
    total_volume = cursor.fetchone()[0] or 0.0
    
    # 2. Account Breakdown
    cursor.execute("SELECT source_account, SUM(amount), COUNT(id) FROM transactions GROUP BY source_account")
    account_stats = []
    for row in cursor.fetchall():
        account_stats.append({
            "account": row[0],
            "total": row[1] or 0.0,
            "count": row[2]
        })
        
    # 3. Monthly Trend (last 6 months)
    cursor.execute("""
        SELECT SUBSTR(date, 1, 7) as month, SUM(amount) as total
        FROM transactions 
        GROUP BY month 
        ORDER BY month DESC 
        LIMIT 6
    """)
    monthly_trend = []
    for row in cursor.fetchall():
        monthly_trend.append({
            "month": row[0],
            "total": row[1] or 0.0
        })
    # Reverse to keep chronological
    monthly_trend.reverse()
    
    conn.close()
    
    return {
        "total_volume": total_volume,
        "account_stats": account_stats,
        "monthly_trend": monthly_trend
    }
