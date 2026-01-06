import os
import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv

# 1. 加载 .env 里的配置
load_dotenv()

api_key = os.getenv("AI_API_KEY")
base_url = os.getenv("AI_BASE_URL")

print(f"正在连接: {base_url} ...")

async def get_models():
    # 2. 初始化客户端
    client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url
    )

    try:
        # 3. 发送标准查询请求 (GET /v1/models)
        response = await client.models.list()
        
        print("\n✅ 连接成功！该平台支持以下模型 ID：")
        print("=" * 40)
        
        # 4. 遍历并打印模型 ID
        #有些平台返回的数据结构比较复杂，我们做一个兼容处理
        model_list = response.data
        
        # 按照字母顺序排序，方便查找
        sorted_models = sorted(model_list, key=lambda x: x.id)

        for model in sorted_models:
            # 重点找包含 'deepseek' 的名字
            if "deepseek" in model.id.lower():
                print(f"✨ {model.id}")  # 给你高亮显示 DeepSeek 相关
            else:
                print(f"   {model.id}")
                
        print("=" * 40)
        print("👉 请复制上面带 '✨' 的其中一个 ID (例如 deepseek-chat 或 deepseek-v3)")
        print("👉 然后填入 backend/main.py 的 model='...' 里面")

    except Exception as e:
        print(f"\n❌ 查询失败: {e}")
        print("请检查 .env 文件里的 AI_BASE_URL 是否正确 (通常不需要加 /chat/completions)")

# 运行异步任务
if __name__ == "__main__":
    asyncio.run(get_models())