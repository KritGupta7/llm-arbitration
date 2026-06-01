from app.critics.accuracy import evaluate_accuracy
from app.critics.logic import evaluate_logic
from app.critics.completeness import evaluate_completeness

question = "What causes tides?"
answer = "Tides are mainly caused by the sun."

accuracy_result = evaluate_accuracy(question, answer)
logic_result = evaluate_logic(question, answer)
completeness_result = evaluate_completeness(question, answer)

print("Accuracy Critic:")
print(accuracy_result)

print("\nLogic Critic:")
print(logic_result)

print("\nCompleteness Critic:")
print(completeness_result)