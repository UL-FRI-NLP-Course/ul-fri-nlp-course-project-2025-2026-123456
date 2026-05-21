import os
import sys
import json
import numpy as np

from scipy.stats import spearmanr
from typing import List, Dict, Optional, Tuple

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from src.db.carapi_schema import CARAPI_SCHEMA_METADATA, ColumnMetadata
from src.db.carapi_column_embeddings import load_column_embeddings
from src.ingestion.embedder import embed_query
from scripts.ingest_carapi_stats import build_and_save_column_embeddings


embedding_models = [ 
                    'all-MiniLM-L6-v2',
                    'Qwen/Qwen3-Embedding-0.6B',
                    'Qwen/Qwen3-Embedding-4B',
                    'BAAI/bge-large-en-v1.5', 
                    'BAAI/bge-m3',
                    'nomic-ai/nomic-embed-text-v1.5',
                    'thenlper/gte-large',
                    'google/embeddinggemma-300m',
                    'jinaai/jina-embeddings-v5-text-small',
                    'jinaai/jina-embeddings-v5-text-nano']


def load_json(file_path: str) -> List[str]:
    if file_path.endswith('.json'):
        with open(file_path, 'r', encoding='utf-8') as fh:
            data = json.load(fh)

    return data

def model_name_to_filename(model_name: str) -> str:
    if '/' in model_name:
        return model_name.split('/')[1]
    return model_name

def embeddings_path(model_name: str) -> str:
    benchmark_embeddings_dir = os.path.join(repo_root, "benchmark", "embeddings")
    model_filename = model_name_to_filename(model_name)
    embeddings_path = os.path.join(benchmark_embeddings_dir, f"{model_filename}.npy")
    return embeddings_path


def build_leave_one_out_vote_tables(test_file: str = None):
    if test_file is None:
        test_file = os.path.join(repo_root, "benchmark", "queries_with_labeled_scores.json")

    test_queries = load_json(test_file)

    benchmark_embeddings_dir = os.path.join(repo_root, "benchmark", "embeddings")
    os.makedirs(benchmark_embeddings_dir, exist_ok=True)

    leave_one_out_dir = os.path.join(repo_root, "benchmark", "leave_one_out")
    os.makedirs(leave_one_out_dir, exist_ok=True)

    model_predictions = {}
    for model in embedding_models:
        build_and_save_column_embeddings(model_name=model, embeddings_path=embeddings_path(model))
        embeddings, metadata = load_column_embeddings(embeddings_path=embeddings_path(model))

        model_predictions[model] = []
        for query in test_queries:
            query_emb = embed_query(query['query'], model_name=model)
            scores = np.dot(embeddings, query_emb)

            # normalize scores to each model has the same scale
            mean = np.mean(scores)
            std = np.std(scores)

            if std > 1e-8:
                scores = (scores - mean) / std
            else:
                scores = np.zeros_like(scores)

            query_scores = {}
            for i, column in enumerate(metadata):
                query_scores[column.name] = float(scores[i])

            model_predictions[model].append(query_scores)

    for target_model in embedding_models:
        leave_one_out_queries = []

        for query_index, query in enumerate(test_queries):
            voted_scores = {}

            for model in embedding_models:
                if model == target_model:
                    continue

                for col_name, score in model_predictions[model][query_index].items():
                    voted_scores[col_name] = voted_scores.get(col_name, 0.0) + score

            divisor = len(embedding_models) - 1
            for col_name in voted_scores:
                voted_scores[col_name] = float(voted_scores[col_name]) / divisor

            leave_one_out_queries.append({
                "query": query["query"],
                "voted_scores": voted_scores,
            })

        output_path = os.path.join(leave_one_out_dir, f"{model_name_to_filename(target_model)}.json")
        with open(output_path, 'w', encoding='utf-8') as fh:
            json.dump(leave_one_out_queries, fh, indent=2)


def load_leave_one_out_vote_table(model_name: str):
    leave_one_out_dir = os.path.join(repo_root, "benchmark", "leave_one_out")
    file_path = os.path.join(leave_one_out_dir, f"{model_name_to_filename(model_name)}.json")

    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Leave-one-out vote table not found: {file_path}. Run build_leave_one_out_vote_tables() first."
        )

    with open(file_path, 'r', encoding='utf-8') as fh:
        return json.load(fh)


