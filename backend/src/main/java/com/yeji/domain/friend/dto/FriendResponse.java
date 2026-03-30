package com.yeji.domain.friend.dto;

import com.yeji.domain.friend.entity.Friendship;
import com.yeji.domain.user.entity.User;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class FriendResponse {
    private Long friendshipId;
    private Long userId;
    private String nickname;
    private String profileImg;
    private String status;

    public static FriendResponse from(Friendship friendship, Long currentUserId) {
        // currentUserId는 AuthUser에서 오므로 ID 비교
        // User 엔티티의 식별자는 getId() 사용
        boolean isRequester = friendship.getRequester().getId().equals(currentUserId);
        User friend = isRequester ? friendship.getReceiver() : friendship.getRequester();

        return FriendResponse.builder()
                .friendshipId(friendship.getId())
                .userId(friend.getId()) // User.getId()
                .nickname(friend.getNickname())
                .profileImg(friend.getProfileImg())
                .status(friendship.getStatus().name())
                .build();
    }

    // 검색용
    public static FriendResponse fromUser(User user) {
        return FriendResponse.builder()
                .userId(user.getId()) // User.getId()
                .nickname(user.getNickname())
                .profileImg(user.getProfileImg())
                .status("NONE") // 친구 관계 아님
                .build();
    }
}