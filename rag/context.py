from collections import defaultdict

def group_by_title(docs):
    ''' input: document chunks '''
    ''' extracts the contents and gruops by document title'''
    groups = defaultdict(list)
    for doc in docs:
        groups[doc.metadata['title']] += [doc.page_content]
    return groups

def build_context(docs):
    groups = group_by_title(docs)
    sections = []
    for title, chunks in groups.items():
        sections += [
            f'# {title}\n\n' + '\n\n'.join(chunks)
        ]
    return "\n\n---\n\n".join(sections)
