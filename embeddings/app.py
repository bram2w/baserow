from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.responses import JSONResponse
from starlette.routing import Route
import onnxruntime as ort
from tokenizers import Tokenizer
import numpy as np
import asyncio
import math
import os

MODEL_DIR = "/model"

# tokenizer.json ships with truncation and fixed padding at 128 tokens, but the
# vectors have always been generated the way transformers' AutoTokenizer did it:
# truncate at the model_max_length of 512 and pad to the longest text in the batch.
tokenizer = Tokenizer.from_file(os.path.join(MODEL_DIR, "tokenizer.json"))
tokenizer.enable_truncation(max_length=512)
tokenizer.enable_padding(pad_id=0, pad_token="[PAD]")


def read_cgroup_cpu_quota():
    try:
        with open("/sys/fs/cgroup/cpu.max") as f:
            quota, period = f.read().split()
        return None if quota == "max" else (int(quota), int(period))
    except (OSError, ValueError):
        pass

    # Older hosts still run cgroup v1, where -1 means unlimited.
    try:
        with open("/sys/fs/cgroup/cpu/cpu.cfs_quota_us") as f:
            quota = int(f.read())
        with open("/sys/fs/cgroup/cpu/cpu.cfs_period_us") as f:
            period = int(f.read())
        return None if quota <= 0 else (quota, period)
    except (OSError, ValueError):
        return None


def default_num_threads():
    # onnxruntime sizes its thread pool by the host cores and ignores the container
    # CPU limit, which causes heavy throttling when the container is limited.
    count = os.process_cpu_count() or 1
    cpu_quota = read_cgroup_cpu_quota()
    if cpu_quota:
        quota, period = cpu_quota
        count = min(count, max(1, math.ceil(quota / period)))
    return count


session_options = ort.SessionOptions()
session_options.intra_op_num_threads = int(
    os.environ.get("EMBEDDINGS_NUM_THREADS") or default_num_threads()
)
model_path = os.path.join(MODEL_DIR, "model.onnx")
session = ort.InferenceSession(
    model_path, session_options, providers=["CPUExecutionProvider"]
)

# Inference already uses all available threads, so running requests in parallel
# would only oversubscribe the CPU.
inference_lock = asyncio.Lock()


def mean_pooling(token_embeddings, attention_mask):
    input_mask_expanded = np.expand_dims(attention_mask, -1)
    input_mask_expanded = np.broadcast_to(input_mask_expanded, token_embeddings.shape).astype(float)
    sum_embeddings = np.sum(token_embeddings * input_mask_expanded, axis=1)
    sum_mask = np.clip(np.sum(input_mask_expanded, axis=1), a_min=1e-9, a_max=None)
    return sum_embeddings / sum_mask


def compute_embeddings(texts):
    encodings = tokenizer.encode_batch(texts)
    ort_inputs = {
        "input_ids": np.array([e.ids for e in encodings], dtype=np.int64),
        "attention_mask": np.array([e.attention_mask for e in encodings], dtype=np.int64),
        "token_type_ids": np.array([e.type_ids for e in encodings], dtype=np.int64),
    }

    ort_outputs = session.run(None, ort_inputs)
    token_embeddings = ort_outputs[0]

    embeddings = mean_pooling(token_embeddings, ort_inputs["attention_mask"])
    embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
    return embeddings.tolist()


async def embed(request):
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    if not data or "texts" not in data:
        return JSONResponse({"error": "Missing texts field"}, status_code=400)

    texts = data["texts"]
    if isinstance(texts, str):
        texts = [texts]

    if not texts:
        return JSONResponse({"error": "Empty texts field"}, status_code=400)

    # Run in a thread so the event loop keeps answering health checks during a
    # long batch.
    async with inference_lock:
        embeddings = await run_in_threadpool(compute_embeddings, texts)

    return JSONResponse({"embeddings": embeddings})

async def health(request):
    return JSONResponse({"status": "healthy"})

app = Starlette(
    routes=[
        Route("/embed", embed, methods=["POST"]),
        Route("/health", health, methods=["GET"]),
    ]
)
