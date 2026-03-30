import type {
    DualFortuneResultV2,
    SajuElement,
    WesternElement,
    WesternKeyword
} from './types';

// Mock Data Generators

const getMockSajuStats = () => ({
    cheongan_jiji: {
        summary: "천간과 지지가 조화를 이루고 있습니다.",
        year: { cheon_gan: "갑", ji_ji: "진" },
        month: { cheon_gan: "을", ji_ji: "사" },
        day: { cheon_gan: "병", ji_ji: "오" },
        hour: { cheon_gan: "정", ji_ji: "미" }
    },
    five_elements: {
        summary: "화(Fire) 기운이 다소 강한 편입니다.",
        elements_list: [
            { code: "wood", label: "목", percent: 20 },
            { code: "fire", label: "화", percent: 40 },
            { code: "earth", label: "토", percent: 20 },
            { code: "metal", label: "금", percent: 10 },
            { code: "water", label: "수", percent: 10 }
        ] as SajuElement[]
    },
    yin_yang_ratio: {
        summary: "양의 기운이 활발합니다.",
        yin: 40,
        yang: 60
    },
    ten_gods: {
        summary: "비견과 식신이 발달하여 활동적입니다.",
        gods_list: [
            { code: "bijyeon", label: "비견", percent: 30 },
            { code: "siksin", label: "식신", percent: 25 },
            { code: "pyeonjae", label: "편재", percent: 15 },
            { code: "jeongguan", label: "정관", percent: 20 },
            { code: "insoo", label: "인수", percent: 10 }
        ] as SajuElement[]
    }
});

const getMockWesternStats = () => ({
    main_sign: { name: "Aquarius" },
    element_summary: "Air elements dominate, suggesting intellectual agility.",
    element_4_distribution: [
        { code: "fire", label: "Fire", percent: 25 },
        { code: "earth", label: "Earth", percent: 20 },
        { code: "air", label: "Air", percent: 40 },
        { code: "water", label: "Water", percent: 15 }
    ] as WesternElement[],
    modality_summary: "Fixed modality provides determination.",
    modality_3_distribution: [
        { code: "cardinal", label: "Cardinal", percent: 30 },
        { code: "fixed", label: "Fixed", percent: 50 },
        { code: "mutable", label: "Mutable", percent: 20 }
    ] as WesternElement[],
    keywords_summary: "Innovation and independence are key themes.",
    keywords: [
        { code: "innovation", label: "Innovation", weight: 90 },
        { code: "independence", label: "Independence", weight: 85 },
        { code: "humanitarian", label: "Humanitarian", weight: 80 }
    ] as WesternKeyword[]
});

export const getRandomFortuneV2 = (): DualFortuneResultV2 => {
    return {
        eastern: {
            score: 85,
            element: "Fire",
            chart: {
                summary: "Year of the Wood Dragon.",
                year: { gan: "Gap", ji: "Jin", element_code: "wood" },
                month: { gan: "Eul", ji: "Sa", element_code: "fire" },
                day: { gan: "Byeong", ji: "O", element_code: "fire" },
                hour: { gan: "Jeong", ji: "Mi", element_code: "earth" }
            },
            stats: getMockSajuStats(),
            final_verdict: {
                summary: "Activity and passion will lead to good results.",
                strength: "Strong drive and creativity.",
                weakness: "Tendency to be impulsive.",
                advice: "Balance your passion with patience."
            },
            lucky: {
                color: "Red",
                number: "7",
                item: "Gold Ring",
                direction: "South",
                place: "Cafe"
            }
        },
        western: {
            score: 88,
            element: "Air",
            stats: getMockWesternStats(),
            fortune_content: {
                overview: "A day full of sudden insights and social connections.",
                detailed_analysis: [
                    { title: "Love", content: "Unexpected encounters may occur." },
                    { title: "Career", content: "Good for brainstorming new ideas." }
                ],
                advice: "Stay open to new perspectives."
            },
            lucky: {
                color: "Electric Blue",
                number: "11",
                item: "Amethyst",
                place: "High places"
            }
        }
    };
};

