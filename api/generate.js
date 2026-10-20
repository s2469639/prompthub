export default async function handler(req, res) {
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

    const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`;

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                systemInstruction: { parts: [{ text: systemInstruction }] },
                contents: [{ parts: [{ text: rawPrompt + "\n\n이 내용을 바탕으로 즉시 복사해서 사용할 수 있는 최종 마크다운 프롬프트를 작성해줘." }] }]
            })
        });

        if (!response.ok) {
            const errorBody = await response.text();
            return res.status(response.status).json({
                error: `Gemini API 호출 실패 (상태 코드 ${response.status})`,
                details: errorBody
            });
        }
        
        const data = await response.json();
        const optimizedText = data.candidates?.[0]?.content?.parts?.[0]?.text;

        if (!optimizedText) {
            return res.status(500).json({
                error: 'AI 응답 형식이 올바르지 않거나 차단되었습니다.',
                details: JSON.stringify(data)
            });
        }

        return res.status(200).json({ 
            rawPrompt: rawPrompt, 
            optimizedPrompt: optimizedText 
        });

    } catch (error) {
        return res.status(500).json({ error: error.message, details: error.stack });
    }
}
