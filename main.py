from app.critics.accuracy import evaluate_accuracy
from app.critics.logic import evaluate_logic

question = "What causes tides?"
answer = "Tides are mainly caused by the sun."

accuracy_result = evaluate_accuracy(question, answer)
logic_result = evaluate_logic(question, answer)

print("Accuracy Critic:")
print(accuracy_result)

print("\nLogic Critic:")
print(logic_result)