def separation_score(scores: np.ndarray, labels: np.ndarray) -> float:
    positive_scores = scores[labels == 1]
    negative_scores = scores[labels == 0]

    if len(positive_scores) < 2 or len(negative_scores) < 2:
        return 0.0

    positive_mean = float(np.mean(positive_scores))
    negative_mean = float(np.mean(negative_scores))

    n_pos = len(positive_scores)
    n_neg = len(negative_scores)

    # Compute sample variances (ddof=1 for unbiased estimate)
    pos_var = float(np.var(positive_scores, ddof=1))
    neg_var = float(np.var(negative_scores, ddof=1))

    # Compute pooled standard deviation (Cohen's d formula)
    pooled_var = ((n_pos - 1) * pos_var + (n_neg - 1) * neg_var) / (n_pos + n_neg - 2)
    pooled_std = float(np.sqrt(pooled_var))

    if pooled_std == 0.0:
        return 0.0

    # Cohen's d: standardized mean difference
    return (positive_mean - negative_mean) / pooled_std


def safe_spearman_correlation(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if len(x) < 2 or len(y) < 2:
        return 0.0

    if np.all(x == x[0]) or np.all(y == y[0]):
        return 0.0

    correlation = spearmanr(x, y).correlation
    return float(correlation) if np.isfinite(correlation) else 0.0

def f1_score(predicted: np.ndarray, labels: np.ndarray) -> float:
    tp = np.sum((predicted == 1) & (labels == 1))
    fp = np.sum((predicted == 1) & (labels == 0))
    fn = np.sum((predicted == 0) & (labels == 1))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    return (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0


def optimize_f1_score(scores: np.ndarray, labels: np.ndarray) -> Tuple[float, float]:
    all_scores = scores.flatten()
    all_labels = labels.flatten()

    thresholds = np.linspace(0.0, 1.0, num=101)

    best_f1 = 0.0
    best_threshold = 0.0

    for t in thresholds:
        pred_labels = (all_scores >= t).astype(np.int32)
        f1 = f1_score(pred_labels, all_labels)

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = t

    return best_f1, best_threshold


def calculate_model_scores(model_name: str, queries: List[str], gt_scores: np.ndarray, gt_labels: np.ndarray):
    spearmanr_scores = []
    separation_scores = []

    embeddings, metadata = load_column_embeddings(embeddings_path(model_name))

    predicted_scores = np.zeros((len(queries), len(metadata)), dtype=np.float32)

    for i, query in enumerate(queries):
        query_emb = embed_query(query, model_name=model_name)
        model_scores = np.dot(embeddings, query_emb)

        predicted_scores[i] = model_scores

        query_gt_scores = gt_scores[i]
        query_gt_labels = gt_labels[i]

        spearmanr_score = safe_spearman_correlation(model_scores, query_gt_scores)
        spearmanr_scores.append(spearmanr_score)

        separation = separation_score(model_scores, query_gt_labels)
        separation_scores.append(separation)

    mean_spearmanr = float(np.mean(spearmanr_scores)) if spearmanr_scores else 0.0
    mean_separation = float(np.mean(separation_scores)) if separation_scores else 0.0

    f1, threshold = optimize_f1_score(predicted_scores, gt_labels)

    return mean_spearmanr, mean_separation, f1, threshold

def score_model_with_leave_one_out(model_name: str, top_k: float = 5):
    leave_one_out_queries = load_leave_one_out_vote_table(model_name)

    queries = [q['query'] for q in leave_one_out_queries]
    all_voted_scores = np.zeros((len(leave_one_out_queries), len(CARAPI_SCHEMA_METADATA)), dtype=np.float32)
    truth_labels = np.zeros((len(leave_one_out_queries), len(CARAPI_SCHEMA_METADATA)), dtype=np.int32)

    for i, query in enumerate(leave_one_out_queries):
        voted_scores = np.zeros(len(CARAPI_SCHEMA_METADATA), dtype=np.float32)
        for j, col_name in enumerate(CARAPI_SCHEMA_METADATA):
            voted_scores[j] = float(query['voted_scores'].get(col_name, 0.0))

        true_indices = np.argsort(voted_scores)[::-1][:top_k]
        labels = np.zeros(len(voted_scores), dtype=np.int32)
        labels[true_indices] = 1

        all_voted_scores[i] = voted_scores
        truth_labels[i] = labels

    mean_spearmanr, mean_separation, f1, threshold = calculate_model_scores(model_name, queries, all_voted_scores, truth_labels)
    final_score = (mean_spearmanr + mean_separation + f1) / 3.0

    print(
        f"Model: {model_name}\n"
        f"  Spearmans correlation: {mean_spearmanr:.4f}\n"
        f"  Separation score: {mean_separation:.4f}\n"
        f"  F1 score: {f1:.4f} at threshold {threshold:.4f}\n"
        f"  Final combined score: {final_score:.4f}"
    )

    return {
        "model_name": model_name,
        "agreement": mean_spearmanr,
        "separation": mean_separation,
        "f1": f1,
        "threshold": threshold,
        "final_score": final_score,
    }


def benchmark_models_with_leave_one_out(top_k: float = 5):
    results = [score_model_with_leave_one_out(model, top_k=top_k) for model in embedding_models]

    print_benchmark_results(results)

    return results


def score_model_with_labeled_data(model_name: str, labeled_queries_file: str):
    labeled_queries = load_json(labeled_queries_file)

    queries = [q['query'] for q in labeled_queries]
    all_labeled_scores = np.zeros((len(labeled_queries), len(CARAPI_SCHEMA_METADATA)), dtype=np.float32)
    truth_labels = np.zeros((len(labeled_queries), len(CARAPI_SCHEMA_METADATA)), dtype=np.int32)

    for i, query in enumerate(labeled_queries):
        labeled_score = np.zeros(len(CARAPI_SCHEMA_METADATA), dtype=np.float32)
        for j, col_name in enumerate(CARAPI_SCHEMA_METADATA):
            labeled_score[j] = float(query['labeled_scores'].get(col_name, 0.0))

        labels = np.where(labeled_score >= 0.5, 1, 0)

        all_labeled_scores[i] = labeled_score
        truth_labels[i] = labels

    mean_spearmanr, mean_separation, f1, threshold = calculate_model_scores(model_name, queries, all_labeled_scores, truth_labels)
    final_score = (mean_spearmanr + mean_separation + f1) / 3.0

    print(
        f"Model: {model_name}\n"
        f"  Spearmans correlation: {mean_spearmanr:.4f}\n"
        f"  Separation score: {mean_separation:.4f}\n"
        f"  F1 score: {f1:.4f} at threshold {threshold:.4f}\n"
        f"  Final combined score: {final_score:.4f}"
    )

    return {
        "model_name": model_name,
        "agreement": mean_spearmanr,
        "separation": mean_separation,
        "f1": f1,
        "threshold": threshold,
        "final_score": final_score,
    }


def benchmark_models():
    labeled_queries_path = os.path.join(repo_root, "benchmark", "queries_with_labeled_scores.json")
    results = []
    for model in embedding_models:
        build_and_save_column_embeddings(model_name=model, embeddings_path=embeddings_path(model))
        result = score_model_with_labeled_data(model, labeled_queries_path)
        results.append(result)

    print_benchmark_results(results)

    return results


def print_benchmark_results(results: List[Dict]):
    results.sort(key=lambda item: item["final_score"], reverse=True)
    print("\nRanked models:")
    model_width = max(len("Model"), max((len(result["model_name"]) for result in results), default=0))
    rank_width = max(len("#"), len(str(len(results))))
    score_width = max(len("Agreement"), len("Separation"), len("Threshold"), len("Final"), 9)
    f1_width = max(len("F1"), 9)

    header = (
        f"{'#':>{rank_width}}  "
        f"{'Model':<{model_width}}  "
        f"{'Agreement':>{score_width}}  "
        f"{'Separation':>{score_width}}  "
        f"{'F1':>{f1_width}}  "
        f"{'Threshold':>{score_width}}  "
        f"{'Final':>{score_width}}"
    )
    print(header)
    print('-' * len(header))
    for i, result in enumerate(results, start=1):
        name = result['model_name']
        row = (
            f"{i:>{rank_width}}  "
            f"{name:<{model_width}}  "
            f"{result['agreement']:>{score_width}.4f}  "
            f"{result['separation']:>{score_width}.4f}  "
            f"{result['f1']:>{f1_width}.4f}  "
            f"{result['threshold']:>{score_width}.4f}  "
            f"{result['final_score']:>{score_width}.4f}"
        )
        print(row)



if __name__ == "__main__":
    benchmark_models()
    
    #build_leave_one_out_vote_tables()
    #benchmark_models_with_leave_one_out()