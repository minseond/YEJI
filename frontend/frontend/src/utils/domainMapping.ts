
/**
 * Unified Domain Mapping System
 * Centralizes all text generation and domain logic for both Eastern (Saju) and Western (Astrology) results.
 */

// =============================================================================
// 1. EASTERN DOMAIN (SAJU)
// =============================================================================

export const EAST_ELEMENTS: Record<string, { label: string; hanja: string; desc: string; keywords: string[] }> = {

    WOOD: { label: "목", hanja: "木", desc: "성장과 활기, 새로움을 추구하는 뻗어나가는 기운", keywords: ["성장", "창의", "인자함"] },
    FIRE: { label: "화", hanja: "火", desc: "열정과 확산, 자신을 드러내고 빛내는 뜨거운 기운", keywords: ["열정", "표현", "예의"] },
    EARTH: { label: "토", hanja: "土", desc: "포용과 중재, 안정감 있게 만물을 품어주는 믿음직한 기운", keywords: ["신용", "중재", "안정"] },
    METAL: { label: "금", hanja: "金", desc: "결단과 결실, 예리하고 원칙을 중시하며 정리하는 기운", keywords: ["결단", "의리", "원칙"] },
    WATER: { label: "수", hanja: "水", desc: "지혜와 흐름, 유연하고 깊은 내면을 탐구하는 기운", keywords: ["지혜", "유연", "통찰"] }
};

export const EAST_TEN_GODS: Record<string, { label: string; group: string; desc: string; meaning: string }> = {
    // Bi-Gyeop (Self)
    BI_GYEON: { label: "비견", group: "BI_GYEOP", desc: "나와 어깨를 나란히 하는 독립적인 기운", meaning: "주체성과 고집이 있으며 자립심이 강한 기운" },
    GANG_JAE: { label: "겁재", group: "BI_GYEOP", desc: "나의 재물을 쟁탈하거나 경쟁하는 강한 기운", meaning: "승부욕이 강하고 재물을 나누거나 경쟁하는 기운" },
    // Sik-Sang (Output)
    SIK_SIN: { label: "식신", group: "SIK_SANG", desc: "먹을 복과 재능을 타고난 풍요로운 기운", meaning: "표현력이 좋고 먹을 복이 있으며 재능을 발휘하는 기운" },
    SANG_GWAN: { label: "상관", group: "SIK_SANG", desc: "기존의 틀을 깨고 화려하게 자신을 뽐내는 기운", meaning: "비판적 지성과 창의성, 권위에 저항하는 화려한 기운" },
    // Jae-Seong (Wealth)
    PYEON_JAE: { label: "편재", group: "JAE_SEONG", desc: "공공의 재물이나 큰 사업적 성취를 쫓는 기운", meaning: "활동적이고 풍류를 즐기며 큰 재물을 꿈꾸는 기운" },
    JEONG_JAE: { label: "정재", group: "JAE_SEONG", desc: "알뜰하게 모은 정당한 재물과 안정적인 기운", meaning: "정직하고 성실하며 안정적인 재물을 추구하는 기운" },
    // Gwan-Seong (Power/Control)
    PYEON_GWAN: { label: "편관", group: "GWAN_SEONG", desc: "나를 강하게 억제하며 명예와 권력을 쥐는 기운", meaning: "카리스마와 인내심, 강한 책임감을 가진 기운" },
    JEONG_GWAN: { label: "정관", group: "GWAN_SEONG", desc: "반듯한 벼슬과 같이 명예와 규범을 지키는 기운", meaning: "명예와 규칙을 중시하며 사회적 지위를 지키는 안정적인 기운" },
    // In-Seong (Resource)
    PYEON_IN: { label: "편인", group: "IN_SEONG", desc: "한 가지 분야에 깊이 파고드는 직관과 고독의 기운", meaning: "예술적 감각과 직관력, 탐구자의 기운" },
    JEONG_IN: { label: "정인", group: "IN_SEONG", desc: "학문과 문서, 어머니와 같은 따뜻한 후원의 기운", meaning: "지혜롭고 학구적이며 주변의 도움을 받는 상서로운 기운" },
    // Special
    DAY_MASTER: { label: "일간", group: "SELF", desc: "나 자신", meaning: "당신의 태생적인 본질이자 자아의 중심이 되는 기운" }
};

export const EAST_TEN_GOD_GROUPS: Record<string, { label: string; keyword: string; desc: string }> = {
    BI_GYEOP: { label: "비겁", keyword: "자립과 자아의 힘 (Self)", desc: "나와 같은 기운으로, 주체성과 자존감을 결정짓는 뿌리입니다." },
    SIK_SANG: { label: "식상", keyword: "표현과 창의의 힘 (Expression)", desc: "내가 밖으로 내뿜는 에너지로, 재능 발휘와 표현력을 상징합니다." },
    JAE_SEONG: { label: "재성", keyword: "결실과 재물의 힘 (Wealth)", desc: "내가 다스리고 취하는 결과물로, 현실 감각과 성과를 뜻합니다." },
    GWAN_SEONG: { label: "관성", keyword: "명예와 사회적 책임 (Power)", desc: "나를 제어하고 다스리는 규칙으로, 사회적 명예와 책임감을 의미합니다." },
    IN_SEONG: { label: "인성", keyword: "지혜와 수용의 힘 (Resource)", desc: "나를 생하고 돕는 기운으로, 지식 습득과 서포트의 에너지를 담고 있습니다." }
};

export const EAST_PILLARS: Record<string, { label: string; context: string; poetic: string }> = {
    year: {
        label: "년주",
        context: "년주는 조상과 가문의 기운, 그리고 당신의 유년기를 나타내는 자리입니다.",
        poetic: "조상의 든든한 기운이 당신의 밑바탕에 흐르고 있으니, 어떠한 풍파에도 흔들리지 말고 당신만의 단단한 인생을 일궈 나가시기 바랍니다."
    },
    month: {
        label: "월주",
        context: "월주는 부모님과의 인연, 사회적 환경, 그리고 직업적 소양을 의미하는 자리입니다.",
        poetic: "당신을 둘러싼 환경이 당신의 재능을 꽃피울 준비가 되어 있으니, 자신을 믿고 당당하게 세상의 중심에 서 보시기 바랍니다."
    },
    day: {
        label: "일주",
        context: "일주는 당신 자신과 배우자 자리로, 성격과 본질을 가장 잘 보여주는 핵심적인 기둥입니다.",
        poetic: "이것이 바로 당신의 가장 순수한 모습이니, 스스로의 특별함을 인정하고 사랑할 때 당신의 운명은 비로소 가장 밝게 빛나기 시작할 것입니다."
    },
    hour: {
        label: "시주",
        context: "시주는 자녀와 미래, 그리고 인생의 후반기 흐름을 나타내는 자리입니다.",
        poetic: "인생의 후반기로 갈수록 당신의 노력이 아름다운 보석으로 변해갈 것이니, 내일을 두려워하지 말고 오늘의 기운을 소중히 간직하시기 바랍니다."
    }
};

