import zipfile
import os

files = {
    ".env": r"""GEMINI_API_KEY=여기에_실제_API_키를_입력하세요
""",
    ".gitignore": r"""node_modules/
.env
.vercel/
""",
    "package.json": r"""{
  "name": "prompt-hub",
  "version": "1.0.0",
  "description": "PromptHub AI Guide & Builder",
  "scripts": {
    "dev": "vercel dev"
  }
}""",
    "vercel.json": r"""{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/$1" },
    { "source": "/(.*)", "destination": "/public/$1" },
    { "source": "/", "destination": "/public/index.html" }
  ]
}""",
    "api/generate.js": r"""export default async function handler(req, res) {
    if (req.method !== 'POST') {
        return res.status(405).json({ error: 'Method not allowed' });
    }

    const { framework, formData } = req.body;
    const apiKey = process.env.GEMINI_API_KEY;

    if (!apiKey) {
        return res.status(500).json({ error: '서버에 API 키가 설정되지 않았습니다 (.env 파일 확인)' });
    }

    let rawPrompt = '';
    for (const [key, value] of Object.entries(formData)) {
        if (value.trim() !== '') rawPrompt += `**${key}**: ${value}\n\n`;
    }

    const systemInstruction = `당신은 프롬프트 엔지니어링 전문가입니다. 사용자가 제공한 구조화된 데이터(${framework} 프레임워크 기반)를 분석하여, AI가 최고의 성능을 낼 수 있는 완벽한 프롬프트로 재설계하세요. 
규칙:
1. 사용자의 원래 의도와 제약 조건을 임의로 누락하지 마세요.
2. 불확실한 부분을 채워주기 위해 필요한 경우에만 Few-shot 예시를 추가하세요.
3. 결과물은 반드시 Markdown 구조로 반환하며, 불필요한 부연 설명이나 인사말은 절대 하지 마세요.`;

    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                systemInstruction: { parts: [{ text: systemInstruction }] },
                contents: [{ parts: [{ text: rawPrompt + "\n\n이 내용을 바탕으로 즉시 복사해서 사용할 수 있는 최종 마크다운 프롬프트를 작성해줘." }] }]
            })
        });

        if (!response.ok) throw new Error(`API 오류: ${response.status}`);
        
        const data = await response.json();
        const optimizedText = data.candidates[0].content.parts[0].text;

        return res.status(200).json({ 
            rawPrompt: rawPrompt, 
            optimizedPrompt: optimizedText 
        });

    } catch (error) {
        return res.status(500).json({ error: error.message });
    }
}""",
    "public/index.html": r"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptHub - AI Prompt Guide & Builder</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
        body { font-family: 'Pretendard', sans-serif; background-color: #F7F6F2; color: #202722; }
        .highlight-var { background-color: #C8F169; padding: 0.1rem 0.3rem; border-radius: 0.25rem; font-weight: bold; }
        .tab-active { border-bottom: 2px solid #263B52; font-weight: bold; color: #263B52; }
        .tab-inactive { color: #68716B; }
        .tab-inactive:hover { color: #263B52; }
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #E5E4DC; border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: #68716B; }
    </style>
</head>
<body class="min-h-screen flex flex-col">
    <nav class="bg-white border-b border-[#E5E4DC] sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between h-16">
            <div class="flex items-center">
                <i class="fa-solid fa-layer-group text-[#263B52] text-2xl mr-3"></i>
                <span class="font-bold text-xl text-[#263B52]">PromptHub</span>
            </div>
            <div class="flex items-center space-x-2 md:space-x-6">
                <button onclick="switchTab('guide')" id="tab-guide" class="tab-active px-2 py-4 text-sm focus:outline-none">가이드 (Library)</button>
                <button onclick="switchTab('builder')" id="tab-builder" class="tab-inactive px-2 py-4 text-sm focus:outline-none">생성기 (Builder)</button>
                <div class="relative group">
                    <button class="text-[#68716B] hover:text-[#263B52] text-sm font-bold border border-[#E5E4DC] px-3 py-1.5 rounded-lg"><i class="fa-solid fa-database mr-2"></i>데이터 관리</button>
                    <div class="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg hidden group-hover:block z-50">
                        <button onclick="exportJSON()" class="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 border-b"><i class="fa-solid fa-download mr-2"></i>백업 (내보내기)</button>
                        <label class="block w-full text-left px-4 py-2 text-sm hover:bg-gray-50 cursor-pointer">
                            <i class="fa-solid fa-upload mr-2"></i>복구 (가져오기)
                            <input type="file" id="importFile" accept=".json" class="hidden" onchange="importJSON(event)">
                        </label>
                    </div>
                </div>
            </div>
        </div>
    </nav>

    <main class="flex-grow max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full">
        <!-- 가이드 탭 -->
        <div id="view-guide" class="block">
            <div class="mb-6 flex flex-col md:flex-row justify-between items-center gap-4">
                <h1 class="text-2xl font-bold text-[#202722]">프롬프트 탐색</h1>
                <input type="text" id="searchInput" onkeyup="filterPrompts()" placeholder="검색어 입력..." class="w-full md:w-80 px-4 py-2 border border-[#E5E4DC] rounded-lg text-sm focus:outline-none focus:border-[#263B52]">
            </div>
            
            <div class="bg-white p-4 rounded-xl border border-[#E5E4DC] shadow-sm mb-8 space-y-3">
                <div class="flex flex-wrap items-center gap-2">
                    <span class="text-sm font-bold text-gray-500 w-16">분야</span>
                    <button onclick="setDomain('all')" id="dom-all" class="filter-btn-dom px-3 py-1 bg-[#263B52] text-white rounded-full text-sm font-medium">전체</button>
                    <button onclick="setDomain('trade')" id="dom-trade" class="filter-btn-dom px-3 py-1 bg-white border border-[#E5E4DC] text-[#68716B] rounded-full text-sm font-medium">무역 업무</button>
                    <button onclick="setDomain('coding')" id="dom-coding" class="filter-btn-dom px-3 py-1 bg-white border border-[#E5E4DC] text-[#68716B] rounded-full text-sm font-medium">바이브 코딩</button>
                    <button onclick="setDomain('general')" id="dom-general" class="filter-btn-dom px-3 py-1 bg-white border border-[#E5E4DC] text-[#68716B] rounded-full text-sm font-medium">일반/기획</button>
                    <div class="w-px h-4 bg-[#E5E4DC] mx-2"></div>
                    <button onclick="toggleFavFilter()" id="fav-filter" class="px-3 py-1 bg-white border border-[#E5E4DC] text-[#68716B] rounded-full text-sm font-medium"><i class="fa-solid fa-star mr-1"></i>즐겨찾기</button>
                </div>
            </div>
            <div id="emptyState" class="hidden text-center py-12 text-gray-500">조건에 맞는 프롬프트가 없습니다.</div>
            <div id="promptGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"></div>
        </div>

        <!-- 빌더 탭 -->
        <div id="view-builder" class="hidden">
            <h1 class="text-2xl font-bold mb-6">동적 프롬프트 빌더</h1>
            <div class="flex flex-col lg:flex-row gap-8">
                <div class="w-full lg:w-5/12 bg-white p-6 rounded-xl border border-[#E5E4DC] shadow-sm flex flex-col">
                    <h2 class="text-lg font-bold mb-4 border-b pb-2"><i class="fa-solid fa-sliders mr-2"></i>프레임워크 선택</h2>
                    <select id="frameworkSelect" onchange="renderDynamicForm()" class="w-full p-2 mb-6 border border-[#E5E4DC] rounded-lg bg-gray-50 focus:border-[#263B52] font-bold">
                        <option value="RTCC">RTCC (Role-Task-Context-Constraints)</option>
                        <option value="COSTAR">CO-STAR (비즈니스 제안/마케팅)</option>
                        <option value="RISEN">R-I-S-E-N (코딩/명확한 작업 지시)</option>
                        <option value="FREE">자유 입력 (초안 개선형)</option>
                    </select>
                    <div id="dynamicFormContainer" class="space-y-4 flex-grow overflow-y-auto"></div>
                    <button onclick="generatePromptWithAPI()" class="w-full mt-6 bg-[#263B52] text-white py-3 rounded-lg font-bold hover:bg-opacity-90 transition">
                        <i class="fa-solid fa-wand-magic-sparkles mr-2"></i>Gemini AI로 최적화
                    </button>
                </div>

                <div class="w-full lg:w-7/12 flex flex-col gap-4">
                    <div class="bg-white p-6 rounded-xl border border-[#E5E4DC] shadow-sm flex-grow flex flex-col">
                        <div class="flex justify-between items-end mb-4 border-b pb-2">
                            <div class="flex space-x-4">
                                <button onclick="switchResultTab('ai')" id="res-tab-ai" class="font-bold text-[#263B52] border-b-2 border-[#263B52] pb-1">AI 최적화 프롬프트</button>
                                <button onclick="switchResultTab('raw')" id="res-tab-raw" class="text-gray-400 hover:text-[#263B52] pb-1">내 입력 원본</button>
                            </div>
                            <button onclick="copyBuilderResult()" class="text-sm bg-[#C8F169] text-[#202722] px-3 py-1 rounded font-bold hover:bg-[#b8e058]">복사</button>
                        </div>
                        <div id="builderResultContainer" class="relative flex-grow">
                            <textarea id="builderResultAI" class="w-full h-full min-h-[400px] p-4 bg-gray-50 rounded-lg font-mono text-sm text-gray-800 border border-gray-200 resize-none" readonly>좌측 폼을 작성하고 생성 버튼을 누르면, AI가 분석한 결과가 나옵니다.</textarea>
                            <textarea id="builderResultRaw" class="w-full h-full min-h-[400px] p-4 bg-gray-50 rounded-lg font-mono text-sm text-gray-500 border border-gray-200 resize-none hidden" readonly></textarea>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- 모달 -->
    <div id="varModal" class="fixed inset-0 bg-black bg-opacity-50 hidden flex items-center justify-center z-50">
        <div class="bg-white rounded-xl max-w-2xl w-full mx-4 max-h-[90vh] flex flex-col shadow-2xl">
            <div class="p-5 border-b border-[#E5E4DC] flex justify-between items-center bg-gray-50 rounded-t-xl">
                <h3 class="font-bold text-lg" id="modalTitle"><i class="fa-solid fa-pen-to-square mr-2"></i>프롬프트 변수 입력</h3>
                <button onclick="closeModal()" class="text-gray-400 hover:text-black"><i class="fa-solid fa-xmark text-xl"></i></button>
            </div>
            <div class="p-6 overflow-y-auto flex-grow flex flex-col md:flex-row gap-6">
                <div class="w-full md:w-1/3 border-b md:border-b-0 md:border-r border-[#E5E4DC] pb-4 md:pb-0 md:pr-4" id="modalVars"></div>
                <div class="w-full md:w-2/3 flex flex-col">
                    <div class="flex justify-between items-center mb-2"><span class="font-bold text-sm text-[#68716B]">실시간 미리보기</span></div>
                    <div id="modalPreview" class="bg-gray-50 p-4 rounded-lg font-mono text-sm text-gray-700 whitespace-pre-wrap h-64 overflow-y-auto border border-gray-200"></div>
                </div>
            </div>
            <div class="p-4 border-t border-[#E5E4DC] bg-gray-50 flex justify-end gap-3 rounded-b-xl">
                <button onclick="closeModal()" class="px-4 py-2 text-sm border bg-white rounded-lg">취소</button>
                <button onclick="copyModalContent()" class="px-5 py-2 text-sm bg-[#263B52] text-white rounded-lg"><i class="fa-solid fa-copy mr-2"></i>복사</button>
            </div>
        </div>
    </div>
    <div id="toast" class="fixed bottom-6 left-1/2 transform -translate-x-1/2 bg-[#263B52] text-white px-6 py-3 rounded-full shadow-lg transition-opacity duration-300 opacity-0 z-50"><span id="toastMsg">복사되었습니다!</span></div>

    <script src="/js/data.js"></script>
    <script src="/js/app.js"></script>
</body>
</html>""",
    "public/js/data.js": r"""const promptData = [
    { id: 1, domain: "trade", taskType: "research", title: "HS Code 설명 (서술형)", tags: ["#무역비즈니스", "#설명", "#초보자"], useCase: "초보자에게 복잡한 무역 개념을 설명할 때", description: "무역 전문가 입장에서 HS Code의 개념을 쉽게 설명합니다.", template: "당신은 10년 경력의 무역전문가입니다.\n중소 기업 수출 담당자가 {설명할개념}을 처음 배우는 상황입니다. 이 사람에게 개념과 중요성을 설명해주세요." },
    { id: 2, domain: "general", taskType: "dev", title: "웹 UI/UX 기획", tags: ["#기획", "#UIUX", "#웹개발"], useCase: "랜딩페이지나 신규 서비스 화면을 기획할 때", description: "15년 경력 디자이너 페르소나를 활용해 레이아웃과 전환율 전략을 제안합니다.", template: "당신은 15년 경력의 시니어 웹 UI/UX 디자이너입니다.\n\n[프로젝트]\n- 제작 목적: {제작목적}\n- 타깃: {주요타깃}\n- 핵심 섹션: {핵심섹션}\n\n[요청]\n1. 레이아웃 구조 제안\n2. 전환율 향상 UX 포인트\n3. 글로벌 벤치마킹 레퍼런스" },
    { id: 3, domain: "trade", taskType: "writing", title: "납기 지연 안내 (지침형)", tags: ["#메일", "#클레임대응"], useCase: "바이어에게 납기 지연을 정중히 알릴 때", description: "지침을 명시하여 깔끔한 이메일을 작성합니다.", template: "아래 규칙을 지켜서 바이어에게 보낼 납기 지연 안내 메일을 작성해주세요.\n\n1. 첫 문장에 사과를 넣을 것\n2. 지연 이유는 한 문장으로 ({지연이유})\n3. 새 납기일({새납기일})을 굵게 표시\n4. 영어로 작성하고 5문장 이내로" },
    { id: 4, domain: "coding", taskType: "dev", title: "개발 진행 규칙", tags: ["#바이브코딩", "#규칙"], useCase: "AI 개발자에게 체계적인 코드 뼈대를 요구할 때", description: "개발에 앞서 프레임워크 제안과 아키텍처를 먼저 확인받게 합니다.", template: "당신은 시니어 개발자입니다. 아래 [규칙]을 엄격히 준수하세요.\n\n[필수 규칙]\n1. 프레임워크 및 배포 환경 최적 제안 먼저 하기\n2. 코드 작성 전 구조(README) 초안 먼저 컨펌받기\n3. 코드 작성 시 주석 의무화\n\n[프로젝트 설명]\n{프로젝트설명}" },
    { id: 5, domain: "general", taskType: "writing", title: "위로 챗봇 소담 (함수형)", tags: ["#챗봇", "#페르소나", "#함수형"], useCase: "상황에 맞는 따뜻한 멘트가 필요할 때", description: "입력-처리-출력의 함수형 구조로 멘트를 생성합니다.", template: "당신은 위로 챗봇 소담입니다. 다음을 반영해 메시지를 쓰세요.\n\n입력: {주제} = {고민거리}\n{독자} = {이름}님\n{말투} = 공손, 유머, 상냥\n\n처리: 위로 메시지 작성\n출력: {\n\"호칭\": \"{이름}님\",\n\"메시지\": \"(300자 이상)\"\n}" },
    { id: 6, domain: "trade", taskType: "research", title: "무역 현직자 평가", tags: ["#평가", "#페르소나", "#현업검증"], useCase: "기획안의 실무 도입 가능성을 검증할 때", description: "15년차 실무자 관점에서 서류를 냉정하게 평가합니다.", template: "당신은 15년차 종합상사 해외영업팀장입니다. 제출된 기획안을 현장 관점에서 냉정하게 검증합니다.\n\n[검토 대상]\n{기획안내용}\n\n[기준]\n1. 실무 도입 가능성 2. 업무 효율성 3. 통관/클레임 리스크\n[출력]\n1. 총평 (Pass/Hold/Fail)\n2. 장점 및 리스크\n3. 현실적 수정안" },
    { id: 7, domain: "general", taskType: "research", title: "다중 페르소나 분석", tags: ["#전략", "#다중관점"], useCase: "신규 전략을 다양한 직군의 시선에서 검토할 때", description: "3가지 입장에서 찬반 의견을 분석합니다.", template: "다음 3명의 전문가 입장에서 우리 회사의 {분석대상}을 분석해주세요.\n- 김부장 (영업 15년, 현장 중심)\n- 이박사 (데이터 중심, 신중함)\n- 박대표 (스타트업, 속도 중시)\n\n각자의 관점에서 찬반 의견을 제시하세요." },
    { id: 8, domain: "trade", taskType: "research", title: "이용자 기반 수출 3단계", tags: ["#초보자", "#수출가이드"], useCase: "특정 이용자의 상황에 맞춘 가이드가 필요할 때", description: "이용자 정보를 입력해 눈높이에 맞는 가이드를 받습니다.", template: "#이용자 정보\n- 직책: {직책}\n- 관심사: {관심사}\n- 우려사항: {우려사항}\n\n#지시\n위 이용자에게 {목표작업} 3단계를 설명하세요. 전문 용어는 최소화하고 3줄 이내로 작성하세요." },
    { id: 9, domain: "trade", taskType: "research", title: "FTA 적용 분석 (통합형)", tags: ["#통합형", "#마크다운"], useCase: "수출 품목의 FTA 혜택을 빠르게 점검할 때", description: "역할, 작업, 제약을 모두 갖춘 통합 뼈대입니다.", template: "#역할: FTA 및 원산지 증명 전문가\n#작업: 수출품목의 FTA 적용 여부 분석\n#입력\n- 품목명: {품목명}\n- 수출국: {수출국} -> 수입국: {수입국}\n#제약\n> 불확실한 내용은 '세관 확인 필요'로 표기\n#출력형식\n```json\n{\"FTA_적용\": boolean, \"협정세율\":\"\", \"필요서류\":[]}\n```" },
    { id: 10, domain: "general", taskType: "research", title: "대안 분석 (기준 평가형)", tags: ["#대안제시", "#비교"], useCase: "여러 방법론이나 도구 중 최적의 선택을 할 때", description: "평가 기준과 비교 대상을 주고 표로 정리합니다.", template: "아래 방법을 다음 기준으로 비교하고 표로 정리하세요.\n\n평가기준:\n- 속도 (빠름/보통/느림)\n- 비용 (무료/저비용/고비용)\n- 확장성 (높음/보통/낮음)\n\n비교대상: {비교항목들_쉼표구분}\n용도: {사용용도}" },
    { id: 11, domain: "coding", taskType: "dev", title: "파이썬 코딩 레시피", tags: ["#레시피", "#가이드"], useCase: "초보자가 코딩 프로젝트를 시작할 때", description: "작업을 단계별 레시피로 분해하여 설명합니다.", template: "#목표: Python 초보자가 {목표프로그램} 만들기\n#상태: {현재상태}\n\n위 목표를 달성하기 위한 단계별 레시피를 쓰세요.\n##STEP{N}: {단계명}\n- 할일: {행동}\n- 완료 기준: {기준}\n- 주의 사항: {흔한실수}" },
    { id: 12, domain: "general", taskType: "writing", title: "역질문 방식 (제안서)", tags: ["#역질문", "#정보수집"], useCase: "AI가 필요한 정보를 먼저 묻게 만들고 싶을 때", description: "결과물을 바로 만들지 않고 질문을 유도합니다.", template: "제가 원하는 결과물은 {원하는결과물}입니다.\n바로 만들지 말고, 먼저 필요한 정보를 질문해주세요. 한 번에 하나의 질문만 하고 제가 답하면 다음 질문으로 넘어가세요. 충분히 모이면 결과물을 작성하세요." },
    { id: 13, domain: "coding", taskType: "improve", title: "인지 검증자 (디버깅)", tags: ["#검증", "#디버깅"], useCase: "코드 에러의 원인과 해결책을 단계별로 찾을 때", description: "바로 답하지 않고 원인 분석부터 수행합니다.", template: "웹페이지에서 아래 에러가 났어요. 바로 고치지 말고 다음 순서로 해주세요.\n1. 에러 뜻 쉬운 말로 한 줄\n2. 원인 후보 3가지\n3. 각 원인 확인 방법\n4. 가장 가능성 높은 원인의 수정 코드\n\n에러: {에러메시지}" },
    { id: 14, domain: "trade", taskType: "writing", title: "CO-STAR 제안서", tags: ["#CO-STAR", "#제안서"], useCase: "상황, 목적, 톤을 명확히 한 비즈니스 제안서", description: "CO-STAR 기법으로 영문 제안서를 작성합니다.", template: "Context: {타깃회사}가 {제품} 소싱을 고려 중입니다.\nObjective: 신규 공급사로 선정하도록 설득\nStyle: 전문적 비즈니스 문서\nTone: 자신감, 협력적\nAudience: 소싱 디렉터\nResponse: 영문 Proposal, {단어수} 단어 이내" },
    { id: 15, domain: "trade", taskType: "writing", title: "FOCUS 링크드인 발굴", tags: ["#FOCUS", "#마케팅"], useCase: "바이어에게 링크드인 첫 메시지를 보낼 때", description: "답장률을 높이기 위한 메시지를 3가지 버전으로 씁니다.", template: "Function: 글로벌 B2B 마케팅 전문가\nObjective: 바이어 답장률 제고\nContext: 우리 회사는 {제품강점}이 강점이며 {타깃국가}의 {타깃업체}를 타깃으로 함\nUtility: LinkedIn 메시지\nSpecifications: 150단어 영문, 3가지 버전(공식/친근/문제해결)" },
    { id: 16, domain: "trade", taskType: "research", title: "ROSES 가격 협상", tags: ["#ROSES", "#협상"], useCase: "바이어와의 가격 협상 전략을 미리 세울 때", description: "목표가와 현재가를 바탕으로 양보 시나리오를 짭니다.", template: "Role: 무역 협상 전문가\nObjective: {바이어국가} 바이어 협상에서 {목표단가} 달성\nScenario:\n- 바이어 제시가: {바이어제시가}\n- 경쟁사: {경쟁사제시가}\n- 강점: {우리강점}\nExpected Solution: 협상 3단계 시나리오 및 대본" },
    { id: 17, domain: "coding", taskType: "dev", title: "RISEN 웹앱 기획", tags: ["#RISEN", "#웹앱"], useCase: "단일 HTML 기반의 웹앱 MVP를 만들 때", description: "비전공자도 에러 없는 프론트엔드 코드를 얻을 수 있습니다.", template: "R(역할): 비전공자를 돕는 웹개발자\nI(지시): {만들고싶은앱} 페이지 작성\nS(단계): 1. 화면설명 2. 코드 3. 사용법\nE(목표): {주요기능} 작동\nN(제한): HTML 한 파일, 외부 라이브러리 금지" },
    { id: 18, domain: "general", taskType: "improve", title: "CoT 심사숙고 (반론 유도)", tags: ["#논리검증", "#CoT"], useCase: "비즈니스 결정을 내리기 전 검증할 때", description: "내 주장에 대한 강력한 반론을 제기하고 분석합니다.", template: "\"{나의주장}\"이라는 주장에 대해 가장 강력한 반론 3가지를 제시하고, 이를 고려해 내가 준비해야 할 전략을 단계별(Chain of Thought)로 생각해 중간 결론을 보여줘." },
    { id: 19, domain: "general", taskType: "improve", title: "질문 개선 다방향 분기", tags: ["#질문개선", "#분기형"], useCase: "내가 쓴 프롬프트가 모호할 때", description: "초안 질문을 3가지 방향으로 개선해 줍니다.", template: "제 질문을 3가지 다른 해석으로 개선해주세요. 각 버전이 어떤 상황에 맞는지 설명하고, 제가 고르면 그것으로 답하세요.\n\n초안: {초안질문}" },
    { id: 20, domain: "general", taskType: "improve", title: "APE 마스터 프롬프트", tags: ["#APE", "#프롬프트설계"], useCase: "복잡한 작업을 위한 완벽한 프롬프트를 만들 때", description: "목표만 주면 AI가 전략을 섞어 최적 프롬프트를 도출합니다.", template: "당신은 프롬프트 엔지니어링 전문가입니다.\n[작업]: {수행할작업}\n[목표]: {원하는결과}\n[제외]: {금지사항}\n\nStep 1: 서로 다른 전략의 후보 3개 생성\nStep 2: 명확성, 실행가능성 평가\nStep 3: 장점을 합친 최종 프롬프트 코드 블록 출력" }
];""",
    "public/js/app.js": r"""let favorites = new Set(JSON.parse(localStorage.getItem('promptFavorites')) || []);
let activeTab = 'ai'; 

function exportJSON() {
    const dataStr = JSON.stringify({ favorites: [...favorites] });
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const link = document.createElement('a');
    link.href = dataUri;
    link.download = 'prompthub_backup.json';
    link.click();
    showToast("데이터가 백업되었습니다.");
}

function importJSON(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
        try {
            const data = JSON.parse(e.target.result);
            if (data.favorites) {
                favorites = new Set(data.favorites);
                localStorage.setItem('promptFavorites', JSON.stringify([...favorites]));
                showToast("데이터가 복구되었습니다.");
                if(document.getElementById('view-guide').classList.contains('block')) renderPrompts();
            }
        } catch (err) { alert("유효하지 않은 파일입니다."); }
    };
    reader.readAsText(file);
}

const frameworkFields = {
    "RTCC": [
        { id: "Role", label: "Role (역할)", type: "input", placeholder: "예: 10년 경력 무역 상사 수출입 전문가" },
        { id: "Task", label: "Task (작업)", type: "input", placeholder: "예: 신제품 샘플 제안 영문 이메일 작성" },
        { id: "Context", label: "Context (배경)", type: "textarea", placeholder: "예: 제품: 스낵, 타깃: 미국 바이어" },
        { id: "Constraints", label: "Constraints (조건)", type: "textarea", placeholder: "예: 정중한 비즈니스 톤, 150단어" }
    ],
    "COSTAR": [
        { id: "Context", label: "Context (맥락)", type: "textarea", placeholder: "예: 미국 대형 유통사가 소싱 고려 중" },
        { id: "Objective", label: "Objective (목표)", type: "input", placeholder: "예: 신규 공급사로 선정 설득" },
        { id: "Style", label: "Style (스타일)", type: "input", placeholder: "예: 전문적이고 데이터 기반" },
        { id: "Tone", label: "Tone (톤)", type: "input", placeholder: "예: 자신감, 협력적" },
        { id: "Audience", label: "Audience (대상)", type: "input", placeholder: "예: 40대 소싱 디렉터" },
        { id: "Response", label: "Response (출력)", type: "textarea", placeholder: "예: 영문 Proposal, 800단어 이내" }
    ],
    "RISEN": [
        { id: "Role", label: "Role (역할)", type: "input", placeholder: "비전공자를 돕는 웹개발자" },
        { id: "Instructions", label: "Instructions (지시)", type: "textarea", placeholder: "바이어 연락처 메모장 앱 작성" },
        { id: "Steps", label: "Steps (단계)", type: "textarea", placeholder: "1. 화면설명 2. 코드 3. 사용법" },
        { id: "EndGoal", label: "End Goal (목표)", type: "textarea", placeholder: "이름, 국가를 입력해 표로 저장" },
        { id: "Narrowing", label: "Narrowing (제약)", type: "textarea", placeholder: "HTML 한 파일, 외부 라이브러리 금지" }
    ],
    "FREE": [
        { id: "Draft", label: "현재 초안 (질문)", type: "textarea", placeholder: "예: 베트남에 화장품 팔려면 어떡해?" },
        { id: "Goal", label: "원하는 결과물", type: "input", placeholder: "예: 6개월 실행 로드맵" },
        { id: "Avoid", label: "피해야 할 것", type: "input", placeholder: "예: 뻔한 얘기, 복잡한 전문용어" }
    ]
};

function renderDynamicForm() {
    const fw = document.getElementById('frameworkSelect').value;
    const container = document.getElementById('dynamicFormContainer');
    container.innerHTML = '';

    frameworkFields[fw].forEach(f => {
        const div = document.createElement('div');
        div.innerHTML = `<label class="block text-sm font-bold text-[#202722] mb-1">${f.label}</label>` + 
            (f.type === 'input' ? `<input type="text" id="df-${f.id}" placeholder="${f.placeholder}" class="w-full p-2 border border-[#E5E4DC] rounded-lg focus:outline-none focus:border-[#263B52]">`
            : `<textarea id="df-${f.id}" rows="2" placeholder="${f.placeholder}" class="w-full p-2 border border-[#E5E4DC] rounded-lg focus:outline-none focus:border-[#263B52]"></textarea>`);
        container.appendChild(div);
    });
}

function switchResultTab(tab) {
    activeTab = tab;
    document.getElementById('builderResultAI').classList.toggle('hidden', tab !== 'ai');
    document.getElementById('builderResultRaw').classList.toggle('hidden', tab !== 'raw');
    document.getElementById('res-tab-ai').className = tab === 'ai' ? 'font-bold text-[#263B52] border-b-2 border-[#263B52] pb-1' : 'text-gray-400 hover:text-[#263B52] pb-1';
    document.getElementById('res-tab-raw').className = tab === 'raw' ? 'font-bold text-[#263B52] border-b-2 border-[#263B52] pb-1' : 'text-gray-400 hover:text-[#263B52] pb-1';
}

async function generatePromptWithAPI() {
    const fw = document.getElementById('frameworkSelect').value;
    const formData = {};
    let hasData = false;
    frameworkFields[fw].forEach(f => {
        const val = document.getElementById(`df-${f.id}`).value.trim();
        formData[f.id] = val;
        if(val) hasData = true;
    });

    if(!hasData) { alert("내용을 입력해주세요."); return; }

    const btn = document.querySelector('button[onclick="generatePromptWithAPI()"]');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-2"></i>최적화 진행 중...';
    btn.classList.add('opacity-50', 'pointer-events-none');
    document.getElementById('builderResultAI').value = "AI가 작성 중입니다...";
    document.getElementById('builderResultRaw').value = "입력 조합 중...";
    switchResultTab('ai');

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ framework: fw, formData: formData })
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error);

        document.getElementById('builderResultRaw').value = result.rawPrompt;
        document.getElementById('builderResultAI').value = result.optimizedPrompt;
    } catch (error) {
        document.getElementById('builderResultAI').value = `오류 발생: ${error.message}\n.env에 API 키를 등록하고 Vercel 환경에서 실행 중인지 확인하세요.`;
    } finally {
        btn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles mr-2"></i>Gemini AI로 최적화';
        btn.classList.remove('opacity-50', 'pointer-events-none');
    }
}

function copyBuilderResult() {
    navigator.clipboard.writeText(document.getElementById(activeTab === 'ai' ? 'builderResultAI' : 'builderResultRaw').value).then(() => showToast());
}

function showToast(msg = "복사되었습니다!") {
    document.getElementById('toastMsg').innerText = msg;
    const t = document.getElementById('toast');
    t.classList.remove('opacity-0');
    setTimeout(() => t.classList.add('opacity-0'), 2000);
}

// 라이브러리 UI 로직 (이전과 동일)
let currentDomain = 'all', currentTask = 'all', showFavoritesOnly = false;
function switchTab(t) {
    document.getElementById('view-guide').classList.toggle('hidden', t !== 'guide');
    document.getElementById('view-builder').classList.toggle('hidden', t !== 'builder');
    document.getElementById('tab-guide').className = t === 'guide' ? 'tab-active px-2 py-4 text-sm' : 'tab-inactive px-2 py-4 text-sm';
    document.getElementById('tab-builder').className = t === 'builder' ? 'tab-active px-2 py-4 text-sm' : 'tab-inactive px-2 py-4 text-sm';
}
function setDomain(d) { currentDomain = d; document.querySelectorAll('.filter-btn-dom').forEach(b => b.className = 'filter-btn-dom px-3 py-1 bg-white border text-[#68716B] rounded-full text-sm'); document.getElementById(`dom-${d}`).className = 'filter-btn-dom px-3 py-1 bg-[#263B52] text-white rounded-full text-sm'; renderPrompts(); }
function setTask(t) { currentTask = t; document.querySelectorAll('.filter-btn-tsk').forEach(b => b.className = 'filter-btn-tsk px-3 py-1 bg-white border text-[#68716B] rounded-full text-sm'); document.getElementById(`tsk-${t}`).className = 'filter-btn-tsk px-3 py-1 bg-[#263B52] text-white rounded-full text-sm'; renderPrompts(); }
function toggleFavFilter() { showFavoritesOnly = !showFavoritesOnly; document.getElementById('fav-filter').className = showFavoritesOnly ? 'px-3 py-1 bg-[#263B52] text-white border rounded-full text-sm' : 'px-3 py-1 bg-white border text-[#68716B] rounded-full text-sm'; renderPrompts(); }
function filterPrompts() { renderPrompts(); }
function toggleFav(id, e) { e.stopPropagation(); favorites.has(id) ? favorites.delete(id) : favorites.add(id); localStorage.setItem('promptFavorites', JSON.stringify([...favorites])); renderPrompts(); }

function renderPrompts() {
    const grid = document.getElementById('promptGrid'), query = document.getElementById('searchInput').value.toLowerCase();
    grid.innerHTML = ''; let vc = 0;
    promptData.forEach(p => {
        if((p.title.toLowerCase().includes(query) || p.description.toLowerCase().includes(query) || p.tags.join(' ').toLowerCase().includes(query))
            && (currentDomain === 'all' || p.domain === currentDomain)
            && (currentTask === 'all' || p.taskType === currentTask)
            && (!showFavoritesOnly || favorites.has(p.id))) {
            vc++;
            const favIcon = favorites.has(p.id) ? '<i class="fa-solid fa-star text-yellow-400"></i>' : '<i class="fa-regular fa-star text-gray-300"></i>';
            const vars = [...new Set([...p.template.matchAll(/\{([^}]+)\}/g)].map(m => m[1]))];
            grid.innerHTML += `<div class="bg-white p-5 rounded-xl border hover:border-[#263B52] flex flex-col justify-between group">
                <div>
                    <div class="flex justify-between items-start mb-3"><div class="flex gap-1 flex-wrap">${p.tags.map(t=>`<span class="text-xs bg-gray-100 px-2 py-0.5 rounded">${t}</span>`).join('')}</div><button onclick="toggleFav(${p.id}, event)">${favIcon}</button></div>
                    <h3 class="font-bold text-lg mb-1 line-clamp-1">${p.title}</h3>
                    <p class="text-xs text-[#263B52] font-semibold mb-3 bg-[#F7F6F2] inline-block px-2 py-1 rounded">💡 상황: ${p.useCase}</p>
                    <p class="text-sm text-gray-600 mb-4 line-clamp-2">${p.description}</p>
                </div>
                <div class="mt-auto">
                    <div class="mb-3 text-xs text-gray-500 bg-gray-50 p-2 rounded"><span class="line-clamp-1">입력: ${vars.length ? vars.map(v=>`{${v}}`).join(', ') : '없음'}</span></div>
                    <button onclick="openModal(${p.id})" class="w-full bg-[#263B52] text-white py-2 rounded font-bold text-sm">템플릿 채우기</button>
                </div></div>`;
        }
    });
    grid.classList.toggle('hidden', vc === 0); document.getElementById('emptyState').classList.toggle('hidden', vc !== 0);
}

