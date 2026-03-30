import instance from './axios';

export interface WalletResponse {
    userId: number;
    balance: number;
    updatedAt: string;
}

export interface TokenHistoryResponse {
    id: number;
    amount: number;
    type: string; // CHARGE, USE
    description: string;
    createdAt: string;
}

// 1. Get My Wallet (Balance)
export const getMyWallet = async (): Promise<WalletResponse> => {
    const response = await instance.get<WalletResponse>('/wallet');
    return response.data;
};

// 2. Get Token History (Optional for now)
export const getTokenHistory = async (page = 0, size = 20) => {
    const response = await instance.get(`/wallet/history?page=${page}&size=${size}`);
    return response.data;
};