// Simple generic mapping for Ganji - in a real app this might be 60 entries
// 60 Ganji Meanings Data
const GANJI_MEANINGS: Record<string, string> = {
    // 1. Wood (Gap/Eul)
    "甲子": "깊은 겨울 차가운 물 위로 솟아오른 거목처럼, 강한 자립심과 개척 정신을 상징하는 기운",
    "乙丑": "겨울 얼어붙은 땅을 뚫고 나오는 끈질긴 생명력의 기운",
    "丙寅": "초봄의 태양처럼 만물을 깨우는 활기차고 명랑한 기운",
    "丁卯": "달밤의 토끼처럼 섬세하고 예민하며, 예술적인 감수성이 풍부한 기운",
    "戊辰": "거대한 산과 용처럼 웅장하고 스케일이 크며, 강한 추진력을 가진 기운",
    "己巳": "따뜻한 들판의 뱀처럼 지혜롭고 현실적이며, 실속을 챙기는 기운",
    "庚午": "달리는 백마처럼 순수하고 열정적이며, 고귀한 이상을 쫓는 기운",
    "辛未": "한여름의 양처럼 인내심이 강하고, 내면이 단단하며 실리적인 기운",
    "壬申": "가을의 물길처럼 끊임없이 흐르는 지혜와 다재다능함을 가진 기운",
    "癸酉": "맑은 샘물과 보석처럼 깨끗하고 총명하며, 완벽함을 추구하는 기운",
    "甲戌": "가을 산의 나무처럼 고독하지만 의리가 있고, 뚝심 있게 자신의 길을 가는 기운",
    "乙亥": "유유자적 흐르는 강물 위 꽃잎처럼, 낭만적이고 온화하며 적응력이 뛰어난 기운",

    // 2. Fire (Byeong/Jeong)
    "丙子": "한밤의 태양처럼 어둠 속에서도 빛나는 이상과 열정을 가진 고귀한 기운",
    "丁丑": "화로 속의 불씨처럼 은근한 끈기와 재능을 품고 있는 기운",
    "戊寅": "거대한 산속의 호랑이처럼 용맹하고 독립심이 강하며, 지도자의 자질을 가진 기운",
    "己卯": "봄날의 들판처럼 생명력이 넘치고, 부드러움 속에 강한 고집을 숨긴 기운",
    "庚辰": "강철 용처럼 강인하고 결단력이 있으며, 큰 목표를 향해 나아가는 기운",
    "辛巳": "빛나는 보석과 뱀처럼 화려하고 예리하며, 남다른 센스와 감각을 지닌 기운",
    "壬午": "호수 위의 달빛처럼 은은하고 매력적이며, 사람을 끄는 힘이 있는 기운",
    "癸未": "여름 끝자락의 비처럼 차분하고 조용하지만, 내면에 깊은 생각을 품은 기운",
    "甲申": "바위 위의 소나무처럼 척박한 환경에서도 꿋꿋하게 자라나는 강인한 생명력의 기운",
    "乙酉": "잘 다듬어진 화초처럼 깔끔하고 단정하며, 섬세한 완벽주의를 지향하는 기운",
    "丙戌": "석양의 노을처럼 아름답고 정열적이지만, 어딘가 쓸쓸함을 담고 있는 감성적인 기운",
    "丁亥": "호수 위의 촛불처럼 신비롭고 영적인 직관력이 뛰어난 기운",

    // 3. Earth (Mu/Gi)
    "戊子": "산 속의 보물처럼 묵묵히 자신의 가치를 쌓아가며 재물을 모으는 기운",
    "己丑": "젖은 흙처럼 포용력이 넓고 끈기가 있으며, 묵묵히 자신의 일을 해내는 기운",
    "庚寅": "숲 속의 맹수처럼 활동적이고 진취적이며, 굽히지 않는 강한 의지를 가진 기운",
    "辛卯": "다듬어진 보석처럼 예리하고 깔끔하며, 자신만의 스타일을 중요시하는 기운",
    "壬辰": "거대한 물줄기를 머금은 용처럼 스케일이 크고, 변화무쌍한 잠재력을 가진 기운",
    "癸巳": "아침 이슬처럼 맑고 영롱하며, 지혜롭고 처세술이 뛰어난 기운",
    "甲午": "한여름의 큰 나무처럼 시원시원하고 솔직하며, 행동력이 강한 기운",
    "乙未": "메마른 땅의 잡초처럼 강한 생활력과 적응력을 가진 끈기의 기운",
    "丙申": "석양의 붉은 태양처럼 화려하고 재주가 많으며, 다방면에 능통한 기운",
    "丁酉": "밤하늘의 별처럼 반짝이는 재능과 예리한 통찰력을 가진 기운",
    "戊戌": "높은 산봉우리처럼 고고하고 주관이 뚜렷하며, 신의를 중요시하는 기운",
    "己亥": "넓은 바다의 흙처럼 포용력이 있고 유연하며, 재물복이 있는 기운",

    // 4. Metal (Gyeong/Sin)
    "庚子": "차가운 물 속의 바위처럼 냉철하고 이성적이며, 깊은 사고력을 가진 기운",
    "辛丑": "겨울의 동토 속에 묻힌 보석처럼 인내하며 때를 기다리는 은근한 기운",
    "壬寅": "새벽의 호랑이처럼 활기차고 기획력이 뛰어나며, 미래를 내다보는 기운",
    "癸卯": "봄비를 맞은 새싹처럼 싱그럽고 순수하며, 사랑받는 매력이 있는 기운",
    "甲辰": "진흙 속에서 피어나는 연꽃처럼 역경을 딛고 일어서는 강인한 기운",
    "乙巳": "꽃 핀 나무 사이를 누비는 뱀처럼 사교적이고 화려하며, 인기를 끄는 기운",
    "丙午": "한낮의 태양처럼 가장 강렬하고 열정적이며, 자신감이 넘치는 기운",
    "丁未": "따뜻한 촛불처럼 온화하고 희생적이며, 타인을 배려하는 기운",
    "戊申": "가을 산의 원숭이처럼 재주가 많고 임기응변이 뛰어나며 실속 있는 기운",
    "己酉": "가을 들판의 곡식처럼 풍요롭고 결실을 맺으며, 알짜배기 실력을 가진 기운",
    "庚戌": "전장의 장군처럼 용맹하고 의리가 있으며, 리더십과 통솔력을 가진 기운",
    "辛亥": "맑은 물에 씻긴 보석처럼 빛나고 총명하며, 예술적 감각이 뛰어난 기운",

    // 5. Water (Im/Gye)
    "壬子": "거대한 바다처럼 깊고 넓은 마음을 가졌으며, 포용력과 지도력이 있는 기운",
    "癸丑": "겨울의 언 땅을 녹이는 봄비처럼 끈기 있고 성실하며, 대기만성형 기운",
    "甲寅": "우람한 거목처럼 곧고 튼튼하며, 자존심과 리더십이 강한 기운",
    "乙卯": "봄의 꽃밭처럼 화사하고 다정다감하며, 친화력이 뛰어난 기운",
    "丙辰": "구름 사이로 비치는 태양처럼 밝고 희망차며, 사람들에게 온기를 주는 기운",
    "丁巳": "어둠을 밝히는 등불처럼 지혜롭고 예의 바르며, 주위를 밝게 만드는 기운",
    "戊午": "화산처럼 폭발적인 에너지를 품고 있으며, 대범하고 카리스마 있는 기운",
    "己未": "여름의 밭처럼 끈기 있고 성실하며, 강한 인내심으로 결실을 맺는 기운",
    "庚申": "단단한 바위처럼 소신이 뚜렷하고 결단력이 있으며, 의리가 강한 기운",
    "辛酉": "가장 순수한 보석처럼 예민하고 깔끔하며, 확실한 주관을 가진 기운",
    "壬戌": "깊은 가을의 바다처럼 속을 알 수 없는 깊이와 거대한 포부의 기운",
    "癸亥": "모든 것을 포용하는 큰 물처럼 지혜롭고 유연하며, 강한 생명력을 가진 기운",
};

