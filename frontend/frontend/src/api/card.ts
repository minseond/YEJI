import api from './axios';

export type CardCategory = 'TARO' | 'HWATU';

export interface CardSelectedCardRequest {
    cardCode: number;
    position: number;
    isReversed: boolean;
}

export interface CardCreateReadingRequest {
    category: CardCategory;
    topic: string; // 'MONEY' | 'LOVE' | 'CAREER' | 'HEALTH' | 'STUDY'
    cards: CardSelectedCardRequest[];
}

export interface CardSelectedCardResponse {
    cardCode: number;
    position: number;
    isReversed: boolean;
}

export interface AiCard {
    position: number;
    position_label: string;
    positionLabel?: string;
    card_code: number;
    cardCode?: number;
    card_name: string;
    cardName?: string;
    card_type: string;
    cardType?: string;
    card_month: number;
    cardMonth?: number;
    keywords: string[];
    is_reversed: boolean;
    isReversed?: boolean;
    interpretation: string;
}

export interface AiSummary {
    overall_theme: string;
    past_to_present?: string;
    present_to_future?: string;
    flow_analysis?: string;
    advice: string;
}

export interface AiLucky {
    color: string;
    luckyColor?: string; // Potential alias
    number: string;
    luckyNumber?: string; // Potential alias
    element?: string;
    direction?: string;
    luckyDirection?: string; // Potential alias
    timing: string;
    luckyTime?: string; // Potential alias
}

export interface AiReadingData {
    meta?: {
        model: string;
        generated_at: string;
    };
    category?: string;
    spread_type?: string;
    question?: string;
    cards?: AiCard[];
    summary?: AiSummary;
    lucky?: AiLucky;
    badges?: string[];
    message?: string; // For fallback/stub
    [key: string]: any;
}

export interface AiReadingResponse {
    success: boolean;
    validated: boolean;
    type: string;
    data: AiReadingData;
    errors: any;
    latency_ms: number;
    message?: string; // Root level fallback
    [key: string]: any;
}

export interface CardResultDetailResponse {
    cardResultId: number;
    userId: number;
    category: CardCategory;
    question: string;
    aiReading: AiReadingResponse;
    score: number;
    status: string;
    createdAt: string;
    cards: CardSelectedCardResponse[];
}

/**
 * Create a new card reading (Taro/Hwatu)
 */
export const createCardReading = async (data: CardCreateReadingRequest): Promise<CardResultDetailResponse> => {
    const response = await api.post<any>('/cards/readings', data);
    return response.data.data ? response.data.data : response.data; // Safely unwrap if backend uses ApiResponse wrapper
};



/**
 * Get Card History List (Correct Endpoint)
 */
export const getCardHistoryList = async (params?: { category?: CardCategory; from?: string; to?: string }): Promise<CardResultDetailResponse[]> => {
    const response = await api.get<any>('/cards/history', { params });
    return response.data.data ? response.data.data : response.data;
};

/**
 * Get Card History Detail
 */
export const getCardHistoryDetail = async (cardResultId: number): Promise<CardResultDetailResponse> => {
    const response = await api.get<any>(`/cards/history/${cardResultId}`);
    return response.data.data ? response.data.data : response.data;
};
