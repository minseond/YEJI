package com.yeji.domain.user.repository;

import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.entity.UserSettings;
import org.springframework.data.jpa.repository.JpaRepository;

public interface UserSettingsRepository extends JpaRepository<UserSettings, Long> {
    Long user(User user);
    // PK가 user_id이므로 기본 Reserved Method인 findById로 조회 가능
}