// Simple generic mapping for Ganji - in a real app this might be 60 entries
export const getGanjiMeaning = (ganji: string): string => {
    return GANJI_MEANINGS[ganji] || "조화롭고 특별한 운명의 흐름을 담고 있는 기운";
};


// =============================================================================
// 2. WESTERN DOMAIN (ASTROLOGY)
// =============================================================================

export const WEST_ELEMENTS: Record<string, { label: string; desc: string; dialogue: string }> = {
    FIRE: {
        label: "불 (Fire)",
        desc: "직관적이고 열정적이며, 영감을 중요시하는 에너지",
        dialogue: "와, 뜨거운 불꽃의 에너지가 느껴지네요! 직관이 뛰어나고 열정이 넘치시는 분이에요. 무언가에 빠지면 온 힘을 다해 뛰어드는 스타일이죠!"
    },
    EARTH: {
        label: "흙 (Earth)",
        desc: "현실적이고 감각적이며, 안정과 물질을 중요시하는 에너지",
        dialogue: "든든한 대지 같은 에너지네요! 현실적이고 차분하며, 말보다 결과로 보여주는 스타일이에요. 안정감이 매력 포인트죠!"
    },
    AIR: {
        label: "공기 (Air)",
        desc: "지적이고 사회적이며, 소통과 아이디어를 중요시하는 에너지",
        dialogue: "자유로운 바람 같은 에너지네요! 호기심이 많고 새로운 것을 배우길 좋아하시죠? 소통 능력이 정말 뛰어나세요!"
    },
    WATER: {
        label: "물 (Water)",
        desc: "감정적이고 공감 능력이 뛰어나며, 유대감을 중요시하는 에너지",
        dialogue: "깊은 바다 같은 감성 에너지네요! 공감 능력이 뛰어나고, 사람들의 마음을 잘 읽으시는 분이에요. 신비로운 매력이 있으시죠!"
    }
};

export const WEST_MODALITIES: Record<string, { label: string; desc: string; dialogue: string }> = {
    CARDINAL: {
        label: "활동성 (Cardinal)",
        desc: "새로운 일을 시작하고 주도하는 리더십의 에너지",
        dialogue: "시작의 에너지가 강하시네요! 남들이 망설일 때 먼저 나서는 개척자 타입이에요. 추진력이 정말 대단하세요!"
    },
    FIXED: {
        label: "고정성 (Fixed)",
        desc: "현재의 상태를 유지하고 안정시키는 끈기의 에너지",
        dialogue: "유지의 에너지가 돋보이네요! 한 번 마음먹으면 끝까지 가는 뚝심이 있어요. 주변에게 큰 신뢰를 주시는 분이에요!"
    },
    MUTABLE: {
        label: "변동성 (Mutable)",
        desc: "상황에 맞춰 유연하게 변화하고 적응하는 에너지",
        dialogue: "변화의 에너지가 흐르고 있네요! 어떤 환경에서도 유연하게 적응하는 능력이 뛰어나세요. 다재다능한 타입이시죠!"
    }
};

export const WEST_KEYWORDS: Record<string, { label: string; desc: string; dialogue: string }> = {
    EMPATHY: {
        label: "공감",
        desc: "타인의 감정을 깊이 이해하는 공감 능력",
        dialogue: "공감 능력이 빛나시네요! 다른 사람의 마음을 잘 읽고 위로해줄 수 있는 따뜻한 분이에요."
    },
    INTUITION: {
        label: "직관",
        desc: "논리보다 앞서는 예리한 직관",
        dialogue: "직관력이 대단하시네요! 설명할 수 없지만 '느낌'으로 정답을 찾아내는 능력이 있어요."
    },
    IMAGINATION: {
        label: "상상력",
        desc: "현실 너머를 꿈꾸는 풍부한 상상력",
        dialogue: "상상력이 풍부하시네요! 남들이 보지 못하는 가능성을 그려내는 창의적인 분이에요."
    },
    BOUNDARY: {
        label: "경계",
        desc: "자신을 지키기 위한 건강한 경계 설정",
        dialogue: "자기 보호 능력이 뛰어나시네요! 건강하게 선을 그을 줄 아는 현명한 분이에요."
    },
    LEADERSHIP: {
        label: "리더십",
        desc: "사람들을 이끄는 카리스마와 지도력",
        dialogue: "타고난 리더시네요! 사람들이 자연스럽게 따르게 되는 카리스마가 있어요."
    },
    PASSION: {
        label: "열정",
        desc: "목표를 향해 돌진하는 뜨거운 열정",
        dialogue: "열정이 넘치시네요! 하고 싶은 일에는 온 힘을 다하는 멋진 분이에요."
    },
    ANALYSIS: {
        label: "분석",
        desc: "현상을 꿰뚫어 보는 날카로운 분석",
        dialogue: "분석력이 날카로우시네요! 복잡한 것도 핵심을 빠르게 파악하는 능력이 있어요."
    },
    STABILITY: {
        label: "안정",
        desc: "흔들리지 않는 편안함과 안정감",
        dialogue: "안정감이 느껴지시네요! 주변 사람들에게 편안함과 신뢰를 주는 분이에요."
    },
    COMMUNICATION: {
        label: "소통",
        desc: "막힘없이 흐르는 소통과 언어 능력",
        dialogue: "소통 능력이 뛰어나시네요! 어떤 사람과도 대화가 술술 통하는 매력이 있어요."
    },
    INNOVATION: {
        label: "혁신",
        desc: "새로운 길을 여는 혁신적인 사고",
        dialogue: "혁신적인 사고를 가지셨네요! 기존의 틀을 깨고 새로운 길을 만드는 분이에요."
    }
};

