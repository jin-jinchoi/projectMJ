<script lang="ts">
	import { onMount } from "svelte";
	import { UserRound, ArrowRight, ArrowLeft, Check } from "lucide-svelte";
	import { promptConfig } from "../config";

	const { promptOptions, defaultSelections } = promptConfig;

	// 선택 옵션 (값은 영어로 저장)
	let selectedGender = defaultSelections.selectedGender;
	let selectedAge = defaultSelections.selectedAge;
	let selectedTheme = defaultSelections.selectedTheme;
	let selectedClass = defaultSelections.selectedClass;

	// 외형
	let selectedBodyType = defaultSelections.selectedBodyType;
	let selectedClothing = defaultSelections.selectedClothing;
	let selectedHairColor = defaultSelections.selectedHairColor;
	let selectedHairLength = defaultSelections.selectedHairLength;
	let selectedHairCurl = defaultSelections.selectedHairCurl;
	let selectedEyeColor = defaultSelections.selectedEyeColor;
	let selectedEyeSize = defaultSelections.selectedEyeSize;

	// 배경
	let selectedFamily = defaultSelections.selectedFamily;
	let selectedFamilyHistory = defaultSelections.selectedFamilyHistory;
	let selectedRegion = defaultSelections.selectedRegion;
	let selectedPersonality = defaultSelections.selectedPersonality;

	// 생성 관련
	let isLoading = false;
	let generatedImage: string | null = null;
	let errorMessage: string | null = null;
	let currentStep = 0;

	const steps = [
		{ name: "기본 정보" },
		{ name: "외형" },
		{ name: "배경" },
		{ name: "확인" },
	];

	interface Option {
		value: string;
		label: string;
	}

	const getOptionLabel = (optionArray: Option[], value: string): string => {
		const option = optionArray.find((opt) => opt.value === value);
		return option ? option.label : String(value); // Ensure return type is string
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

	const generatePrompt = (): string => {
		return `(masterpiece, best quality, high detail, anime, grey background, from head to toe), 
		a ${selectedAge} ${selectedBodyType} ${selectedGender} character in ${selectedTheme} setting, 
		wearing a ${selectedClothing}, with ${selectedHairColor} ${selectedHairLength} hair (${selectedHairCurl}), 
		${selectedEyeColor} eyes, ${selectedEyeSize} eyes, detailed facial features, ultra HD`;
	};

	async function generateImage() {
		isLoading = true;
		generatedImage = null;
		errorMessage = null;

		try {
			const payload = {
				prompt: generatePrompt(),
				negative_prompt:
					"((bad hands:1)), ((extra fingers:1)), ((deformed hands:1)), ((unhealthy hands:1)), ((excess limbs:1.1)),((lowres)),((worst quality)), ((bad quality)), ((low quality)), naked, nsfw",
				num_inference_steps: 20,
				width: 512,
				height: 768,
				guidance_scale: 7,
			};

			console.log("이미지 생성 프롬프트:", payload);

			const response = await fetch("http://127.0.0.1:7861/sdapi/v1/txt2img", {
				method: "POST",
				headers: {
					"Content-Type": "application/json",
				},
				body: JSON.stringify(payload),
			});

			if (!response.ok) {
				throw new Error(
					`API 요청 실패: ${response.status} ${response.statusText}`,
				);
			}

			const data = await response.json();

			if (data.images && data.images.length > 0) {
				console.log("이미지 생성 완료");
				// base64 이미지를 표시
				generatedImage = `data:image/png;base64,${data.images[0]}`;
			} else {
				throw new Error("이미지가 생성되지 않았습니다.");
			}
		} catch (error) {
			console.error("이미지 생성 중 오류:", error);
			errorMessage =
				error instanceof Error
					? error.message
					: "알 수 없는 오류가 발생했습니다.";
		} finally {
			isLoading = false;
		}
	}
</script>

<h2 class="mb-4 text-3xl font-semibold text-gray-600">Diffusers</h2>
<div class="grid w-full grid-cols-2 gap-8 p-4">
	<!-- 왼쪽 컬럼: 단계별 입력 폼 -->
	<div class="p-6 bg-white shadow-lg rounded-xl">
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

				<!-- 직업 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">직업</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.classOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedClass ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedClass = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>
			{:else if currentStep === 1}
				<!-- 체형 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">체형</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.bodyTypeOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedBodyType ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedBodyType = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 의상 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">의상</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.clothingOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedClothing ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedClothing = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">머리색</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.hairColorOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedHairColor ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedHairColor = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<div class="flex justify-between">
					<div class="mb-6">
						<h3 class="mb-3 text-lg font-semibold text-gray-700">머리길이</h3>
						<div class="flex flex-wrap gap-2">
							{#each promptOptions.hairLengthOptions as option}
								<button
									class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedHairLength ===
									option.value
										? 'bg-blue-500 text-white border-blue-500'
										: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
									on:click={() => (selectedHairLength = option.value)}
								>
									{option.label}
								</button>
							{/each}
						</div>
					</div>
					<div class="mb-6">
						<h3 class="mb-3 text-lg font-semibold text-gray-700">머릿결</h3>
						<div class="flex flex-wrap gap-2">
							{#each promptOptions.hairCurlOptions as option}
								<button
									class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedHairCurl ===
									option.value
										? 'bg-blue-500 text-white border-blue-500'
										: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
									on:click={() => (selectedHairCurl = option.value)}
								>
									{option.label}
								</button>
							{/each}
						</div>
					</div>
				</div>

				<div class="flex justify-between">
					<div class="mb-6">
						<h3 class="mb-3 text-lg font-semibold text-gray-700">눈동자 색</h3>
						<div class="flex flex-wrap gap-2">
							{#each promptOptions.eyeColorOptions as option}
								<button
									class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedEyeColor ===
									option.value
										? 'bg-blue-500 text-white border-blue-500'
										: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
									on:click={() => (selectedEyeColor = option.value)}
								>
									{option.label}
								</button>
							{/each}
						</div>
					</div>
					<div class="mb-6">
						<h3 class="mb-3 text-lg font-semibold text-gray-700">눈 크기</h3>
						<div class="flex flex-wrap gap-2">
							{#each promptOptions.eyeSizeOptions as option}
								<button
									class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedEyeSize ===
									option.value
										? 'bg-blue-500 text-white border-blue-500'
										: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
									on:click={() => (selectedEyeSize = option.value)}
								>
									{option.label}
								</button>
							{/each}
						</div>
					</div>
				</div>
			{:else if currentStep === 2}
				<!-- 가족 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">가족</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.familyOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedFamily ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedFamily = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 가문의 역사 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">가문의 역사</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.familyHistoryOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedFamilyHistory ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedFamilyHistory = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 출신 지역 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">출신 지역</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.regionOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedRegion ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedRegion = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>

				<!-- 성격 유형 -->
				<div class="mb-6">
					<h3 class="mb-3 text-lg font-semibold text-gray-700">성격 유형</h3>
					<div class="flex flex-wrap gap-2">
						{#each promptOptions.personalityOptions as option}
							<button
								class="px-4 py-2 rounded-lg text-sm border transition-colors duration-200 {selectedPersonality ===
								option.value
									? 'bg-blue-500 text-white border-blue-500'
									: 'bg-white text-gray-700 border-gray-300 hover:bg-gray-100'}"
								on:click={() => (selectedPersonality = option.value)}
							>
								{option.label}
							</button>
						{/each}
					</div>
				</div>
			{:else if currentStep === 3}
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
							<span class="text-sm text-gray-500">직업</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.classOptions,
									selectedClass,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">체형</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.bodyTypeOptions,
									selectedBodyType,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">의상</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.clothingOptions,
									selectedClothing,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">머리색</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.hairColorOptions,
									selectedHairColor,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">머리길이</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.hairLengthOptions,
									selectedHairLength,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">머릿결</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.hairCurlOptions,
									selectedHairCurl,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">눈동자색</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.eyeColorOptions,
									selectedEyeColor,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">눈크기</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.eyeSizeOptions,
									selectedEyeSize,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">가족</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.familyOptions,
									selectedFamily,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">가문의 역사</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.familyHistoryOptions,
									selectedFamilyHistory,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">출신 지역</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.regionOptions,
									selectedRegion,
								)}</span
							>
						</div>

						<div class="flex flex-col">
							<span class="text-sm text-gray-500">성격 유형</span>
							<span class="font-medium"
								>{getOptionLabel(
									promptOptions.personalityOptions,
									selectedPersonality,
								)}</span
							>
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
			<!-- <h2 class="mb-2 text-xl font-bold text-gray-800">캐릭터 결과</h2> -->

			<div class="flex flex-col items-center justify-center w-full h-full">
				{#if isLoading}
					<div class="text-center">
						<p class="mb-3 text-gray-700">캐릭터를 생성하는 중입니다...</p>
						<div
							class="inline-block w-12 h-12 mt-2 border-4 border-blue-200 rounded-full border-l-blue-600 animate-spin"
						></div>
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
					</div>
				{:else if generatedImage}
					<div class="text-center">
						<img
							src={generatedImage}
							alt="생성된 캐릭터"
							class="object-contain rounded-lg shadow-lg max-w-full max-h-[500px]"
						/>
						<div class="mt-4">
							<a
								href={generatedImage}
								download="generated-character.png"
								class="inline-flex items-center px-6 py-3 font-medium text-white transition duration-200 bg-green-600 rounded-lg hover:bg-green-700"
							>
								저장하기
							</a>
						</div>
					</div>
				{/if}
			</div>
		</div>
	</div>
</div>
