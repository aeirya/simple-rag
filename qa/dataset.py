import json
from pathlib import Path

_DATA_BASE_DIR=Path('data/qa')

def load_jsonl(path: str | Path) -> list[dict]:
    path = Path(path)

    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def filter(questions, qtype:str = 'all'):
    if qtype in ['A']:
        qtype = 'answerable'
    if qtype in ['B']:
        qtype = 'near_distractor'
    if qtype in ['C']:
        qtype = 'out_of_domain'

    if qtype in ['all', None]:
        return questions

def get_path(path):
    path = Path(path)
    path = path.with_suffix('.jsonl')
    if path.exists(): return path
    path = _DATA_BASE_DIR / path
    assert path.exists()
    return path
    
def load_question_file(path, qtype=None):
    path = get_path(path)
    questions = load_jsonl(path)
    if qtype:
        questions = filter(questions, qtype)
    return questions

def format_question(item):
    options = [f'{k}: {v}' for k,v in item['choices'].items()]
    question = item['question']
    return '\n'.join([question] + options)

def load_data(dataset):
    for item in load_question_file(dataset):
        yield format_question(item), item['answer']
        
def load_all():
    ds = []
    for file in _DATA_BASE_DIR.glob('*.jsonl'):
        ds += load_data(file)
    