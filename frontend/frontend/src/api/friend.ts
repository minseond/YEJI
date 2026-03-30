import api from './axios';

export interface Friend {
    friendshipId?: number;  // 친구관계 ID (검색 시에는 없음)
    userId: number;         // 유저 ID
    nickname: string;       // 닉네임
    name?: string;          // 실제 이름 (선택적)
    profileImg?: string;    // 프로필 이미지 URL
    status: 'PENDING' | 'ACCEPTED' | 'NONE';  // 친구 상태
}

// FRIEND-001: 친구 검색 (닉네임으로 유저 검색)
export const searchFriends = async (keyword: string): Promise<Friend[]> => {
    const response = await api.get<{ data: Friend[] }>('/friends/search', {
        params: { keyword }
    });
    return response.data.data;
};

// FRIEND-002: 친구 요청 보내기
export const sendFriendRequest = async (targetUserId: number): Promise<void> => {
    await api.post('/friends/requests', { targetUserId });
};

// FRIEND-003: 친구 요청 처리 (수락/거절)
export const handleFriendRequest = async (requestId: number, accept: boolean): Promise<void> => {
    await api.patch(`/friends/requests/${requestId}`, { accept });
};

// FRIEND-004: 내 친구 목록 조회
export const getMyFriends = async (): Promise<Friend[]> => {
    const response = await api.get<{ data: Friend[] }>('/friends');
    return response.data.data;
};

// FRIEND-005: 친구 삭제
export const deleteFriend = async (friendUserId: number): Promise<void> => {
    await api.delete(`/friends/${friendUserId}`);
};

// FRIEND-006: 받은 친구 요청 목록 조회
export const getPendingRequests = async (): Promise<Friend[]> => {
    const response = await api.get<{ data: Friend[] }>('/friends/pending');
    return response.data.data;
};
