import time,os,json
from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI # 引入异步通讯器
from dotenv import load_dotenv # 引入环境变量加载器
from sqlalchemy.orm import Session
from sqlalchemy import desc

# 1. 加载 .env 文件里的配置
load_dotenv()

# 2. 初始化 OpenAI 客户端
# 它会自动读取环境变量里的 AI_API_KEY，但 Base URL 需要手动指定
client = AsyncOpenAI(
    base_url=os.getenv("AI_BASE_URL"), 
    api_key=os.getenv("AI_API_KEY")
)

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

# --- 定义数据格式 ---
class TextRequest(BaseModel):
    text: str

# --- 核心功能：文本分析接口 ---
@app.post("/analyze")
async def analyze_text(request: TextRequest):
    # 检查是否配置了 Key
    if not os.getenv("AI_API_KEY"):
        raise HTTPException(status_code=500, detail="后端未配置 API Key")

    try:
        # --- 真正的 AI 调用时刻 ---
        # 这是一个耗时操作，所以要用 await
        response = await client.chat.completions.create(
            model="deepseek-v3.1", # 如果用 Kimi 改成 "moonshot-v1-8k"
            messages=[
                # 系统提示词：给 AI 设定人设
                {"role": "system", "content": "你是一个幽默且专业的文本分析助手。请分析用户发来的文本，并返回JSON格式结果。"},
                # 用户的问题：要求它按我们前端需要的格式返回
                {"role": "user", "content": f"""
                请分析这段话：'{request.text}'
                
                请直接返回纯 JSON 格式（不要用 ```json 包裹），必须包含以下字段：
                1. length (数字): 字数
                2. is_question (布尔值): 是否包含疑问
                3. sentiment (字符串): 情感倾向（积极/消极/中性/愤怒等）
                4. keywords (数组): 提取3个关键词
                5. ai_reply (字符串): 你对这段话的幽默回复
                """}
            ],
            temperature=0.7,
        )

        # 获取 AI 的回答内容
        raw_content = response.choices[0].message.content

        # =========== 新增：在这里打印查看 ============
        print("\n" + "="*20 + " AI 原始数据 " + "="*20)
        print(response.choices[0]) # 这行代码会把内容输出到你的 VS Code 终端
        print("="*55 + "\n")
        # ===========================================
        
        # 因为大模型有时候会返回多余的文字，我们需要简单清洗一下，确保是 JSON
        # 这里为了演示简单，我们假设 AI 很听话返回了纯 JSON
        # 在生产环境中，这里通常需要更复杂的解析逻辑
        
        # 尝试清洗一下（去掉可能的 markdown 符号）
        clean_content = raw_content.replace("```json", "").replace("```", "").strip()
        
        result = json.loads(clean_content)
        
        return result

    except Exception as e:
        print(f"调用 AI 出错: {e}")
        # 如果出错，返回一个兜底的假数据，防止前端崩掉
        return {
            "length": len(request.text),
            "is_question": "?" in request.text,
            "sentiment": "分析失败",
            "keywords": ["错误"],
            "ai_reply": f"哎呀，AI 脑子短路了：{str(e)}"
        }

@app.get("/")
def read_root():
    return {"Hello": "World"}