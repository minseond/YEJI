import React, { createContext, useContext, useState, type ReactNode } from 'react';
import type { Character, UserCollection } from '../api/collection';
import { getMyCollections, equipCharacter as apiEquipCharacter, unequipCharacter as apiUnequipCharacter } from '../api/collection';
import { getUserInfo } from '../api/auth';

// ========================================
// Types
// ========================================

interface EquippedCharacter {
    id: number;
    name: string;
    type: 'EAST' | 'WEST';
    imageUrl: string;
}

interface CollectionContextType {
    equippedEast: EquippedCharacter | null;
    equippedWest: EquippedCharacter | null;
    myCollections: UserCollection[];
    isLoading: boolean;

    // Actions
    loadEquippedCharacters: (userId: number) => Promise<void>;
    loadMyCollections: () => Promise<void>;
    equipCharacter: (characterId: number, type: 'EAST' | 'WEST') => Promise<void>;
    unequipCharacter: (type: 'EAST' | 'WEST') => Promise<void>;
}

// ========================================
// Context
// ========================================

const CollectionContext = createContext<CollectionContextType | undefined>(undefined);

// ========================================
// Provider Component
// ========================================

interface CollectionProviderProps {
    children: ReactNode;
}

export const CollectionProvider: React.FC<CollectionProviderProps> = ({ children }) => {
    const [equippedEast, setEquippedEast] = useState<EquippedCharacter | null>(null);
    const [equippedWest, setEquippedWest] = useState<EquippedCharacter | null>(null);
    const [myCollections, setMyCollections] = useState<UserCollection[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // Load equipped characters from user info
    const loadEquippedCharacters = async (userId: number) => {
        try {
            setIsLoading(true);
            const userInfo = await getUserInfo(userId);

            setEquippedEast(userInfo.equipEast || null);
            setEquippedWest(userInfo.equipWest || null);
        } catch (error) {
            console.error('Failed to load equipped characters:', error);
        } finally {
            setIsLoading(false);
        }
    };

    // Load my collections
    const loadMyCollections = async () => {
        try {
            setIsLoading(true);
            const collections = await getMyCollections();
            setMyCollections(collections);
        } catch (error) {
            console.error('Failed to load my collections:', error);
        } finally {
            setIsLoading(false);
        }
    };

    // Equip character with optimistic update
    const equipCharacter = async (characterId: number, type: 'EAST' | 'WEST') => {
        // Find character from collections for optimistic update
        const collection = myCollections.find(c => c.character.id === characterId);
        if (!collection) {
            console.error('Character not found in collections');
            return;
        }

        const optimisticCharacter: EquippedCharacter = {
            id: collection.character.id,
            name: collection.character.name,
            type: collection.character.type,
            imageUrl: collection.character.imageUrl,
        };

        // Optimistic update
        const previousEast = equippedEast;
        const previousWest = equippedWest;

        if (type === 'EAST') {
            setEquippedEast(optimisticCharacter);
        } else {
            setEquippedWest(optimisticCharacter);
        }

        try {
            await apiEquipCharacter(characterId, type);
        } catch (error) {
            console.error('Failed to equip character:', error);
            // Rollback on error
            setEquippedEast(previousEast);
            setEquippedWest(previousWest);
            throw error;
        }
    };

    // Unequip character with optimistic update
    const unequipCharacter = async (type: 'EAST' | 'WEST') => {
        // Optimistic update
        const previousEast = equippedEast;
        const previousWest = equippedWest;

        if (type === 'EAST') {
            setEquippedEast(null);
        } else {
            setEquippedWest(null);
        }

        try {
            await apiUnequipCharacter(type);
        } catch (error) {
            console.error('Failed to unequip character:', error);
            // Rollback on error
            setEquippedEast(previousEast);
            setEquippedWest(previousWest);
            throw error;
        }
    };

    const value: CollectionContextType = {
        equippedEast,
        equippedWest,
        myCollections,
        isLoading,
        loadEquippedCharacters,
        loadMyCollections,
        equipCharacter,
        unequipCharacter,
    };

    return (
        <CollectionContext.Provider value={value}>
            {children}
        </CollectionContext.Provider>
    );
};

// ========================================
// Custom Hook
// ========================================

export const useCollection = (): CollectionContextType => {
    const context = useContext(CollectionContext);
    if (!context) {
        throw new Error('useCollection must be used within CollectionProvider');
    }
    return context;
};
