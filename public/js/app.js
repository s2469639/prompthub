let favorites = new Set(JSON.parse(localStorage.getItem('promptFavorites')) || []);
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

window.onload = () => { renderPrompts(); renderDynamicForm(); };
