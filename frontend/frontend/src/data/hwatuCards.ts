export interface HwatuCard {
    code: number;
    month: number;
    name: string;
    img: string;
    desc: string;
    detailedDesc: string;
}

// Map index 0-47 to Hwatu cards
export const HWATU_CARDS: Record<number, HwatuCard> = {
    0: { code: 0, month: 1, name: '송학 (松鶴) - 광', img: '/assets/hwatu/hwatu_00.png', desc: '천 리 길도 한 걸음부터', detailedDesc: '소나무는 변치 않는 지조를, 학은 고귀함을 상징합니다. 인고의 시간을 지나 고귀한 성취를 이룰 징조입니다.' },
    1: { code: 1, month: 1, name: '송학 (松鶴) - 열', img: '/assets/hwatu/hwatu_01.png', desc: '기쁜 소식의 시작', detailedDesc: '홍단은 경사스러운 소식을 의미합니다. 주변에서 반가운 소식이 들려올 것입니다.' },
    2: { code: 2, month: 1, name: '송학 (松鶴) - 홍단', img: '/assets/hwatu/hwatu_02.png', desc: '티끌 모아 태산', detailedDesc: '작은 노력이 모여 큰 결실을 맺는 기초가 되는 카드입니다.' },
    3: { code: 3, month: 1, name: '송학 (松鶴) - 피', img: '/assets/hwatu/hwatu_03.png', desc: '기초를 다지는 시기', detailedDesc: '서두르지 말고 주변을 정리하며 내실을 다져야 할 때입니다.' },

    4: { code: 4, month: 2, name: '매조 (梅鳥) - 열', img: '/assets/hwatu/hwatu_04.png', desc: '봄바람에 실려오는 소식', detailedDesc: '매화 가지에 앉은 휘파람새는 반가운 손님이나 소식을 의미합니다. 긍정적인 변화의 기운이 감돌고 있습니다.' },
    5: { code: 5, month: 2, name: '매조 (梅鳥) - 홍단', img: '/assets/hwatu/hwatu_05.png', desc: '화합과 소통', detailedDesc: '사람들 사이의 관계가 원만해지고 뜻밖의 조력자를 만날 수 있습니다.' },
    6: { code: 6, month: 2, name: '매조 (梅鳥) - 피', img: '/assets/hwatu/hwatu_06.png', desc: '새로운 생명력', detailedDesc: '겨울을 이기고 피어나는 매화처럼 새로운 활력이 솟아나는 시기입니다.' },
    7: { code: 7, month: 2, name: '매조 (梅鳥) - 피', img: '/assets/hwatu/hwatu_06.png', desc: '준비된 시작', detailedDesc: '겉으로 보이지 않아도 내면에서는 이미 성장이 시작되었습니다.' },

    8: { code: 8, month: 3, name: '벚꽃 (櫻花) - 광', img: '/assets/hwatu/hwatu_08.png', desc: '만개한 행운', detailedDesc: '벚꽃이 만개하듯 당신의 운세도 절정에 달했습니다. 화려한 성취가 예상됩니다.' },
    9: { code: 9, month: 3, name: '벚꽃 (櫻花) - 열 (막패)', img: '/assets/hwatu/hwatu_09.png', desc: '아름다운 결실', detailedDesc: '정성을 들인 일이 아름답게 마무리되어 사람들의 인정을 받게 됩니다.' },
    10: { code: 10, month: 3, name: '벚꽃 (櫻花) - 홍단', img: '/assets/hwatu/hwatu_10.png', desc: '즐거운 에너지', detailedDesc: '축제 같은 분위기 속에서 즐거운 시간을 보내게 될 징조입니다.' },
    11: { code: 11, month: 3, name: '벚꽃 (櫻花) - 피', img: '/assets/hwatu/hwatu_11.png', desc: '조화로운 일상', detailedDesc: '주변 환경과 잘 어우러져 평온한 발전을 이루게 됩니다.' },

    12: { code: 12, month: 4, name: '흑싸리 (黑) - 열', img: '/assets/hwatu/hwatu_12.png', desc: '신속한 움직임', detailedDesc: '기회가 왔을 때 빠르게 움직여야 합니다. 때를 놓치지 않는 결단력이 중요합니다.' },
    13: { code: 13, month: 4, name: '흑싸리 (黑) - 초단', img: '/assets/hwatu/hwatu_13.png', desc: '끈기 있는 전진', detailedDesc: '싸리나무처럼 유연하면서도 강한 생명력으로 목표를 향해 나아가세요.' },
    14: { code: 14, month: 4, name: '흑싸리 (黑) - 피', img: '/assets/hwatu/hwatu_14.png', desc: '성실함의 보상', detailedDesc: '묵묵히 자기 자리를 지키는 성실함이 결국 보상을 가져다줄 것입니다.' },
    15: { code: 15, month: 4, name: '흑싸리 (黑) - 피', img: '/assets/hwatu/hwatu_14.png', desc: '내실을 기함', detailedDesc: '겉치레보다는 실질적인 이득을 챙겨야 하는 시기입니다.' },

    16: { code: 16, month: 5, name: '난초 (蘭草) - 열', img: '/assets/hwatu/hwatu_16.png', desc: '고고한 품격', detailedDesc: '난초의 향기처럼 당신의 평판이 널리 알려지고 존경을 받게 됩니다.' },
    17: { code: 17, month: 5, name: '난초 (蘭草) - 초단', img: '/assets/hwatu/hwatu_17.png', desc: '올바른 신념', detailedDesc: '자신의 가치관을 지키며 행동할 때 뜻하지 않은 행운이 찾아옵니다.' },
    18: { code: 18, month: 5, name: '난초 (蘭草) - 피', img: '/assets/hwatu/hwatu_18.png', desc: '잔잔한 평화', detailedDesc: '큰 기폭 없이 평탄한 흐름 속에 안정을 찾는 시기입니다.' },
    19: { code: 19, month: 5, name: '난초 (蘭草) - 피', img: '/assets/hwatu/hwatu_18.png', desc: '정서적 충만', detailedDesc: '마음의 여유를 가지고 주변을 돌아보면 소중한 것을 발견하게 됩니다.' },

    20: { code: 20, month: 6, name: '모란 (牡丹) - 열', img: '/assets/hwatu/hwatu_20.png', desc: '부귀영화의 상징', detailedDesc: '나비가 꽃을 찾듯 부와 명예가 당신을 따를 운세입니다.' },
    21: { code: 21, month: 6, name: '모란 (牡丹) - 청단', img: '/assets/hwatu/hwatu_21.png', desc: '냉철한 판단', detailedDesc: '감정에 치우치지 않고 이성적으로 판단하면 큰 이득을 얻을 수 있습니다.' },
    22: { code: 22, month: 6, name: '모란 (牡丹) - 피', img: '/assets/hwatu/hwatu_22.png', desc: '화려한 변신', detailedDesc: '자신을 가꾸고 드러내기에 좋은 시기입니다. 긍정적인 주목을 받게 됩니다.' },
    23: { code: 23, month: 6, name: '모란 (牡丹) - 피', img: '/assets/hwatu/hwatu_22.png', desc: '결실을 위한 준비', detailedDesc: '지금의 노력이 화려한 꽃을 피우기 위한 자양분이 될 것입니다.' },

    24: { code: 24, month: 7, name: '홍싸리 (紅) - 열', img: '/assets/hwatu/hwatu_24.png', desc: '활발한 활동', detailedDesc: '멧돼지가 돌진하듯 거침없는 추진력이 필요한 시기입니다.' },
    25: { code: 25, month: 7, name: '홍싸리 (紅) - 초단', img: '/assets/hwatu/hwatu_25.png', desc: '끈기 있는 승부', detailedDesc: '포기하지 않고 끝까지 밀고 나가면 결국 원하는 바를 얻습니다.' },
    26: { code: 26, month: 7, name: '홍싸리 (紅) - 피', img: '/assets/hwatu/hwatu_26.png', desc: '역동적인 기운', detailedDesc: '주변 상황이 빠르게 변화하며 당신의 활동 범위를 넓혀줄 것입니다.' },
    27: { code: 27, month: 7, name: '홍싸리 (紅) - 피', img: '/assets/hwatu/hwatu_26.png', desc: '자신감 있는 행보', detailedDesc: '스스로를 믿고 나아가면 장벽을 극복할 수 있습니다.' },

    28: { code: 28, month: 8, name: '공산 (空山) - 광', img: '/assets/hwatu/hwatu_28.png', desc: '어둠 뒤에 찾아올 만월', detailedDesc: '빈 산 위에 뜬 보름달은 고요함 속의 충만함을 뜻합니다. 머지않아 노력이 결실을 맺을 것입니다.' },
    29: { code: 29, month: 8, name: '공산 (空山) - 열', img: '/assets/hwatu/hwatu_29.png', desc: '통찰력과 지혜', detailedDesc: '높은 곳에서 내려다보듯 상황을 전체적으로 파악하는 지혜가 필요합니다.' },
    30: { code: 30, month: 8, name: '공산 (空山) - 피', img: '/assets/hwatu/hwatu_30.png', desc: '마음의 비움', detailedDesc: '욕심을 내려놓을 때 오히려 더 큰 것을 얻게 되는 순리를 따르세요.' },
    31: { code: 31, month: 8, name: '공산 (空山) - 피', img: '/assets/hwatu/hwatu_30.png', desc: '고요한 발전', detailedDesc: '드러나지 않게 실력을 쌓으며 기회를 기다리는 인내의 시간입니다.' },

    32: { code: 32, month: 9, name: '국진 (菊) - 열', img: '/assets/hwatu/hwatu_32.png', desc: '장수와 건강', detailedDesc: '국화꽃처럼 은은한 향기와 끈질긴 생명력으로 건강한 발전을 이룹니다.' },
    33: { code: 33, month: 9, name: '국진 (菊) - 청단', img: '/assets/hwatu/hwatu_33.png', desc: '신중한 마무리', detailedDesc: '중요한 일을 마무리할 때는 돌다리도 두드려보고 건너는 신중함이 필요합니다.' },
    34: { code: 34, month: 9, name: '국진 (菊) - 피', img: '/assets/hwatu/hwatu_34.png', desc: '깊어가는 숙련도', detailedDesc: '자신의 분야에서 전문성을 인정받고 내실을 다지게 됩니다.' },
    35: { code: 35, month: 9, name: '국진 (菊) - 피', img: '/assets/hwatu/hwatu_34.png', desc: '은근한 끈기', detailedDesc: '쉽게 포기하지 않는 태도가 결국 행운의 여신을 미소 짓게 할 것입니다.' },

    36: { code: 36, month: 10, name: '단풍 (丹楓) - 열', img: '/assets/hwatu/hwatu_36.png', desc: '화려한 피날레', detailedDesc: '단풍이 산을 물들이듯 당신의 성취가 만인에게 증명될 시기입니다.' },
    37: { code: 37, month: 10, name: '단풍 (丹楓) - 청단', img: '/assets/hwatu/hwatu_37.png', desc: '이성적인 정돈', detailedDesc: '복잡한 상황을 깔끔하게 정리하고 새로운 계획을 세우기에 최적입니다.' },
    38: { code: 38, month: 10, name: '단풍 (丹楓) - 피', img: '/assets/hwatu/hwatu_38.png', desc: '결실을 거두는 기쁨', detailedDesc: '그동안 노력한 대가를 충분히 누려도 좋은 풍요로운 시기입니다.' },
    39: { code: 39, month: 10, name: '단풍 (丹楓) - 피', img: '/assets/hwatu/hwatu_38.png', desc: '아름다운 변화', detailedDesc: '새로운 모습으로 탈바꿈하며 더 큰 성장을 준비하는 단계입니다.' },

    40: { code: 40, month: 11, name: '오동 (梧桐) - 광', img: '/assets/hwatu/hwatu_40.png', desc: '최고의 권위', detailedDesc: '봉황이 깃드는 오동나무처럼 명예와 권위가 드높아질 길조입니다.' },
    41: { code: 41, month: 11, name: '오동 (梧桐) - 열', img: '/assets/hwatu/hwatu_41.png', desc: '든든한 기반', detailedDesc: '한 분야에서 독보적인 위치를 점하거나 강력한 우군을 얻게 됩니다.' },
    42: { code: 42, month: 11, name: '오동 (梧桐) - 피', img: '/assets/hwatu/hwatu_42.png', desc: '안정적인 성장', detailedDesc: '흔들림 없이 뿌리를 내리고 꾸준한 발전을 이어가게 됩니다.' },
    43: { code: 43, month: 11, name: '오동 (梧桐) - 피', img: '/assets/hwatu/hwatu_42.png', desc: '플러스 알파의 행운', detailedDesc: '예상치 못한 배의 이득이나 행운이 찾아올 수 있는 기대되는 카드입니다.' },

    44: { code: 44, month: 12, name: '비 (雨) - 광', img: '/assets/hwatu/hwatu_44.png', desc: '비를 피하며 때를 기다림', detailedDesc: '서두르지 말고 잠시 멈추어 주변을 살피십시오. 비가 그친 뒤 땅은 더 굳어질 것입니다.' },
    45: { code: 45, month: 12, name: '비 (雨) - 열', img: '/assets/hwatu/hwatu_45.png', desc: '유연한 대처', detailedDesc: '상황에 따라 유연하게 대처하면 큰 위기도 기회로 바꿀 수 있습니다.' },
    46: { code: 46, month: 12, name: '비 (雨) - 띠', img: '/assets/hwatu/hwatu_46.png', desc: '조심스러운 행보', detailedDesc: '돌발 변수에 대비하며 신중하게 한 걸음씩 나아가야 안전합니다.' },
    47: { code: 47, month: 12, name: '비 (雨) - 피', img: '/assets/hwatu/hwatu_47.png', desc: '마지막 보은', detailedDesc: '끝까지 최선을 다할 때 보이지 않는 손길이 당신을 도울 것입니다.' },
};

export const getHwatuCardByCode = (code: number): HwatuCard | undefined => {
    return HWATU_CARDS[code];
};
