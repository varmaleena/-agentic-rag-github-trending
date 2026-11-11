# Agentic RAG for GitHub repositories

FastAPI serves a LangGraph workflow over GitHub README chunks indexed in Qdrant. The scheduled job searches for popular public repositories created in the past 30 days. Terraform defines a 15-minute ingestion schedule.

- `POST /api/query` and `/ws/chat` execute the same graph. The WebSocket sends node transitions, streamed answer text, and the final score, retries, and graph path.
- The graph grades retrieved context and rewrites the query up to three times by default. If retrieval still lacks relevant evidence, the answer says so. Failed and skipped evaluations have a null score and are excluded from the dashboard average.
- A score below the configured threshold flags retrieved points in Qdrant. The next ingestion run refreshes flagged repositories before fetching new ones. Deterministic point IDs let ingestion update chunks in place.
- README text is treated as untrusted source data in prompts. A heuristic ingestion filter skips repositories containing common instruction-override or secret-extraction patterns. The filter can miss obfuscated attacks and skip benign documentation that quotes those patterns.

## Run locally

Install Python 3.11+, Node.js, and run a Qdrant instance reachable at `localhost:6333` or configure its host and port. From the repository root, install dependencies and populate the index. First use downloads the BGE embedding model.

```sh
python -m pip install -r backend/requirements.txt
python ingestion/lambda_handler.py
```

Ingestion reads `GITHUB_TOKEN` from the environment if set. Run the API from the repository root.

```sh
python -m uvicorn app.main:app --app-dir backend --port 8000
```

The default provider is Bedrock, using the AWS SDK credential chain and the configured `BEDROCK_MODEL_ID`. To use Vertex AI, enable the API in your Google Cloud project, configure Application Default Credentials, and set `LLM_PROVIDER=vertex`, `GOOGLE_CLOUD_PROJECT`, and `GEMINI_MODEL`. `GOOGLE_CLOUD_LOCATION` defaults to `global`. See the [Vertex AI streaming example](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/samples/googlegenaisdk-textgen-with-txt-stream).

In a second terminal, run the frontend and open the local URL printed by Vite.

```sh
cd frontend
npm ci
npm run dev
```

Run the offline tests from the repository root.

```sh
python -m pytest tests -q
```

## Benchmark

The evaluation harness compares one-pass RAG against the corrective graph on the same Qdrant collection and provider. Use a frozen collection and a JSONL file with 30–50 distinct reviewed questions. Each row needs `question`, `answer`, `repo` (owner/name), and `chunk_index` for a reference chunk containing the answer. Keep ingestion paused during the run so the corpus stays fixed. The benchmark graph does not write reindex flags.

```sh
python backend/evaluate_rag.py golden.jsonl --output benchmark-results.json
```

Hit@5 checks whether the final retrieval contains the reference chunk. The judge scores faithfulness to the retrieved sources and relevancy to the question with the expected answer as a reference. The generated Markdown table reports coverage for each judge metric.

The reviewed golden set and live benchmark results are pending.

## Deployment

The AWS Terraform configuration is under `infra/`. It expects a built backend image and an `ingestion.zip` deployment package. Include the ingestion modules, the backend `app` package, and the runtime dependencies in the ingestion deployment package. Local tests use mocked model calls and an in-memory Qdrant instance.
