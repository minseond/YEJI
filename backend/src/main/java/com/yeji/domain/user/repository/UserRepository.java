package com.yeji.domain.user.repository;

import com.yeji.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface UserRepository extends JpaRepository<User, Long> {

    // 소셜 로그인 시 이메일로 회원을 찾기 위해 사용
    Optional<User> findByEmail(String email);

    // 닉네임 중복 체크용
    boolean existsByNickname(String nickname);

    Optional<User> findByNickname(String nickname);

    // 소셜 기능 친구 찾을 때
    List<User> findByNicknameContaining(String nickname);

}