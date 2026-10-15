FROM python:3.14.8-slim-trixie AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY _download_model.py .

RUN pip install --no-cache-dir \
    huggingface_hub==2.2.0 \
    transformers==5.19.0 && \
    python _download_model.py && \
    rm _download_model.py

FROM python:3.14.8-slim-trixie

COPY --from=builder /model /model

RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Nothing installs packages at runtime, so pip only adds CVEs.
RUN pip install --no-cache-dir \
    onnxruntime==1.26.0 \
    tokenizers==0.23.3 \
    starlette==1.8.0 \
    uvicorn==0.54.0 && \
    pip uninstall -y --root-user-action=ignore pip && \
    rm -rf /root/.cache

WORKDIR /app
COPY app.py .

EXPOSE 80
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
