FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/huggingface

WORKDIR /app

# Build a CPU-only PyTorch environment. The repository's development lockfile
# contains NVIDIA/CUDA wheels, which are unnecessary and far too large for a
# small CPU Droplet.
COPY requirements.txt ./
RUN grep -v -E '^(cuda-|nvidia-|triton==|torch==)' requirements.txt > /tmp/requirements-cpu.txt \
    && pip install --index-url https://download.pytorch.org/whl/cpu torch==2.12.0 \
    && pip install -r /tmp/requirements-cpu.txt

# Bake the embedding model into the image. config.py keeps Hugging Face offline
# at runtime, so container starts do not depend on model-download availability.
RUN HF_HUB_OFFLINE=0 python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY . ./

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--proxy-headers"]
