
def rag_template1():
    template = """
    Answer the multiple-choice question using the retrieved documents as the main evidence.

    Retrieved documents:
    {documents}

    Question:
    {question}

    Output only one letter: A, B, C, or D.
    Exactly one character from this set: A B C D.
    Do not write words. Do not explain.

    Answer:
    """.strip()
    return template


rag_template = rag_template1()