
import { useState, useEffect } from 'react';

const STORAGE_KEY = 'USER_EQUIP_SETTINGS';

export const getCharacterSettings = () => {
    try {
        const stored = localStorage.getItem(STORAGE_KEY);
        if (!stored) return { east: 'soiseol', west: 'stella' };

        const parsed = JSON.parse(stored);
        if (!parsed || typeof parsed !== 'object') return { east: 'soiseol', west: 'stella' };

        return {
            east: parsed.east || 'soiseol',
            west: parsed.west || 'stella'
        };
    } catch (e) {
        console.error('Failed to parse character settings:', e);
        return { east: 'soiseol', west: 'stella' };
    }
};

export const saveCharacterSettings = (settings: { east: string, west: string }) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    window.dispatchEvent(new Event('character-equip-changed'));
};

export const useCharacterSettings = () => {
    const [settings, setSettings] = useState(getCharacterSettings());

    useEffect(() => {
        const handleStorageChange = () => {
            setSettings(getCharacterSettings());
        };

        window.addEventListener('character-equip-changed', handleStorageChange);
        window.addEventListener('storage', handleStorageChange); // Also listen for cross-tab changes

        return () => {
            window.removeEventListener('character-equip-changed', handleStorageChange);
            window.removeEventListener('storage', handleStorageChange);
        };
    }, []);

    return settings;
};

export const CHARACTER_SETTINGS = getCharacterSettings(); // For backward compatibility if needed, but better to use getter

export type CharacterType = 'normal' | 'loading' | 'smile' | 'wink' | 'angry' | 'annoying' | 'explain' | 'loading2' | 'loading3' | 'loading4' | 'loading5' | 'loading6' | 'smile2' | 'suprize' | 'thinking';

export interface CharacterVisualConfig {
    scale: number;
    yOffset: string;
}

export const CHARACTER_VISUAL_CONFIG: Record<string, CharacterVisualConfig> = {
    soiseol: { scale: 1.15, yOffset: '0%' },
    hongseol: { scale: 1.1, yOffset: '0%' },
    stella: { scale: 0.95, yOffset: '0%' },
    nell: { scale: 1.0, yOffset: '0%' },
    // Default for others
    default: { scale: 1.0, yOffset: '0%' }
};

export const getCharacterVisualConfig = (id: string): CharacterVisualConfig => {
    return CHARACTER_VISUAL_CONFIG[id.toLowerCase()] || CHARACTER_VISUAL_CONFIG.default;
};

// Use strict glob import to ensure Vite processes these assets
// The key will be the relative path from THIS file.
// Correct path from src/utils/character.ts to src/assets is ../assets
const characterAssets = import.meta.glob('../assets/character/**/*.png', {
    eager: true,
    query: '?url',
    import: 'default'
}) as Record<string, string>;

/**
 * Returns the image path for a given character and type.
 * Uses import.meta.glob to reliably resolve paths in Vite.
 */
export const getCharacterImage = (region: 'east' | 'west', name: string, type: CharacterType = 'normal') => {
    // Construct the relative path exactly as it would appear in the glob keys
    // Globs are relative to the file.
    // 1. Try exact match first
    let path = `../assets/character/${region}/${name}/${name}_${type}.png`;
    let assetUrl = characterAssets[path];

    if (assetUrl) return assetUrl;

    // 2. Try case-insensitive lookup
    // Normalizing requested path for comparison
    // We strictly look for the pattern: ../assets/character/[region]/[name]/[name]_[type].png
    // But we relax casing on the [name] part specifically.

    const targetKey = path.toLowerCase();
    const foundKey = Object.keys(characterAssets).find(key => key.toLowerCase() === targetKey);

    if (foundKey) {
        return characterAssets[foundKey];
    }

    // 3. Fallback logic (also case-insensitive)
    if (type !== 'normal') {
        const fallbackPath = `../assets/character/${region}/${name}/${name}_normal.png`;
        const fallbackUrl = characterAssets[fallbackPath];
        if (fallbackUrl) return fallbackUrl;

        const fallbackTargetKey = fallbackPath.toLowerCase();
        const foundFallbackKey = Object.keys(characterAssets).find(key => key.toLowerCase() === fallbackTargetKey);

        if (foundFallbackKey) return characterAssets[foundFallbackKey];
    }

    // 4. Log failure
    console.warn(`[getCharacterImage] Image not found for path: ${path}`);
    return '';
};

