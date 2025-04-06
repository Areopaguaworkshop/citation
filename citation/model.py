from typing import Optional, Union, Dict
import dspy
from datetime import date
from utils import input_class, pdf_md
from form import (
    CitationsForBook,
    CitationsForThesis,
    CitationsForArticle,
    ThesisType
)

# Configure dspy with ollama
lm = dspy.LM(model="ollama/qwen2.5")
dspy.settings.configure(lm=lm)

class ArticleSignature(dspy.Signature):
    """Extract citation information for articles."""
    text = dspy.InputField(desc="Text content of the document (可以是中文或英文)")
    author = dspy.OutputField(desc="Author (last name, first name). For Chinese names, keep original order 作者姓名")
    year = dspy.OutputField(desc="Publication year 出版年份")
    title = dspy.OutputField(desc="Article title 文章标题")
    container_title = dspy.OutputField(desc="Journal or book name 期刊或书籍名称")
    location = dspy.OutputField(desc="Publication location 出版地")
    publisher = dspy.OutputField(desc="Publisher name 出版社")
    page_start = dspy.OutputField(desc="Starting page number 起始页码")
    page_end = dspy.OutputField(desc="Ending page number 结束页码")
    journal_number = dspy.OutputField(desc="Journal number 期号")
    volume = dspy.OutputField(desc="Volume number 卷号")
    doi = dspy.OutputField(desc="DOI number DOI号")

# Updated signature for extracting book citation information.
class BookSignature(dspy.Signature):
    text = dspy.InputField(desc="Text content of the copyright page (可以是中文或英文)")
    author = dspy.OutputField(desc="Book author. For Chinese names, keep original order 作者姓名")
    year = dspy.OutputField(desc="Publication year 出版年份")
    title = dspy.OutputField(desc="Book title 书籍标题")
    location = dspy.OutputField(desc="Publication location 出版地")
    publisher = dspy.OutputField(desc="Publisher name 出版社")
    volume = dspy.OutputField(desc="Volume number 卷号")
    doi = dspy.OutputField(desc="DOI number DOI号")
    thesis_type = dspy.OutputField(desc="Thesis type (PhD博士/Master硕士)")

def safe_int(value, default=0):
    """Safely convert value to int, returning default if conversion fails."""
    if not value or value == 'N/A':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def pdf_search(file_path: str) -> Union[CitationsForBook, CitationsForThesis, CitationsForArticle]:
    """
    Search PDF content and create appropriate citation object.
    1. Call input_class(file_path) to decide which citation type is relevant.
    2. Use pdf_md to obtain markdown content.
    3. If input_class returns a type for book or thesis, use LM model "ollama/qwen2.5" and BookSignature.
       Then, inspect the content for thesis keywords to decide if it is a thesis.
       Return CitationsForThesis or CitationsForBook accordingly.
    4. If input_class returns CitationsForArticle, use LM model "ollama/qwen2.5" to extract article fields.
    """
    citation_type = input_class(file_path)
    content = pdf_md(file_path)
    
    if citation_type == CitationsForArticle:
        lm_target = dspy.LM(model="ollama/qwen2.5", temperature=0.1)  # Lower temperature for more focused output
        dspy.settings.configure(lm=lm_target)
        article_extractor = dspy.ChainOfThought(ArticleSignature)
        # Add instruction prefix for Chinese content
        content_with_instruction = "请仔细分析以下文献的书目信息（可能是中文或英文）：\n\n" + content
        fields = article_extractor.__call__(**{"text": content_with_instruction})
        return CitationsForArticle(
            author=fields.get('author', ''),
            year=safe_int(fields.get('year'), 0),
            title=fields.get('title', ''),
            container_title=fields.get('container_title', ''),
            location=fields.get('location', ''),
            publisher=fields.get('publisher', ''),
            page_start=safe_int(fields.get('page_start'), 0),
            page_end=safe_int(fields.get('page_end'), 0),
            journal_number=safe_int(fields.get('journal_number')) if fields.get('journal_number') else None,
            volume=safe_int(fields.get('volume')) if fields.get('volume') else None,
            doi=fields.get('doi')
        )
    else:
        lm_target = dspy.LM(model="ollama/qwen2.5", temperature=0.1)
        dspy.settings.configure(lm=lm_target)
        book_extractor = dspy.ChainOfThought(BookSignature)
        content_with_instruction = "请仔细分析以下文献的版权页信息（可能是中文或英文）：\n\n" + content
        fields = book_extractor.__call__(**{"text": content_with_instruction})
        content_lower = content.lower()
        is_thesis = any(kw in content_lower for kw in ["phd thesis", "doctoral thesis", "master thesis", "master's thesis", "dissertation"])
        if is_thesis:
            thesis_type = ThesisType.PHD if any(t in content_lower for t in ["phd", "doctoral", "dissertation"]) else ThesisType.MASTER
            return CitationsForThesis(
                author=fields.get('author', ''),
                year=safe_int(fields.get('year'), 0),
                title=fields.get('title', ''),
                location=fields.get('location', ''),
                publisher=fields.get('publisher', ''),
                thesis_type=thesis_type,
                doi=fields.get('doi')
            )
        else:
            return CitationsForBook(
                author=fields.get('author', ''),
                year=safe_int(fields.get('year'), 0),
                title=fields.get('title', ''),
                location=fields.get('location', ''),
                publisher=fields.get('publisher', ''),
                doi=fields.get('doi')
            )
