from fastapi import FastAPI, HTTPException, Response, WebSocket, WebSocketDisconnect
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

import websocket as ws_client
from websockets.exceptions import ConnectionClosed


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

COMFY_SERVER = "http://192.168.1.133:8188"
COMFY_WS = "ws://192.168.1.133:8188/ws"

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.comfy_connections: Dict[str, ws_client.WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket

        # 웹소켓 연결
        try: 
            comfy_ws = ws_client.create_connection(f"{COMFY_WS}?clientId={client_id}")
            self.comfy_connections[client_id] = comfy_ws
            return True
        except Exception as e:
            print("CompyUI 웹 소켓 연결 오류:", {str(e)})
            return False

    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        
        if client_id in self.comfy_connections:
            try:
                self.comfy_connections[client_id].close()
            except:
                pass
            del self.comfy_connections[client_id]

    async def send_message(self, client_id: str, message: str):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                print(f"메시지 전송 오류: {str(e)}")
                self.disconnect(client_id)
    
    async def send_bytes(self, client_id: str, data: bytes):
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_bytes(data)
            except Exception as e:
                print(f"바이너리 데이터 전송 오류: {str(e)}")
                self.disconnect(client_id)
    
    def get_comfy_ws(self, client_id: str):
        return self.comfy_connections.get(client_id)

manager = ConnectionManager()

class PromptRequest(BaseModel):              
    # prompt: Dict[str, Any]
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

# 이미지 미리보기 - 중복 엔드포인트 제거하고 여러 폴더 타입 시도하는 로직으로 통합
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
    

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # 클라이언트 연결 설정
    connection_success = await manager.connect(websocket, client_id)
    
    if not connection_success:
        await websocket.send_text(json.dumps({
            "type": "connection_error",
            "message": "ComfyUI 서버에 연결할 수 없습니다."
        }))
        await websocket.close(1011, "ComfyUI 서버 연결 실패")
        return
    
    # 연결 성공 메시지 전송
    await manager.send_message(client_id, json.dumps({
        "type": "connection_status",
        "status": "connected",
        "message": "ComfyUI 서버에 연결되었습니다."
    }))
    
    # try:
    #     # 클라이언트 메시지 처리
    #     while True:
    #         # 클라이언트로부터 메시지 수신
    #         data = await websocket.receive_text()
    #         request_data = json.loads(data)
            
    #         # 메시지 유형에 따라 처리
    #         if request_data.get("type") == "prompt":
    #             # 워크플로우 로드
    #             workflow = load_workflow(request_data.get("workflow_name", "default"))
                
    #             # 프롬프트 텍스트 적용
    #             workflow["4"]["inputs"]["text"] = request_data.get("prompt_text", "")
                
    #             # 시드 설정
    #             seed = request_data.get("seed")
    #             if seed is not None:
    #                 workflow["11"]["inputs"]["seed"] = seed
    #             else:
    #                 # 랜덤 시드 생성
    #                 workflow["11"]["inputs"]["seed"] = random.randint(1, 9999999999)
                
    #             # ComfyUI에 요청 보내기
    #             result = queue_prompt(workflow, client_id)
    #             prompt_id = result["prompt_id"]
                
    #             # 프롬프트 ID 전송
    #             await manager.send_message(client_id, json.dumps({
    #                 "type": "prompt_queued",
    #                 "prompt_id": prompt_id
    #             }))
                
    #             # ComfyUI 웹소켓에서 상태 모니터링
    #             asyncio.create_task(monitor_prompt_progress(client_id, prompt_id))
                
    # except WebSocketDisconnect:
    #     # 연결 해제
    #     manager.disconnect(client_id)
    # except Exception as e:
    #     # 오류 처리
    #     print(f"웹소켓 오류: {str(e)}")
    #     try:
    #         await manager.send_message(client_id, json.dumps({
    #             "type": "error",
    #             "message": str(e)
    #         }))
    #     except:
    #         pass
    #     manager.disconnect(client_id)

async def monitor_prompt_progress(client_id: str, prompt_id: str):
    comfy_ws = manager.get_comfy_ws(client_id)
    if not comfy_ws:
        return
    
    try:
        # 초기 진행률 설정
        progress = 0
        current_node = ""
        
        # ComfyUI 웹소켓 메시지 수신
        while True:
            try:
                out = comfy_ws.recv()
                
                if isinstance(out, str):
                    message = json.loads(out)
                    
                    # 실행 상태 메시지 처리
                    if message['type'] == 'executing':
                        data = message['data']
                        
                        # 현재 프롬프트 ID 확인
                        if data['prompt_id'] == prompt_id:
                            # 현재 노드 정보 업데이트
                            if data['node'] is not None:
                                current_node = data['node']
                                # 노드 실행 정보 추가 확인
                                node_info = {}
                                if "exec_info" in data and data["exec_info"]:
                                    node_info = data["exec_info"]
                                    # KSampler 노드일 경우 진행률 계산
                                    if "KSampler" in current_node and "step" in node_info and "steps" in node_info:
                                        progress = int((node_info["step"] / node_info["steps"]) * 100)
                                
                                # 진행 상황 클라이언트에 전송
                                await manager.send_message(client_id, json.dumps({
                                    "type": "progress",
                                    "prompt_id": prompt_id,
                                    "node": current_node,
                                    "progress": progress,
                                    "node_info": node_info
                                }))
                            else:
                                # 실행 완료
                                await manager.send_message(client_id, json.dumps({
                                    "type": "execution_complete",
                                    "prompt_id": prompt_id
                                }))
                                
                                # 이미지 결과 조회 및 전송
                                try:
                                    history = fetch_history(prompt_id)
                                    
                                    # 이미지 URL 및 시드값 추출
                                    image_urls = []
                                    seed_value = None
                                    
                                    if prompt_id in history:
                                        prompt_history = history[prompt_id]
                                        
                                        # 시드값 찾기
                                        if "prompt" in prompt_history and "11" in prompt_history["prompt"]:
                                            seed_value = prompt_history["prompt"]["11"]["inputs"]["seed"]
                                        
                                        # 이미지 찾기 - 자세한 로깅 추가
                                        if "outputs" in prompt_history:
                                            print(f"이미지 출력 노드들: {list(prompt_history['outputs'].keys())}")
                                            
                                            for node_id, output in prompt_history["outputs"].items():
                                                print(f"노드 {node_id} 출력 검사 중...")
                                                
                                                if "images" in output:
                                                    print(f"노드 {node_id}에서 이미지 {len(output['images'])}개 발견:")
                                                    
                                                    for image in output["images"]:
                                                        print(f"  - 이미지: {image['filename']} (타입: {image['type']})")
                                                        image_urls.append({
                                                            "filename": image["filename"],
                                                            "subfolder": image["subfolder"],
                                                            "type": image["type"],
                                                            "url": f"/api/image?filename={image['filename']}&subfolder={image['subfolder']}&type={image['type']}"
                                                        })
                                                else:
                                                    print(f"노드 {node_id}에 이미지 출력 없음")
                                    
                                    # 결과 전송
                                    await manager.send_message(client_id, json.dumps({
                                        "type": "result",
                                        "prompt_id": prompt_id,
                                        "seed": seed_value,
                                        "images": image_urls
                                    }))
                                    
                                except Exception as e:
                                    print(f"결과 처리 오류: {str(e)}")
                                    await manager.send_message(client_id, json.dumps({
                                        "type": "error",
                                        "message": f"결과 처리 오류: {str(e)}"
                                    }))
                                
                                # 모니터링 종료
                                break
                else:
                    # 바이너리 데이터(미리보기 이미지) 처리
                    if current_node == 'save_image_websocket_node':
                        # 이미지 데이터를 클라이언트에 전송
                        await manager.send_bytes(client_id, out)
                        
                        # 이미지 미리보기 정보 전송
                        await manager.send_message(client_id, json.dumps({
                            "type": "preview",
                            "prompt_id": prompt_id,
                            "node": current_node
                        }))
            
            except ConnectionClosed:
                break
            except Exception as e:
                print(f"메시지 처리 오류: {str(e)}")
                # 오류 전송
                await manager.send_message(client_id, json.dumps({
                    "type": "error",
                    "message": f"메시지 처리 오류: {str(e)}"
                }))
                break
                
    except Exception as e:
        print(f"모니터링 오류: {str(e)}")
        await manager.send_message(client_id, json.dumps({
            "type": "error",
            "message": f"모니터링 오류: {str(e)}"
        }))


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