"""
データベースマイグレーションスクリプト
新しいカラムを追加する
"""
import sqlite3
import os
from config import Config

def migrate_database():
    """データベースに新しいカラムを追加する"""
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'fashion_app.db')
    
    # データベースファイルが存在しない場合は作成
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 新しいカラムを追加（存在しない場合のみ）
        columns_to_add = [
            "detected_colors TEXT",
            "detected_category VARCHAR(20)",
            "detected_subcategory VARCHAR(20)",
            "detection_confidence FLOAT",
            "shape_analysis TEXT",
            "size_estimation TEXT"
        ]
        
        for column in columns_to_add:
            column_name = column.split()[0]
            try:
                cursor.execute(f"ALTER TABLE clothing ADD COLUMN {column}")
                print(f"Added column: {column_name}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    print(f"Column {column_name} already exists, skipping...")
                else:
                    raise e
        
        conn.commit()
        print("Database migration completed successfully!")
        
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()