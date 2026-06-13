# knowledge_bot.py
import os
import sqlite3
import json
from dotenv import load_dotenv
from openai import OpenAI
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

class KnowledgeBot:
    def __init__(self):
        print("🤖 初始化知识库机器人...")
        
        # 加载embedding模型
        self.embed_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # 初始化ChromaDB
        self.chroma_client = chromadb.PersistentClient(path="./knowledge_db")
        self.collection = self._get_or_create_collection()
        
        # 初始化SQLite辅助数据库（用于准确计数）
        self._init_sqlite()
        
        # 同步计数
        self._sync_count()
        
        # 检查是否需要添加初始知识
        if self.get_count() == 0:
            print("📖 正在加载初始知识...")
            initial_knowledge = [
                "Python装饰器是一种高阶函数，可以在不修改原函数代码的情况下增加功能。",
                "AI Agent的三大核心组件：大语言模型（大脑）、工具集（手脚）、记忆系统（笔记本）。",
                "RAG（检索增强生成）通过外挂知识库解决LLM知识过时和幻觉问题。",
                "DeepSeek是一个高性能大语言模型，API兼容OpenAI接口格式。"
            ]
            for k in initial_knowledge:
                self.add_knowledge(k)
        else:
            print(f"📚 加载了已有的 {self.get_count()} 条知识")
        
        print("✅ 初始化完成！")
    
    def _init_sqlite(self):
        """初始化SQLite数据库"""
        self.conn = sqlite3.connect('./knowledge_db/meta.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_meta (
                id TEXT PRIMARY KEY,
                content TEXT,
                created_at REAL
            )
        ''')
        self.conn.commit()
    
    def _sync_count(self):
        """同步ChromaDB和SQLite的计数"""
        chroma_count = self.collection.count()
        sqlite_count = self.cursor.execute("SELECT COUNT(*) FROM knowledge_meta").fetchone()[0]
        
        if chroma_count != sqlite_count:
            print(f"⚠️ 检测到计数不一致，正在修复...")
            # 如果SQLite有但Chroma没有，需要重建
            if sqlite_count > chroma_count:
                # 这种情况很少见，先不做处理
                pass
    
    def get_count(self):
        """获取准确的知识数量（从SQLite读取）"""
        return self.cursor.execute("SELECT COUNT(*) FROM knowledge_meta").fetchone()[0]
    
    def _get_or_create_collection(self):
        try:
            return self.chroma_client.get_collection("my_bot")
        except:
            return self.chroma_client.create_collection("my_bot")
    
    def add_knowledge(self, content):
        """添加知识到知识库"""
        import time
        import hashlib
        
        # 生成唯一ID
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        doc_id = f"doc_{int(time.time())}_{content_hash}"
        
        # 检查是否已存在
        existing = self.cursor.execute("SELECT id FROM knowledge_meta WHERE id = ?", (doc_id,)).fetchone()
        if existing:
            print(f"⏭️ 跳过重复：{content[:50]}...")
            return
        
        # 添加到ChromaDB
        embedding = self.embed_model.encode(content).tolist()
        self.collection.add(
            ids=[doc_id],
            embeddings=[embedding],
            documents=[content]
        )
        
        # 添加到SQLite
        self.cursor.execute(
            "INSERT INTO knowledge_meta (id, content, created_at) VALUES (?, ?, ?)",
            (doc_id, content, time.time())
        )
        self.conn.commit()
        
        print(f"✅ 已添加：{content[:50]}... (总数: {self.get_count()})")
    
    def search(self, query, top_k=3):
        """检索相关知识"""
        query_embedding = self.embed_model.encode(query).tolist()
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return results['documents'][0] if results['documents'] else []
    
    def ask(self, question):
        """问答"""
        docs = self.search(question)
        
        if not docs:
            return "📚 知识库中还没有相关信息，请先用 'add' 命令添加知识。"
        
        context = "\n---\n".join(docs)
        prompt = f"""请根据以下资料回答问题。如果资料中没有相关信息，请说"资料库中没有相关信息"。

资料：
{context}

问题：{question}

回答："""
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content
    
    def run(self):
        """运行交互式界面"""
        print("\n" + "=" * 50)
        print("📚 知识库问答机器人")
        print("=" * 50)
        print("命令说明：")
        print("  - 直接输入问题进行问答")
        print("  - add <内容> 添加知识")
        print("  - list 查看知识库数量")
        print("  - quit 退出")
        print("=" * 50)
        
        while True:
            user_input = input("\n💬 你：").strip()
            
            if user_input.lower() == 'quit':
                print("👋 再见！")
                self.conn.close()
                break
            
            elif user_input.lower() == 'list':
                count = self.get_count()
                chroma_count = self.collection.count()
                print(f"📊 知识库中共有 {count} 条知识")
                if count != chroma_count:
                    print(f"⚠️ 提示：ChromaDB显示 {chroma_count} 条，计数可能不同步")
            
            elif user_input.startswith('add '):
                content = user_input[4:].strip()
                if content:
                    self.add_knowledge(content)
                else:
                    print("❌ 内容不能为空")
            
            else:
                print("🤔 思考中...")
                answer = self.ask(user_input)
                print(f"🤖 助手：{answer}")

# 运行
if __name__ == "__main__":
    bot = KnowledgeBot()
    bot.run()