
const tarotAssetMap = import.meta.glob('../assets/타로카드/**/*.jpg', { eager: true }) as Record<string, { default: string }>;

export const getTarotImage = (code: string | number): string => {
    // Handle string codes from API (e.g., "PENTACLES_SEVEN", "WANDS_TWO", "JUSTICE")
    if (typeof code === 'string') {
        const codeToFileMap: Record<string, string> = {
            // Major Arcana
            'FOOL': '0. 바보 카드',
            'MAGICIAN': '1. 마법사 카드',
            'HIGH_PRIESTESS': '2. 여사제 카드',
            'EMPRESS': '3. 여황제 카드',
            'EMPEROR': '4. 황제 카드',
            'HIEROPHANT': '5. 교황 카드',
            'LOVERS': '6. 연인 카드',
            'CHARIOT': '7. 전차 카드',
            'STRENGTH': '8. 힘 카드',
            'HERMIT': '9. 은둔자 카드',
            'WHEEL_OF_FORTUNE': '10. 운명의 수레바퀴',
            'JUSTICE': '11. 정의 카드',
            'HANGED_MAN': '12. 행맨 카드',
            'DEATH': '13. 죽음 카드',
            'TEMPERANCE': '14. 절제 카드',
            'DEVIL': '15. 악마 카드',
            'TOWER': '16. 타워 카드',
            'STAR': '17. 별 카드',
            'MOON': '18. 달 카드',
            'SUN': '19. 태양 카드',
            'JUDGEMENT': '20. 심판 카드',
            'WORLD': '21. 세계 카드',

            // Wands (완드)
            'WANDS_ACE': '완드 에이스',
            'WANDS_TWO': '완드2',
            'WANDS_THREE': '완드3',
            'WANDS_FOUR': '완드4',
            'WANDS_FIVE': '완드5',
            'WANDS_SIX': '완드6',
            'WANDS_SEVEN': '완드7',
            'WANDS_EIGHT': '완드8',
            'WANDS_NINE': '완드9',
            'WANDS_TEN': '완드10',
            'WANDS_PAGE': '완드 페이지',
            'WANDS_KNIGHT': '완드 나이트',
            'WANDS_QUEEN': '완드 퀸',
            'WANDS_KING': '완드 킹',

            // Cups (컵)
            'CUPS_ACE': '컵 에이스',
            'CUPS_TWO': '컵2',
            'CUPS_THREE': '컵3',
            'CUPS_FOUR': '컵4',
            'CUPS_FIVE': '컵5',
            'CUPS_SIX': '컵6',
            'CUPS_SEVEN': '컵7',
            'CUPS_EIGHT': '컵8',
            'CUPS_NINE': '컵9',
            'CUPS_TEN': '컵10',
            'CUPS_PAGE': '컵 페이지',
            'CUPS_KNIGHT': '컵 나이트',
            'CUPS_QUEEN': '컵 퀸',
            'CUPS_KING': '컵 킹',

            // Swords (소드)
            'SWORDS_ACE': '소드 에이스',
            'SWORDS_TWO': '소드2',
            'SWORDS_THREE': '소드3',
            'SWORDS_FOUR': '소드4',
            'SWORDS_FIVE': '소드5',
            'SWORDS_SIX': '소드6',
            'SWORDS_SEVEN': '소드7',
            'SWORDS_EIGHT': '소드8',
            'SWORDS_NINE': '소드9',
            'SWORDS_TEN': '소드10',
            'SWORDS_PAGE': '소드 페이지',
            'SWORDS_KNIGHT': '소드 나이트',
            'SWORDS_QUEEN': '소드 퀸',
            'SWORDS_KING': '소드 킹',

            // Pentacles (펜타클)
            'PENTACLES_ACE': '펜타클 에이스',
            'PENTACLES_TWO': '펜타클2',
            'PENTACLES_THREE': '펜타클3',
            'PENTACLES_FOUR': '펜타클4',
            'PENTACLES_FIVE': '펜타클5',
            'PENTACLES_SIX': '펜타클6',
            'PENTACLES_SEVEN': '펜타클7',
            'PENTACLES_EIGHT': '펜타클8',
            'PENTACLES_NINE': '펜타클9',
            'PENTACLES_TEN': '펜타클10',
            'PENTACLES_PAGE': '펜타클 페이지',
            'PENTACLES_KNIGHT': '펜타클 나이트',
            'PENTACLES_QUEEN': '펜타클 퀸',
            'PENTACLES_KING': '펜타클 킹',
        };

        const fileNameFragment = codeToFileMap[code];

        if (!fileNameFragment) {
            console.warn(`[getTarotImage] Unknown card code: ${code}`);
            return '';
        }

        // Find the matching path in the globbed map
        const matchedPath = Object.keys(tarotAssetMap).find(path =>
            path.includes(fileNameFragment)
        );

        if (!matchedPath) {
            console.warn(`[getTarotImage] No image found for: ${fileNameFragment}`);
            return '';
        }

        return tarotAssetMap[matchedPath].default;
    }

    // Handle numeric codes (0-21) for Major Arcana
    const cardId = Number(code);
    const codeToFileMap: Record<number, string> = {
        0: '0. 바보 카드',
        1: '1. 마법사 카드',
        2: '2. 여사제 카드',
        3: '3. 여황제 카드',
        4: '4. 황제 카드',
        5: '5. 교황 카드',
        6: '6. 연인 카드',
        7: '7. 전차 카드',
        8: '8. 힘 카드',
        9: '9. 은둔자 카드',
        10: '10. 운명의 수레바퀴',
        11: '11. 정의 카드',
        12: '12. 행맨 카드',
        13: '13. 죽음 카드',
        14: '14. 절제 카드',
        15: '15. 악마 카드',
        16: '16. 타워 카드',
        17: '17. 별 카드',
        18: '18. 달 카드',
        19: '19. 태양 카드',
        20: '20. 심판 카드',
        21: '21. 세계 카드'
    };

    const fileNameFragment = codeToFileMap[cardId] || String(code);

    // Find the matching path in the globbed map
    const matchedPath = Object.keys(tarotAssetMap).find(path =>
        path.includes(fileNameFragment)
    );

    return matchedPath ? tarotAssetMap[matchedPath].default : '';
};