export const WEST_ZODIAC_SIGNS: Record<string, { title: string; dialogue: string; desc: string }> = {
    "물병자리": {
        title: "개성 넘치는 혁신가",
        dialogue: "물병자리시군요! 독창적인 아이디어와 인류애가 넘치는 분이에요. 남다른 시각으로 세상을 바라보시죠!",
        desc: "기존의 틀을 깨고 새로운 미래를 그리는 혁신가입니다. 독창적인 사고방식과 인류애를 겸비하고 있죠."
    },
    "물고기자리": {
        title: "꿈꾸는 예술가",
        dialogue: "물고기자리시군요! 풍부한 상상력과 깊은 공감 능력을 가진 감성적인 분이에요. 예술적 감각도 뛰어나시죠!",
        desc: "경계 없는 상상력과 깊은 바다 같은 공감 능력을 지녔습니다. 세상을 아름답게 물들이는 예술가적 기질이 있습니다."
    },
    "양자리": {
        title: "용감한 개척자",
        dialogue: "양자리시군요! 도전을 두려워하지 않는 용감한 개척자예요. 어떤 일이든 먼저 나서는 리더 타입이시죠!",
        desc: "두려움 없이 세상에 맞서는 용감한 전사입니다. 꺼지지 않는 불꽃처럼 열정적으로 삶을 개척해나갑니다."
    },
    "황소자리": {
        title: "신뢰의 완주자",
        dialogue: "황소자리시군요! 차분하고 인내심이 강하시네요. 한 번 시작하면 끝까지 해내는 믿음직한 분이에요!",
        desc: "흔들리지 않는 편안함과 끈기를 지녔습니다. 아름다움과 풍요를 사랑하며, 묵묵히 자신의 길을 걷습니다."
    },
    "쌍둥이자리": {
        title: "재치있는 소통가",
        dialogue: "쌍둥이자리시군요! 호기심이 많고 재치가 넘치세요. 어떤 자리에서든 분위기를 이끄는 매력이 있어요!",
        desc: "바람처럼 자유롭고 호기심이 넘칩니다. 뛰어난 언변과 재치로 세상과 소통하는 매력적인 지식 탐험가입니다."
    },
    "게자리": {
        title: "따뜻한 수호자",
        dialogue: "게자리시군요! 가족과 소중한 사람을 위해서라면 뭐든 하는 따뜻한 마음씨의 소유자예요!",
        desc: "단단한 껍질 속에 부드러운 마음을 감추고 있습니다. 내 사람을 지키는 따뜻한 모성애와 보호 본능을 지녔습니다."
    },
    "사자자리": {
        title: "빛나는 왕",
        dialogue: "사자자리시군요! 자신감 넘치고 당당한 매력의 소유자예요. 무대 위의 스타처럼 빛나시죠!",
        desc: "태양처럼 뜨거운 열정과 자신감을 지녔습니다. 어디서나 빛나는 존재감으로 무대의 주인공이 되는 타고난 리더입니다."
    },
    "처녀자리": {
        title: "완벽주의자",
        dialogue: "처녀자리시군요! 섬세하고 분석적이시네요. 디테일을 놓치지 않는 완벽주의자 스타일이에요!",
        desc: "순수하고 섬세한 영혼의 소유자입니다. 날카로운 분석력으로 완벽을 추구하며, 세상에 질서를 부여합니다."
    },
    "천칭자리": {
        title: "조화의 중재자",
        dialogue: "천칭자리시군요! 균형과 조화를 중시하는 평화주의자예요. 미적 감각도 뛰어나시죠!",
        desc: "우아함과 품격을 잃지 않는 평화주의자입니다. 뛰어난 균형 감각으로 세상의 조화를 이끌어냅니다."
    },
    "전갈자리": {
        title: "깊은 통찰자",
        dialogue: "전갈자리시군요! 깊은 통찰력과 강한 의지를 가지셨어요. 비밀을 간직하는 신비로운 매력이 있으시죠!",
        desc: "본질을 꿰뚫어 보는 통찰력과 강렬한 의지를 지녔습니다. 신비로운 매력 뒤에 뜨거운 열정을 감추고 있습니다."
    },
    "사수자리": {
        title: "자유로운 모험가",
        dialogue: "사수자리시군요! 자유와 모험을 사랑하는 낙천적인 분이에요. 새로운 경험을 찾아 떠나는 걸 좋아하시죠!",
        desc: "드넓은 세상을 향해 화살을 쏘아 올리는 모험가입니다. 자유를 사랑하며, 언제나 더 높은 리상을 추구합니다."
    },
    "염소자리": {
        title: "성실한 성취자",
        dialogue: "염소자리시군요! 목표를 향해 꾸준히 나아가는 성실한 분이에요. 책임감이 정말 강하시네요!",
        desc: "험난한 산을 오르는 산양처럼 끈기 있고 성실합니다. 강한 책임감으로 결국 정상에 오르는 대기만성형 인재입니다."
    }
};

// 별자리 대화 생성 (개념 → 결과 → 의미)
export const getWestZodiacDialogue = (name: string): string => {
    for (const key in WEST_ZODIAC_SIGNS) {
        if (name.includes(key)) {
            const zodiac = WEST_ZODIAC_SIGNS[key];
            return `별자리는 당신이 태어난 순간 태양이 어디에 있었는지를 나타내요. 당신의 태양별자리는.... ${zodiac.dialogue}`;
        }
    }
    return "신비로운 별의 아이";
};

export const getWestZodiacTitle = (name: string): string => {
    for (const key in WEST_ZODIAC_SIGNS) {
        if (name.includes(key)) {
            return WEST_ZODIAC_SIGNS[key].title;
        }
    }
    return "신비로운 별의 아이";
};

// Legacy support for UI description
export const getWestZodiacDesc = (name: string): string => {
    for (const key in WEST_ZODIAC_SIGNS) {
        if (name.includes(key)) {
            return WEST_ZODIAC_SIGNS[key].desc;
        }
    }
    return "별들의 속삭임을 듣는 당신";
};


// =============================================================================
// 3. DIALOGUE GENERATORS
// =============================================================================

// Helper to wrap dynamic variables (brackets removed for clean display)
const wrap = (text: string | number) => `${text}`;

// --- EASTERN GENERATORS ---

export const genEastPillarDialogue = (pillarKey: string, ganji: string) => {
    const pillar = EAST_PILLARS[pillarKey];
    const meaning = getGanjiMeaning(ganji);
    return `당신의 ${pillar.label}는 ${wrap(ganji)}입니다. 이 기둥은 ${wrap(meaning)}입니다.`;
};

export const genEastElementDialogue = (strongCode: string, weakCode?: string) => {
    const strong = EAST_ELEMENTS[strongCode];
    if (!strong) return "오행의 기운이 조화롭게 어우러져 있습니다.";

    const weak = weakCode ? EAST_ELEMENTS[weakCode] : null;

    if (weak) {
        return `오행(五行)이란 만물을 구성하는 다섯 가지 기운입니다. 당신은 ${wrap(strong.label)}(${strong.hanja})의 기운이 가장 강하며, 상대적으로 ${wrap(weak.label)}(${weak.hanja})의 기운이 보완이 필요하군요. ${wrap(strong.desc)}이 당신의 강점입니다.`;
    } else {
        return `오행(五行)이란 만물을 구성하는 다섯 가지 기운입니다. 당신은 ${wrap(strong.label)}(${strong.hanja})의 기운이 가장 강하게 나타납니다. ${wrap(strong.desc)}이 당신의 대표적인 특징입니다.`;
    }
};

export const genEastYinYangDialogue = (yin: number, yang: number, summary: string) => {
    const ratio = `${Math.round(yin)}:${Math.round(yang)}`;
    let desc = "";

    if (yin > 60) {
        desc = "음(陰)의 기운이 강하여 차분하고 내면을 중요시하는 성향이 돋보입니다. 겉으로 드러내기보다 속으로 갈무리하는 힘이 강하시군요.";
    } else if (yang > 60) {
        desc = "양(陽)의 기운이 강하여 활동적이고 적극적인 성향이 돋보입니다. 생각보다 행동이 앞서며 에너지를 밖으로 발산하는 스타일이시군요.";
    } else {
        desc = "음(陰)과 양(陽)의 기운이 조화롭게 어우러져 있습니다. 상황에 따라 차분함과 열정을 유연하게 발휘할 수 있는 균형 잡힌 기운입니다.";
    }

    return `음양(陰陽)은 세상의 두 가지 근본 에너지입니다. 당신의 음양 비율은 ${wrap(ratio)}입니다. ${desc}`;
};

export const getEastYinYangSummary = (yin: number, yang: number) => {
    if (yin > 60) return "내면의 충실함과 차분한 지혜가 돋보이는 음(陰)의 기운";
    if (yang > 60) return "적극적인 행동력과 열정이 빛나는 양(陽)의 기운";
    return "음과 양이 서로를 보완하며 조화를 이루는 균형 잡힌 기운";
};

