from sqlalchemy import Column, Integer, String, Text
from .database import Base


# --- 定义我们的第一张表 ---
class AnalysisRecord(Base):
    __tablename__ = "analysis_records"  # 在数据库里的表名

    id = Column(Integer, primary_key=True, index=True)  # 身份证号 (自增)
    text_content = Column(Text)  # 用户输入的内容
    ai_reply = Column(Text)  # AI 回复的内容
    sentiment = Column(String)  # 情感倾向
    word_count = Column(Integer)  # 字数
