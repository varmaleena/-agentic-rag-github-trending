"""Compare plain retrieval and corrective RAG against a frozen corpus and golden set."""
import argparse
import json
from pathlib import Path
from statistics import mean

from app.api.routes import graph_config
from app.graph.graph import build_graph


def load_questions(path):
    questions = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not 30 <= len(questions) <= 50:
        raise ValueError("Provide 30–50 reviewed questions")
    if len({row["question"] for row in questions}) != len(questions):
        raise ValueError("Questions must be unique")
    for row in questions:
        for key in ("question", "answer", "repo"):
            if not isinstance(row[key], str) or not row[key].strip():
                raise ValueError(f"Missing {key} in benchmark case")
        if type(row["chunk_index"]) is not int or row["chunk_index"] < 0:
            raise ValueError("Expected a nonnegative reference chunk_index")
    return questions


def run_case(graph, case):
    state = graph.invoke(
        {"query": case["question"], "reference_answer": case["answer"]}, config=graph_config()
    )
    hit = any(
        doc["payload"].get("repo_name", "").casefold() == case["repo"].casefold()
        and doc["payload"].get("chunk_index") == case["chunk_index"]
        for doc in state.get("documents", [])
    )
    return {
        "question": case["question"],
        "hit_at_5": hit,
        "faithfulness": state.get("faithfulness"),
        "relevancy": state.get("relevancy"),
        "error": state.get("error"),
        "graph_path": state["graph_path"],
    }


def summary(rows, field):
    values = [row[field] for row in rows if row[field] is not None]
    return f"{mean(values):.3f} ({len(values)}/{len(rows)})" if values else "— (0 scored)"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("golden_set", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path, help="Index a pinned GitHub corpus in local Qdrant")
    parser.add_argument("--readme-cache", type=Path, help="Optional local README cache for the snapshot")
    args = parser.parse_args()
    questions = load_questions(args.golden_set)
    if args.snapshot:
        from benchmark_snapshot import index_snapshot

        points = index_snapshot(args.snapshot, args.readme_cache)
        print(f"Indexed {points} snapshot chunks", flush=True)
    results = {}
    for name, corrective in (("Plain RAG", False), ("Corrective RAG", True)):
        graph = build_graph(corrective=corrective, write_reindex_flags=False)
        results[name] = []
        for number, case in enumerate(questions, 1):
            results[name].append(run_case(graph, case))
            print(f"{name}: {number}/{len(questions)}", flush=True)

    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("| System | N | Hit@5 | Faithfulness (scored/total) | Relevancy (scored/total) |")
    print("| --- | ---: | ---: | ---: | ---: |")
    for name, rows in results.items():
        print(f"| {name} | {len(rows)} | {mean(r['hit_at_5'] for r in rows):.1%} | "
              f"{summary(rows, 'faithfulness')} | {summary(rows, 'relevancy')} |")


if __name__ == "__main__":
    main()
