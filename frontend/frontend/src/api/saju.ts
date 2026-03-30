import api from './axios';
import type { IntegratedFortuneResult } from '../data/types';

// ----------------------------------------------------------------------



// Backend uses the authenticated user's stored profile data.
// No request body is needed.
export const getSajuAnalysis = async (): Promise<IntegratedFortuneResult> => {
    try {
        // Use 'any' temporarily to handle inconsistent wrapping
        const response = await api.post<any>('/saju/analyze');

        // Handle potential double-wrapping (e.g. { success: true, data: { analysis_result: ... } })
        // or single wrapping ({ success: true, analysis_result: ... })
        const body = response.data;

        if (body.data && body.data.analysis_result) {
            return body.data.analysis_result;
        }
        if (body.analysis_result) {
            return body.analysis_result;
        }

        if (body.data) {
            // Fallback: maybe body.data IS the result? (Check against 'eastern' key)
            if (body.data.eastern) return body.data;
        }

        throw new Error("Invalid API Response format: analysis_result missing");
    } catch (error) {
        console.error("[SajuAPI] Request Failed:", error);
        throw error;
    }
};

export const getSajuResult = async (): Promise<IntegratedFortuneResult> => {
    try {
        const response = await api.get<any>('/saju/result');

        // Same wrapping logic as analyze
        const body = response.data;
        if (body.data && body.data.analysis_result) {
            return body.data.analysis_result;
        }
        if (body.analysis_result) {
            return body.analysis_result;
        }
        if (body.data && body.data.eastern) {
            return body.data;
        }

        throw new Error("Invalid API Response format for /saju/result");
    } catch (error) {
        console.error("[SajuAPI] getSajuResult Failed:", error);
        throw error;
    }
};

export interface SajuHistoryResponse {
    user_info: {
        name: string;
        gender: 'M' | 'F';
        birth_year: number;
        birth_month: number;
        birth_day: number;
        birth_time: string;
        calendar_type: string;
    };
    analysis_result: IntegratedFortuneResult;
}

export const getSajuHistory = async (): Promise<SajuHistoryResponse> => {
    try {
        const response = await api.get<any>('/saju/history');
        const body = response.data;

        // Backend returns: { success: true, meta: {...}, analysis_result: {...} }
        // But we need user_info, so we'll fetch it separately or return without it
        if (body.data && body.data.analysis_result) {
            return {
                user_info: null as any, // Backend doesn't provide user_info in this endpoint
                analysis_result: body.data.analysis_result
            };
        }

        // Direct structure
        if (body.analysis_result) {
            return {
                user_info: null as any,
                analysis_result: body.analysis_result
            };
        }

        throw new Error("Invalid API Response format for /saju/history");
    } catch (error) {
        console.error("[SajuAPI] getSajuHistory Failed:", error);
        throw error;
    }
};
