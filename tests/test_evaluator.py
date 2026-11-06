from src.evaluation.evaluator import run_evaluation
import json

def test_evaluation():
    """Run RAGAS evaluation and print scores."""
    scores = run_evaluation()

    print("\n" + "="*50)
    print(" RAGAS EVALUATION RESULTS")
    print("="*50)
    print(f"  Faithfulness:       {scores['faithfulness']:.3f}")
    print(f"  Answer Relevancy:   {scores['answer_relevancy']:.3f}")
    print(f"  Context Precision:  {scores['context_precision']:.3f}")
    print(f"  Context Recall:     {scores['context_recall']:.3f}")
    print("="*50)

    # Save scores to file for CI/CD tracking
    with open("evaluation_scores.json", "w") as f:
        json.dump(scores, f, indent=2)
    print("\n Scores saved to evaluation_scores.json")

    # Quality gates — fail if scores drop below threshold
    assert scores["faithfulness"] >= 0.5, \
        f"Faithfulness too low: {scores['faithfulness']}"
    assert scores["context_precision"] >= 0.5, \
        f"Context Precision too low: {scores['context_precision']}"

    print(" All quality gates passed")

if __name__ == "__main__":
    test_evaluation()