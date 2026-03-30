
// THEMES is used by FortuneResult for styling
export const THEMES: Record<string, any> = {
    total: { primary: 'text-amber-400', secondary: 'text-amber-200', bgFrom: 'from-amber-900', bgTo: 'to-black' },
    love: { primary: 'text-pink-400', secondary: 'text-pink-200', bgFrom: 'from-pink-900', bgTo: 'to-black' },
    wealth: { primary: 'text-yellow-400', secondary: 'text-yellow-200', bgFrom: 'from-yellow-900', bgTo: 'to-black' },
    career: { primary: 'text-blue-400', secondary: 'text-blue-200', bgFrom: 'from-blue-900', bgTo: 'to-black' },
    health: { primary: 'text-green-400', secondary: 'text-green-200', bgFrom: 'from-green-900', bgTo: 'to-black' },
};

// --- LEAF NODE TYPES (Reusable Basic Types) ---

export interface SajuElement {
    code: string;
    label: string;
    percent: number;
}

export interface WesternElement {
    code: string;
    label: string;
    // value: number; // Removed as per request (only percent matters)
    percent: number;
}

export interface WesternKeyword {
    code: string;
    label: string;
    weight: number;
}

// --- UNIFIED USER FORTUNE DEFINITION ---
export interface UserFortune {
    // 1. Eastern Fortune (Saju)
    eastern: {
        score: number; // 0-100 score
        element: string; // Representative element
        chart: {
            summary: string;
            year: { gan: string; ji: string; element_code: string };
            month: { gan: string; ji: string; element_code: string };
            day: { gan: string; ji: string; element_code: string };
            hour: { gan: string; ji: string; element_code: string };
        };
        stats: {
            cheongan_jiji: {
                summary: string;
                year: { cheon_gan: string; ji_ji: string };
                month: { cheon_gan: string; ji_ji: string };
                day: { cheon_gan: string; ji_ji: string };
                hour: { cheon_gan: string; ji_ji: string };
            };
            five_elements: {
                summary: string;
                elements_list: SajuElement[];
            };
            yin_yang_ratio: {
                summary: string;
                yin: number;
                yang: number;
            };
            ten_gods: {
                summary: string;
                gods_list: SajuElement[];
            };
        };
        final_verdict: {
            summary: string;
            strength: string;
            weakness: string;
            advice: string;
        };
        lucky: {
            color: string;
            number: string;
            item: string;
            direction?: string;
            place?: string;
        };
    };

    // 2. Western Fortune (Astrology)
    western: {
        score: number; // 0-100 score
        element: string; // Representative element
        stats: {
            main_sign: {
                name: string; // e.g. "Aquarius"
            };
            element_summary: string;
            // List size: Exactly 4 items (Fire, Earth, Air, Water).
            // Sum of percent should be approximately 100.
            element_4_distribution: WesternElement[];

            modality_summary: string;
            // List size: Exactly 3 items (Cardinal, Fixed, Mutable).
            // Sum of percent should be approximately 100.
            modality_3_distribution: WesternElement[];

            keywords_summary: string;
            // List size: Variable (typically top 3-5 keywords).
            keywords: WesternKeyword[];
        };
        fortune_content: {
            overview: string;
            detailed_analysis: {
                title: string;
                content: string;
            }[];
            advice: string;
        };
        lucky: {
            color: string;
            number: string;
            item?: string;
            place?: string;
        };
    };
}

// --- BACKWARD COMPATIBILITY ALIASES ---
export type SajuDataV2 = UserFortune['eastern'];
export type WesternFortuneDataV2 = UserFortune['western'];
export type IntegratedFortuneResult = UserFortune;
export type SajuChart = UserFortune['eastern']['chart'];
export type SajuStats = UserFortune['eastern']['stats'];
export type WesternStats = UserFortune['western']['stats'];
export type WesternFortuneContent = UserFortune['western']['fortune_content'];
export type DualFortuneResultV2 = IntegratedFortuneResult;
