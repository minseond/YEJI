export interface FortuneDetail {
    title: string;
    content: string;
}

export type FortuneCategory = 'total' | 'love' | 'wealth' | 'career' | 'health';

export interface FortuneTheme {
    primary: string;   // Main color (text-500)
    secondary: string; // Lighter accent (text-200)
    bgFrom: string;    // Gradient from
    bgTo: string;      // Gradient to
    pattern: string;   // Background pattern image path (optional)
    iconColor: string;
}

export interface FortuneData {
    id: string;
    category: FortuneCategory;
    summary: string;
    keywords: {
        text: string;
        desc: string; // Tooltip content
    }[];
    mainElement: string;
    mainElementDesc: string;
    details: FortuneDetail[];
    lucky: {
        color: string;
        number: string;
        item: string;
        direction?: string;
    };
}

export interface DualFortuneResult {
    eastern: FortuneData;
    western: FortuneData;
}

// --- DATA POOLS ---

const EASTERN_FORTUNES: FortuneData[] = [
    {
        id: 'e1',
        category: 'total',
        summary: "거대한 불길이 숲을 태우니, 새로운 싹이 돋아날 준비를 하는 형국입니다.",
        keywords: [
            { text: "열정", desc: "꺼지지 않는 마음의 불꽃" },
            { text: "변화", desc: "옛 허물을 벗고 새로 태어남" },
            { text: "시작", desc: "두려움 없는 첫 발걸음" },
            { text: "창의성", desc: "남들과 다른 독창적 시선" }
        ],
        mainElement: "병화(丙火)",
        mainElementDesc: "태양과 같은 밝고 강렬한 불의 기운",
        details: [
            {
                title: "총운",
                content: "당신의 사주는 한여름의 태양과 같습니다. 주변을 밝게 비추는 리더십이 타고났으나, 때로는 과한 열정이 독이 될 수 있습니다. 올해는 그 열정을 한 곳에 집중한다면 큰 성과를 거둘 수 있는 시기입니다."
            },
            {
                title: "재물운",
                content: "불이 금을 녹이는 형상이니, 노력한 만큼 재물이 쌓입니다. 다만 충동적인 소비는 불처럼 재산을 태워버릴 수 있으니 주의가 필요합니다."
            },
            {
                title: "연애운",
                content: "화려한 도화살이 들어와 이성에게 인기가 많은 시기입니다. 하지만 불꽃처럼 금방 타오르고 금방 꺼질 수 있으니, 은은한 촛불 같은 마음가짐이 필요합니다."
            }
        ],
        lucky: { color: "Deep Red", number: "7", item: "붉은색 장신구", direction: "남쪽" }
    },
    {
        id: 'e2',
        category: 'career',
        summary: "바위 틈 사이로 흐르는 맑은 물처럼, 장애물을 유연하게 피해가는 지혜가 돋보입니다.",
        keywords: [
            { text: "지혜", desc: "난관을 헤쳐나가는 슬기" },
            { text: "유연함", desc: "부드러움이 강함을 이긴다" },
            { text: "명예", desc: "드높아지는 이름" },
            { text: "이동", desc: "더 넓은 곳으로의 진출" }
        ],
        mainElement: "계수(癸水)",
        mainElementDesc: "끊임없이 흐르는 지혜로운 물의 기운",
        details: [
            {
                title: "직업운",
                content: "막힘이 있어도 결국은 바다로 흘러가는 물처럼, 지금의 어려움은 훗날의 큰 성취를 위한 과정입니다. 기획이나 영업 등 유동적인 업무에서 두각을 나타낼 것입니다."
            },
            {
                title: "성취",
                content: "작은 물방울이 모여 바위를 뚫듯, 꾸준함이 당신의 가장 큰 무기입니다. 단기간의 성과보다는 장기적인 안목으로 프로젝트를 추진하세요."
            },
            {
                title: "조언",
                content: "고인 물은 썩기 마련입니다. 끊임없이 새로운 지식을 습득하고 변화를 두려워하지 마세요."
            }
        ],
        lucky: { color: "Navy", number: "1", item: "만년필", direction: "북쪽" }
    },
    {
        id: 'e3',
        category: 'wealth',
        summary: "황금 들판에 곡식이 무르익으니, 곳간을 넓혀야 할 풍요로운 시기입니다.",
        keywords: [
            { text: "풍요", desc: "넘쳐나는 재화와 곡식" },
            { text: "결실", desc: "노력에 대한 정당한 보상" },
            { text: "안정", desc: "흔들리지 않는 편안함" },
            { text: "투자", desc: "미래를 위한 씨앗 뿌리기" }
        ],
        mainElement: "기토(己土)",
        mainElementDesc: "만물을 길러내는 비옥한 흙의 기운",
        details: [
            {
                title: "재물운",
                content: "흙이 금을 품고 있는 형상입니다. 뜻밖의 횡재보다는 정당한 노력의 대가로 재물이 모입니다. 부동산이나 토지 관련 운이 매우 좋습니다."
            },
            {
                title: "사업운",
                content: "기반이 탄탄하니 확장을 꾀해도 좋습니다. 믿을 수 있는 사람들과의 협업이 큰 이익을 가져다 줄 것입니다."
            },
            {
                title: "관리",
                content: "들어오는 것보다 지키는 것이 중요합니다. 알뜰하게 관리하면 자손 대대로 이어질 부를 축적할 수 있습니다."
            }
        ],
        lucky: { color: "Yellow Ochre", number: "5", item: "도자기", direction: "중앙" }
    },
    {
        id: 'e4',
        category: 'love',
        summary: "봄바람에 벚꽃이 흩날리듯, 설레는 인연이 당신의 문을 두드립니다.",
        keywords: [
            { text: "설렘", desc: "가슴 뛰는 새로운 만남" },
            { text: "매력", desc: "주변을 끌어당기는 힘" },
            { text: "인연", desc: "하늘이 맺어준 사이" },
            { text: "화합", desc: "서로 다름을 이해하는 마음" }
        ],
        mainElement: "을목(乙木)",
        mainElementDesc: "부드럽고 끈질긴 생명력을 가진 화초",
        details: [
            {
                title: "애정운",
                content: "도화살이 강하게 들어와 어디를 가나 주목받는 시기입니다. 솔로라면 운명의 상대를 만날 확률이 높으며, 커플이라면 관계가 한층 깊어질 것입니다."
            },
            {
                title: "매력 포인트",
                content: "당신의 상냥하고 부드러운 말씨가 상대방의 마음을 사로잡습니다. 꾸밈없는 솔직함이 최고의 무기입니다."
            },
            {
                title: "주의",
                content: "지나친 배려는 오히려 오해를 살 수 있습니다. 때로는 자신의 감정을 확실하게 표현하는 것이 관계 발전에 도움이 됩니다."
            }
        ],
        lucky: { color: "Pink", number: "3", item: "향수", direction: "동쪽" }
    }
];

