import os
from typing import List, Union, Protocol
import requests
from venv import logger
from transformers import AutoTokenizer

# 通用接口定义
class TextSplitter(Protocol):
    def __init__(self, model_name: str, api_key: str="", api_url: str="https://ark.cn-beijing.volces.com/api/v3/tokenization"):
        try:
            self.spliter = HFTransformerSplitter(model_name)
        except Exception as e:
            logger.error(f"本地模型加载失败: {str(e)}")
            self.spliter = VolcanoAPISplitter(model_name, api_key, api_url)

    def split_into_chunks(self, text: str, max_tokens: int) -> List[str]:
        return self.spliter.split_into_chunks(text, max_tokens)

# HuggingFace Transformers 实现
class HFTransformerSplitter:
    def __init__(self, model_name: str = "BAAI/bge-large-zh-v1.5"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def split_into_chunks(self, text: str, max_tokens: int) -> List[str]:
        """基于本地tokenizer的分块实现"""
        tokens = self.tokenizer.encode(text, add_special_tokens=False)
        chunks = []
        
        for i in range(0, len(tokens), max_tokens):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = self.tokenizer.decode(chunk_tokens)
            chunks.append(chunk_text)
        
        return chunks

# 火山方舟API实现（使用offset映射）
class VolcanoAPISplitter:
    def __init__(self, model_name, api_key: str, api_url: str = "https://ark.cn-beijing.volces.com/api/v3/tokenization"):
        self.model_name = model_name
        self.api_key = api_key
        self.api_url = api_url
    
    def _call_tokenize_api(self, text: str) -> tuple[List[int], List[tuple[int, int]]]:
        """调用火山引擎分词API（包含offset mapping）"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(
                self.api_url,
                json={"text": [text], "model": self.model_name},
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            # 假设API返回格式（根据实际文档调整）
            token_ids = data["data"][0]["token_ids"]
            offsets = [tuple(offset) for offset in data["data"][0]["offset_mapping"]]
            
            if len(token_ids) != len(offsets):
                raise ValueError("Token与offset数量不匹配")
            
            return token_ids, offsets
        except Exception as e:
            raise RuntimeError(f"API调用失败: {str(e)}")
    
    def split_into_chunks(self, text: str, max_tokens: int) -> List[str]:
        """基于API offset mapping的分块实现"""
        try:
            token_ids, offsets = self._call_tokenize_api(text)
        except RuntimeError as e:
            logger.error(f"API调用失败: {str(e)}")
            return [text]  # 降级策略：返回原始文本
            
        chunks = []
        
        for i in range(0, len(token_ids), max_tokens):
            chunk_offsets = offsets[i:i + max_tokens]
            
            if not chunk_offsets:
                continue
                
            # 计算文本区间
            start = chunk_offsets[0][0]
            end = chunk_offsets[-1][1]
            
            # 安全截取
            chunk = text[max(0, start):min(end, len(text))]
            chunks.append(chunk)
        
        return chunks if chunks else [text]

# 统一调用示例
def main():
    # 本地模型使用示例
    hf_splitter = TextSplitter("BAAI/bge-large-zh-v1.5")
    hf_chunks = hf_splitter.split_into_chunks("大模型技术正在快速发展", max_tokens=2)
    print("HuggingFace 分块结果:", hf_chunks)
    
    # 火山API使用示例
    api_key = os.getenv("VOLC_API_KEY", "")
    volcano_splitter = TextSplitter(model_name="doubao-embedding-text-240715", api_key=api_key)
    api_chunks = volcano_splitter.split_into_chunks("大模型技术正在快速发展", max_tokens=2)
    print("火山引擎分块结果:", api_chunks)

if __name__ == "__main__":
    main()