<script lang="ts">
	import { onMount, onDestroy } from "svelte";
	import {
		UserRound,
		ArrowRight,
		ArrowLeft,
		Check,
		Wifi,
		WifiOff,
	} from "lucide-svelte";
	import { promptConfig } from "../config";

	const { promptOptions, defaultSelections } = promptConfig;

	let selectedGender = defaultSelections.selectedGender;
	let selectedAge = defaultSelections.selectedAge;
	let selectedTheme = defaultSelections.selectedTheme;
	let randomPrompt = defaultSelections.randomPrompt;

	// 생성 관련
	let isLoading = false;
	let generatedImage: string | null = null;
	let errorMessage: string | null = null;
	let currentStep = 0;
	let seedValue: number | null = null;

	// 웹소켓 관련
	let socket: WebSocket | null = null;
	let isConnected = false;
	let connectionStatus = "연결 대기 중";
	let progressValue = 0;
	let currentNode = "";
	let currentPromptId: string | null = null;

	// 이미지 처리 중 표시할 진행 상태
	let processingStage = "";

	const steps = [{ name: "선택" }, { name: "입력" }, { name: "확인" }];

	interface Option {
		value: string;
		label: string;
	}

	const getOptionLabel = (optionArray: Option[], value: string): string => {
		const option = optionArray.find((opt) => opt.value === value);
		return option ? option.label : String(value);
	};

	const nextStep = () => {
		if (currentStep < steps.length - 1) {
			currentStep++;
		}
	};

	const prevStep = () => {
		if (currentStep > 0) {
			currentStep--;
		}
	};

	// 웹소켓 연결 설정
	onMount(() => {
		connectWebSocket();
	});

	// 컴포넌트 종료 시 웹소켓 연결 종료
	onDestroy(() => {
		if (socket) {
			socket.close();
		}
	});

	// 웹소켓 연결 함수
	function connectWebSocket() {
		// 연결 상태 초기화
		isConnected = false;
		connectionStatus = "연결 시도 중...";

		// 클라이언트 ID 생성
		const clientId = `svelte_${Date.now()}`;

		// 웹소켓 연결
		socket = new WebSocket(`ws://localhost:8000/ws/${clientId}`);

		// 연결 이벤트 핸들러
		socket.onopen = () => {
			console.log("웹소켓 연결됨");
			isConnected = true;
			connectionStatus = "연결";
		};

		// 메시지 이벤트 핸들러
		socket.onmessage = (event) => {
			// 바이너리 데이터 (이미지 미리보기)는 현재 사용하지 않음
			if (typeof event.data === "string") {
				// JSON 메시지 처리
				try {
					const message = JSON.parse(event.data);
					handleWebSocketMessage(message);
				} catch (error) {
					console.error("웹소켓 메시지 파싱 오류:", error);
				}
			}
		};

		// 연결 종료 이벤트 핸들러
		socket.onclose = (event) => {
			isConnected = false;
			connectionStatus = `종료: ${event.reason || "알 수 없는 이유"}`;
			console.log("웹소켓 연결 종료:", event);

			// 3초 후 재연결 시도
			setTimeout(connectWebSocket, 3000);
		};

		// 오류 이벤트 핸들러
		socket.onerror = (error) => {
			isConnected = false;
			connectionStatus = "오류";
			console.error("웹소켓 오류:", error);
		};
	}

	// 웹소켓 메시지 처리 함수
	function handleWebSocketMessage(message: any) {
		console.log("웹소켓 메시지 수신:", message);

		switch (message.type) {
			case "connection_status":
				isConnected = message.status === "connected";
				connectionStatus = message.message;
				break;

			case "connection_error":
				isConnected = false;
				connectionStatus = message.message;
				errorMessage = message.message;
				break;

			case "prompt_queued":
				currentPromptId = message.prompt_id;
				processingStage = "프롬프트 큐에 추가됨";
				break;

			case "progress":
				// 진행 상황 업데이트
				currentNode = message.node || "";
				progressValue = message.progress || 0;

				// 노드 이름에 따라 진행 단계 표시
				if (currentNode.includes("Check")) {
					processingStage = "모델 로드 중...";
				} else if (currentNode.includes("CLIP")) {
					processingStage = "텍스트 분석 중...";
				} else if (
					currentNode.includes("KSampler") ||
					currentNode.includes("Sampler")
				) {
					processingStage = `이미지 생성 중... ${progressValue}%`;
				} else if (currentNode.includes("VAE")) {
					processingStage = "이미지 디코딩 중...";
				} else if (currentNode.includes("SaveImage")) {
					processingStage = "이미지 저장 중...";
				} else {
					processingStage = `${currentNode} 처리 중...`;
				}
				break;

			case "execution_complete":
				// 실행 완료 처리
				progressValue = 100;
				processingStage = "처리 완료, 결과를 불러오는 중...";
				break;

			case "result":
				// 최종 결과 처리
				seedValue = message.seed;

				if (message.images && message.images.length > 0) {
					const outputImages = message.images.filter(
						(img: any) => img.type === "output",
					);
					if (outputImages.length > 0) {
						// output 타입 이미지 사용
						const imageUrl = outputImages[0].url;
						generatedImage = `http://localhost:8000${imageUrl}`;
					} else {
						// output 타입이 없으면 첫 번째 이미지 사용
						const imageUrl = message.images[0].url;
						generatedImage = `http://localhost:8000${imageUrl}`;
					}
				}

				console.log("최종 이미지", generatedImage);

				// 로딩 상태 종료
				isLoading = false;
				processingStage = "";
				break;

			case "error":
				// 오류 처리
				errorMessage = message.message;
				isLoading = false;
				processingStage = "";
				break;
		}
	}

	// 서버 재연결 함수
	function reconnectServer() {
		if (socket) {
			socket.close();
		}
		connectWebSocket();
	}

	// 프롬프트 생성
	const generatePrompt = (): string => {
		return `(masterpiece, best quality, high detail, anime, gray background, background with nothing, 
		from head to toe, Standing straight ahead and looking at the viewer), 
		a ${selectedAge} ${selectedGender} character in ${selectedTheme} setting,`;
	};

	// 웹소켓을 통한 이미지 생성 요청
	function generateImageViaWebSocket() {
		if (!socket || socket.readyState !== WebSocket.OPEN) {
			errorMessage =
				"서버에 연결되어 있지 않습니다. 다시 연결을 시도해 주세요.";
			return;
		}

		// 로딩 상태 시작
		isLoading = true;
		generatedImage = null;
		errorMessage = null;
		progressValue = 0;
		currentNode = "";
		processingStage = "준비 중...";

		// 프롬프트 생성 + 랜덤
		let positivePrompt = generatePrompt();
		if (randomPrompt && randomPrompt.trim() !== "") {
			positivePrompt += ` ${randomPrompt.trim()}`;
		}

		// 메시지 데이터 준비
		const promptData = {
			type: "prompt",
			prompt_text: positivePrompt,
			workflow_name: "default",
			seed: null, // 랜덤 시드 사용
		};

		// 메시지 전송
		socket.send(JSON.stringify(promptData));
		console.log("웹소켓을 통해 프롬프트 전송:", promptData);
	}

	// 기존 HTTP API를 통한 이미지 생성 요청
	async function generateImage() {
		// 웹소켓이 연결된 경우 웹소켓을 통해 요청
		if (isConnected && socket && socket.readyState === WebSocket.OPEN) {
			generateImageViaWebSocket();
			return;
		}

		// 웹소켓 연결이 없는 경우 기존 방식으로 요청 진행
		isLoading = true;
		generatedImage = null;
		errorMessage = null;

		try {
			let positivePrompt = generatePrompt();

			if (randomPrompt && randomPrompt.trim() !== "") {
				positivePrompt += ` ${randomPrompt.trim()}`;
			}

			console.log("사용 프롬프트:", positivePrompt);

			const promptData = {
				prompt_text: positivePrompt,
				workflow_name: "default",
				client_id: `svelte_${Date.now()}`,
			};

			console.log(positivePrompt);
			console.log("이미지 생성 프롬프트 전송:", promptData);

			const response = await fetch("http://localhost:8000/api/generate-image", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(promptData),
			});

			if (!response.ok) {
				throw new Error(
					`API 요청 실패: ${response.status} ${response.statusText}`,
				);
			}

			const data = await response.json();
			console.log("API 응답:", data);

			const promptId = data.prompt_id;
			console.log("프롬프트ID:", promptId);

			fetchGeneratedImage(promptId);
		} catch (error) {
			console.error("이미지 생성 중 오류:", error);
			errorMessage =
				error instanceof Error
					? error.message
					: "알 수 없는 오류가 발생했습니다.";
			isLoading = false;
		}
	}

	// 기존 이미지 가져오기 함수 (웹소켓 연결이 실패했을 때 폴백용)
	async function fetchGeneratedImage(promptId: string) {
		try {
			console.log("히스토리 데이터 확인 시작, promptId:", promptId);

			const historyResponse = await fetch(
				`http://localhost:8000/api/history/${promptId}`,
				{ cache: "no-store" },
			);

			if (!historyResponse.ok) {
				throw new Error("히스토리 정보를 가져오는데 실패했습니다.");
			}

			const historyData = await historyResponse.json();
			console.log("히스토리 데이터:", historyData);

			// promptId로 시작하는 객체 내에서 정보를 찾습니다
			if (
				historyData &&
				historyData[promptId] &&
				historyData[promptId].outputs
			) {
				const outputs = historyData[promptId].outputs;

				// 출력 노드들을 검사합니다 (19가 SaveImage 노드입니다)
				for (const nodeId in outputs) {
					const nodeOutput = outputs[nodeId];
					if (nodeOutput && nodeOutput.images && nodeOutput.images.length > 0) {
						const image = nodeOutput.images[0];
						const imageName = image.filename;

						// 파일명을 포함하여 이미지 URL 생성
						const imageUrl = `http://localhost:8000/api/image?filename=${encodeURIComponent(imageName)}`;
						console.log("이미지 생성 완료:", imageUrl);

						generatedImage = imageUrl;

						// 시드 값 찾기 (RandomNoise 노드는 37번입니다)
						try {
							if (
								historyData[promptId].prompt &&
								historyData[promptId].prompt["37"]
							) {
								seedValue =
									historyData[promptId].prompt["37"].inputs.noise_seed;
								console.log("시드 값:", seedValue);
							}
						} catch (error) {
							console.error("시드 값 찾기 오류:", error);
						}

						// 로딩 상태 종료
						isLoading = false;
						return true;
					}
				}
			}

			// 이미지를 찾지 못한 경우 1초 후 다시 시도합니다 (최대 30초)
			console.warn("이미지를 찾지 못했습니다, 다시 시도합니다...");
			if (isLoading) {
				setTimeout(() => fetchGeneratedImage(promptId), 1000);
			}
			return false;
		} catch (error) {
			console.error("이미지 정보 가져오기 오류:", error);
			errorMessage =
				error instanceof Error
					? error.message
					: "이미지 정보를 가져오는데 실패했습니다.";
			isLoading = false;
			return false;
		}
	}