const WESTERN_FORTUNES: FortuneData[] = [
    {
        id: 'w1',
        category: 'total',
        summary: "목성이 당신의 지평을 넓혀주고, 토성은 구조적인 안정을 요구합니다.",
        keywords: [
            { text: "확장", desc: "한계를 뛰어넘는 성장" },
            { text: "규율", desc: "자제력이 가져다주는 힘" },
            { text: "비전", desc: "보이지 않는 미래를 보는 눈" },
            { text: "조화", desc: "모든 것의 균형" }
        ],
        mainElement: "물병자리 태양",
        mainElementDesc: "카리스마 넘치는 존재감과 비전 있는 마인드",
        details: [
            {
                title: "종합 운세",
                content: "명왕성이 당신의 1하우스로 이동하면서 내면의 깊은 변화가 시작되고 있습니다. 낡은 껍질을 벗어던지고 더 강인한 자신의 모습으로 거듭나는 시기입니다. 미지의 세계를 받아들이세요."
            },
            {
                title: "직업 & 야망",
                content: "직업 영역에 들어온 화성이 당신에게 과감한 도전을 종용합니다. 올해의 성공 열쇠는 '혁신'입니다. 파격적인 아이디어를 제안하는 것을 두려워하지 마세요."
            },
            {
                title: "사랑 & 관계",
                content: "금성이 파트너십 구역에서 역행하며 해결되지 않은 문제들을 다시 돌아보게 합니다. 영혼의 단짝과도 같은 인연이 과거의 사회적 관계에서 나타날 수 있습니다."
            }
        ],
        lucky: { color: "Electric Blue", number: "11", item: "자수정" }
    },
    {
        id: 'w2',
        category: 'career',
        summary: "10하우스의 토성이 당신의 권위와 명성을 공고히 합니다.",
        keywords: [
            { text: "권위", desc: "자연스럽게 따르는 존경" },
            { text: "구조", desc: "탄탄한 기반 위에 짓는 집" },
            { text: "유산", desc: "오래도록 남을 업적" },
            { text: "집중", desc: "목표를 향한 흔들림 없는 시선" }
        ],
        mainElement: "염소자리 MC",
        mainElementDesc: "야망 있고 규율 잡힌 등산가",
        details: [
            {
                title: "직업적 경로",
                content: "당신의 노력이 드디어 결실을 맺고 있습니다. 상사나 윗사람으로부터의 인정이 임박했습니다. 승진을 요구하거나 더 많은 책임을 맡기에 완벽한 타이밍입니다."
            },
            {
                title: "도전 과제",
                content: "번아웃을 조심하세요. 당신의 추진력은 존경받아 마땅하지만, 기계도 정비가 필요한 법입니다. 효율성을 유지하기 위해 휴식 시간을 일정에 꼭 포함하세요."
            },
            {
                title: "전략",
                content: "즉각적인 승리보다는 장기적인 계획이 유리합니다. 벽돌 한 장 한 장을 쌓아 당신만의 제국을 건설하세요."
            }
        ],
        lucky: { color: "Charcoal Grey", number: "8", item: "플래너" }
    },
    {
        id: 'w3',
        category: 'wealth',
        summary: "2하우스에 머무는 금성이 풍요과 럭셔리를 끌어당깁니다.",
        keywords: [
            { text: "풍요", desc: "강물처럼 흐르는 번영" },
            { text: "럭셔리", desc: "더 나은 것을 누리는 기쁨" },
            { text: "가치", desc: "진정한 가치를 알아보는 눈" },
            { text: "매력", desc: "기회를 자연스럽게 끌어당김" }
        ],
        mainElement: "황소자리 달",
        mainElementDesc: "물질적 편안함에서 오는 정서적 안정",
        details: [
            {
                title: "재정 전망",
                content: "지금은 돈이 쉽게 들어오는 시기입니다. 예술, 미용, 부동산 투자가 유리합니다. 당신의 미적 감각을 믿으세요."
            },
            {
                title: "소비 습관",
                content: "편안함을 주는 물건에 돈을 쓰고 싶은 충동이 들 수 있습니다. 자신을 위한 선물은 좋지만, 감정적인 지출이 되지 않도록 주의하세요."
            },
            {
                title: "팁",
                content: "자산을 다시 점검해보세요. 이미 소유하고 있는 것 중에 가치가 크게 오른 것이 있을 수 있습니다."
            }
        ],
        lucky: { color: "Emerald Green", number: "6", item: "동전" }
    },
    {
        id: 'w4',
        category: 'love',
        summary: "해왕성이 꿈같은 마법을 부려 로맨스를 동화처럼 만듭니다.",
        keywords: [
            { text: "로맨스", desc: "가장 순수한 형태의 사랑" },
            { text: "꿈", desc: "소망을 현실로 이루는 힘" },
            { text: "교감", desc: "영혼과 영혼의 깊은 대화" },
            { text: "환상", desc: "단조로운 일상에서의 탈출" }
        ],
        mainElement: "물고기자리 금성",
        mainElementDesc: "조건 없는 사랑과 무한한 공감",
        details: [
            {
                title: "애정운",
                content: "장밋빛 안경을 쓰고 세상을 보는 시기이지만, 지금은 그래도 괜찮습니다. 시적이고 다정한 순간들을 즐기세요. 창의적인 파트너가 나타날 수 있습니다."
            },
            {
                title: "친밀감",
                content: "감정적인 취약함을 드러낼수록 유대감이 강해집니다. 진심을 숨기지 마세요. 그것이 당신의 가장 큰 강점입니다."
            },
            {
                title: "주의사항",
                content: "타인을 기쁘게 하기 위해 자신의 욕구를 희생하지 않도록 하세요. 깊은 사랑 안에서도 건강한 경계선은 필요합니다."
            }
        ],
        lucky: { color: "Seafoam Green", number: "2", item: "진주" }
    }
];

