// Tarot Card Database - Major Arcana (22 Cards)

export interface TarotCard {
    id: string;
    number: number;
    name: string;
    nameEn: string;
    category: 'major' | 'minor';
    imagePath: string;
    uprightMeaning: string;
    reversedMeaning: string;
    uprightKeywords: string[];
    reversedKeywords: string[];
}

export const MAJOR_ARCANA: TarotCard[] = [
    {
        id: 'major-0-fool',
        number: 0,
        name: '바보',
        nameEn: 'The Fool',
        category: 'major',
        imagePath: '메이저/0. 바보 카드.jpg',
        uprightMeaning: '새로운 시작, 순수한 가능성, 자유로운 영혼을 상징합니다. 당신은 두려움 없이 새로운 여정을 시작할 준비가 되어 있습니다. 순수한 열정과 호기심이 당신을 이끌 것입니다. 과거의 제약에서 벗어나 자유롭게 탐험하세요.',
        reversedMeaning: '무모함, 경솔한 결정, 준비 부족을 의미합니다. 너무 서두르거나 위험을 간과하고 있을 수 있습니다. 현실을 직시하지 않고 맹목적으로 나아가는 것은 위험합니다. 신중하게 계획을 세우고 준비하세요.',
        uprightKeywords: ['새로운 시작', '순수함', '자유', '모험'],
        reversedKeywords: ['무모함', '경솔함', '준비 부족', '위험']
    },
    {
        id: 'major-1-magician',
        number: 1,
        name: '마법사',
        nameEn: 'The Magician',
        category: 'major',
        imagePath: '메이저/1. 마법사 카드.jpg',
        uprightMeaning: '창조력, 의지력, 능력의 현현을 뜻합니다. 당신은 목표를 달성하는 데 필요한 모든 도구와 능력을 갖추고 있습니다. 창의력과 집중력이 최고조에 달했으며, 원하는 것을 현실로 만들 수 있는 시기입니다. 자신감을 가지고 행동하세요.',
        reversedMeaning: '재능의 낭비, 조작, 속임수를 나타냅니다. 능력이 있음에도 불구하고 올바르게 사용하지 못하고 있습니다. 거짓말이나 조작으로 목표를 이루려 하거나, 자신의 재능을 과신하고 있을 수 있습니다.',
        uprightKeywords: ['창조력', '의지력', '능력', '자신감'],
        reversedKeywords: ['조작', '거짓', '재능 낭비', '과신']
    },
    {
        id: 'major-2-high-priestess',
        number: 2,
        name: '여사제',
        nameEn: 'The High Priestess',
        category: 'major',
        imagePath: '메이저/2. 여사제 카드.jpg',
        uprightMeaning: '직관, 내면의 지혜, 신비를 상징합니다. 당신의 내면의 목소리에 귀를 기울이세요. 표면 아래 숨겨진 진실이 있으며, 직관이 당신을 올바른 방향으로 이끌 것입니다. 조용히 명상하고 내면의 지혜를 신뢰하세요.',
        reversedMeaning: '직관 무시, 비밀, 숨겨진 의도를 나타냅니다. 내면의 목소리를 듣지 않고 외부의 소음에만 집중하고 있습니다. 중요한 정보가 숨겨져 있거나, 자신의 본능을 억압하고 있을 수 있습니다.',
        uprightKeywords: ['직관', '지혜', '신비', '내면'],
        reversedKeywords: ['직관 무시', '비밀', '억압', '혼란']
    },
    {
        id: 'major-3-empress',
        number: 3,
        name: '여황제',
        nameEn: 'The Empress',
        category: 'major',
        imagePath: '메이저/3. 여황제 카드.jpg',
        uprightMeaning: '풍요, 창조성, 자연의 아름다움을 상징합니다. 당신의 삶에 풍요와 번영이 찾아올 것입니다. 양육하고 돌보는 에너지가 강하며, 창조적인 프로젝트가 결실을 맺을 시기입니다. 자연과 아름다움을 즐기세요.',
        reversedMeaning: '창조력 부족, 의존, 과잉 보호를 의미합니다. 스스로를 돌보지 못하거나 타인에게 지나치게 의존하고 있습니다. 창조적인 에너지가 막혀 있거나, 지나친 통제로 성장을 방해하고 있을 수 있습니다.',
        uprightKeywords: ['풍요', '창조성', '양육', '번영'],
        reversedKeywords: ['의존', '과잉보호', '창조력 부족', '막힘']
    },
    {
        id: 'major-4-emperor',
        number: 4,
        name: '황제',
        nameEn: 'The Emperor',
        category: 'major',
        imagePath: '메이저/4. 황제 카드.jpg',
        uprightMeaning: '권위, 구조, 리더십을 상징합니다. 당신은 상황을 통제하고 질서를 세울 능력이 있습니다. 명확한 규칙과 구조를 통해 목표를 달성할 것입니다. 책임감과 리더십을 발휘하세요.',
        reversedMeaning: '독재, 경직성, 통제 부족을 나타냅니다. 지나치게 엄격하거나 독단적이 되어 주변 사람들을 억압하고 있습니다. 또는 반대로 필요한 규율과 구조가 부족할 수 있습니다.',
        uprightKeywords: ['권위', '리더십', '구조', '안정'],
        reversedKeywords: ['독재', '경직', '억압', '무질서']
    },
    {
        id: 'major-5-hierophant',
        number: 5,
        name: '교황',
        nameEn: 'The Hierophant',
        category: 'major',
        imagePath: '메이저/5. 교황 카드.jpg',
        uprightMeaning: '전통, 교육, 영적 지도를 상징합니다. 전통적인 방법과 가르침이 도움이 될 것입니다. 멘토나 스승의 조언을 구하거나, 기존의 시스템 안에서 안정을 찾으세요. 영적 성장의 시기입니다.',
        reversedMeaning: '반항, 비순응, 독단주의를 의미합니다. 기존의 규칙과 전통에 반발하거나, 새로운 방법을 추구하고 있습니다. 또는 경직된 사고방식에 갇혀 변화를 거부하고 있을 수 있습니다.',
        uprightKeywords: ['전통', '교육', '영적 지도', '순응'],
        reversedKeywords: ['반항', '비순응', '독단', '경직']
    },
    {
        id: 'major-6-lovers',
        number: 6,
        name: '연인',
        nameEn: 'The Lovers',
        category: 'major',
        imagePath: '메이저/6. 연인 카드.jpg',
        uprightMeaning: '사랑, 조화, 중요한 선택을 상징합니다. 깊은 유대감과 완벽한 조화를 경험할 것입니다. 중요한 관계나 결정의 기로에 서 있으며, 마음과 가치관이 일치하는 선택을 해야 합니다.',
        reversedMeaning: '불균형, 잘못된 선택, 불화를 나타냅니다. 관계에서 조화가 깨지거나 가치관의 충돌이 있습니다. 중요한 선택을 미루거나 잘못된 판단을 할 위험이 있습니다.',
        uprightKeywords: ['사랑', '조화', '선택', '유대'],
        reversedKeywords: ['불화', '잘못된 선택', '불균형', '갈등']
    },
    {
        id: 'major-7-chariot',
        number: 7,
        name: '전차',
        nameEn: 'The Chariot',
        category: 'major',
        imagePath: '메이저/7. 전차 카드.jpg',
        uprightMeaning: '의지, 승리, 전진을 상징합니다. 당신의 결단력과 집중력이 승리를 가져올 것입니다. 상반된 힘을 조화롭게 통제하며 목표를 향해 나아가세요. 자신감을 가지고 전진하세요.',
        reversedMeaning: '통제 상실, 방향 상실, 좌절을 의미합니다. 상황이 통제 불능 상태이거나 명확한 방향을 잃었습니다. 서로 다른 욕구나 목표 사이에서 갈등하고 있을 수 있습니다.',
        uprightKeywords: ['의지', '승리', '통제', '전진'],
        reversedKeywords: ['통제 상실', '방향 상실', '좌절', '갈등']
    },
    {
        id: 'major-8-strength',
        number: 8,
        name: '힘',
        nameEn: 'Strength',
        category: 'major',
        imagePath: '메이저/8. 힘 카드.jpg',
        uprightMeaning: '내면의 힘, 용기, 인내를 상징합니다. 부드러움과 연민으로 어려움을 극복할 수 있습니다. 물리적 힘이 아닌 내면의 강인함과 자제력이 필요한 시기입니다. 인내심을 가지세요.',
        reversedMeaning: '자신감 부족, 자제력 상실, 나약함을 나타냅니다. 내면의 두려움이나 의심에 지배당하고 있습니다. 감정을 통제하지 못하거나 필요한 용기가 부족할 수 있습니다.',
        uprightKeywords: ['내면의 힘', '용기', '인내', '연민'],
        reversedKeywords: ['나약함', '자신감 부족', '자제력 상실', '두려움']
    },
    {
        id: 'major-9-hermit',
        number: 9,
        name: '은둔자',
        nameEn: 'The Hermit',
        category: 'major',
        imagePath: '메이저/9. 은둔자 카드.jpg',
        uprightMeaning: '성찰, 고독, 내면의 탐구를 상징합니다. 혼자만의 시간을 통해 진정한 자아를 발견할 것입니다. 외부의 소음에서 벗어나 내면을 들여다보고 영적 성장을 추구하세요.',
        reversedMeaning: '고립, 외로움, 회피를 의미합니다. 건강한 성찰이 아닌 세상으로부터의 도피입니다. 지나친 고독이 우울과 고립으로 이어지거나, 필요한 내면의 성찰을 회피하고 있을 수 있습니다.',
        uprightKeywords: ['성찰', '지혜', '내면 탐구', '고독'],
        reversedKeywords: ['고립', '외로움', '회피', '우울']
    },
    {
        id: 'major-10-wheel',
        number: 10,
        name: '운명의 수레바퀴',
        nameEn: 'Wheel of Fortune',
        category: 'major',
        imagePath: '메이저/10. 운명의 수레바퀴.jpg',
        uprightMeaning: '운명의 전환, 행운, 변화의 순환을 상징합니다. 긍정적인 변화와 새로운 기회가 찾아올 것입니다. 인생의 흐름을 받아들이고 변화에 적응하세요. 행운의 시기입니다.',
        reversedMeaning: '불운, 저항, 부정적 순환을 나타냅니다. 불운한 시기를 겪고 있거나 변화에 저항하고 있습니다. 같은 실수를 반복하거나 부정적인 패턴에 갇혀 있을 수 있습니다.',
        uprightKeywords: ['행운', '변화', '전환점', '순환'],
        reversedKeywords: ['불운', '저항', '부정적 패턴', '정체']
    },
    {
        id: 'major-11-justice',
        number: 11,
        name: '정의',
        nameEn: 'Justice',
        category: 'major',
        imagePath: '메이저/11. 정의 카드.jpg',
        uprightMeaning: '공정성, 진실, 균형을 상징합니다. 공정한 판단과 정의로운 결과를 얻을 것입니다. 진실이 밝혀지고 정당한 보상을 받을 시기입니다. 올바른 선택을 하세요.',
        reversedMeaning: '불공정, 편견, 불균형을 의미합니다. 부당한 대우를 받거나 편향된 판단이 내려질 수 있습니다. 자신의 행동에 대한 책임을 회피하거나 진실을 외면하고 있을 수 있습니다.',
        uprightKeywords: ['공정', '진실', '균형', '책임'],
        reversedKeywords: ['불공정', '편견', '불균형', '회피']
    },
    {
        id: 'major-12-hanged-man',
        number: 12,
        name: '매달린 사람',
        nameEn: 'The Hanged Man',
        category: 'major',
        imagePath: '메이저/12. 행맨 카드.jpg',
        uprightMeaning: '희생, 새로운 관점, 멈춤을 상징합니다. 잠시 멈추고 다른 시각에서 상황을 바라보세요. 의도적인 희생이나 양보가 더 큰 깨달음을 가져올 것입니다.',
        reversedMeaning: '무의미한 희생, 저항, 정체를 나타냅니다. 불필요한 희생으로 시간을 낭비하고 있습니다. 변화를 거부하거나 새로운 관점을 받아들이지 못하고 있을 수 있습니다.',
        uprightKeywords: ['희생', '새 관점', '멈춤', '깨달음'],
        reversedKeywords: ['무의미한 희생', '저항', '정체', '거부']
    },
    {
        id: 'major-13-death',
        number: 13,
        name: '죽음',
        nameEn: 'Death',
        category: 'major',
        imagePath: '메이저/13. 죽음 카드.jpg',
        uprightMeaning: '변화, 종결, 재탄생을 상징합니다. 오래된 것이 끝나고 새로운 시작이 찾아옵니다. 두려워하지 말고 자연스러운 변화를 받아들이세요. 진정한 변화는 성장을 가져올 것입니다.',
        reversedMeaning: '변화 저항, 정체, 끝나지 않는 것을 의미합니다. 필요한 변화를 거부하거나 끝내야 할 것을 붙잡고 있습니다. 과거에 집착하여 앞으로 나아가지 못하고 있습니다.',
        uprightKeywords: ['변화', '종결', '재탄생', '해방'],
        reversedKeywords: ['저항', '정체', '집착', '거부']
    },
    {
        id: 'major-14-temperance',
        number: 14,
        name: '절제',
        nameEn: 'Temperance',
        category: 'major',
        imagePath: '메이저/14. 절제 카드.jpg',
        uprightMeaning: '균형, 조화, 인내를 상징합니다. 극단을 피하고 중용의 길을 걸으세요. 서로 다른 요소들을 조화롭게 혼합하여 완벽한 균형을 찾을 것입니다. 인내심을 가지세요.',
        reversedMeaning: '불균형, 과잉, 극단을 나타냅니다. 삶의 균형이 깨지고 한쪽으로 치우쳐 있습니다. 극단적인 행동이나 조급함으로 조화를 해치고 있을 수 있습니다.',
        uprightKeywords: ['균형', '조화', '인내', '중용'],
        reversedKeywords: ['불균형', '과잉', '극단', '조급함']
    },
    {
        id: 'major-15-devil',
        number: 15,
        name: '악마',
        nameEn: 'The Devil',
        category: 'major',
        imagePath: '메이저/15. 악마 카드.jpg',
        uprightMeaning: '속박, 유혹, 물질주의를 상징합니다. 중독이나 집착에 사로잡혀 있을 수 있습니다. 하지만 쇠사슬은 느슨하며, 벗어날 수 있습니다. 자신을 가두는 것이 무엇인지 인식하세요.',
        reversedMeaning: '해방, 자유, 깨달음을 의미합니다. 오랜 중독이나 집착에서 벗어나고 있습니다. 진정한 자유를 향해 나아가며, 자신을 속박하던 것들을 극복하고 있습니다.',
        uprightKeywords: ['속박', '유혹', '중독', '집착'],
        reversedKeywords: ['해방', '자유', '극복', '깨달음']
    },
    {
        id: 'major-16-tower',
        number: 16,
        name: '탑',
        nameEn: 'The Tower',
        category: 'major',
        imagePath: '메이저/16. 타워 카드.jpg',
        uprightMeaning: '급격한 변화, 파괴, 깨달음을 상징합니다. 예상치 못한 충격적인 사건이 일어날 것입니다. 하지만 이는 거짓된 기반을 무너뜨리고 진실을 드러내는 과정입니다. 파괴 후에는 재건이 옵니다.',
        reversedMeaning: '변화 회피, 재앙 방지, 점진적 붕괴를 나타냅니다. 필요한 변화를 피하려 하거나, 큰 충격을 완화하고 있습니다. 또는 천천히 무너지는 상황을 경험하고 있을 수 있습니다.',
        uprightKeywords: ['급변', '파괴', '충격', '진실'],
        reversedKeywords: ['회피', '점진적 붕괴', '방지', '저항']
    },
    {
        id: 'major-17-star',
        number: 17,
        name: '별',
        nameEn: 'The Star',
        category: 'major',
        imagePath: '메이저/17. 별 카드.jpg',
        uprightMeaning: '희망, 치유, 영감을 상징합니다. 어두운 시기가 지나고 밝은 미래가 기다리고 있습니다. 희망을 잃지 마세요. 당신의 꿈과 목표는 반드시 이루어질 것입니다. 치유의 시간입니다.',
        reversedMeaning: '절망, 신념 상실, 낙담을 의미합니다. 희망을 잃고 미래가 어둡게만 보입니다. 자신감과 믿음이 부족하며, 꿈을 포기하고 싶은 마음이 들 수 있습니다.',
        uprightKeywords: ['희망', '치유', '영감', '낙관'],
        reversedKeywords: ['절망', '낙담', '신념 상실', '어둠']
    },
    {
        id: 'major-18-moon',
        number: 18,
        name: '달',
        nameEn: 'The Moon',
        category: 'major',
        imagePath: '메이저/18. 달 카드.jpg',
        uprightMeaning: '환상, 직관, 무의식을 상징합니다. 모든 것이 명확하지 않으며 혼란스러울 수 있습니다. 직관을 믿되, 환상과 현실을 구분하세요. 숨겨진 진실이 드러날 것입니다.',
        reversedMeaning: '명료함, 진실 발견, 공포 극복을 나타냅니다. 혼란이 걷히고 진실이 밝혀집니다. 두려움과 환상에서 벗어나 현실을 직시하고 있습니다.',
        uprightKeywords: ['환상', '직관', '무의식', '혼란'],
        reversedKeywords: ['명료함', '진실', '공포 극복', '해소']
    },
    {
        id: 'major-19-sun',
        number: 19,
        name: '태양',
        nameEn: 'The Sun',
        category: 'major',
        imagePath: '메이저/19. 태양 카드.jpg',
        uprightMeaning: '기쁨, 성공, 활력을 상징합니다. 모든 것이 밝고 긍정적입니다. 성공과 행복이 당신을 기다리고 있으며, 삶의 단순한 기쁨을 즐길 시기입니다. 자신감 넘치게 빛나세요.',
        reversedMeaning: '우울, 실패, 활력 부족을 의미합니다. 기쁨을 느끼기 어렵고 에너지가 부족합니다. 긍정적인 면을 보지 못하거나 성공을 완전히 즐기지 못하고 있습니다.',
        uprightKeywords: ['기쁨', '성공', '활력', '긍정'],
        reversedKeywords: ['우울', '실패', '에너지 부족', '비관']
    },
    {
        id: 'major-20-judgement',
        number: 20,
        name: '심판',
        nameEn: 'Judgement',
        category: 'major',
        imagePath: '메이저/20. 심판 카드.jpg',
        uprightMeaning: '각성, 재생, 내면의 부름을 상징합니다. 과거를 돌아보고 새로운 인생의 단계로 나아갈 시간입니다. 내면의 부름에 응답하고 진정한 자아로 거듭나세요.',
        reversedMeaning: '자기 의심, 후회, 내면의 비판을 나타냅니다. 과거에 얽매여 앞으로 나아가지 못하고 있습니다. 자신을 너무 가혹하게 판단하거나 내면의 부름을 무시하고 있습니다.',
        uprightKeywords: ['각성', '재생', '용서', '부름'],
        reversedKeywords: ['후회', '자기 의심', '비판', '정체']
    },
    {
        id: 'major-21-world',
        number: 21,
        name: '세계',
        nameEn: 'The World',
        category: 'major',
        imagePath: '메이저/21. 세계 카드.jpg',
        uprightMeaning: '완성, 성취, 전체성을 상징합니다. 긴 여정이 끝나고 목표를 달성했습니다. 완벽한 조화와 성취감을 느끼며, 새로운 시작을 위한 준비가 되어 있습니다. 축하합니다!',
        reversedMeaning: '미완성, 지연, 부족함을 의미합니다. 목표 달성이 지연되거나 완성하지 못한 과제가 있습니다. 성취감을 느끼지 못하거나 여전히 무언가 부족하다고 느낍니다.',
        uprightKeywords: ['완성', '성취', '조화', '축하'],
        reversedKeywords: ['미완성', '지연', '부족', '불완전']
    }
];

// Shuffle function using Fisher-Yates algorithm
export const shuffleDeck = (deck: TarotCard[]): TarotCard[] => {
    const shuffled = [...deck];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
};

// Get random cards from deck
export const getRandomCards = (deck: TarotCard[], count: number): TarotCard[] => {
    const shuffled = shuffleDeck(deck);
    return shuffled.slice(0, count);
};

export default MAJOR_ARCANA;
