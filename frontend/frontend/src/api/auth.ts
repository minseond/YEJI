import api from './axios';

// Login Request Type
interface LoginRequest {
    email: string;
    password: string;
}

// Token Response Type
interface TokenResponse {
    accessToken: string;
    refreshToken: string;
}

export interface UserResponse {
    id: number;
    email: string;
    nickname: string;
    profileImg: string;
    nameKor: string | null;
    birthDate: string | null; // "YYYY-MM-DD"
    birthTime: string | null; // "HH:MM:SS"
    isSolar: boolean;
    gender: 'M' | 'F' | null;
    equipEast?: {
        id: number;
        name: string;
        type: 'EAST' | 'WEST';
        imageUrl: string;
    } | null;
    equipWest?: {
        id: number;
        name: string;
        type: 'EAST' | 'WEST';
        imageUrl: string;
    } | null;
}

export interface UserUpdateRequest {
    nickname?: string;
    profileImg?: string;
    nameKor?: string;
    nameChn?: string;
    birthDate?: string;
    birthTime?: string;
    isSolar?: boolean;
    gender?: 'M' | 'F';
}

export const login = async (data: LoginRequest): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/user/login', data);
    return response.data;
};

export const getUserInfo = async (userId: number): Promise<UserResponse> => {
    const response = await api.get<UserResponse>(`/user/${userId}`);
    return response.data;
};

// Signup Request Type
export interface SignupRequest {
    email: string;
    password: string;
    nickname: string;
}

export const signup = async (data: SignupRequest): Promise<UserResponse> => {
    const response = await api.post<UserResponse>('/user/signup', data);
    return response.data;
};

export const updateProfile = async (data: UserUpdateRequest): Promise<UserResponse> => {
    const response = await api.patch<UserResponse>('/user/me', data);
    return response.data;
};


export const verifyPassword = async (password: string): Promise<boolean> => {
    try {
        await api.post('/user/verify-password', { password });
        return true;
    } catch (error) {
        return false;
    }
};

// --- Password Reset APIs ---

export interface EmailRequest {
    email: string;
}

export interface EmailVerificationRequest {
    email: string;
    code: string;
}

export interface PasswordResetRequest {
    email: string;
    code: string;
    newPassword: string;
}

export const sendEmailVerification = async (email: string): Promise<void> => {
    await api.post('/user/email/send', { email });
};

export const verifyEmail = async (data: EmailVerificationRequest): Promise<boolean> => {
    const response = await api.post<boolean>('/user/email/verify', data);
    return response.data;
};

export const resetPassword = async (data: PasswordResetRequest): Promise<void> => {
    await api.post('/user/password/reset', data);
};

// --- User Settings APIs ---

export interface UserSettings {
    pushEnabled: boolean;
    marketingAgreed: boolean;
    soundEnabled: boolean;
    vibEnabled: boolean;
}

export interface UserSettingsUpdateRequest {
    pushEnabled?: boolean;
    marketingAgreed?: boolean;
    soundEnabled?: boolean;
    vibEnabled?: boolean;
}

export const fetchSettings = async (userId: number): Promise<UserSettings> => {
    const response = await api.get<UserSettings>(`/user/${userId}/settings`);
    return response.data;
};

export const updateSettings = async (userId: number, data: UserSettingsUpdateRequest): Promise<UserSettings> => {
    const response = await api.patch<UserSettings>(`/user/${userId}/settings`, data);
    return response.data;
};

// --- Account Deletion ---

export const sendWithdrawVerification = async (): Promise<void> => {
    await api.post('/user/me/withdraw/send');
};

export const withdrawUser = async (code: string): Promise<void> => {
    // Axios DELETE requests with body need 'data' property
    await api.delete('/user/me', { data: { code } });
};

// --- Duplicate Check APIs ---

export const checkEmailDuplication = async (email: string): Promise<boolean> => {
    const response = await api.get<boolean>(`/user/check-email?email=${email}`);
    return response.data;
};

export const checkNicknameDuplication = async (nickname: string): Promise<boolean> => {
    const response = await api.get<boolean>(`/user/check-nickname?nickname=${nickname}`);
    return response.data;
};

