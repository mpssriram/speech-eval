FROM condaforge/miniforge3:25.3.1-0@sha256:1e65803d646bf8503728001dddb5756f3e8235e0883c19b5a5ad1da85cff0905

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv UV_PYTHON_INSTALL_DIR=/opt/python \
    CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
    PATH=/opt/venv/bin:/opt/conda/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg rubberband-cli sox libsndfile1 git make curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv==0.12.21 \
    && conda create -y -n aligner -c conda-forge \
       python=3.14 montreal-forced-aligner=3.4.2 kalpy=0.10.5 \
    && conda clean -afy
RUN usermod --login sriram --home /home/sriram --move-home ubuntu \
    && groupmod --new-name sriram ubuntu \
    && ln -s /opt/conda /home/sriram/miniforge3
ENV MFA_ROOT_DIR=/home/sriram/Documents/MFA
RUN mkdir -p "$MFA_ROOT_DIR/pretrained_models/acoustic" \
       "$MFA_ROOT_DIR/pretrained_models/dictionary" "$MFA_ROOT_DIR/pretrained_models/g2p" \
    && curl --fail --location --retry 4 --show-error \
       https://github.com/MontrealCorpusTools/mfa-models/releases/download/acoustic-english_mfa-v3.1.0/english_mfa.zip \
       -o "$MFA_ROOT_DIR/pretrained_models/acoustic/english_mfa.zip" \
    && curl --fail --location --retry 4 --show-error \
       https://github.com/MontrealCorpusTools/mfa-models/releases/download/dictionary-english_us_mfa-v3.1.0/english_us_mfa.dict \
       -o "$MFA_ROOT_DIR/pretrained_models/dictionary/english_us_mfa.dict" \
    && curl --fail --location --retry 4 --show-error \
       https://github.com/MontrealCorpusTools/mfa-models/releases/download/g2p-english_us_mfa-v3.0.0/english_us_mfa.zip \
       -o "$MFA_ROOT_DIR/pretrained_models/g2p/english_us_mfa.zip" \
    && chown -R sriram:sriram /home/sriram
COPY docker/mfa_models.sha256 /tmp/mfa_models.sha256
RUN sha256sum -c /tmp/mfa_models.sha256

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --extra dev --no-install-project
COPY src ./src
COPY api ./api
COPY configs ./configs
COPY tests ./tests
COPY scripts ./scripts
COPY reports ./reports
COPY Makefile Dockerfile docker-compose.yml ./
ARG GIT_COMMIT=""
ENV SPEECHEVAL_GIT_COMMIT=${GIT_COMMIT}
RUN uv sync --frozen --extra dev \
    && mkdir -p data .pytest_work/tmp reports/reproduced \
    && chown -R sriram:sriram /app
USER sriram
ENTRYPOINT []
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=12 \
    CMD python -c "from urllib.request import urlopen; urlopen('http://127.0.0.1:8000/api/health',timeout=4)"
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
