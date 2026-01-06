from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# 1. 指定数据库地址
# 这会在你的 backend 目录下生成一个叫 sql_app.db 的文件
# 1. 自动获取当前文件 (database.py) 所在的绝对路径
# __file__ 是当前文件的名字
# dirname 也就是拿到 ".../backend" 这个目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 2. 拼接出数据库文件的完整路径
# 结果类似: /Users/你的名字/项目/backend/sql_app.db
DB_FILE_PATH = os.path.join(BASE_DIR, "sql_app.db")

# 3. 赋值给 SQLAlchemy
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE_PATH}"

# 2. 创建引擎 (也就是连接器)
# connect_args={"check_same_thread": False} 是 SQLite 专用的配置
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. 创建会话工厂
# 以后我们要读写数据，都要通过这个 SessionLocal 领号
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. 创建基础模型类
# 后面我们要定义的表，都要继承这个 Base
Base = declarative_base()

# --- 定义我们的第一张表 ---
class AnalysisRecord(Base):
    __tablename__ = "analysis_records" # 在数据库里的表名

    id = Column(Integer, primary_key=True, index=True) # 身份证号 (自增)
    text_content = Column(Text)       # 用户输入的内容
    ai_reply = Column(Text)           # AI 回复的内容
    sentiment = Column(String)        # 情感倾向
    word_count = Column(Integer)      # 字数