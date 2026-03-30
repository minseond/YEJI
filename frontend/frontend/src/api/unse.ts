import api from './axios';

// Interfaces for Requests
export interface UnseGreetingRequest {
    session_id: string;
    category: string;
    force_regenerate?: boolean;
    char1_code?: string;
    char2_code?: string;
    birth_date?: string;
    birth_time?: string;
}

export interface UnseChatTurnRequest {
    session_id: string;
    message: string;
    char1_code?: string;
    char2_code?: string;
}

// Interfaces for Responses
export interface UnseMessage {
    character: string;
    type: string; // 'GREETING', 'QUESTION', 'ANSWER'
    content: string;
    timestamp: string;
}

export interface UnseGreetingResponse {
    session_id: string; // AI session ID
    category: string;
    messages: UnseMessage[];
    turn: number;
    suggested_question: string;
    is_complete: boolean;
}

export interface UnseChatTurnResponse {
    session_id: string;
    message?: string; // AI answer
    messages?: UnseMessage[];
    event?: string;
}

export interface FortuneChatSummary {
    session_id: string;
    category: string;
    fortune_type: string;
    fortune: {
        character: string;
        score: number;
        one_line: string;
        keywords: string[];
        detail: string;
    };
}

export interface AnalysisSection {
    section: string;
    title: string;
    description: string;
}

export interface TodayFortuneAnalysis {
    fortune_id: string;
    fortune_type: string;
    category: string;
    score: string;
    keyword: string;
    details: AnalysisSection[];
    cache_source: string;
}

// Helper for Character Mapping
import { getCharacterSettings } from '../utils/character';

// Mappings as per user request
export const EAST_CHAR_MAP: Record<string, string> = {
    'soiseol': 'SOISEOL',
    'buchae_woman': 'HWARIN',
    'sinseon': 'CHEONGWOON'
};

export const WEST_CHAR_MAP: Record<string, string> = {
    'stella': 'STELLA',
    'Ticker': 'KYLE',
    'princess': 'ELARIA'
};

export const getRegionByCode = (code: string): 'east' | 'west' => {
    const westCodes = Object.values(WEST_CHAR_MAP);
    if (westCodes.includes(code)) return 'west';
    return 'east';
};

// API Functions
export const startGreeting = async (data: UnseGreetingRequest): Promise<UnseGreetingResponse> => {
    // Get current character settings
    const settings = getCharacterSettings();

    // Map to API Enums
    const char1 = EAST_CHAR_MAP[settings.east] || 'SOISEOL';
    const char2 = WEST_CHAR_MAP[settings.west] || 'STELLA';

    // Update Request Data
    const requestData = {
        ...data,
        char1_code: char1,
        char2_code: char2
    };

    const response = await api.post<any>('/unse/prompt', requestData);
    // Backend returns ApiResponse<UnseGreetingResponse>, so data.data is the payload
    return response.data.data;
};

export const sendChatTurn = async (data: UnseChatTurnRequest): Promise<UnseChatTurnResponse> => {
    // Get current character settings
    const settings = getCharacterSettings();
    const char1 = EAST_CHAR_MAP[settings.east] || 'SOISEOL';
    const char2 = WEST_CHAR_MAP[settings.west] || 'STELLA';

    const requestData = {
        ...data,
        char1_code: char1,
        char2_code: char2
    };

    const response = await api.post<any>('/unse/chat/turn', requestData);
    return response.data.data;
};

export const startSession = async (): Promise<{ session_id: string }> => {
    // Get current character settings
    const settings = getCharacterSettings();

    // Map to API Enums
    const char1 = EAST_CHAR_MAP[settings.east] || 'SOISEOL';
    const char2 = WEST_CHAR_MAP[settings.west] || 'STELLA';

    const response = await api.post<any>('/session/start', {
        char1_code: char1,
        char2_code: char2
    });
    return response.data.data;
};

export const getSessionSummary = async (sessionId: string, type: 'eastern' | 'western', category: string): Promise<FortuneChatSummary> => {
    // Backend endpoint: /unse/final/{sessionId} (Confirmed via UnseController.java)
    const response = await api.get<any>(`/unse/final/${sessionId}`, {
        params: { type } // Controller doesn't take 'category' param
    });
    return response.data.data; // ApiResponse.ok wraps result in 'data'
};

export const getTodayAnalysis = async (sessionId: string, type: 'east' | 'west', category: string): Promise<TodayFortuneAnalysis> => {
    // API endpoint: /unse/today/analysis/{sessionId}?type=...&category=...
    const response = await api.get<any>(`/unse/today/analysis/${sessionId}`, {
        params: { type, category }
    });
    return response.data.data;
};

export async function* sendChatTurnStream(data: UnseChatTurnRequest): AsyncGenerator<any, void, unknown> {
    const token = localStorage.getItem('accessToken');

    // Get current character settings
    const settings = getCharacterSettings();
    const char1 = EAST_CHAR_MAP[settings.east] || 'SOISEOL';
    const char2 = WEST_CHAR_MAP[settings.west] || 'STELLA';

    const requestData = {
        ...data,
        char1_code: char1,
        char2_code: char2
    };

    try {
        const response = await fetch('/unse/chat/turn', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error("API Error Response Body:", errorText);
            throw new Error(`API Error ${response.status}: ${errorText}`);
        }

        if (!response.body) return;

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const blocks = buffer.split('\n\n');
            buffer = blocks.pop() || '';

            for (const block of blocks) {
                const lines = block.split('\n');
                for (const line of lines) {
                    if (line.startsWith('data:')) {
                        const jsonStr = line.replace('data:', '').trim();
                        if (!jsonStr) continue;
                        try {
                            const parsed = JSON.parse(jsonStr);
                            yield parsed;
                        } catch (e) {
                            console.error("Stream parse error", e);
                        }
                    }
                }
            }
        }

        // Process remaining buffer if any
        if (buffer.trim()) {
            const lines = buffer.split('\n');
            for (const line of lines) {
                if (line.startsWith('data:')) {
                    const jsonStr = line.replace('data:', '').trim();
                    if (!jsonStr) continue;
                    try {
                        yield JSON.parse(jsonStr);
                    } catch (e) {
                        console.error("Stream parse error (final)", e);
                    }
                }
            }
        }
    } catch (e) {
        console.error("sendChatTurnStream encountered error:", e);
        throw e;
    }
}

// History Interfaces
// History Interfaces
export interface UnseResultListItem {
    id: number;
    category: string;
    status: string; // 'COMPLETE' etc.
    score: number;
    created_at: string; // LocalDateTime string
}

export interface UnseResultDetail {
    id: number;
    category: string;
    status: string;
    score: number;
    analysis_result: any; // JSON structure containing summary, details, etc.
    created_at: string;
}

// History API Functions
export const getUnseHistory = async (): Promise<UnseResultListItem[]> => {
    const response = await api.get<any>('/unse/history');
    return response.data.data;
};

export const getUnseDetail = async (resultId: number): Promise<UnseResultDetail> => {
    const response = await api.get<any>(`/unse/result/${resultId}`);
    return response.data.data;
};
