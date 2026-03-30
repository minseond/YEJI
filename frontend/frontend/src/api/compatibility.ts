import api from './axios';

// Request Types
export interface CompatibilityRequest {
    targetUserId?: number;
    targetName: string;
    relationType?: string;
    birthData: {
        gender: 'M' | 'F';
        is_solar: boolean;
        birth_date: string; // YYYY-MM-DD
        birth_time?: string; // HH:mm
    };
}

// AI Response Types (nested in resultData)
export interface RelationshipDynamics {
    communication: { desc: string };
    flexibility: { desc: string };
    stability: { desc: string };
    passion: { desc: string };
    growth: { desc: string };
}

export interface CompatibilitySummary {
    keywords: string[];
    desc: string;
}

export interface ZodiacAspect {
    title: string;
    desc: string;
}

export interface ZodiacAspects {
    moon_resonance: ZodiacAspect;
    mercury_communication: ZodiacAspect;
    venus_mars_values: ZodiacAspect;
    saturn_stability: ZodiacAspect;
}

export interface NumerologyItem {
    title: string;
    desc: string;
}

export interface Numerology {
    life_path: NumerologyItem;
    destiny: NumerologyItem;
    complement: NumerologyItem;
}

export interface EastAnalysis {
    relationship_dynamics: RelationshipDynamics;
    compatibility_summary: CompatibilitySummary;
}

export interface WestAnalysis {
    zodiac: {
        aspects: ZodiacAspects;
    };
    numerology: Numerology;
}

export interface CompatibilityMessage {
    east: EastAnalysis;
    west: WestAnalysis;
}

export interface CompatibilityResultData {
    score: {
        total: number;
        east: number;
        west: number;
    };
    grade: string;
    grade_label: string;
    score_range: string;
    message: CompatibilityMessage;
}

// Backend Response Type
export interface CompatibilityResponse {
    id: number;
    targetId?: number;
    targetName: string;
    relationType?: string;
    resultData: CompatibilityResultData; // AI 분석 결과
    createdAt: string;
}

/**
 * COMPAT-001: Create Compatibility Analysis
 */
export const createCompatibility = async (data: CompatibilityRequest): Promise<CompatibilityResponse> => {
    const response = await api.post<any>('/compatibility/results', data);
    return response.data.data;
};

/**
 * COMPAT-002: Get Compatibility History List
 */
export const getCompatibilityHistory = async (): Promise<CompatibilityResponse[]> => {
    const response = await api.get<any>('/compatibility/results');
    return response.data.data;
};

/**
 * COMPAT-003: Get Compatibility Detail
 */
export const getCompatibilityDetail = async (resultId: number): Promise<CompatibilityResponse> => {
    const response = await api.get<any>(`/compatibility/results/${resultId}`);
    return response.data.data;
};
