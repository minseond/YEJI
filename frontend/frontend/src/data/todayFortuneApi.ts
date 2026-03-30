
import todayFortuneData from './todayFortune.json';

export interface FortuneDetail {
    type: string;
    score: number;
    summary: string;
    keywords: string[];
    description: string;
    luckyItem: string;
}

export interface TodayFortuneDataEntry {
    id: string;
    topic: string;
    east: FortuneDetail;
    west: FortuneDetail;
}

export const getTodayFortuneByTopic = (topic: string): TodayFortuneDataEntry => {
    const found = todayFortuneData.find((entry) => entry.id === topic);
    if (!found) {
        // Fallback to 'total' or first item if topic not found
        return todayFortuneData[0] as TodayFortuneDataEntry;
    }
    return found as TodayFortuneDataEntry;
};

export const getRandomTodayFortune = (): TodayFortuneDataEntry => {
    const randomIndex = Math.floor(Math.random() * todayFortuneData.length);
    return todayFortuneData[randomIndex] as TodayFortuneDataEntry;
};
