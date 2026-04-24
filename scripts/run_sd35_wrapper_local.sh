#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if [[ -f ".env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

export SD35_WRAPPER_BACKEND="${SD35_WRAPPER_BACKEND:-diffusers}"
DEFAULT_SD35_DIFFUSERS_MODEL="${SD35_DIFFUSERS_MODEL_ID:-${SD35_MODEL:-stabilityai/stable-diffusion-3.5-medium}}"
if [[ "${DEFAULT_SD35_DIFFUSERS_MODEL,,}" == *"tensorrt"* ]]; then
  DEFAULT_SD35_DIFFUSERS_MODEL="stabilityai/stable-diffusion-3.5-medium"
fi
export SD35_DIFFUSERS_MODEL_ID="${DEFAULT_SD35_DIFFUSERS_MODEL}"
export SD35_FALLBACK_DIFFUSERS_MODEL_ID="${SD35_FALLBACK_DIFFUSERS_MODEL_ID:-stabilityai/sdxl-turbo}"
export SD35_DEVICE="${SD35_DEVICE:-cuda}"
export SD35_TORCH_DTYPE="${SD35_TORCH_DTYPE:-float16}"
export SD35_ENABLE_CPU_OFFLOAD="${SD35_ENABLE_CPU_OFFLOAD:-true}"
export SD35_WRAPPER_HOST="${SD35_WRAPPER_HOST:-127.0.0.1}"
export SD35_WRAPPER_PORT="${SD35_WRAPPER_PORT:-8188}"

exec "${ROOT_DIR}/.venv/bin/python" -m scripts.sd35_wrapper
