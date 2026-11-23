# MethaTwin on Hugging Face Spaces (Docker SDK).
# The Space holds only this Dockerfile, its README (Space config) and the trained surrogates (66 MB, Git LFS).
# The app code is cloned from GitHub at build time, so GitHub stays the single source of truth.
FROM python:3.14-slim

# libgomp1: OpenMP runtime needed by XGBoost and scikit-learn
RUN apt-get update && apt-get install -y --no-install-recommends git libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Spaces run the container as user 1000
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user PATH=/home/user/.local/bin:$PATH PYTHONUNBUFFERED=1
WORKDIR /home/user

ARG REPO=Louay22-stack/MethaTwin
ARG REF=main
# Re-clone whenever the branch moves: ADD re-fetches this URL on every build and busts the cache if it changed
ADD --chown=user https://api.github.com/repos/${REPO}/git/refs/heads/${REF} /tmp/ref.json
RUN git clone --depth 1 --branch ${REF} https://github.com/${REPO}.git app

WORKDIR /home/user/app
RUN pip install --no-cache-dir --user -r deploy/huggingface/requirements.txt

COPY --chown=user surrogates.joblib 04_models_and_simulations/step6_surrogate/models/surrogates.joblib

EXPOSE 7860
CMD ["streamlit", "run", "05_code/dashboard/app.py", "--server.port=7860", "--server.address=0.0.0.0", \
     "--server.headless=true", "--browser.gatherUsageStats=false"]