let cPrompt, cInputs = {};
function openModal(id) {
    cPrompt = promptData.find(p => p.id === id); cInputs = {};
    const vars = [...new Set([...cPrompt.template.matchAll(/\{([^}]+)\}/g)].map(m => m[1]))];
    const mc = document.getElementById('modalVars'); mc.innerHTML = '';
    if(!vars.length) mc.innerHTML = '<div class="text-sm text-gray-400 mt-10 text-center">입력할 변수가 없습니다.</div>';
    else vars.forEach((v, i) => { cInputs[v] = ''; mc.innerHTML += `<div class="mb-4"><label class="block text-sm font-bold mb-1">${v}</label><textarea oninput="uP('${v}', this.value)" rows="1" class="w-full p-2 border rounded focus:border-[#263B52] text-sm resize-y" placeholder="${v} 입력..."></textarea></div>`; });
    uPR(); document.getElementById('varModal').classList.remove('hidden');
}
function closeModal() { document.getElementById('varModal').classList.add('hidden'); }
function uP(k, v) { cInputs[k] = v; uPR(); }
function uPR() {
    let rt = cPrompt.template;
    Object.keys(cInputs).forEach(k => { rt = rt.replace(new RegExp(`\\{${k}\\}`, 'g'), cInputs[k] ? `<span class="highlight-var">${cInputs[k]}</span>` : `<span class="text-red-400 font-bold bg-red-50 px-1 rounded">{${k}}</span>`); });
    document.getElementById('modalPreview').innerHTML = rt;
}
function copyModalContent() {
    let rt = cPrompt.template;
    Object.keys(cInputs).forEach(k => { rt = rt.replace(new RegExp(`\\{${k}\\}`, 'g'), cInputs[k] || `{${k}}`); });
    navigator.clipboard.writeText(rt).then(() => showToast("템플릿이 복사되었습니다!")); closeModal();
}

window.onload = () => { renderPrompts(); renderDynamicForm(); };"""
}

def create_zip():
    print("🚀 PromptHub ZIP 파일 생성을 시작합니다...")
    zip_filename = "prompt-hub.zip"
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zf:
        for filepath, content in files.items():
            # 폴더 구조는 zipfile이 자동으로 인식
            zf.writestr(filepath, content.strip() + "\n")
            print(f"  + {filepath} 추가됨")

    print(f"\n✅ 완료! 현재 폴더에 '{zip_filename}' 파일이 생성되었습니다.")
    print("이제 압축을 풀고 npm install -> npm run dev 로 실행하세요!")

if __name__ == "__main__":
    create_zip()