export const genEastTenGodDialogue = (rank: number, godCode: string) => {
    const god = EAST_TEN_GODS[godCode];
    if (!god) return "";

    const group = EAST_TEN_GOD_GROUPS[god.group];
    const rankText = rank === 1 ? "가장 주도적인" : rank === 2 ? "두 번째로 강력한" : "당신을 지탱하는";

    return `${rank}순위는 ${wrap(god.label)}입니다. 이 별은 '${wrap(group.label)}' 그룹에 속하며, ${wrap(group.keyword)}을 상징하죠. ${wrap(group.desc)} 당신의 삶에서는 ${wrap(god.meaning)}의 방식으로 ${rankText} 에너지를 발휘하고 있습니다.`;
};

export const genEastTenGodSummaryDialogue = (summaryText: string) => {
    return `${wrap(summaryText)}`;
};

export const getTenGodIntro = (): string => {
    return "이제 당신의 사회적 성격과 운명의 작용력을 결정짓는 '십신(十神)'을 분석해 보겠습니다. 십신은 당신의 타고난 기운이 세상과 어떻게 소통하는지를 보여주는 열 가지 별을 의미합니다.";
};

// --- WESTERN GENERATORS// 4원소 대화 생성 (개념 → 결과 → 의미)
export const genWestElementDialogue = (topElementCode: string, summary: string) => {
    const el = WEST_ELEMENTS[topElementCode];
    if (el && el.dialogue) {
        return `4원소는 세상과 사람을 이루는 기본 에너지예요. 불, 흙, 공기, 물! 당신의 차트를 보니 ${el.label}의 기운이 가장 강하게 나타나네요. ${el.dialogue}`;
    }
    return summary || "신비로운 균형을 이루고 있어요!";
};
// 3양태 대화 생성 (개념 → 결과 → 의미)
export const genWestModalityDialogue = (topModalityCode: string) => {
    const mod = WEST_MODALITIES[topModalityCode];
    if (mod && mod.dialogue) {
        return `양태는 에너지가 어떻게 움직이는지를 보여줘요. 시작하는 힘, 유지하는 힘, 변화하는 힘! 당신은 ${mod.label}의 성향이 강하네요. ${mod.dialogue}`;
    }
    return "독특한 에너지 패턴을 가지고 있어요!";
};
// 키워드 대화 생성 (개념 → 결과 → 의미)
export const genWestKeywordDialogue = (keywordLabel: string, summary: string) => {
    // 키워드 코드 찾기
    let foundKeyword: { label: string; desc: string; dialogue: string } | undefined;
    for (const code in WEST_KEYWORDS) {
        if (WEST_KEYWORDS[code].label === keywordLabel) {
            foundKeyword = WEST_KEYWORDS[code];
            break;
        }
    }

    if (foundKeyword && foundKeyword.dialogue) {
        return `별들의 배치를 분석한 결과, 당신의 가장 큰 강점은 ${foundKeyword.label}이에요! ${foundKeyword.dialogue}`;
    }
    return summary || "특별한 재능이 숨어 있어요!";
};

// =============================================================================
// 4. DAILY FORTUNE UTILS (Zodiac Based)
// =============================================================================

/**
 * Category-specific fortune messages
 * Maps [Category] -> [Grade] -> string[]
 */
