
export const CHEONGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
export const CHEONGAN_KOR = ['갑', '을', '병', '정', '무', '기', '경', '신', '임', '계'];

export const JIJI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];
export const JIJI_KOR = ['자', '축', '인', '묘', '진', '사', '오', '미', '신', '유', '술', '해'];

export const ANIMALS = ['쥐', '소', '호랑이', '토끼', '용', '뱀', '말', '양', '원숭이', '닭', '개', '돼지'];

export const ELEMENTS = [
    { name: '목(木)', color: '#4caf50', hex: 'text-green-400', border: 'border-green-500' }, // 甲, 乙
    { name: '화(火)', color: '#f44336', hex: 'text-red-400', border: 'border-red-500' },     // 丙, 丁
    { name: '토(土)', color: '#ffb300', hex: 'text-yellow-400', border: 'border-yellow-500' }, // 戊, 己
    { name: '금(金)', color: '#e0e0e0', hex: 'text-gray-200', border: 'border-gray-300' },   // 庚, 辛
    { name: '수(水)', color: '#2196f3', hex: 'text-blue-400', border: 'border-blue-500' },   // 壬, 癸
];

export interface GapjaInfo {
    year: number;
    gan: string; // Hanja
    ji: string;  // Hanja
    korGan: string;
    korJi: string;
    korGanji: string; // e.g., 갑자
    hanjaGanji: string; // e.g., 甲子
    animal: string;
    element: typeof ELEMENTS[0];
}

export const getGapjaInfo = (year: number): GapjaInfo => {
    // Reference: 1984 is Gapja (甲子) - Just calculating offset
    // 10 Cheongan cycles: (year - 4) % 10
    // 12 Jiji cycles: (year - 4) % 12

    // Ensure positive index even for pre-1900 if needed (though we target 1920+)
    const ganIndex = (year - 4) % 10 < 0 ? ((year - 4) % 10) + 10 : (year - 4) % 10;
    const jiIndex = (year - 4) % 12 < 0 ? ((year - 4) % 12) + 12 : (year - 4) % 12;

    const elementIndex = Math.floor(ganIndex / 2);

    return {
        year,
        gan: CHEONGAN[ganIndex],
        ji: JIJI[jiIndex],
        korGan: CHEONGAN_KOR[ganIndex],
        korJi: JIJI_KOR[jiIndex],
        korGanji: `${CHEONGAN_KOR[ganIndex]}${JIJI_KOR[jiIndex]}`,
        hanjaGanji: `${CHEONGAN[ganIndex]}${JIJI[jiIndex]}`,
        animal: ANIMALS[jiIndex],
        element: ELEMENTS[elementIndex]
    };
};
