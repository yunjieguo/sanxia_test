"""
数据库迁移脚本：添加 image_path 字段到 annotations 表

运行方式：python migrations/add_image_path_to_annotations.py
"""
import sqlite3
import os
import sys

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings


def migrate():
    """执行迁移"""
    # 从 DATABASE_URL 中提取数据库文件路径
    db_url = settings.DATABASE_URL
    # sqlite:///./app.db -> ./app.db
    db_path = db_url.replace('sqlite:///', '')

    if not os.path.exists(db_path):
        print(f"错误：数据库文件不存在：{db_path}")
        return False

    print(f"开始迁移数据库：{db_path}")

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(annotations)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'image_path' in columns:
            print("image_path 字段已存在，跳过迁移")
            conn.close()
            return True

        # 添加 image_path 字段
        print("正在添加 image_path 字段...")
        cursor.execute("""
            ALTER TABLE annotations
            ADD COLUMN image_path VARCHAR(500)
        """)

        conn.commit()
        print("[OK] image_path 字段添加成功")

        # 验证
        cursor.execute("PRAGMA table_info(annotations)")
        columns = [col[1] for col in cursor.fetchall()]

        if 'image_path' in columns:
            print("[OK] 迁移验证成功")
            conn.close()
            return True
        else:
            print("[ERROR] 迁移验证失败")
            conn.close()
            return False

    except Exception as e:
        print(f"[ERROR] 迁移失败：{e}")
        return False


if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
