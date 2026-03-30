import api from './axios';

// ========================================
// TypeScript Interfaces
// ========================================

export interface Character {
    id: number;
    name: string;
    type: 'EAST' | 'WEST';
    grade: 'COMMON' | 'RARE' | 'EPIC' | 'LEGENDARY';
    imageUrl: string;
    description: string;
    isActive: boolean;
}

export interface UserCollection {
    id: number;
    character: Character;
    acquiredAt: string; // ISO 8601 format
}

export interface CharacterEquipRequest {
    characterId: number | null; // null to unequip
    type: 'EAST' | 'WEST';
}

// ========================================
// API Functions
// ========================================

/**
 * COL-001: Get all active characters (전체 캐릭터 도감 조회)
 */
export const getAllCharacters = async (): Promise<Character[]> => {
    const response = await api.get<{ data: Character[] }>('/collection/characters');
    return response.data.data;
};

/**
 * COL-002: Get my owned characters (내 보유 캐릭터 조회)
 */
export const getMyCollections = async (): Promise<UserCollection[]> => {
    const response = await api.get<{ data: UserCollection[] }>('/collection/my-characters');
    return response.data.data;
};

/**
 * COL-003: Get character detail (캐릭터 상세 조회)
 */
export const getCharacterDetail = async (characterId: number): Promise<Character> => {
    const response = await api.get<{ data: Character }>(`/collection/characters/${characterId}`);
    return response.data.data;
};

/**
 * COL-004: Equip character (캐릭터 장착)
 * @param characterId - Character ID to equip (null to unequip)
 * @param type - Slot type ('EAST' or 'WEST')
 */
export const equipCharacter = async (characterId: number | null, type: 'EAST' | 'WEST'): Promise<void> => {
    const request: CharacterEquipRequest = { characterId, type };
    await api.patch('/collection/equip', request);
};

/**
 * Convenience function: Unequip character (캐릭터 장착 해제)
 */
export const unequipCharacter = async (type: 'EAST' | 'WEST'): Promise<void> => {
    await equipCharacter(null, type);
};
