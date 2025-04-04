from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import uuid
import json
import urllib.request
import urllib.parse
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import os
import random
import asyncio

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COMFY_SERVER = "http://192.168.1.133:8188"

class PromptRequest(BaseModel):              
    prompt_text: str  # 텍스트 프롬프트
    workflow_name: str = "0404test" 
    client_id: Optional[str] = None
    seed: Optional[int] = None  # 옵션: 시드값

workflow_dir = "workflow"
os.makedirs(workflow_dir, exist_ok=True)

# 워크플로우 호출
def load_workflow(workflow_name="0404test"):
    workflow_path = os.path.join(workflow_dir, f"{workflow_name}.json")
    print(f"워크플로우 로드 경로: {workflow_path}")

    try:
        if os.path.exists(workflow_path):
            with open(workflow_path, 'r', encoding="utf-8") as f:
                workflow = json.load(f)
                print(f"워크플로우 노드 목록: {list(workflow.keys())}")
                return workflow
        else:
            raise HTTPException(status_code=404, detail=f"워크플로우 '{workflow_name}'를 찾을 수 없습니다.")
    except Exception as e:
        print(f"워크플로우 로드 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"워크플로우 로드 오류: {str(e)}")

# CompyUI에 이미지 생성 요청
def queue_prompt(prompt, client_id=None):
    if not client_id:
        client_id = str(uuid.uuid4())
    
    p = {
        "prompt": prompt,
        "client_id": client_id
    }
    
    data = json.dumps(p).encode("utf-8")
    req = urllib.request.Request(f"{COMFY_SERVER}/prompt", data=data, method="POST")

    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read())
    except Exception as e:
        # 에러 발생
        raise HTTPException(status_code=500, detail=f"ComfyUI 서버 오류: {str(e)}")

# 이미지 가져오기
def fetch_image(filename, subfolder, folder_type):
    try:
        data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
        url_values = urllib.parse.urlencode(data)
        url = f"{COMFY_SERVER}/view?{url_values}"
        print(f"이미지 요청 URL: {url}")
        with urllib.request.urlopen(url) as response:
            return response.read()
    except Exception as e:
        print(f"이미지 가져오기 오류 상세: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이미지 가져오기 오류: {str(e)}")
        
# 히스토리 데이터 가져오기
def fetch_history(prompt_id):
    try:
        url = f"{COMFY_SERVER}/history/{prompt_id}"
        print(f"히스토리 요청 URL: {url}")
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"히스토리 데이터 가져오기 오류: {str(e)}")

# 엔드포인트
# 이미지 생성
@app.post('/api/generate-image')
async def generate_image(request: PromptRequest):
    try:
        # 워크플로우 로드
        workflow = load_workflow(request.workflow_name)
        
        # 프롬프트 텍스트 적용
        workflow["4"]["inputs"]["text"] = request.prompt_text
        
        # 시드 설정 (제공된 경우)
        if request.seed is not None:
            workflow["11"]["inputs"]["seed"] = request.seed
        else:
            # 랜덤 시드 생성
            workflow["11"]["inputs"]["seed"] = random.randint(1, 9999999999)
        
        print(f"워크플로우 로드: {request.workflow_name}, 프롬프트: {request.prompt_text}")
        
        # SaveImage 노드가 있는지 확인 (이미 워크플로우에 있으므로 추가 필요 없음)
        print("SaveImage 노드 확인:", "12" in workflow)

        # ComfyUI에 요청 보내기
        client_id = request.client_id or f"api_{uuid.uuid4()}"
        result = queue_prompt(workflow, client_id)
        return result
    except Exception as e:
        print(f"이미지 생성 오류 상세: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이미지 생성 오류: {str(e)}")