</script>

<h2 class="mb-4 text-3xl font-semibold text-gray-600">
	CompyUI 예시코드를 활용한 이미지 생성 (웹소켓 연동)
</h2>
<div class="grid w-full grid-cols-2 gap-8 p-4">
	<!-- 왼쪽 컬럼: 단계별 입력 폼 -->
	<div class="p-6 bg-white shadow-lg rounded-xl">
		<div class="flex items-center justify-end mb-2">
			<div
				class="flex items-center gap-2 px-3 py-1 text-sm rounded-full {isConnected
					? 'bg-green-100 text-green-700'
					: 'bg-red-100 text-red-700'}"
			>
				{#if isConnected}
					<Wifi size={16} />
				{:else}
					<WifiOff size={16} />
				{/if}
				<span>{connectionStatus}</span>
				{#if !isConnected}
					<button
						on:click={reconnectServer}
						class="px-2 py-0.5 ml-2 text-xs text-white bg-blue-500 rounded hover:bg-blue-600"
					>
						연결
					</button>
				{/if}
			</div>
		</div>
		<!-- 스텝 인디케이터 -->
		<div class="mb-6">
			<div class="flex justify-between mb-4">
				{#each steps as step, index}
					<div
						class="flex flex-col items-center"
						class:text-blue-600={currentStep >= index}
						class:text-gray-400={currentStep < index}
					>
						<button
							class="flex items-center justify-center w-10 h-10 mb-2 border-2 rounded-full"
							class:border-blue-600={currentStep >= index}
							class:bg-blue-600={currentStep > index}
							class:border-gray-300={currentStep < index}
							on:click={() => {
								currentStep = index;
							}}
						>
							{#if currentStep > index}
								<Check class="text-white" size={18} />
							{:else}
								<span>{index + 1}</span>
							{/if}
						</button>
						<span class="text-sm">{step.name}</span>
					</div>

					{#if index < steps.length - 1}
						<div class="flex-grow pt-5">
							<div class="h-0.5 bg-gray-300"></div>
						</div>
					{/if}
				{/each}
			</div>
		</div>

		<!-- 단계별 폼 내용 -->
		<div class="min-h-[400px]">
			{#if currentStep === 0}
				<!-- 성별 선택 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">성별</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.genderOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedGender ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedGender = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 나이 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">나이</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.ageOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedAge ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedAge = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 테마 및 세계관 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">
						테마 및 세계관
					</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.themeOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedTheme ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedTheme = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>
				<!-- 랜덤 -->
			{:else if currentStep === 1}
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">
						사용자 지정 프롬프트
					</h3>
					<div class="flex flex-wrap gap-2">
						<textarea
							value={randomPrompt}
							on:input={(e: Event) => {
								randomPrompt = (e.target as HTMLTextAreaElement).value;
							}}
							name="randomPrompt"
							id="randomPrompt"
							class="w-full px-4 py-2 text-sm text-gray-700 transition-colors duration-200 bg-white border border-gray-300 rounded-lg resize-none hover:bg-gray-100"
						></textarea>
					</div>
				</div>
			{:else if currentStep === 2}
				<div class="p-4 space-y-4 rounded-lg bg-gray-50">
					<!-- 모든 선택 항목 요약 표시 -->
					<div class="grid grid-cols-2 gap-4">
						<div class="flex flex-col">
							<span class="text-sm text-gray-500">성별</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.genderOptions,
									selectedGender,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">나이</span>
							<span class="font-medium"
								>{getOptionLabel(promptOptions.ageOptions, selectedAge)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">테마 및 세계관</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.themeOptions,
									selectedTheme,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">사용자 입력 프롬프트</span>
							<span class="font-medium">{randomPrompt}</span>
						</div>
					</div>
				</div>
			{/if}
		</div>

		<!-- 단계 버튼 -->
		<div class="flex justify-between pt-6 mt-6 border-t border-gray-200">
			<button
				on:click={prevStep}
				class="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-opacity-50 {currentStep ===
				0
					? 'opacity-0'
					: 'opacity-100'}"
				disabled={currentStep === 0}
			>
				<ArrowLeft size={16} class="mr-1" />
				이전
			</button>

			{#if currentStep === steps.length - 1}
				<button
					on:click={generateImage}
					disabled={isLoading}
					class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed"
				>
					{isLoading ? "캐릭터 생성 중..." : "캐릭터 생성하기"}
				</button>
			{:else}
				<button
					on:click={nextStep}
					class="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-50"
				>
					다음
					<ArrowRight size={16} class="ml-1" />
				</button>
			{/if}
		</div>
	</div>

	<div class="flex flex-col w-full gap-6">
		<div class="w-full p-4 text-center bg-white shadow-lg rounded-xl">
			<div class="flex flex-col items-center justify-center w-full h-full">
				{#if isLoading}
					<div class="w-full text-center">
						<p class="mb-3 text-gray-700">
							{processingStage || "캐릭터를 생성하는 중입니다..."}
						</p>

						<!-- 진행 표시줄 -->
						{#if progressValue > 0}
							<div class="w-full bg-gray-200 rounded-full h-2.5 mb-4">
								<div
									class="bg-blue-600 h-2.5 rounded-full"
									style="width: {progressValue}%"
								></div>
							</div>
						{:else}
							<div
								class="w-full h-2 mb-4 overflow-hidden bg-gray-200 rounded-full"
							>
								<div
									class="h-full bg-blue-500 rounded-full animate-progress"
								></div>
							</div>
						{/if}

						<!-- 현재 작업 노드 표시 -->
						{#if currentNode}
							<p class="text-xs text-gray-500">현재 처리 중: {currentNode}</p>
						{/if}
					</div>
				{:else if !generatedImage && !errorMessage}
					<div
						class="flex items-center justify-center w-full max-w-md bg-gray-100 rounded-lg aspect-square"
					>
						<div class="flex flex-col items-center text-gray-400">
							<UserRound size={100} />
						</div>
					</div>
				{:else if errorMessage}
					<div class="w-full p-4 text-red-700 rounded-lg bg-red-50">
						<p>오류 발생: {errorMessage}</p>
						{#if !isConnected}
							<button
								on:click={reconnectServer}
								class="px-4 py-2 mt-3 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
							>
								서버 연결 시도
							</button>
						{/if}
					</div>
				{:else if generatedImage}
					<div class="text-center">
						<img
							src={generatedImage}
							alt="생성된 캐릭터"
							class="object-contain rounded-lg shadow-lg max-w-full max-h-[500px]"
						/>
						{#if seedValue}
							<p class="mt-2 text-gray-700">시드: {seedValue}</p>
						{/if}
						<div class="mt-4">
							<button
								on:click={generateImage}
								disabled={isLoading}
								class="inline-flex items-center px-6 py-3 ml-2 font-medium text-white transition duration-200 bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
							>
								다시 생성
							</button>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>

<style>
	/* 프로그레스 바 애니메이션 */
	@keyframes progress {
		0% {
			width: 0%;
			margin-left: 0%;
		}
		50% {
			width: 30%;
			margin-left: 70%;
		}
		100% {
			width: 0%;
			margin-left: 100%;
		}
	}

	.animate-progress {
		animation: progress 1.5s ease-in-out infinite;
	}
</style>
