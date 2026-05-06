from pathlib import Path
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

def wiki_documents(wiki_dir=Path('data/wiki')):
    for path in wiki_dir.glob('*.md'):
        text = path.read_text().strip()
        title = path.stem.replace('_', ' ')

        yield Document(page_content=text, metadata={'title': title})

def wiki_chunks(chunk_size, chunk_overlap, min_chars=20):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    docs = wiki_documents()
    chunks = splitter.split_documents(docs)
    
    min_chars = chunk_overlap
    return [
        c for c in chunks
        if len(c.page_content) >= min_chars
    ]

import re
def tokenize(text):
    return re.findall(r"\w+", text.lower())

def wiki_bm25_retriever(k=2, chunk_size=200, chunk_overlap=40):
    docs =  wiki_chunks(chunk_size, chunk_overlap)
    retriever = BM25Retriever.from_documents(
        docs,
        k=k,
        bm25_params={"k1": 1.5, "b": 0.85},
        preprocess_func=tokenize,
        )
    return lambda query: retriever.invoke(query)

bm25 = wiki_bm25_retriever