export const CATEGORY_FORTUNE_MESSAGES: Record<string, Record<string, string[]>> = {
    love: {
        great: [
            "인연을 맺기에 더없이 완벽한 날입니다. 진심을 전한다면 반드시 통할 거예요. 과감히 도전하세요!",
            "천생연분의 기운이 강하게 비치는 날입니다. 소개팅이나 데이트에서 예상치 못한 설렘을 만나겠네요.",
            "사랑의 결실을 맺기에 최적의 기운입니다. 고백을 고민 중이라면 바로 오늘이 그날입니다.",
            "상대방의 마음이 당신을 향해 활짝 열려 있습니다. 당신의 매력이 정점에 달하는 하루가 될 거예요.",
            "혼자라면 운명적인 만남이, 커플이라면 깊은 고백이 이어질 행운 가득한 연애운입니다."
        ],
        good: [
            "주변 사람들과의 교감이 활발해지고 다정함이 넘치는 하루입니다. 작은 친절이 큰 인연으로 이어질 수 있어요.",
            "기분 좋은 설렘이 공기 중에 흐르고 있네요. 가벼운 연락 한 번이 의외의 진전으로 이어질 거예요.",
            "상대의 마음을 편안하게 해주는 매력이 돋보이는 날입니다. 자연스러운 대화 속에서 사랑이 싹트겠네요.",
            "관심 있는 사람이 있다면 조금 더 적극적으로 다가가 보세요. 상대방도 당신의 호의를 기다리고 있답니다.",
            "따뜻한 배려가 행운을 불러옵니다. 서로의 차이를 인정할 때 관계가 한 층 더 깊어질 거예요."
        ],
        average: [
            "평온하고 잔잔한 애정운입니다. 큰 변화보다는 현재의 관계를 유지하며 소소한 대화를 즐기세요.",
            "익숙함 속에서 소중함을 발견하는 하루가 되겠네요. 가까운 사람의 고마움을 다시 한번 되새겨보세요.",
            "특별한 사건은 없지만 서로를 신뢰할 수 있는 편안한 흐름입니다. 함께 차 한 잔 어떠세요?",
            "새로운 인연보다는 주변의 사람들과 정을 쌓기 좋은 날입니다. 서두르지 말고 천천히 마음을 나누세요.",
            "자기 자신을 먼저 사랑해 주는 시간을 가져보세요. 당신이 빛나야 좋은 인연도 찾아오는 법입니다."
        ],
        bad: [
            "말 한마디에 오해가 생길 수 있으니 감정 조절에 신경 써야 합니다. 예민한 화제는 잠시 피하세요.",
            "상대방의 태도가 조금 차갑게 느껴질 수 있지만, 개인적인 스트레스일 확률이 큽니다. 여유를 가지세요.",
            "오늘은 고백이나 중요한 약속보다는 조용히 혼자만의 시간을 갖는 것이 애정운에 도움이 됩니다.",
            "지나친 기대는 실망을 부를 수 있습니다. 상대의 상황을 먼저 배려해 주는 지혜가 필요합니다.",
            "질투나 소유욕이 고개를 들 수 있는 날입니다. 서로의 자유를 존중해 줄 때 관계가 지탱됩니다."
        ]
    },
    wealth: {
        great: [
            "금전의 흐름이 막힘없이 시원하게 뚫리는 날입니다. 투자나 계약에서 기대 이상의 성과를 거두겠네요!",
            "뜻하지 않은 장소에서 재물이 들어올 기운입니다. 횡재수가 있으니 작은 복권 한 장도 좋겠군요.",
            "재테크의 안목이 날카로워지는 날입니다. 오랫동안 고민했던 수익 모델이 있다면 실행에 옮기세요.",
            "경제적인 자유에 한 걸음 더 다가가는 최고의 운세입니다. 곳간이 채워지니 마음도 넉넉해집니다.",
            "협상에서 유리한 고지를 점할 수 있습니다. 당신의 가치를 증명하고 합당한 보상을 쟁취하세요."
        ],
        good: [
            "부지런히 움직인 만큼 확실한 보상이 따르는 실속 있는 하루입니다. 노력의 결실이 눈에 보이네요.",
            "주변의 조언이 재물운을 높여줍니다. 경제 관련 뉴스를 꼼꼼히 살피면 좋은 기회를 발견할 거예요.",
            "소비보다는 저축이나 자산 관리에 집중해 보세요. 작은 지출을 줄이는 것이 행운의 시작입니다.",
            "금전 거래가 원만하게 이루어지는 날입니다. 빌려준 돈을 받거나 유리한 조건으로 합의를 보겠네요.",
            "작은 이익이 모여 큰 산을 이룹니다. 티끌 모아 태산이라는 말처럼 알뜰하게 자산을 관리하세요."
        ],
        average: [
            "들어오고 나가는 돈의 밸런스가 맞는 평탄한 흐름입니다. 무리한 지출만 없다면 무난한 하루입니다.",
            "금전적인 욕심보다는 현재의 자산 상태를 유지하는 데 만족하세요. 큰 변화를 꾀하기엔 이릅니다.",
            "쇼핑이나 지출 계획이 있다면 한 번 더 고민해 보세요. 꼭 필요한 물건인지 차분히 따져보시기 바랍니다.",
            "남의 말만 믿고 투자하는 것은 위험할 수 있습니다. 주관을 뚜렷이 하고 실속을 챙기세요.",
            "가계부를 정리하며 새 나가는 돈을 점검해 볼 시간입니다. 꼼꼼한 관리가 미래의 부를 부릅니다."
        ],
        bad: [
            "지갑 속에 구멍이 난 듯 지출이 늘어날 수 있습니다. 충동구매를 각별히 주의해야 하는 날입니다.",
            "투자로 인한 손실이 생길 수 있으니 새로운 도전은 잠시 멈추세요. 오늘은 현금 보유가 상책입니다.",
            "금전 문제로 사람과 다툼이 생길 수 있습니다. 돈 거래는 명확하게 하거나 가급적 피하는 것이 좋겠네요.",
            "예상치 못한 수리비나 공과금 지출이 발생할 수 있습니다. 비상금을 미리 체크해 두는 것이 현명합니다.",
            "무모한 도박이나 사행성 행위는 금물입니다. 땀 흘려 번 돈의 소중함을 잊지 마세요."
        ]
    },
    career: {
        great: [
            "승진이나 프로젝트 성공의 기운이 강력합니다! 당신의 능력이 십분 발휘되어 주변을 놀라게 하겠네요.",
            "커리어의 전환점이 될 만한 좋은 제안이 찾아옵니다. 자신을 믿고 거침없이 앞으로 나아가세요.",
            "상사나 동료들에게 전폭적인 지지를 받는 날입니다. 리더십을 발휘하여 성과를 이끌어내기에 충분합니다.",
            "해결하지 못했던 난제가 마법처럼 풀리는 날입니다. 당신의 아이디어가 회사의 핵심 전략이 되겠군요.",
            "명예운이 드높아져 이름이 널리 알려지는 계기가 생깁니다. 당당하게 당신의 무대를 즐기세요."
        ],
        good: [
            "업무 효율이 오르고 실수가 적은 생산적인 하루입니다. 차곡차곡 쌓아온 노력이 인정받기 시작합니다.",
            "팀워크가 빛을 발하는 날입니다. 협동하여 문제를 해결할 때 더 큰 즐거움과 보람을 느낄 수 있습니다.",
            "새로운 기술이나 지식을 습득하기에 아주 좋은 타이밍입니다. 자기계발에 시간을 투자해 보세요.",
            "작은 성취감들이 모여 자신감을 북돋아줍니다. 오늘 하루도 긍정적인 에너지로 업무에 매진하세요.",
            "이직이나 전직을 고민한다면 긍정적인 신호가 보이기 시작합니다. 차분하게 포트폴리오를 준비해 보세요."
        ],
        average: [
            "반복되는 일상이지만 책임감을 가지고 임해야 하는 시기입니다. 기본에 충실할 때 성장의 기반이 마련됩니다.",
            "큰 성과보다는 맡은 바 소임을 다하는 데 집중하세요. 묵묵히 자리를 지키는 것이 지금의 최선입니다.",
            "회의나 보고에서 지나친 주장은 삼가고 경청하는 태도를 유지하세요. 소통이 곧 경쟁력입니다.",
            "과도한 업무에 지칠 수 있으니 적절한 휴식을 병행하세요. 건강한 컨디션이 업무의 질을 결정합니다.",
            "미래에 대한 막연한 불안감보다는 현재 단계에서 배울 점을 찾아보세요. 모든 경험은 자산이 됩니다."
        ],
        bad: [
            "업무상 사소한 실수가 생길 수 있으니 서류나 메일을 꼼꼼히 재확인하세요. 확인은 다다익선입니다.",
            "동료와의 의견 충돌로 스트레스를 받을 수 있습니다. 감성보다는 이성적으로 상황을 판단하세요.",
            "예정과 다르게 스케줄이 꼬일 수 있으니 유연한 시간 관리가 필요합니다. 우선순위를 잘 정하세요.",
            "정신적으로 피로도가 높은 날입니다. 중요한 프로젝트의 핵심 결정은 최상의 컨디션일 때로 미루세요.",
            "내부적인 구설수에 휘말리지 않도록 언행에 주의하세요. 실력을 묵묵히 쌓는 것만이 정답입니다."
        ]
    },
    health: {
        great: [
            "몸과 마음이 생기를 되찾고 에너지가 넘쳐흐르는 날입니다! 컨디션이 최상이니 무엇이든 즐겁게 해내겠네요.",
            "오랜 지병이나 통증이 완화되는 기분 좋은 소식이 있습니다. 꾸준한 관리가 드디어 빛을 발합니다.",
            "운동 효과가 극대화되는 날입니다. 오늘만큼은 평소보다 조금 더 활동적인 취미를 즐겨보아도 좋겠군요.",
            "안색이 맑아지고 표정이 밝아져 매력이 배가되는 하루입니다. 건강한 아름다움이 당신을 빛내줄 거예요.",
            "충분한 숙면과 영양 섭취로 심신이 완벽한 균형을 이룹니다. 활력 있는 하루를 만끽하세요."
        ],
        good: [
            "안정적인 리듬을 유지하며 건강하게 하루를 보낼 수 있습니다. 가벼운 산책이 에너지를 더해줄 거예요.",
            "식습관 개선이나 영양제 섭취가 몸에 잘 받는 시기입니다. 자신에게 맞는 건강법을 실천해 보세요.",
            "스트레스 해소 방법이 효과를 거두어 마음이 한결 가벼워집니다. 긍정적인 생각이 만병통치약입니다.",
            "충분한 수분 섭취와 규칙적인 생활이 행운의 비결입니다. 사소한 습관이 당신의 건강을 지켜줍니다.",
            "사람들과 즐겁게 웃고 대화하는 것이 정신 건강에 큰 도움이 됩니다. 활기찬 에너지를 나누세요."
        ],
        average: [
            "전반적으로 무난한 컨디션이지만 무리는 금물입니다. 몸이 보내는 작은 신호들에 귀를 기울여 주세요.",
            "충분한 휴식이 필요한 때입니다. 일과 후에 반신욕이나 명상으로 하루의 피로를 말끔히 씻어내세요.",
            "날씨나 온도 변화에 예민할 수 있으니 겉옷을 챙기거나 적정 환경을 유지하는 데 신경 쓰세요.",
            "기력이 조금 떨어질 수 있으니 보양식을 챙겨 먹거나 일찍 잠자리에 들어 기력을 보충하세요.",
            "규칙적인 일상의 리듬을 유지하는 것만으로도 충분히 건강한 하루입니다. 조급해하지 마세요."
        ],
        bad: [
            "과로로 인한 피로가 누적될 수 있습니다. 오늘만큼은 모든 일을 뒤로하고 절대적인 휴식을 취하세요.",
            "소화 기관이 예민해질 수 있으니 자극적인 음식이나 과식은 삼가야 합니다. 속을 편하게 유지하세요.",
            "면역력이 일시적으로 저하될 수 있는 날입니다. 위생 관리에 철저히 하고 감기나 감염에 주의하세요.",
            "운동 중 부상의 위험이 있으니 과격한 동작은 자제하고 스트레칭 위주로 몸을 풀어주세요.",
            "수면의 질이 떨어져 하루 종일 몽롱할 수 있습니다. 따뜻한 차 한 잔으로 긴장을 이완시켜 보세요."
        ]
    },
    academic: {
        great: [
            "두뇌 회전이 놀라울 정도로 빠르고 명석해지는 날입니다! 어려운 문제도 막힘없이 풀려나갈 거예요.",
            "집중력이 최고조에 달해 단시간에 방대한 양의 학습을 소화합니다. 오늘이 성적 향상의 기회입니다.",
            "시험이나 발표에서 놀라운 행운이 따릅니다. 당신이 준비한 내용이 핵심 주제로 나올 확률이 높네요.",
            "지적 호기심이 폭발하며 공부하는 즐거움을 깨닫는 날입니다. 배움 자체가 가장 큰 보상이 되겠군요.",
            "합격운이 문을 두드리고 있습니다. 오랫동안 간절히 원했던 결과가 당신의 노력을 배신하지 않을 거예요."
        ],
        good: [
            "끈기 있게 공부를 밀어붙일 수 있는 성실함이 돋보이는 날입니다. 엉덩이가 무거운 사람이 승리합니다.",
            "복습 효과가 뛰어납니다. 이전에 이해가 안 갔던 개념들이 비로소 머릿속에 정리되는 희열을 느껴보세요.",
            "주변 친구들이나 멘토에게 좋은 자극을 받는 날입니다. 선의의 경쟁을 통해 실력을 한 단계 높이세요.",
            "학업 계획이 차근차근 실행되어 성취감을 맛봅니다. 목표량 달성 후의 달콤한 휴식을 즐기세요.",
            "언어 학습이나 암기 과목에서 두각을 나타내는 날입니다. 자투리 시간을 활용해 실력을 쌓아보세요."
        ],
        average: [
            "공부에 대한 의지는 있지만 잡다한 생각이 많아질 수 있습니다. 책상 정리부터 하며 마음을 가다듬으세요.",
            "슬럼프 기운이 들 땐 너무 자책하지 마세요. 잠시 다른 환경으로 장소를 옮겨 공부하는 것을 추천합니다.",
            "어려운 진도를 나가기보다는 아는 내용을 견고하게 다지는 시간이 필요합니다. 기본기가 곧 실력입니다.",
            "학습 보조 도구나 강의 정보를 잘 활용해 보세요. 효율적인 방법을 찾는 것이 무작정 하는 것보다 낫습니다.",
            "결과에 연연하기보다 과정에 집중하는 담대함이 필요합니다. 매일 조금씩 나아가는 자신을 응원하세요."
        ],
        bad: [
            "집중력이 평소보다 떨어지고 쉽게 피로를 느낍니다. 억지로 붙들기보다 짧고 굵게 공부하고 쉬세요.",
            "중요한 시험이나 과제 제출 전이라면 실수가 없는지 두 번 세 번 점검하세요. 덜렁거리다 놓치기 쉽습니다.",
            "학업 스트레스가 심해져 짜증이 날 수 있습니다. 좋아하는 간식이나 산책으로 기분을 먼저 전환하세요.",
            "스마트폰이나 게임 등 유혹거리가 많은 날입니다. 공부할 때만큼은 주변 환경의 방해 요소를 제거하세요.",
            "경쟁자와 자신을 비교하며 우울해질 수 있습니다. 당신만의 페이스를 유지하는 것이 승리의 길입니다."
        ]
    },
    today: {
        great: [
            "하늘이 당신을 돕는 날입니다! 꼬였던 일들이 술술 풀리고 생각지 못한 행운이 찾아옵니다.",
            "오늘의 주인공은 당신입니다. 망설였던 일이 있다면 과감하게 도전해보세요.",
            "금전운과 명예운이 모두 따르는 최고의 하루입니다. 주변 사람들에게 베풀면 더 큰 복이 돌아옵니다.",
            "뜻밖의 귀인을 만나 도움을 받을 수 있습니다. 새로운 인연을 소중히 여기세요.",
            "기대 이상의 성과를 거둘 수 있는 날입니다. 자신감을 가지고 목표를 향해 나아가세요."
        ],
        good: [
            "활기 넘치는 기운이 가득합니다. 부지런히 움직이면 그만큼 알찬 결실을 맺을 것입니다.",
            "기다리던 반가운 소식이 들려올 수 있습니다. 기분 좋은 변화가 시작되는 날입니다.",
            "주변의 인정과 칭찬을 받을 수 있는 날입니다. 당신의 능력을 마음껏 발휘해보세요.",
            "작은 노력으로 큰 기쁨을 얻을 수 있습니다. 긍정적인 마음가짐이 행운을 부릅니다.",
            "협력운이 좋습니다. 혼자보다는 함께할 때 더 좋은 결과를 얻을 수 있습니다."
        ],
        average: [
            "평온하고 순조로운 하루입니다. 소소한 일상 속에서 행복을 발견할 수 있습니다.",
            "마음이 여유롭고 안정을 찾는 날입니다. 차 한 잔의 여유를 즐겨보세요.",
            "특별한 일은 없지만, 그만큼 평화로운 날입니다. 현재의 안정을 즐기세요.",
            "꾸준함이 빛을 발하는 날입니다. 하던 일을 묵묵히 해나가면 좋은 결과가 있을 것입니다.",
            "대인관계가 원만해지는 날입니다. 오랜 친구에게 연락해 보는 것도 좋겠습니다."
        ],
        bad: [
            "기운이 약간 가라앉아 있습니다. 무리한 활동보다는 차분하게 내실을 기하세요.",
            "작은 실수가 겹칠 수 있으니 꼼꼼하게 확인하는 습관이 필요한 날입니다.",
            "계획대로 되지 않아 답답할 수 있지만, 곧 지나갈 구름입니다. 인내심을 가지세요.",
            "사람 사이에서 소소한 오해가 생길 수 있습니다. 말을 아끼는 것이 지혜로운 하루입니다.",
            "소지품 분실에 유의하세요. 물건을 잘 챙기고 주변 정리를 하는 것이 좋습니다."
        ]
    }
};



