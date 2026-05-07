from .context import build_context
from .template import rag_template
from model.base import init_llm 


def rag_input_builder(retriever):
    def build(q):
        docs = retriever(q)
        context = build_context(docs)
        return {
            'question': q,
            'documents': context,
        }
    return build


def init_rag_model(retriever):
    if retriever is None:
        return init_llm(template=None)

    model = init_llm(template=rag_template)
    input_builder = rag_input_builder(retriever)
    return lambda q, **kwargs: model(**input_builder(q), **kwargs)
