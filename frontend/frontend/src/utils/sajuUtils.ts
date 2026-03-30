
/**
 * Utility for Saju and Zodiac calculations
 */

export interface FiveElementsData {
    name: string;
    value: number;
    color: string;
    hanja: string;
}

/**
 * Get Western Zodiac sign based on month and day
 */
export const getWesternZodiac = (birthDate: string | null) => {
    if (!birthDate) return { name: '알 수 없음', icon: '✨' };

    const date = new Date(birthDate);
    if (isNaN(date.getTime())) return { name: '알 수 없음', icon: '✨' };

    const m = date.getMonth() + 1;
    const d = date.getDate();

    const signs = [
        { name: '염소자리', icon: '♑', start: { m: 12, d: 22 }, end: { m: 1, d: 19 } },
        { name: '물병자리', icon: '♒', start: { m: 1, d: 20 }, end: { m: 2, d: 18 } },
        { name: '물고기자리', icon: '♓', start: { m: 2, d: 19 }, end: { m: 3, d: 20 } },
        { name: '양자리', icon: '♈', start: { m: 3, d: 21 }, end: { m: 4, d: 19 } },
        { name: '황소자리', icon: '♉', start: { m: 4, d: 20 }, end: { m: 5, d: 20 } },
        { name: '쌍둥이자리', icon: '♊', start: { m: 5, d: 21 }, end: { m: 6, d: 21 } },
        { name: '게자리', icon: '♋', start: { m: 6, d: 22 }, end: { m: 7, d: 22 } },
        { name: '사자자리', icon: '♌', start: { m: 7, d: 23 }, end: { m: 8, d: 22 } },
        { name: '처녀자리', icon: '♍', start: { m: 8, d: 23 }, end: { m: 9, d: 22 } },
        { name: '천칭자리', icon: '♎', start: { m: 9, d: 23 }, end: { m: 10, d: 23 } },
        { name: '전갈자리', icon: '♏', start: { m: 10, d: 24 }, end: { m: 11, d: 22 } },
        { name: '사수자리', icon: '♐', start: { m: 11, d: 23 }, end: { m: 12, d: 21 } },
    ];

    const found = signs.find(z => {
        if (z.name === '염소자리') {
            return (m === 12 && d >= 22) || (m === 1 && d <= 19);
        }
        return (m === z.start.m && d >= z.start.d) || (m === z.end.m && d <= z.end.d);
    });

    return found || { name: '알 수 없음', icon: '✨' };
};

/**
 * Simplified Five Elements (Ohang) distribution calculation
 * In a real app, this would use a Manseuryeok algorithm.
 * For now, we use a deterministic hash-based distribution from the birth date/time.
 */
export const calculateFiveElements = (birthDate: string | null, birthTime: string | null): FiveElementsData[] => {
    const elements = [
        { name: '화', hanja: '火', color: '#f44336' },
        { name: '수', hanja: '水', color: '#2196f3' },
        { name: '목', hanja: '木', color: '#4caf50' },
        { name: '금', hanja: '金', color: '#e0e0e0' },
        { name: '토', hanja: '土', color: '#ffb300' },
    ];

    if (!birthDate) {
        return elements.map(e => ({ ...e, value: 20 }));
    }

    // A simple deterministic shuffle based on input string
    const seed = `${birthDate}${birthTime || ''}`;
    let hash = 0;
    for (let i = 0; i < seed.length; i++) {
        hash = ((hash << 5) - hash) + seed.charCodeAt(i);
        hash |= 0;
    }

    // Generate pseudo-random values that sum to 100
    const values: number[] = [];
    let remaining = 100;
    for (let i = 0; i < 4; i++) {
        const v = Math.max(5, Math.min(35, Math.floor(((Math.abs(hash) >> (i * 2)) % 30) + 10)));
        values.push(v);
        remaining -= v;
        hash = hash ^ (hash >> 3); // Mutate hash
    }
    values.push(remaining);

    // Shuffle values to avoid fixed distribution patterns
    return elements.map((e, i) => ({
        ...e,
        value: values[i]
    }));
};
