from app.critics.accuracy import evaluate_accuracy
from app.critics.logic import evaluate_logic
from app.critics.completeness import evaluate_completeness
from app.adjudicator import adjudicate


question = "What causes tides?"
answer = "Tides are mainly caused by the sun."

accuracy = evaluate_accuracy(question, answer)
logic = evaluate_logic(question, answer)
completeness = evaluate_completeness(question, answer)

verdict = adjudicate(
    accuracy,
    logic,
    completeness
)

print(verdict)