@app.get('/api/image')
async def get_image_preview(filename: str, subfolder: str = "", folder_type: str = "output"):
    try:
        print(f"이미지 요청: filename={filename}, subfolder={subfolder}, folder_type={folder_type}")
        
        # 여러 폴더 타입 시도
        folder_types_to_try = [folder_type]  # 우선 요청된 타입부터 시도
        
        # 요청된 타입이 output이나 temp가 아니면 둘 다 추가로 시도
        if folder_type != "output":
            folder_types_to_try.append("output")
        if folder_type != "temp":
            folder_types_to_try.append("temp")
            
        # 요청된 타입이 빈 문자열이면 기본값으로 output 사용
        if folder_type == "":
            folder_types_to_try = ["output", "temp"]
        
        for type_to_try in folder_types_to_try:
            try:
                data = {"filename": filename, "subfolder": subfolder, "type": type_to_try}
                url_values = urllib.parse.urlencode(data)
                print('이미지 값', url_values)
                full_url = f"{COMFY_SERVER}/view?{url_values}"
                print(f"시도 중: {full_url}")
                
                with urllib.request.urlopen(full_url) as response:
                    image_data = response.read()
                    print(f"이미지 로드 성공 ({type_to_try}): {len(image_data)} 바이트")
                    return Response(content=image_data, media_type="image/png")
            except urllib.error.HTTPError as e:
                print(f"{type_to_try} 폴더에서 이미지를 찾지 못했습니다: {e.code} {e.reason}")
                continue
                
        # 모든 시도 실패
        raise HTTPException(status_code=404, detail="이미지를 찾을 수 없습니다")
                
    except Exception as e:
        print(f"이미지 호출 상세 오류: {str(e)}")
        
        # 사용 가능한 파일 목록 확인 시도
        try:
            # 최근 프롬프트 ID 가져오기
            with urllib.request.urlopen(f"{COMFY_SERVER}/history") as response:
                history_data = json.loads(response.read())
                prompt_ids = list(history_data.keys())
                
                if prompt_ids:
                    latest_prompt_id = prompt_ids[-1]
                    print(f"최근 프롬프트 ID: {latest_prompt_id}")
                    
                    # 최근 이미지 정보 가져오기
                    prompt_info = history_data[latest_prompt_id]
                    if "outputs" in prompt_info:
                        for node_id, output in prompt_info["outputs"].items():
                            if "images" in output:
                                print(f"노드 {node_id}의 이미지들:")
                                for img in output["images"]:
                                    print(f"  - {img['filename']} (타입: {img['type']}, 폴더: {img['subfolder']})")
        except Exception as hist_error:
            print(f"히스토리 정보 확인 중 오류: {str(hist_error)}")
            
        raise HTTPException(status_code=500, detail=f"이미지 호출 오류: {str(e)}")

#히스토리 데이터 가져오기
@app.get('/api/history/{prompt_id}')
async def get_prompt_history(prompt_id: str):
    try:
        history_data = fetch_history(prompt_id)
        

        # 히스토리 데이터에서 이미지 정보 출력
        if prompt_id in history_data:
            prompt_info = history_data[prompt_id]
            print("프롬프트 정보:", prompt_info)
            if "outputs" in prompt_info:
                print("이미지 출력 정보:")
                for node_id, output in prompt_info["outputs"].items():
                    if "images" in output:
                        print(f"노드 {node_id}의 이미지들:")
                        for img in output["images"]:
                            print(f"  - {img['filename']} (타입: {img['type']}, 폴더: {img['subfolder']})")
        
        return history_data
    except Exception as e:
        print(f"히스토리 호출 오류 상세: {str(e)}")
        raise HTTPException(status_code=500, detail=f"히스토리 호출 오류: {str(e)}")

@app.get('/api/status')
async def check_status():
    try:
        # ComfyUI 서버 연결 확인
        with urllib.request.urlopen(f"{COMFY_SERVER}/system_stats") as response:
            return {"status": "connected", "message": "ComfyUI 서버가 실행 중입니다."}
    except Exception as e:
        return {"status": "disconnected", "message": f"ComfyUI 서버에 연결할 수 없습니다: {str(e)}"}
    
if __name__ == "__main__":
    import uvicorn
    print("파이썬 FastAPI 서버 실행")
    uvicorn.run(app, host="0.0.0.0", port=8000)