export const getDailyZodiacFortune = (zodiacName: string, score: number, category: string = 'today'): string => {
    // 1. Get Today's Date String (YYYY-MM-DD)
    const now = new Date();
    const dateStr = `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;

    // 2. Deterministic Hash for Message Selection
    let hash = 0;
    const key = dateStr + zodiacName + category + "fortune_v4";
    for (let i = 0; i < key.length; i++) {
        hash = ((hash << 5) - hash) + key.charCodeAt(i);
        hash |= 0;
    }
    const seed = Math.abs(hash);

    // 3. Determine Grade
    let grade = "average";
    if (score >= 90) grade = "great";
    else if (score >= 70) grade = "good";
    else if (score >= 40) grade = "average";
    else grade = "bad";

    // 4. Safely pick message
    const catData = CATEGORY_FORTUNE_MESSAGES[category.toLowerCase()] || CATEGORY_FORTUNE_MESSAGES.today;
    const messages = catData[grade] || catData.average;
    const msgIndex = seed % messages.length;

    return messages[msgIndex];
};

// Lucky Elements Pool (Constants)
const LUCKY_COLORS = [
    { name: "적토색", eng: "Red Earth" }, { name: "남색", eng: "Navy" }, { name: "연두색", eng: "Light Green" },
    { name: "황금색", eng: "Gold" }, { name: "순백색", eng: "Pure White" }, { name: "진회색", eng: "Dark Gray" },
    { name: "보라색", eng: "Purple" }, { name: "청록색", eng: "Teal" }, { name: "장미색", eng: "Rose" },
    { name: "호박색", eng: "Amber" }, { name: "하늘색", eng: "Sky Blue" }, { name: "검은색", eng: "Black" }
];

const LUCKY_DIRECTIONS = ["동쪽", "서쪽", "남쪽", "북쪽", "남동쪽", "북동쪽", "남서쪽", "북서쪽", "중심", "창가", "밝은 곳", "조용한 곳"];

const LUCKY_TIMES = [
    "07:00 ~ 09:00", "09:00 ~ 11:00", "11:00 ~ 13:00", "13:00 ~ 15:00",
    "15:00 ~ 17:00", "17:00 ~ 19:00", "19:00 ~ 21:00", "21:00 ~ 23:00",
    "23:00 ~ 01:00", "01:00 ~ 03:00", "03:00 ~ 05:00", "05:00 ~ 07:00"
];

const LUCKY_ENERGIES = [
    "목(木)의 성장 기운", "화(火)의 열정 기운", "토(土)의 안정 기운", "금(金)의 결단 기운", "수(水)의 지혜 기운",
    "강력한 비겁의 추진력", "부드러운 식상의 창의성", "단단한 재성의 결실", "반듯한 관성의 명예", "깊은 인성의 지혜"
];

const LUCKY_NUMBERS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "11", "22", "33"];

const LUCKY_PLACES_WESTERN = [
    "창가", "테라스", "정원", "도서관", "높은 곳", "탁 트인 곳", "아늑한 구석", "따뜻한 조명 아래",
    "남쪽 창가", "북쪽 조용한 방", "동쪽 베란다", "서쪽 서재", "분수대 근처", "고풍스러운 카페"
];

export interface LuckyInfoUnified {
    // East specific
    direction?: string;
    time?: string;
    energy?: string;
    // West specific
    color?: string;
    number?: string;
    place?: string;
}

export const getDailyLuckyInfoUnified = (mode: 'eastern' | 'western', seedKey: string): LuckyInfoUnified => {
    const now = new Date();
    const dateStr = `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;

    let hash = 0;
    const fullKey = dateStr + seedKey + (mode === 'eastern' ? "_east_v3" : "_west_v3");
    for (let i = 0; i < fullKey.length; i++) {
        hash = ((hash << 5) - hash) + fullKey.charCodeAt(i);
        hash |= 0;
    }
    const seed = Math.abs(hash);

    if (mode === 'eastern') {
        return {
            direction: LUCKY_DIRECTIONS[seed % LUCKY_DIRECTIONS.length],
            time: LUCKY_TIMES[(seed >> 2) % LUCKY_TIMES.length],
            energy: LUCKY_ENERGIES[(seed >> 4) % LUCKY_ENERGIES.length]
        };
    } else {
        return {
            color: LUCKY_COLORS[seed % LUCKY_COLORS.length].name,
            number: LUCKY_NUMBERS[(seed >> 2) % LUCKY_NUMBERS.length],
            place: LUCKY_PLACES_WESTERN[(seed >> 4) % LUCKY_PLACES_WESTERN.length]
        };
    }
};

