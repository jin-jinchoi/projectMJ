<script lang="ts">
	import { UserRound, ArrowRight, ArrowLeft, Check } from "lucide-svelte";
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

	// 프롬프트 생성
	const generatePrompt = (): string => {
		return `(masterpiece, best quality, high detail, anime, gray background, background with nothing, 
		from head to toe, Standing straight ahead and looking at the viewer), 
		a ${selectedAge} ${selectedGender} character in ${selectedTheme} setting,`;
	};

	// 기존 HTTP API를 통한 이미지 생성 요청
	async function generateImage() {
		// 웹소켓 연결이 없는 경우 기존 방식으로 요청 진행
		isLoading = true;
		generatedImage = null;
		errorMessage = null;

		try {
			let positivePrompt = generatePrompt();
			let seedNumber = null;

			if (randomPrompt && randomPrompt.trim() !== "") {
				positivePrompt += ` ${randomPrompt.trim()}`;
			}

			console.log("사용 프롬프트:", positivePrompt);

			const promptData = {
				prompt_text: positivePrompt,
				workflow_name: "0404test",
				client_id: `svelte_${Date.now()}`,
				seed: seedNumber,
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

				for (const nodeId in outputs) {
					const nodeOutput = outputs[nodeId];
					if (nodeOutput && nodeOutput.images && nodeOutput.images.length > 0) {
						const image = nodeOutput.images[0];
						const imageName = image.filename;

						// 파일명을 포함하여 이미지 URL 생성
						const imageUrl = `http://localhost:8000/api/image?filename=${encodeURIComponent(imageName)}`;
						console.log("이미지 생성 완료:", imageUrl);

						generatedImage = imageUrl;

						// seedValue = historyData[promptId].prompt["11"];
						// console.log(seedValue);

						try {
							if (
								historyData[promptId].prompt &&
								historyData[promptId].prompt["11"]
							) {
								seedValue = historyData[promptId].prompt["11"].inputs.seed;
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
		<div class="flex items-center justify-end mb-2"></div>
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
						<div class="w-full bg-gray-200 rounded-full h-2.5 mb-4">
							<div class="bg-blue-600 h-2.5 rounded-full"></div>
						</div>
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
						<!-- {#if !isConnected}
							<button
								on:click={reconnectServer}
								class="px-4 py-2 mt-3 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
							>
								서버 연결 시도
							</button>
						{/if} -->
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
