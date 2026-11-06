import os
import json
import boto3
from dotenv import load_dotenv
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall
)
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_aws import ChatBedrock, BedrockEmbeddings

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

GOLDEN_TEST_SET = [
    {
        "question": "Does the client patent's circulating conveyor carrying mould containers have prior art?",
        "ground_truth": "Yes, GB2296214 discloses a circulating conveyor carrying mould containers combined with mould container parts.",
        "contexts_query": "circulating conveyor carrying mould containers brick manufacturing"
    },
    {
        "question": "Does the client patent's reservoir for clay above the mould containers have prior art?",
        "ground_truth": "Yes, GB2296214 discloses a reservoir for clay arranged above the mould containers.",
        "contexts_query": "reservoir clay above mould containers"
    },
    {
        "question": "Does the means for moving mould container parts to form a protruding edge have prior art?",
        "ground_truth": "Yes, GB2296214 discloses means for moving mould container parts filled with green bricks to form a protruding edge.",
        "contexts_query": "moving mould container parts protruding edge green bricks"
    },
]


def get_ragas_llm():
    """Return a LangChain Bedrock LLM wrapped for RAGAS."""
    llm = ChatBedrock(
        model_id="amazon.nova-pro-v1:0",
        region_name=AWS_REGION
    )
    return LangchainLLMWrapper(llm)


def get_ragas_embeddings():
    """Return Bedrock embeddings wrapped for RAGAS."""
    embeddings = BedrockEmbeddings(
        model_id="amazon.titan-embed-text-v2:0",
        region_name=AWS_REGION
    )
    return LangchainEmbeddingsWrapper(embeddings)


def run_evaluation() -> dict:
    """
    Run RAGAS evaluation against the golden test set using Bedrock.
    Returns a dict of metric scores.
    """
    from src.ingestion.embedder import embed_text
    from src.ingestion.pinecone_store import get_index

    index = get_index()

    questions = []
    answers = []
    contexts = []
    ground_truths = []

    print("\n Running RAGAS evaluation...")

    for test_case in GOLDEN_TEST_SET:
        print(f"\n  Q: {test_case['question'][:80]}...")

        query_embedding = embed_text(test_case["contexts_query"])
        results = index.query(
            vector=query_embedding,
            top_k=3,
            include_metadata=True
        )

        context_texts = [
            match.metadata.get("text", "")
            for match in results.matches
            if match.metadata.get("text")
        ]

        answer = _generate_answer(test_case["question"], context_texts)

        questions.append(test_case["question"])
        answers.append(answer)
        contexts.append(context_texts)
        ground_truths.append(test_case["ground_truth"])

        print(f"  A: {answer[:100]}...")

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": answers,
        "contexts": contexts,
        "ground_truth": ground_truths
    })

    # Configure RAGAS to use Bedrock instead of OpenAI
    ragas_llm = get_ragas_llm()
    ragas_embeddings = get_ragas_embeddings()

    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]
    for metric in metrics:
        metric.llm = ragas_llm
        metric.embeddings = ragas_embeddings

    print("\n  Computing RAGAS metrics...")
    scores = evaluate(dataset, metrics=metrics)

    results_dict = {
        "faithfulness": round(float(scores.to_pandas()["faithfulness"].mean()), 3),
        "answer_relevancy": round(float(scores.to_pandas()["answer_relevancy"].mean()), 3),
        "context_precision": round(float(scores.to_pandas()["context_precision"].mean()), 3),
        "context_recall": round(float(scores.to_pandas()["context_recall"].mean()), 3),
    }

    return results_dict


def _generate_answer(question: str, contexts: list[str]) -> str:
    """Generate an answer to a question given retrieved contexts."""
    bedrock = boto3.client("bedrock-runtime", region_name=AWS_REGION)

    context_text = "\n\n".join(contexts[:3])

    prompt = f"""Based on the following patent text, answer the question concisely.

PATENT TEXT:
{context_text}

QUESTION:
{question}

Answer in 1-2 sentences based only on the provided text."""

    body = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        "inferenceConfig": {
            "maxTokens": 200,
            "temperature": 0.1
        }
    })

    response = bedrock.invoke_model(
        modelId="amazon.nova-pro-v1:0",
        contentType="application/json",
        accept="application/json",
        body=body
    )

    result = json.loads(response["body"].read())
    return result["output"]["message"]["content"][0]["text"].strip()