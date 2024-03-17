FROM pytorch/pytorch:2.2.1-cuda12.1-cudnn8-runtime

WORKDIR /app

RUN apt update
RUN apt install -y git curl libgl1

# Install comfyui
RUN git clone --depth 1 --branch execution_model_inversion https://github.com/guill/ComfyUI.git .
RUN pip install -r requirements.txt

# Install custom nodes
WORKDIR /app/custom_nodes
RUN for repo in \
    "jags111/efficiency-nodes-comfyui" \
    "vivax3794/ComfyUI-Vivax-Nodes" \
    "crystian/ComfyUI-Crystools" \
    "MatissesProjects/MatisseComfyNodes" \
    "sipherxyz/comfyui-art-venture" \
    "WASasquatch/was-node-suite-comfyui" \
    "Kosinkadink/ComfyUI-AnimateDiff-Evolved" \
    "Kosinkadink/ComfyUI-VideoHelperSuite" \
    "Kosinkadink/ComfyUI-Advanced-ControlNet" \
    ; do \
    git clone --depth 1 https://github.com/$repo.git && \
    touch $(basename $repo)/requirements.txt && \
    pip install -r $(basename $repo)/requirements.txt; \
    done
WORKDIR /app
RUN pip install segment_anything omegaconf

EXPOSE 8188
CMD ["python", "main.py", "--listen"]

HEALTHCHECK --interval=5s --timeout=10s --retries=5 \
  CMD curl -f http://localhost:8188


