from util.log import pretty_print
from langchain_core.prompts import PromptTemplate
from langchain_ollama.llms import OllamaLLM


def default_template():
    template = """
    Respond to the question with a single letter: A,B,C or D. Only output the letter of the correct answer.
    Question: {question}
    Answer:
    """.strip()
    return template


def init_llm(model='gemma2:2b', template=None):
    ''' use ollama for invoking a local llm '''

    if template is None:
        template = default_template()

    prompt = PromptTemplate.from_template(template)
    # deterministic model
    model = OllamaLLM(model=model,temperature=0,num_predict=1,top_k=10,top_p=0.5, keep_alive="10m")
    chain = prompt | model

    def predict(question, **kwargs):
        print_input = kwargs.pop('print_input', False)
        inputs = {"question": question, **kwargs}
        
        if print_input:
            pretty_print(inputs)

        return chain.invoke(inputs).strip()

    return predict