package com.yeji.domain.user.entity;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDateTime;

@Entity
@Getter
@Table(name = "user_settings")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@EntityListeners(AuditingEntityListener.class)
public class UserSettings {

    @Id
    @Column(name = "user_id")
    private Long id; // User ID와 동일한 값을 가짐 (Shared PK)

    @OneToOne(fetch = FetchType.LAZY)
    @MapsId // User의 PK를 이 테이블의 PK이자 FK로 사용
    @JoinColumn(name = "user_id")
    private User user;

    @Column(name = "push_enabled", nullable = false)
    private boolean pushEnabled;

    @Column(name = "marketing_agreed", nullable = false)
    private boolean marketingAgreed;

    @Column(name = "sound_enabled", nullable = false)
    private boolean soundEnabled;

    @Column(name = "vib_enabled", nullable = false)
    private boolean vibEnabled;

    @LastModifiedDate
    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @Builder
    public UserSettings(User user, boolean pushEnabled, boolean marketingAgreed, boolean soundEnabled, boolean vibEnabled) {
        this.user = user;
        this.pushEnabled = pushEnabled;
        this.marketingAgreed = marketingAgreed;
        this.soundEnabled = soundEnabled;
        this.vibEnabled = vibEnabled;
    }

    // 기본 설정값 생성 메서드
    public static UserSettings createDefault(User user) {
        return UserSettings.builder()
                .user(user)
                .pushEnabled(true)
                .marketingAgreed(false)
                .soundEnabled(true)
                .vibEnabled(true)
                .build();
    }

    public void update(Boolean pushEnabled, Boolean marketingAgreed, Boolean soundEnabled, Boolean vibEnabled) {
        if (pushEnabled != null) this.pushEnabled = pushEnabled;
        if (marketingAgreed != null) this.marketingAgreed = marketingAgreed;
        if (soundEnabled != null) this.soundEnabled = soundEnabled;
        if (vibEnabled != null) this.vibEnabled = vibEnabled;
    }
}