# 로컬 SD3.5 Wrapper 연결 가이드

## 왜 wrapper가 필요한가

메인 FastAPI 앱은 이미지 생성을 아래 endpoint로 요청합니다.

```text
POST http://127.0.0.1:8188/sd35/generate
```

하지만 ComfyUI나 diffusers는 이 endpoint를 기본으로 제공하지 않습니다. 그래서 중간에 작은 FastAPI wrapper를 하나 띄워, 메인 앱이 보내는 `prompt`를 실제 로컬 모델 추론 코드로 넘겨야 합니다.

## 현재 제공하는 wrapper

파일:

```text
scripts/sd35_wrapper.py
```

지원 모드:

- `fallback`: 모델 없이 Pillow로 대체 이미지를 생성합니다. endpoint 연결 테스트와 발표 시연용입니다.
- `diffusers`: Hugging Face diffusers로 Stable Diffusion 3.5를 로드해 실제 이미지를 생성합니다.

## 1. 연결 테스트용 fallback wrapper 실행

모델 설치 없이 바로 실행할 수 있습니다.

```bash
source .venv/bin/activate
python -m scripts.sd35_wrapper
```

다른 터미널에서 확인:

```bash
curl http://127.0.0.1:8188/health
```

메인 앱의 `.env`는 빠른 기본값 기준 아래처럼 맞춰져 있습니다.

```env
IMAGE_PROVIDER=sd35
SD35_ENDPOINT_URL=http://127.0.0.1:8188/sd35/generate
SD35_MODEL=stabilityai/sdxl-turbo
SD35_WIDTH=1024
SD35_HEIGHT=768
SD35_STEPS=4
SD35_GUIDANCE_SCALE=2.0
SD35_FALLBACK_TO_LOCAL=true
```

이 상태에서 메인 앱을 실행하면:

```bash
source .venv/bin/activate
python run.py
```

브라우저에서 생성 시 wrapper가 만든 이미지가 배경으로 들어갑니다.

## 2. 실제 SD3.5 diffusers wrapper 실행

먼저 PyTorch CUDA 버전을 설치해야 합니다. PyTorch 설치 명령은 GPU/CUDA 버전에 따라 달라지므로 공식 안내를 따르는 것을 권장합니다.

```text
https://pytorch.org/get-started/locally/
```

그 다음 diffusers 계열을 설치합니다.

```bash
source .venv/bin/activate
pip install -U diffusers transformers accelerate safetensors sentencepiece protobuf
```

또는 이 저장소에 추가한 전용 requirements 파일로 한 번에 설치할 수 있습니다.

```bash
source .venv/bin/activate
pip install -r requirements-sd35.txt
```

Hugging Face 모델 접근이 필요한 경우 로그인합니다.

```bash
huggingface-cli login
```

실제 모델 모드로 wrapper를 실행합니다.

```bash
source .venv/bin/activate
SD35_WRAPPER_BACKEND=diffusers \
SD35_DIFFUSERS_MODEL_ID=stabilityai/sdxl-turbo \
SD35_TORCH_DTYPE=float16 \
SD35_DEVICE=cuda \
SD35_ENABLE_CPU_OFFLOAD=true \
python -m scripts.sd35_wrapper
```

이 저장소에서는 아래 실행 스크립트로 같은 설정을 바로 사용할 수 있습니다.

```bash
./scripts/run_sd35_wrapper_local.sh
```

참고:

- Stable Diffusion 3.5 계열은 Hugging Face gated repo 인증이 필요할 수 있습니다.
- 현재 실행 스크립트 기본값은 인증 없이 바로 돌려볼 수 있는 `stabilityai/sdxl-turbo`입니다.
- 추후 HF 접근 권한이 준비되면 `SD35_DIFFUSERS_MODEL_ID=stabilityai/stable-diffusion-3.5-medium` 또는 `...-large`로 바꿔 사용할 수 있습니다.

GPU 메모리가 부족하면 먼저 아래 선택지를 고려하세요.

- `stabilityai/stable-diffusion-3.5-large-turbo` 사용
- 이미지 크기를 `1024x1024` 또는 `1024x768`로 낮추기
- `SD35_ENABLE_CPU_OFFLOAD=true` 사용
- ComfyUI/TensorRT 최적화 workflow 사용

## 3. wrapper API 형식

요청 예시:

```json
{
  "model": "stabilityai/sdxl-turbo",
  "prompt": "premium cafe campaign background, no text",
  "negative_prompt": "readable text, logo, watermark",
  "width": 1024,
  "height": 768,
  "num_inference_steps": 4,
  "guidance_scale": 2.0,
  "response_format": "b64_json"
}
```

응답:

```json
{
  "provider": "sd35-diffusers",
  "model": "stabilityai/stable-diffusion-3.5-large",
  "data": [
    {
      "b64_json": "..."
    }
  ]
}
```

메인 앱은 이 응답을 받아 `app/static/generated/backgrounds/`에 저장하고 배너 합성에 사용합니다.

## 참고 공식 문서

- Stable Diffusion 3.5 Large model card: https://huggingface.co/stabilityai/stable-diffusion-3.5-large
- Diffusers SD3 pipeline docs: https://huggingface.co/docs/diffusers/en/api/pipelines/stable_diffusion/stable_diffusion_3
- PyTorch install selector: https://pytorch.org/get-started/locally/
