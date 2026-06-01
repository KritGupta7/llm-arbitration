from app.critics.accuracy import evaluate_accuracy

question = "What causes tides?"
answer = "Tides are mainly caused by the sun."

result = evaluate_accuracy(question, answer)

print(result)
print(result.score)
print(result.issue)