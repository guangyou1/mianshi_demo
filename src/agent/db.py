import psycopg2
from dotenv import load_dotenv
import os
#demo
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS stock_analysis (
    id SERIAL PRIMARY KEY,
    stock_data TEXT NOT NULL,
    summary TEXT NOT NULL,
    sentiment VARCHAR(20) NOT NULL,
    risk_level VARCHAR(20) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

_initialized = False


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """激活数据库：建表，确保表结构就绪。应在应用启动时调用一次。"""
    global _initialized
    if _initialized:
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    cur.close()
    conn.close()
    _initialized = True


def save_analysis(stock_data: str, summary: str, sentiment: str, risk_level: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO stock_analysis (stock_data, summary, sentiment, risk_level) VALUES (%s, %s, %s, %s) RETURNING id;",
        (stock_data, summary, sentiment, risk_level),
    )
    record_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    return record_id


def get_all_analysis() -> list[dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, stock_data, summary, sentiment, risk_level, created_at FROM stock_analysis ORDER BY created_at DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [
        {
            "id": row[0],
            "stock_data": row[1],
            "summary": row[2],
            "sentiment": row[3],
            "risk_level": row[4],
            "created_at": row[5],
        }
        for row in rows
    ]


def test_connection():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()[0]
        cur.close()
        conn.close()
        print(f"连接成功！PostgreSQL 版本: {version}")
        return True
    except Exception as e:
        print(f"连接失败: {e}")
        return False


if __name__ == "__main__":
    test_connection()
    init_db()
    print("数据库已激活")