// --- THEME DATA ---
// NOTE: Colors should be Tailwind class compatible or hex codes
export const THEMES: Record<FortuneCategory, FortuneTheme> = {
    total: {
        primary: 'text-amber-500',
        secondary: 'text-amber-200',
        bgFrom: 'from-amber-900/20',
        bgTo: 'to-black',
        pattern: 'pattern_oriental.png',
        iconColor: 'text-amber-500'
    },
    love: {
        primary: 'text-rose-500',
        secondary: 'text-rose-200',
        bgFrom: 'from-rose-900/20',
        bgTo: 'to-black',
        pattern: 'pattern_hearts.png', // Hypothetical
        iconColor: 'text-rose-400'
    },
    wealth: {
        primary: 'text-yellow-500',
        secondary: 'text-yellow-200',
        bgFrom: 'from-yellow-900/20',
        bgTo: 'to-black',
        pattern: 'pattern_coins.png',
        iconColor: 'text-yellow-400'
    },
    career: {
        primary: 'text-blue-500',
        secondary: 'text-blue-200',
        bgFrom: 'from-blue-900/20',
        bgTo: 'to-black',
        pattern: 'pattern_geometric.png',
        iconColor: 'text-blue-400'
    },
    health: {
        primary: 'text-emerald-500',
        secondary: 'text-emerald-200',
        bgFrom: 'from-emerald-900/20',
        bgTo: 'to-black',
        pattern: 'pattern_leaves.png',
        iconColor: 'text-emerald-400'
    }
};


// --- UTILITY ---

export const getRandomFortune = (): DualFortuneResult => {
    // Simple random selection
    const eastern = EASTERN_FORTUNES[Math.floor(Math.random() * EASTERN_FORTUNES.length)];
    const western = WESTERN_FORTUNES[Math.floor(Math.random() * WESTERN_FORTUNES.length)];

    return { eastern, western };
};
