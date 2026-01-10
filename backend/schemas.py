from pydantic import BaseModel

# 这里专门存放“前端发来的数据格式”
# Pydantic 用来校验数据，确保前端没乱发
class TextRequest(BaseModel):
    text: str