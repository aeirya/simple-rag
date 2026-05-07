from langchain_classic.evaluation import ExactMatchStringEvaluator

def gen_evaluator():
    evaluator = ExactMatchStringEvaluator()
    return lambda ans, ref: evaluator.evaluate_strings(prediction=ans,reference=ref)['score']

def eval_model(
    model, 
    dataset, 
    print_input=False, 
    print_answers=False,
    print_scores=False,
    return_wrongs=False,
    ):

    scorer = gen_evaluator()
    ok = 0
    wrongs = []
    for i, (q, ref) in enumerate(dataset):
        ans = model(q, print_input=print_input)
        sc = scorer(ans, ref)
        if sc == 1.0: 
            ok += 1
        else:
            wrongs += [i] 
        acc = round(100 * ok / (i+1), 2)

        if print_answers:
            print('answered:', ans, 'correct:', ref)
            print('--')
        if print_scores:
            print('round', i, '| acc:', acc)
            print('--')
    
    if return_wrongs:
        return acc, wrongs
    return acc