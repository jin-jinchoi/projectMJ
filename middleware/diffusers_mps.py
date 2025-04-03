from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import torch
from diffusers import StableDiffusionPipeline
# FluxPipeline StableDiffusionPipeline
import base64
from io import BytesIO

# FastAPI 프레임워크를 사용해서 서버 생성
app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model_id = "runwayml/stable-diffusion-v1-5" 

# Linaqruf/anything-v3.0
# runwayml/stable-diffusion-v1-5

device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"using device: {device}")

# Stable Diffusion의 전체 과정을 하나의 파이프라인으로 처리
pipe = StableDiffusionPipeline.from_pretrained(
    model_id,
     # MPS에서는 float32가 더 안정적
    torch_dtype=torch.float32, 
    safety_checker=None
)

pipe = pipe.to(device)
#모델 성능 최적화
pipe.enable_attention_slicing()
pipe.enable_vae_tiling()

class TextToImageRequest(BaseModel):
    prompt: str
    negative_prompt: str = ""
    width: int = 512
    height: int = 512
    steps: int = 20  
    cfg_scale: float = 7.0 
    sampler_name: str = "Euler a"


# 이미지 생성 엔드포인트
@app.post("/sdapi/v1/txt2img")
async def generate_image(request: TextToImageRequest):
    try:
      
        image = pipe(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            width=request.width,
            height=request.height,
            num_inference_steps=request.steps, 
            guidance_scale=request.cfg_scale, 
    
        ).images[0]

        # base64 인코딩된 문자열로 변환
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return {"images": [img_str]}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 서버 상태 확인
@app.get("/health")
async def health_check():
    return {"status": "healthy", "model": model_id, "device": device}

if __name__ == "__main__":
    import uvicorn
    print(f"Starting server with {model_id} model on {device}...")
    uvicorn.run(app, host="127.0.0.1", port=7861)