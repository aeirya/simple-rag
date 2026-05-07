def pretty_print(input):
    print("QUESTION:")

    q = input['question']
    for line in q.split('\n'):
        print('\t', line)

    if 'documents' in input:
        print("DOCUMENTS")
        for i, doc in enumerate(input['documents'].split('\n\n---\n\n')):
            print(f'{i}:', '\t', doc)
            print()
    
