# rag_demo.py
import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
import hashlib

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ========== 1. 准备你的文档 ==========
documents = [
    {"id": "doc1", "content": "Python装饰器是一个函数，它接受另一个函数作为参数，并返回一个新的函数。常用于日志、计时等场景。"},
    {"id": "doc2", "content": "智能体Agent是一个能够自主感知环境、做出决策并执行动作的AI系统。"},
    {"id": "doc3", "content": "提示词工程是设计和优化输入提示以引导LLM输出期望结果的技术。"},
]

# ========== 2. 创建向量数据库 ==========
# 使用sentence-transformers生成embedding（本地运行，免费）
try:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    use_local = True
    print("✅ 已加载本地embedding模型")
except ImportError:
    print("❌ 请先运行: pip install sentence-transformers")
    exit(1)

# 创建ChromaDB客户端
persist_dir = "./chroma_db"
import shutil
if os.path.exists(persist_dir):
    shutil.rmtree(persist_dir)

chroma_client = chromadb.PersistentClient(path=persist_dir)
collection = chroma_client.create_collection(name="my_knowledge")

# 添加文档
print("正在添加文档到向量库...")
for doc in documents:
    embedding = model.encode(doc["content"]).tolist()
    collection.add(
        ids=[doc["id"]],
        embeddings=[embedding],
        documents=[doc["content"]]
    )
print(f"✅ 已添加 {len(documents)} 条文档")

# ========== 3. 检索函数 ==========
def search(query, top_k=2):
    """检索相关文档"""
    query_embedding = model.encode(query).tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k
    )
    return results['documents'][0] if results['documents'] else []

# ========== 4. RAG问答 ==========
def ask(question):
    """使用RAG回答问题"""
    # 检索相关文档
    docs = search(question)
    
    if not docs:
        context = "没有找到相关文档。"
    else:
        context = "\n---\n".join(docs)
    
    # 构建提示词
    prompt = f"""请根据以下参考资料回答问题。如果资料中没有相关信息，请说"根据现有资料无法回答"。

参考资料：
{context}

问题：{question}

回答："""
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content

# ========== 5. 测试 ==========
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("RAG问答系统测试")
    print("=" * 50)
    
    test_questions = [
        "什么是Python装饰器？",
        "智能体Agent是什么？",
        "今天天气怎么样？"  # 文档中没有，应回答无法回答
    ]
    
    for q in test_questions:
        print(f"\n问题：{q}")
        answer = ask(q)
        print(f"回答：{answer}")
        print("-" * 40)