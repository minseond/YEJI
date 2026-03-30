package com.yeji.domain.friend.service;

import com.yeji.domain.friend.dto.FriendResponse;
import com.yeji.domain.friend.entity.Friendship;
import com.yeji.domain.friend.entity.FriendshipStatus;
import com.yeji.domain.friend.repository.FriendshipRepository;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import com.yeji.global.jwt.AuthUser;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class FriendService {
    private final FriendshipRepository friendshipRepository;
    private final UserRepository userRepository;

    // FRIEND-001 친구 검색
    public List<FriendResponse> searchFriends(String keyword) {
        List<User> users = userRepository.findByNicknameContaining(keyword);
        return users.stream()
                .map(FriendResponse::fromUser)
                .collect(Collectors.toList());
    }

    // FRIEND-002 친구 요청
    @Transactional
    public void requestFriend(AuthUser authUser, Long targetUserId) {
        if (authUser.getUserId().equals(targetUserId)) {
            throw new IllegalStateException("자기 자신에게 친구 요청을 보낼 수 없습니다!");
        }

        User requester = userRepository.findById(authUser.getUserId())
                .orElseThrow(() -> new IllegalArgumentException("사용자를 찾을 수 없습니다."));
        User receiver = userRepository.findById(targetUserId)
                .orElseThrow(() -> new IllegalArgumentException("해당 유저를 찾을 수 없습니다."));

        if (friendshipRepository.findRelation(requester, receiver).isPresent()) {
            throw new IllegalArgumentException("이미 친구 관계이거나, 친구 요청이 발송된 상태입니다.");
        }

        Friendship friendship = Friendship.builder()
                .requester(requester)
                .receiver(receiver)
                .status(FriendshipStatus.PENDING)
                .build();

        friendshipRepository.save(friendship);
    }

    // FRIEND-003 요청 처리(수락, 거절)
    @Transactional
    public void handleRequest(AuthUser authUser, Long requestId, boolean accept) {
        Friendship friendship = friendshipRepository.findById(requestId)
                .orElseThrow(() -> new IllegalArgumentException("요청을 찾을 수 없습니다."));

        if (!friendship.getReceiver().getId().equals(authUser.getUserId())) {
            throw new IllegalArgumentException("본인에게 온 요청만 처리할 수 있습니다.");
        }

        if (accept) {
            friendship.accept();
        } else {
            friendshipRepository.delete(friendship);
        }
    }

    // FRIEND-004 친구 목록
    public List<FriendResponse> getMyFriends(AuthUser authUser) {
        return friendshipRepository.findAllByUserIdAndStatus(authUser.getUserId(), FriendshipStatus.ACCEPTED).stream()
                .map(f -> FriendResponse.from(f, authUser.getUserId()))
                .collect(Collectors.toList());
    }

    // FRIEND-005 친구 삭제
    @Transactional
    public void deleteFriend(AuthUser authUser, Long friendUserId) {
        User me = userRepository.getReferenceById(authUser.getUserId());
        User friend = userRepository.getReferenceById(friendUserId);

        Friendship friendship = friendshipRepository.findRelation(me, friend)
                .orElseThrow(() -> new IllegalArgumentException("친구 관계가 아닌 사용자입니다."));

        friendshipRepository.delete(friendship);
    }

    // FRIEND-006 받은 친구 요청 목록
    public List<FriendResponse> getReceivedRequests(AuthUser authUser) {
        // 내가 Receiver이고 Status가 PENDING인 목록 조회
        return friendshipRepository.findAllByReceiverIdAndStatus(authUser.getUserId(), FriendshipStatus.PENDING).stream()
                .map(f -> FriendResponse.from(f, authUser.getUserId())) // 요청을 보낸 사람(Requester) 정보를 반환
                .collect(Collectors.toList());
    }
}