/**
 * Returns the image path for SD characters in public/assets/character/SD캐릭터
 * Maps English IDs to Korean folder names and substitutes missing poses.
 */
export const getSDCharacterImage = (region: 'east' | 'west', id: string, type: string = 'normal') => {
    // 1. Map English ID to Korean Name (e.g., 'soiseol' -> '소이설')
    const koreanName = getCharacterName(region, id);
    const regionName = region === 'east' ? '동양' : '서양';

    // 2. Map Pose Type (since SD folder has different pose names)
    let pose = type;
    if (type === 'loading' || type === 'loading2') pose = 'normal';
    else if (type === 'loading3' || type === 'loading4') pose = 'smile';
    else if (type === 'loading5' || type === 'loading6') pose = 'thinking';
    // Fallback for any other custom types that might not exist in SD folder
    const validSDPoses = ['normal', 'smile', 'thinking', 'angry', 'annoying', 'explain', 'suprize'];
    if (!validSDPoses.includes(pose)) {
        pose = 'normal';
    }

    // 3. Construct Public Path
    let folderName = koreanName.replace(/\s/g, '');

    // Special mapping for inconsistencies
    if (folderName === '홍주') folderName = '홍설';

    return `/assets/character/SD캐릭터/${regionName}/${folderName}/${folderName}_${pose}.png`;
};

// --- Name Loading Logic ---

// Load all name.txt files
// Key format: ../assets/character/east/soiseol/name.txt
const characterNameAssets = import.meta.glob('../assets/character/**/name.txt', {
    eager: true,
    query: '?raw',
    import: 'default'
}) as Record<string, string>;

/**
 * Returns the character's name from name.txt
 */
export const getCharacterName = (region: 'east' | 'west', id: string): string => {
    if (!id) return region === 'east' ? '홍설' : '넬';

    // 1. Try exact match
    const path = `../assets/character/${region}/${id}/name.txt`;
    if (characterNameAssets[path]) {
        return characterNameAssets[path].trim().replace(/[.\n]+$/, ''); // Remove trailing dots or newlines
    }

    // 2. Case-insensitive lookup
    const targetKey = path.toLowerCase();
    const foundKey = Object.keys(characterNameAssets).find(key => key.toLowerCase() === targetKey);
    if (foundKey) {
        return characterNameAssets[foundKey].trim().replace(/[.\n]+$/, '');
    }

    // 3. Fallback
    return id.toUpperCase();
};

// --- Saju Intro Text Loading Logic ---

// Load all saju/intro.txt files
// Key format: ../assets/character/east/soiseol/saju/intro.txt
const characterSajuIntroAssets = import.meta.glob('../assets/character/**/saju/intro.txt', {
    eager: true,
    query: '?raw',
    import: 'default'
}) as Record<string, string>;

/**
 * Returns the character's saju intro text from saju/intro.txt
 */
