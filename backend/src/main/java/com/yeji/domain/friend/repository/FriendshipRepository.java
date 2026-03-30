package com.yeji.domain.friend.repository;

import com.yeji.domain.friend.entity.Friendship;
import com.yeji.domain.friend.entity.FriendshipStatus;
import com.yeji.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

public interface FriendshipRepository extends JpaRepository<Friendship, Long> {

    // User 엔티티의 id 필드 사용 (f.requester.id)
    @Query("SELECT f FROM Friendship f LEFT JOIN FETCH f.requester LEFT JOIN FETCH f.receiver " +
            "WHERE (f.requester.id = :userId OR f.receiver.id = :userId)")
    List<Friendship> findAllByUserId(@Param("userId") Long userId);

    @Query("SELECT f FROM Friendship f LEFT JOIN FETCH f.requester LEFT JOIN FETCH f.receiver " +
            "WHERE (f.requester.id = :userId OR f.receiver.id = :userId) AND f.status = :status")
    List<Friendship> findAllByUserIdAndStatus(@Param("userId") Long userId, @Param("status") FriendshipStatus status);

    @Query("SELECT f FROM Friendship f " +
            "WHERE (f.requester = :u1 AND f.receiver = :u2) OR (f.requester = :u2 AND f.receiver = :u1)")
    Optional<Friendship> findRelation(@Param("u1") User u1, @Param("u2") User u2);

    // 받은 친구 요청 목록 조회 (Receiver가 나이고, 상태가 Pending인 경우)
    List<Friendship> findAllByReceiverIdAndStatus(Long receiverId, FriendshipStatus status);
}