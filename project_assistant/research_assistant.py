import os
import json
import asyncio
import hashlib
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
import re

load_dotenv()

class ResearchAssistant:
    """智能研究助手"""
    
    def __init__(self):
        self.llm = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com"
        )
        self.kb_file = "knowledge_base/papers.json"
        self._ensure_kb_exists()
    
    def _ensure_kb_exists(self):
        """确保知识库文件存在"""
        os.makedirs("knowledge_base", exist_ok=True)
        if not os.path.exists(self.kb_file):
            with open(self.kb_file, "w", encoding="utf-8") as f:
                json.dump([], f)
    
    def _get_paper_id(self, title):
        """根据标题生成论文ID"""
        return hashlib.md5(title.encode()).hexdigest()[:8]
    
    def _save_to_kb(self, paper_data):
        """保存论文到知识库"""
        with open(self.kb_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        
        # 检查是否已存在
        paper_id = paper_data["id"]
        for i, p in enumerate(papers):
            if p["id"] == paper_id:
                papers[i] = paper_data
                break
        else:
            papers.append(paper_data)
        
        with open(self.kb_file, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        
        return paper_id
    
    def _search_arxiv(self, query):
        """搜索arXiv论文（通过arXiv API）"""
        url = f"http://export.arxiv.org/api/query?search_query=all:{query}&start=0&max_results=1"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # 解析XML获取论文信息
                soup = BeautifulSoup(response.content, "lxml-xml")
                entry = soup.find("entry")
                if entry:
                    title = entry.find("title").text.strip()
                    # 移除多余换行
                    title = " ".join(title.split())
                    
                    summary = entry.find("summary").text.strip()
                    summary = " ".join(summary.split())
                    
                    authors = [a.text for a in entry.find_all("name")]
                    
                    link = entry.find("id").text
                    
                    return {
                        "title": title,
                        "authors": authors,
                        "summary": summary,
                        "url": link,
                        "source": "arXiv"
                    }
            return None
        except Exception as e:
            print(f"   ⚠️ arXiv搜索失败: {str(e)}")
            return None
    
    def _fetch_arxiv_by_id(self, paper_id):
        """通过arXiv ID获取论文"""
        url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "lxml-xml")
                entry = soup.find("entry")
                if entry:
                    title = entry.find("title").text.strip()
                    title = " ".join(title.split())
                    summary = entry.find("summary").text.strip()
                    summary = " ".join(summary.split())
                    authors = [a.text for a in entry.find_all("name")]
                    link = entry.find("id").text
                    return {
                        "title": title,
                        "authors": authors,
                        "summary": summary,
                        "url": link,
                        "source": "arXiv"
                    }
            return None
        except Exception as e:
            print(f"   ⚠️ 获取arXiv论文失败: {str(e)}")
            return None
    
    def _parse_paper_input(self, user_input):
        """解析用户输入，判断是URL还是标题"""
        # 检查是否是arXiv URL
        arxiv_url_pattern = r'arxiv\.org/abs/(\d+\.\d+)'
        match = re.search(arxiv_url_pattern, user_input)
        if match:
            paper_id = match.group(1)
            return {"type": "arxiv_id", "id": paper_id}
        
        # 检查是否是arXiv ID
        arxiv_id_pattern = r'^\d+\.\d+$'
        if re.match(arxiv_id_pattern, user_input.strip()):
            return {"type": "arxiv_id", "id": user_input.strip()}
        
        # 否则当作标题搜索
        return {"type": "title", "query": user_input}
    
    def translate_to_chinese(self, text, max_length=3000):
        """将英文摘要翻译成中文"""
        if len(text) > max_length:
            text = text[:max_length] + "..."
        
        prompt = f"""请将以下英文内容翻译成中文，保持学术专业性：

{text}

翻译："""
        
        response = self.llm.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response.choices[0].message.content
    
    def generate_summary(self, paper_data):
        """生成论文的中文解读"""
        prompt = f"""
请阅读以下论文信息，生成一份简洁的中文学术解读：

标题：{paper_data['title']}
作者：{', '.join(paper_data['authors'][:3])}
摘要：{paper_data['summary'][:2000]}

请按以下格式输出：
1. 一句话总结（20字以内）
2. 核心贡献（3个要点）
3. 适用场景（举例说明）
4. 技术亮点（2-3个）
5. 个人评价（客观评价这篇论文的价值）
"""
        
        response = self.llm.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5
        )
        return response.choices[0].message.content
    
    def search_knowledge_base(self, keyword):
        """搜索知识库"""
        with open(self.kb_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        
        results = []
        for paper in papers:
            if keyword.lower() in paper["title"].lower() or \
               keyword.lower() in paper.get("summary", "").lower():
                results.append(paper)
        
        return results
    
    def list_all_papers(self):
        """列出所有已保存的论文"""
        with open(self.kb_file, "r", encoding="utf-8") as f:
            papers = json.load(f)
        return papers
    
    async def process_paper(self, user_input):
        """处理用户输入，获取论文并生成解读"""
        print(f"\n📚 正在处理: {user_input}")
        print("-" * 60)
        
        # 1. 解析输入
        parsed = self._parse_paper_input(user_input)
        
        # 2. 获取论文信息
        paper_info = None
        
        if parsed["type"] == "arxiv_id":
            print(f"   📄 通过arXiv ID获取: {parsed['id']}")
            paper_info = self._fetch_arxiv_by_id(parsed["id"])
        else:
            print(f"   🔍 搜索: {parsed['query']}")
            paper_info = self._search_arxiv(parsed["query"])
        
        if not paper_info:
            return {"error": "未找到相关论文，请检查输入是否正确"}
        
        print(f"   ✅ 找到论文: {paper_info['title'][:50]}...")
        
        # 3. 检查知识库是否已有
        paper_id = self._get_paper_id(paper_info["title"])
        
        # 4. 生成中文翻译
        print("   🌐 正在翻译摘要...")
        chinese_summary = self.translate_to_chinese(paper_info["summary"])
        
        # 5. 生成解读
        print("   📝 正在生成解读...")
        interpretation = self.generate_summary(paper_info)
        
        # 6. 组装数据
        paper_data = {
            "id": paper_id,
            "title": paper_info["title"],
            "authors": paper_info["authors"],
            "url": paper_info["url"],
            "source": paper_info.get("source", "Unknown"),
            "summary": paper_info["summary"],
            "chinese_summary": chinese_summary,
            "interpretation": interpretation,
            "saved_at": datetime.now().isoformat()
        }
        
        # 7. 保存到知识库
        self._save_to_kb(paper_data)
        print(f"   💾 已保存到知识库 (ID: {paper_id})")
        
        return paper_data

def display_paper(paper_data):
    """显示论文解读"""
    print("\n" + "=" * 70)
    print(f"📖 {paper_data['title']}")
    print("=" * 70)
    print(f"👨‍🔬 作者: {', '.join(paper_data['authors'][:5])}")
    if len(paper_data['authors']) > 5:
        print(f"   ... 等{len(paper_data['authors'])}位作者")
    print(f"🔗 链接: {paper_data['url']}")
    print(f"📅 保存时间: {paper_data.get('saved_at', '未知')}")
    
    print("\n" + "-" * 70)
    print("📌 中文摘要：")
    print("-" * 70)
    print(paper_data['chinese_summary'][:500] + ("..." if len(paper_data['chinese_summary']) > 500 else ""))
    
    print("\n" + "-" * 70)
    print("📝 AI解读：")
    print("-" * 70)
    print(paper_data['interpretation'])
    print("=" * 70)

async def main():
    assistant = ResearchAssistant()
    
    while True:
        print("\n" + "=" * 60)
        print("🤖 智能研究助手")
        print("=" * 60)
        print("命令：")
        print("  输入 arXiv ID 或论文标题 → 获取并解读论文")
        print("  /list → 查看知识库所有论文")
        print("  /search [关键词] → 搜索知识库")
        print("  /view [ID] → 查看论文详情")
        print("  /quit → 退出")
        print("-" * 60)
        
        user_input = input("\n请输入: ").strip()
        
        if user_input == "/quit":
            print("👋 再见！")
            break
        
        elif user_input == "/list":
            papers = assistant.list_all_papers()
            if not papers:
                print("📭 知识库为空")
            else:
                print(f"\n📚 知识库共有 {len(papers)} 篇论文：")
                for i, p in enumerate(papers):
                    print(f"  {i+1}. [{p['id']}] {p['title'][:50]}...")
            continue
        
        elif user_input.startswith("/search "):
            keyword = user_input[8:].strip()
            results = assistant.search_knowledge_base(keyword)
            if not results:
                print(f"🔍 未找到包含 '{keyword}' 的论文")
            else:
                print(f"\n🔍 找到 {len(results)} 篇相关论文：")
                for p in results:
                    print(f"  [{p['id']}] {p['title']}")
            continue
        
        elif user_input.startswith("/view "):
            paper_id = user_input[6:].strip()
            papers = assistant.list_all_papers()
            found = None
            for p in papers:
                if p["id"] == paper_id:
                    found = p
                    break
            if found:
                display_paper(found)
            else:
                print(f"❌ 未找到ID为 {paper_id} 的论文")
            continue
        
        elif user_input:
            if len(user_input) < 3:
                print("⚠️ 输入太短，请提供论文标题或arXiv ID")
                continue
            
            result = await assistant.process_paper(user_input)
            if "error" in result:
                print(f"❌ {result['error']}")
            else:
                display_paper(result)

if __name__ == "__main__":
    asyncio.run(main())