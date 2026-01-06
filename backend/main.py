import time, os, json
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI  # 引入异步通讯器
from dotenv import load_dotenv  # 引入环境变量加载器
from sqlalchemy.orm import Session
from sqlalchemy import desc

# --- 引入我们刚才写的数据库配置 ---
from .database import engine, SessionLocal, Base, AnalysisRecord

# 1. 加载 .env 文件里的配置
load_dotenv()

# 2. 初始化 OpenAI 客户端
# 它会自动读取环境变量里的 AI_API_KEY，但 Base URL 需要手动指定
client = AsyncOpenAI(base_url=os.getenv("AI_BASE_URL"), api_key=os.getenv("AI_API_KEY"))

# --- 关键动作：自动创建数据库表 ---
# 这一行代码运行后，会自动生成 sql_app.db 文件
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- 关键配置：解决跨域问题 (CORS) ---
# 允许前端 (http://localhost:5173) 访问后端
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 数据库依赖项 ---
# 这是一个“借还”机制：
# 每次请求来了，借你一个 db 会话；请求结束了，自动关闭 db。
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 定义数据格式 ---
class TextRequest(BaseModel):
    text: str


# --- 核心功能：文本分析接口 ---
@app.post("/analyze")
async def analyze_text(request: TextRequest, db: Session = Depends(get_db)):  # 注入 db
    # 检查是否配置了 Key
    if not os.getenv("AI_API_KEY"):
        raise HTTPException(status_code=500, detail="后端未配置 API Key")

    try:
        # 1. 调用 AI
        # 这是一个耗时操作，所以要用 await
        response = await client.chat.completions.create(
            model="deepseek-v3.1",  # 如果用 Kimi 改成 "moonshot-v1-8k"
            messages=[
                # 系统提示词：给 AI 设定人设
                {
                    "role": "system",
                    "content": "你是一个幽默且专业的文本分析助手。请分析用户发来的文本，并返回JSON格式结果。",
                },
                # 用户的问题：要求它按我们前端需要的格式返回
                {
                    "role": "user",
                    "content": f"""
                请分析这段话：'{request.text}'
                
                请直接返回纯 JSON 格式（不要用 ```json 包裹），必须包含以下字段：
                1. length (数字): 字数
                2. is_question (布尔值): 是否包含疑问
                3. sentiment (字符串): 情感倾向（积极/消极/中性/愤怒等）
                4. keywords (数组): 提取3个关键词
                5. ai_reply (字符串): 你对这段话的幽默回复
                """,
                },
            ],
            temperature=0.7,
        )

        # 2. 解析数据
        # 获取 AI 的回答内容
        raw_content = response.choices[0].message.content

        # # =========== 新增：在这里打印查看 ============
        # print("\n" + "=" * 20 + " AI 原始数据 " + "=" * 20)
        # print(response.choices[0])  # 这行代码会把内容输出到你的 VS Code 终端
        # print("=" * 55 + "\n")
        # # ===========================================

        # 因为大模型有时候会返回多余的文字，我们需要简单清洗一下，确保是 JSON
        # 这里为了演示简单，我们假设 AI 很听话返回了纯 JSON
        # 在生产环境中，这里通常需要更复杂的解析逻辑

        # 尝试清洗一下（去掉可能的 markdown 符号）
        clean_content = raw_content.replace("```json", "").replace("```", "").strip()

        result = json.loads(clean_content)

        # =========== 新增：存入数据库 ===========
        print(f"正在保存数据: {request.text[:10]}...")

        # 创建一条新记录对象
        db_record = AnalysisRecord(
            text_content=request.text,
            ai_reply=result["ai_reply"],
            sentiment=result["sentiment"],
            word_count=result["length"],
        )

        db.add(db_record)  # 把记录放进购物车
        db.commit()  # 结账 (真正写入文件)
        db.refresh(db_record)  # 刷新 (为了拿到自增的 id)

        print(f"✅ 保存成功！记录ID: {db_record.id}")
        # ======================================

        return result

    except Exception as e:
        print(f"出错: {e}")
        return {
            "length": 0,
            "is_question": False,
            "sentiment": "Error",
            "keywords": [],
            "ai_reply": f"系统错误: {str(e)}",
        }


# ✅✅✅ 关键点 2：补上获取历史记录的接口 ✅✅✅
# 如果没有这个，你前端下面的列表就拿不到数据
@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    records = db.query(AnalysisRecord).order_by(desc(AnalysisRecord.id)).limit(10).all()
    return records


# --- 新增：流式聊天接口 ---
@app.post("/chat")
async def chat_stream(request: TextRequest,db:Session = Depends(get_db)):
    # 1. 定义一个生成器函数 (Generator)
    # 它的作用是：一边收 AI 的字，一边往外吐
    async def generate():
        accumulated_reply = ''
        try:
            stream = await client.chat.completions.create(
                model="deepseek-v3.1",  # 或者你正在用的 deepseek-v3.1
                messages=[
                    {"role": "system", "content": "你是一个乐于助人的聊天助手。"},
                    {"role": "user", "content": request.text},
                ],
                stream=True,  # <--- 关键开关！开启流式模式
            )

            # 循环读取每一个“碎片”
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    # 1。yield 是 Python 生成器的语法，意思是“产出这一小块”
                    accumulated_reply += content
                    # 可以在这里打印看看：print(content, end="")
                    yield content
                    
                    # 2。SSE 规范：每条数据前加 data:，每条消息后空一行
                    # yield f"data: {content}\n\n"
            
            # === 循环结束，说明 AI 说完了 ===
            # ✅ 3. 在这里一次性存入数据库
            print(f"流式对话结束，存入数据库: {accumulated_reply[:10]}...")
            
            # 因为是纯聊天，没有情感分析字段，我们填入默认值
            db_record = AnalysisRecord(
                text_content=request.text,
                ai_reply=accumulated_reply, # 存的是完整的话
                sentiment="对话模式",       # 标记一下这是聊天
                word_count=len(accumulated_reply)
            )
            db.add(db_record)
            db.commit()

        except Exception as e:
            yield f"出错了: {str(e)}"

    # 2. 返回一个流式响应对象
    # media_type="text/event-stream" 告诉浏览器：这可是流数据哦
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/")
def read_root():
    return {"Hello": "World"}