export const getCharacterSajuIntro = (region: 'east' | 'west', id: string): string => {
    // 1. Try exact match
    const path = `../assets/character/${region}/${id}/saju/intro.txt`;
    if (characterSajuIntroAssets[path]) {
        return characterSajuIntroAssets[path].trim().replace(/[.\n]+$/, '').replace(/['"]+/g, ''); // Remove trailing dots, newlines, and quotes
    }

    // 2. Case-insensitive lookup
    const targetKey = path.toLowerCase();
    const foundKey = Object.keys(characterSajuIntroAssets).find(key => key.toLowerCase() === targetKey);
    if (foundKey) {
        return characterSajuIntroAssets[foundKey].trim().replace(/[.\n]+$/, '').replace(/['"]+/g, '');
    }

    // 3. Fallback texts
    if (region === 'east') return "하늘과 땅은 이미 당신의 길을 알고 있답니다...";
    return "별들의 속삭임이 들리시나요...";
};

// --- Duo Intro/Outro Script Loading Logic ---
// Load all duo/saju_intro and duo/saju_outro txt files
const duoIntroAssets = import.meta.glob('../assets/character/duo/saju_intro/*.txt', {
    eager: true,
    query: '?raw',
    import: 'default'
}) as Record<string, string>;

const duoOutroAssets = import.meta.glob('../assets/character/duo/saju_outro/*.txt', {
    eager: true,
    query: '?raw',
    import: 'default'
}) as Record<string, string>;

const selectionIntroAssets = import.meta.glob('../assets/character/duo/selection_intro/*.txt', {
    eager: true,
    query: '?raw',
    import: 'default'
}) as Record<string, string>;

export interface DuoIntroStep {
    char: 'east' | 'west';
    text: string;
    emotion?: CharacterType;
}

export const getDuoIntroScript = (eastId: string, westId: string): DuoIntroStep[] => {
    return loadDuoScript(duoIntroAssets, eastId, westId, 'intro');
};

export const getDuoOutroScript = (eastId: string, westId: string): DuoIntroStep[] => {
    return loadDuoScript(duoOutroAssets, eastId, westId, 'outro');
};

export const getSelectionIntroScript = (eastId: string, westId: string): DuoIntroStep[] => {
    return loadDuoScript(selectionIntroAssets, eastId, westId, 'selection_intro');
};

const loadDuoScript = (assets: Record<string, string>, eastId: string, westId: string, type: 'intro' | 'outro' | 'selection_intro'): DuoIntroStep[] => {
    const eId = eastId.toLowerCase();
    const wId = westId.toLowerCase();
    let folder = 'saju_intro';
    if (type === 'outro') folder = 'saju_outro';
    if (type === 'selection_intro') folder = 'selection_intro';

    // Path: ../assets/character/duo/{folder}/{eId}_{wId}_{type}.txt
    let path = `../assets/character/duo/${folder}/${eId}_${wId}_${type}.txt`;
    let content = assets[path];

    if (!content) {
        // Case-insensitive fallback
        const target = `${eId}_${wId}_${type}.txt`.toLowerCase();
        const foundKey = Object.keys(assets).find(key => key.toLowerCase().endsWith(target));
        if (foundKey) content = assets[foundKey];
    }

    if (!content) {
        console.warn(`[getDuoScript] ${type} script not found for ${eId} x ${wId}.`);
        if (type === 'intro') {
            return [
                { char: 'west', text: "오늘의 별들이 당신에게 어떤 이야기를 속삭일까요?" },
                { char: 'east', text: "음양의 흐름을 통해 당신의 하루를 미리 짚어드리겠습니다." },
                { char: 'west', text: "우주의 흐름은 매 순간 변하니, 지금 이 순간이 가장 중요합니다." },
                { char: 'east', text: "준비되셨다면, 당신의 하루를 펼쳐보겠습니다." }
            ];
        } else {
            return [
                { char: 'west', text: "별들이 당신의 길을 비추기 시작했습니다." },
                { char: 'east', text: "운명의 흐름을 읽어보겠습니다." },
                { char: 'east', text: "자, 그대에게 깃든 기운을 확인해봅시다." }
            ];
        }
    }

    const lines = content.split('\n').map(l => l.trim()).filter(l => l.length > 0 && !l.startsWith('[PLACEHOLDER]'));
    if (lines.length === 0) return []; // Handle placeholder empty files

    const steps: DuoIntroStep[] = [];
    lines.forEach((line, idx) => {
        // Parse Emotion Tag: (emotion) at end of line
        let text = line;
        let emotion: CharacterType | undefined = undefined;

        // Supported: normal, loading, smile, wink, angry, annoying, explain, loading2, smile2, suprize, thinking
        const match = line.match(/\s*\((normal|loading|smile|wink|angry|annoying|explain|loading2|smile2|suprize|thinking)\)$/i);
        if (match) {
            emotion = match[1].toLowerCase() as CharacterType;
            text = line.replace(match[0], '').trim();
        }

        steps.push({
            char: idx % 2 === 0 ? 'east' : 'west', // Logic assumed consistent with previous
            text: text,
            emotion: emotion
        });
    });

    return steps;
};


// --- Input Script Loading Logic ---
// Load all saju_input txt files
// Key format: ../assets/character/east/soiseol/saju_input/name.txt
const characterInputAssets = import.meta.glob('../assets/character/**/saju_input/*.txt', {
    eager: true,
    query: '?raw',
    import: 'default'
}) as Record<string, string>;

/**
 * Returns the character's specific input hover script
 */
export const getCharacterInputScript = (region: 'east' | 'west', id: string, field: string): string | null => {
    // 1. Try exact match
    const path = `../assets/character/${region}/${id}/saju_input/${field}.txt`;
    if (characterInputAssets[path]) {
        return characterInputAssets[path].trim();
    }

    // 2. Case-insensitive lookup
    const targetKey = path.toLowerCase();
    const foundKey = Object.keys(characterInputAssets).find(key => key.toLowerCase() === targetKey);
    if (foundKey) {
        return characterInputAssets[foundKey].trim();
    }

    return null;
};
