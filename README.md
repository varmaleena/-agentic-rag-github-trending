# Agentic RAG for GitHub repositories

FastAPI serves a LangGraph workflow over GitHub README chunks indexed in Qdrant. The scheduled job searches for popular public repositories created in the past 30 days. Terraform defines a 15-minute ingestion schedule.

- `POST /api/query` and `/ws/chat` execute the same graph. The WebSocket sends node transitions, streamed answer text, and the final score, retries, and graph path.
- The graph grades retrieved context and rewrites the query up to three times by default. If retrieval still lacks relevant evidence, the answer says so. Failed and skipped evaluations have a null score and are excluded from the dashboard average.
- A score below the configured threshold flags retrieved points in Qdrant. The next ingestion run refreshes flagged repositories before fetching new ones. Deterministic point IDs let ingestion update chunks in place.
- README text is treated as untrusted source data in prompts. A heuristic ingestion filter skips repositories containing common instruction-override or secret-extraction patterns. The filter can miss obfuscated attacks and skip benign documentation that quotes those patterns.

## Run locally

Install Python 3.11+, Node.js, and run a Qdrant instance reachable at `localhost:6333` or configure its host and port. From the repository root, install dependencies and populate the index. First use downloads the BGE small v1.5 ONNX embedding model. When upgrading an existing installation from Sentence Transformers, rebuild into a fresh Qdrant collection so both indexing and retrieval use the same runtime.

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

The evaluation harness compares one-pass RAG against the corrective graph on the same Qdrant collection and provider. Use a frozen collection and a JSONL file with 30–50 distinct reviewed questions. Each row needs `question`, `answer`, `repo` (owner/name), and `chunk_index` for a reference chunk containing the answer. Keep ingestion paused during the run so the corpus stays fixed. Benchmark runs leave the indexed corpus unchanged.

```sh
python backend/evaluate_rag.py golden.jsonl --output benchmark-results.json
```

Hit@5 checks whether the final retrieval contains the reference chunk. The judge scores faithfulness to the retrieved sources and relevancy to the question with the expected answer as a reference. The generated Markdown table reports coverage for each judge metric.

The checked-in golden set contains 30 source-grounded questions and answers from eight public GitHub repositories. The snapshot manifest pins each README by Git blob ID. To recreate the benchmark using the bundled corpus, run:

```sh
python backend/evaluate_rag.py benchmark/golden.jsonl --snapshot benchmark/corpus.json --output benchmark-local.json
```

The recorded run used Bedrock Amazon Nova Lite (`us.amazon.nova-lite-v1:0`) for generation and judging, BGE small v1.5 via FastEmbed, and 97 real README chunks in local Qdrant. See the [golden questions](benchmark/golden.jsonl) and [per-question results](benchmark/results.json).

| System | Questions | Hit@5 | Faithfulness (scored/total) | Relevancy (scored/total) |
| --- | ---: | ---: | ---: | ---: |
| Plain RAG | 30 | 19/30 (63.3%) | 0.957 (30/30) | 0.907 (30/30) |
| Corrective RAG | 30 | 19/30 (63.3%) | 0.982 (28/30) | 0.979 (28/30) |

The corrective graph rewrote five queries and abstained on two. On the 28 questions both systems answered and scored, faithfulness was 0.961 for plain RAG and 0.982 for corrective RAG, and relevancy was 0.914 and 0.979. These are judge scores from one run on a small corpus. The retrieval hit rate was unchanged.

## MCP retriever

Launch the read-only MCP tool over stdio from the backend directory:

```sh
python -m app.retriever_mcp
```

Configure your orchestrator to launch that command with the backend as its working directory and the same Qdrant settings as the API. Call `retrieve_repositories` with a `query` and an optional `limit` between 1 and 20. Results contain document IDs, similarity scores, repository names, source URLs, and untrusted README text.

## History and tracing

Query history is stored in SQLite at `data/query_history.sqlite3` by default. Set `HISTORY_DATABASE_URL` to use PostgreSQL across service instances. Production deployments should use a TLS-verified database connection and restrict dashboard access to trusted users.

Set `OTEL_EXPORTER_OTLP_ENDPOINT` for an OTLP HTTP collector or `OTEL_EXPORTER_OTLP_TRACES_ENDPOINT` for a traces-specific URL. The API emits a request span and a span per graph node. Span durations reflect actual execution. Retry counts and provider-reported token counts are included where available. Query and README text are omitted from span attributes.

## Deployment

**Cloud Run** uses Vertex AI by default in [infra/cloud-run](infra/cloud-run). Supply a Google Cloud project, an enabled Gemini model ID, a registry image built with `docker build backend`, an HTTPS Qdrant URL, and two existing Google Secret Manager secret IDs for the Qdrant API key and PostgreSQL connection URL. Cloud Run terminates HTTPS and requires an authorized invoker. The service account uses Application Default Credentials.

**AWS** uses Bedrock and retains the 15-minute ingestion schedule. Build the backend image with `docker build backend` and the Lambda image from the root with `docker build --platform linux/amd64 --provenance=false -f ingestion/Dockerfile .`, then push both images to ECR. Set the image URIs, ACM certificate ARN, HTTPS Qdrant URL, and Secrets Manager ARNs for the Qdrant key, database URL, and GitHub token. Each secret contains a plain string. Point your DNS name at the ALB and use that name for HTTPS. Review the Terraform plan before upgrading an existing AWS stack. Migrate the legacy EC2 Qdrant collection to the authenticated endpoint before retiring the old instance.

For either backend, set `VITE_API_URL` at frontend build time. An HTTPS API URL makes the chat use WSS.
