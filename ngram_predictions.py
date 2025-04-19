from collections import defaultdict

def build_ngrams(history, n):
    ngrams = defaultdict(list)
    for i in range(len(history) - n):
        context = tuple(history[i:i+n])
        next_item = history[i+n]
        ngrams[context].append(next_item)
    return ngrams

def predict_next_is_pk(history):
    if len(history) < 2:
        return False
    ngrams = build_ngrams(history, 2)
    context = tuple(history[-2:])
    possible = ngrams.get(context, [])
    return possible.count('Pk') / len(possible) > 0.5 if possible else False

def predict_next_is_purple(history):
    if len(history) < 2:
        return False
    ngrams = build_ngrams(history, 2)
    context = tuple(history[-2:])
    possible = ngrams.get(context, [])
    return possible.count('P') / len(possible) > 0.5 if possible else False

def predict_next_is_blue(history):
    if len(history) < 2:
        return False
    ngrams = build_ngrams(history, 2)
    context = tuple(history[-2:])
    possible = ngrams.get(context, [])
    return possible.count('B') / len(possible) > 0.5 if possible else False

def recommend_next_category(history):
    if len(history) < 2:
        return 'B'
    ngrams = build_ngrams(history, 2)
    context = tuple(history[-2:])
    possible = ngrams.get(context, [])
    if not possible:
        return 'B'
    counts = {'B': 0, 'P': 0, 'Pk': 0}
    for item in possible:
        counts[item] += 1
    return max(counts.items(), key=lambda x: x[1])[0]