// --- WESTERN DAILY FORTUNE ---



export const getDailyWesternFortune = (signName: string, score: number, category: string = 'today'): string => {
    const now = new Date();
    const dateStr = `${now.getFullYear()}-${now.getMonth() + 1}-${now.getDate()}`;

    let hash = 0;
    const key = dateStr + signName + category + "west_fortune_v3";
    for (let i = 0; i < key.length; i++) {
        hash = ((hash << 5) - hash) + key.charCodeAt(i);
        hash |= 0;
    }
    const seed = Math.abs(hash);

    // Use same category logic as Eastern for consistency
    let grade = "average";
    if (score >= 90) grade = "great";
    else if (score >= 75) grade = "good";
    else if (score >= 45) grade = "average";
    else grade = "bad";

    const catData = CATEGORY_FORTUNE_MESSAGES[category.toLowerCase()] || CATEGORY_FORTUNE_MESSAGES.today;
    const messages = catData[grade] || catData.average;
    const msgIndex = seed % messages.length;

    return messages[msgIndex];
};

export const getCurrentSunSign = (): { name: string; kor: string; icon: string; engName: string } => {
    const now = new Date();
    const month = now.getMonth() + 1;
    const day = now.getDate();

    if ((month === 3 && day >= 21) || (month === 4 && day <= 19)) return { name: "양자리", kor: "Aries", engName: "Aries", icon: "♈" };
    if ((month === 4 && day >= 20) || (month === 5 && day <= 20)) return { name: "황소자리", kor: "Taurus", engName: "Taurus", icon: "♉" };
    if ((month === 5 && day >= 21) || (month === 6 && day <= 21)) return { name: "쌍둥이자리", kor: "Gemini", engName: "Gemini", icon: "♊" };
    if ((month === 6 && day >= 22) || (month === 7 && day <= 22)) return { name: "게자리", kor: "Cancer", engName: "Cancer", icon: "♋" };
    if ((month === 7 && day >= 23) || (month === 8 && day <= 22)) return { name: "사자자리", kor: "Leo", engName: "Leo", icon: "♌" };
    if ((month === 8 && day >= 23) || (month === 9 && day <= 23)) return { name: "처녀자리", kor: "Virgo", engName: "Virgo", icon: "♍" };
    if ((month === 9 && day >= 24) || (month === 10 && day <= 22)) return { name: "천칭자리", kor: "Libra", engName: "Libra", icon: "♎" };
    if ((month === 10 && day >= 23) || (month === 11 && day <= 22)) return { name: "전갈자리", kor: "Scorpio", engName: "Scorpio", icon: "♏" };
    if ((month === 11 && day >= 23) || (month === 12 && day <= 24)) return { name: "사수자리", kor: "Sagittarius", engName: "Sagittarius", icon: "♐" };
    if ((month === 12 && day >= 25) || (month === 1 && day <= 19)) return { name: "염소자리", kor: "Capricorn", engName: "Capricorn", icon: "♑" };
    if ((month === 1 && day >= 20) || (month === 2 && day <= 18)) return { name: "물병자리", kor: "Aquarius", engName: "Aquarius", icon: "♒" };
    return { name: "물고기자리", kor: "Pisces", engName: "Pisces", icon: "♓" };
};
