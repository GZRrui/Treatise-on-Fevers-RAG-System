import json
import re
from pathlib import Path
from typing import Any, Dict, List

from config import CLEAN_DATA_PATH, RAW_DATA_PATH


class DataLoader:
    """Load and clean source article data."""

    def __init__(self, raw_path: str | None = None):
        self.raw_path = Path(raw_path) if raw_path else RAW_DATA_PATH
        self.clean_path = CLEAN_DATA_PATH

    def load_raw_data(self) -> List[Dict[str, Any]]:
        if not self.raw_path.exists():
            raise FileNotFoundError(f"原始数据文件不存在: {self.raw_path}")

        with open(self.raw_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        print(f"✅ 成功加载原始数据，共 {len(data)} 条条文")
        return data

    def clean_text(self, text: str) -> str:
        if not text:
            return ''

        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return text.strip()

    def normalize_article_number(self, article: Dict[str, Any]) -> Dict[str, Any]:
        article['standard_id'] = article.get('id', 0)
        article['id_range'] = str(article.get('id', 0))
        return article

    def extract_formulas(self, text: str) -> List[str]:
        formula_patterns = [
            r'([\u4e00-\u9fff]{2,}汤)主之',
            r'([\u4e00-\u9fff]{2,}汤)',
            r'宜([\u4e00-\u9fff]{2,}汤)',
            r'与([\u4e00-\u9fff]{2,}汤)',
        ]

        formulas: List[str] = []
        for pattern in formula_patterns:
            formulas.extend(re.findall(pattern, text))

        return sorted(set(formulas))

    def clean_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned: List[Dict[str, Any]] = []

        for article in data:
            raw_text = article.get('text')
            if raw_text is None:
                raw_text = article.get('section', '')

            text = self.clean_text(raw_text)
            if not text:
                continue

            cleaned_article = {
                'id': article.get('id', 0),
                'chapter': article.get('chapter', ''),
                'section': article.get('section', ''),
                'category': article.get('category', ''),
                'text': text,
            }
            cleaned_article = self.normalize_article_number(cleaned_article)
            cleaned_article['formulas'] = self.extract_formulas(text)
            cleaned.append(cleaned_article)

        return cleaned

    def save_clean_data(self, data: List[Dict[str, Any]]) -> None:
        self.clean_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.clean_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        print(f"✅ 清洗后数据已保存至: {self.clean_path}")

    def load_clean_data(self) -> List[Dict[str, Any]]:
        if not self.clean_path.exists():
            raise FileNotFoundError(f"清洗后数据文件不存在: {self.clean_path}")
        with open(self.clean_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def process(self) -> List[Dict[str, Any]]:
        print('=' * 50)
        print('步骤1: 数据加载与清洗')
        print('=' * 50)
        raw_data = self.load_raw_data()
        print('\n正在进行数据清洗...')
        clean_data = self.clean_data(raw_data)
        self.save_clean_data(clean_data)
        self._print_statistics(clean_data)
        return clean_data

    def _print_statistics(self, data: List[Dict[str, Any]]) -> None:
        print('\n📊 数据统计:')
        print(f'  - 总条文数: {len(data)}')
        chapters: Dict[str, int] = {}
        for article in data:
            chapter = article.get('chapter', '未知')
            chapters[chapter] = chapters.get(chapter, 0) + 1
        print('\n  按篇章分布:')
        for chapter, count in chapters.items():
            print(f'    - {chapter}: {count} 条')
        unique_formulas = sorted({formula for article in data for formula in article.get('formulas', [])})
        print(f'\n  - 涉及方剂数: {len(unique_formulas)}')


if __name__ == '__main__':
    loader = DataLoader()
    data = loader.process()
    print(f'\n✅ 数据处理完成，共 {len(data)} 条清洗后条文')