export const getMockDailyFortune = (type: string, topic: string) => {
    // Generate context-aware mock data based on topic
    let eastSummary = "";
    let westSummary = "";
    let eastDetails = "";
    let westDetails = "";
    let keywords: string[] = [];

    if (topic === 'love') {
        eastSummary = "도화살이 강하게 들어오는 날입니다. 새로운 인연을 기대해보세요.";
        westSummary = "Venus favors your sign today. Romantic energies are high.";
        eastDetails = "오늘은 이성운이 매우 좋습니다. 평소 마음에 두던 사람에게 연락을 해보거나, 새로운 모임에 나가는 것을 추천합니다. 당신의 매력이 돋보이는 하루가 될 것입니다.";
        westDetails = "Love is in the air. Existing relationships deepen, and singles might find a sparking connection. Be open to expressing your feelings.";
        keywords = ["설렘", "인연", "매력", "Romance", "Passion"];
    } else if (topic === 'wealth') {
        eastSummary = "재물운이 따르는 하루입니다. 투자를 고려해보세요.";
        westSummary = "Jupiter brings expansion to your finances.";
        eastDetails = "정재와 편재가 조화롭게 들어와 금전적인 이득을 취하기 좋은 날입니다. 뜻밖의 수입이 생기거나, 투자했던 곳에서 좋은 소식이 들려올 수 있습니다.";
        westDetails = "A good day for financial planning or taking calculated risks. Opportunities for growth are abundant.";
        keywords = ["이득", "투자", "행운", "Growth", "Prosperity"];
    } else if (topic === 'career') {
        eastSummary = "직장에서 능력을 인정받을 기회가 옵니다.";
        westSummary = "Saturn rewards your hard work and discipline.";
        eastDetails = "관운이 들어와 승진이나 취업에 유리한 기운이 작용합니다. 맡은 업무에서 성과를 내어 윗사람에게 칭찬을 받을 수 있습니다. 적극적으로 나서세요.";
        westDetails = "Your professional reputation is highlighted. Focus on long-term goals and demonstrate your reliability.";
        keywords = ["성취", "인정", "기회", "Success", "Ambition"];
    } else if (topic === 'health') {
        eastSummary = "컨디션 조절이 필요한 하루입니다. 휴식을 취하세요.";
        westSummary = "Mars indicates high energy, but watch out for burnout.";
        eastDetails = "일간이 다소 약해져 있어 피로를 쉽게 느낄 수 있습니다. 무리한 운동보다는 가벼운 산책이나 명상이 좋습니다. 충분한 수면을 취하세요.";
        westDetails = "Physical energy is high, but direct it wisely. Avoid stress and prioritize self-care routines.";
        keywords = ["휴식", "건강", "밸런스", "Vitality", "Self-care"];
    } else if (topic === 'academic') {
        eastSummary = "학업에 집중하기 최상의 날입니다. 머리가 맑아집니다.";
        westSummary = "Mercury sharpens your mind and communication skills.";
        eastDetails = "인수가 강하게 들어와 학문이나 연구에 몰입하기 좋은 날입니다. 어려운 문제도 쉽게 풀리고, 새로운 지식을 습득하는 데 효율이 높습니다.";
        westDetails = "Ideal for studying, writing, or learning new skills. Your mental clarity is at its peak.";
        keywords = ["집중", "지혜", "성장", "Focus", "Intellect"];
    } else {
        eastSummary = "평온하고 무난한 하루가 예상됩니다.";
        westSummary = "The stars align to bring you balance and harmony.";
        eastDetails = "특별한 사고 없이 물 흐르듯 유연하게 보낼 수 있는 하루입니다. 주변 사람들과의 관계도 원만하며, 소소한 행복을 느낄 수 있습니다.";
        westDetails = "A balanced day suitable for reflection and maintaining stability. Enjoy the calm moments.";
        keywords = ["평화", "안정", "조화", "Peace", "Harmony"];
    }

    return {
        session_id: "mock_session_123",
        category: "GENERAL",
        fortune_type: "DAILY",
        east: {
            fortune: {
                character: "CHEONGWOON",
                score: Math.floor(Math.random() * 20) + 80, // 80-99
                one_line: eastSummary,
                keywords: keywords.slice(0, 3),
                detail: eastDetails
            }
        },
        west: {
            fortune: {
                character: "STELLA",
                score: Math.floor(Math.random() * 20) + 80, // 80-99
                one_line: westSummary,
                keywords: keywords.slice(2, 5),
                detail: westDetails
            }
        }
    };
};
