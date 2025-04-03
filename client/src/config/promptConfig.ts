export interface OptionItem {
	label: string;
	value: string;
}

export interface PromptOptions {
	genderOptions: OptionItem[];
	themeOptions: OptionItem[];
	familyOptions: OptionItem[];
	familyHistoryOptions: OptionItem[];
	regionOptions: OptionItem[];
	ageOptions: OptionItem[];
	bodyTypeOptions: OptionItem[];
	clothingOptions: OptionItem[];
	classOptions: OptionItem[];
	//
	personalityOptions: OptionItem[];
	//
	hairColorOptions: OptionItem[];
	hairCurlOptions: OptionItem[];
	hairLengthOptions: OptionItem[];
	//
	eyeColorOptions: OptionItem[];
	eyeSizeOptions: OptionItem[];
}

export const promptOptions: PromptOptions = {
	genderOptions: [
		{ label: "남성", value: "male" },
		{ label: "여성", value: "female" },
		{ label: "중성적인", value: "androgynous" },
	],

	themeOptions: [
		{ label: "중세 판타지", value: "medieval fantasy" },
		{ label: "사이버펑크", value: "cyberpunk" },
		{ label: "스팀펑크", value: "steampunk" },
		{ label: "신화", value: "mythological" },
		{ label: "현대 밀리터리", value: "modern military" },
		{ label: "하이틴 스타일", value: "high school " },
	],

	familyOptions: [
		{ label: "있음", value: "has family" },
		{ label: "없음", value: "no family" },
	],

	familyHistoryOptions: [
		{ label: "신생가문", value: "new family" },
		{ label: "유망가문", value: "promising family" },
		{ label: "명문가문", value: "noble family" },
		{ label: "전설적인 가문", value: "legendary family" },
	],

	regionOptions: [
		{ label: "도시", value: "urban" },
		{ label: "시골", value: "rural" },
	],

	ageOptions: [
		{ label: "청년 (20~40)", value: "young" },
		{ label: "중년 (40~60)", value: "middle-aged" },
		{ label: "노년 (60~100)", value: "old" },
	],

	bodyTypeOptions: [
		{ label: "날씬형", value: "slim" },
		{ label: "비만형", value: "chubby" },
		{ label: "근육형", value: "muscular" },
		{ label: "왜소형", value: "petite" },
	],

	clothingOptions: [
		{ label: "캐주얼 복장", value: "casual wear" },
		{ label: "왕족 갑옷", value: "royal armor" },
		{ label: "닌자 복장", value: "ninja outfit" },
		{ label: "정장", value: "business suit" },
		{ label: "아이돌 무대 의상", value: "idol stage outfit " },
		{ label: "고딕 드레스", value: "gothic dress" },
	],

	classOptions: [
		{ label: "전사", value: "warrior" },
		{ label: "기사", value: "knight" },
		{ label: "도적", value: "thief" },
		{ label: "궁수", value: "archer" },
		{ label: "마법사", value: "wizard" },
	],

	personalityOptions: [
		{ label: "외향적", value: "extroverted" },
		{ label: "내향적", value: "introverted" },
		{ label: "감성적", value: "emotional" },
		{ label: "이성적", value: "rational" },
	],

	hairColorOptions: [
		{ label: "검정", value: "black" },
		{ label: "갈색", value: "brown" },
		{ label: "금발", value: "blonde" },
		{ label: "빨간색", value: "red" },
		{ label: "하얀색", value: "white" },
		{ label: "은색", value: "silver" },
		{ label: "분홍색", value: "pink" },
		{ label: "파란색", value: "blue" },
		{ label: "초록색", value: "green" },
		{ label: "보라색", value: "purple" },
	],

	hairLengthOptions: [
		{ label: "짧은", value: "short" },
		{ label: "중간", value: "medium" },
		{ label: "긴", value: "long" },
	],

	hairCurlOptions: [
		{ label: "직모", value: "straight" },
		{ label: "반곱슬", value: "wavy" },
		{ label: "곱슬", value: "curly" },
	],

	eyeColorOptions: [
		{ label: "검정", value: "black" },
		{ label: "갈색", value: "brown" },
		{ label: "파란색", value: "blue" },
		{ label: "초록색", value: "green" },
		{ label: "빨간색", value: "red" },
		{ label: "금색", value: "golden" },
		{ label: "은색", value: "silver" },
		{ label: "보라색", value: "purple" },
	],

	eyeSizeOptions: [
		{ label: "큰", value: "large" },
		{ label: "작은", value: "small" },
	],
};

export const defaultSelections = {
	selectedGender: "male",
	selectedTheme: "medieval fantasy",
	selectedFamily: "has family",
	selectedFamilyHistory: "new family",
	selectedRegion: "urban",
	selectedAge: "young",
	selectedBodyType: "slim",
	selectedClothing: "casual wear",
	selectedClass: "warrior",
	selectedPersonality: "extroverted",
	selectedHairColor: "black",
	selectedHairLength: "short",
	selectedHairCurl: "straight",
	selectedEyeColor: "black",
	selectedEyeSize: "large",
	randomPrompt: '',
};
