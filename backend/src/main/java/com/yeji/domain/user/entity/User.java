package com.yeji.domain.user.entity;

import com.yeji.domain.collection.entity.Character;
import com.yeji.domain.user.dto.UserUpdateRequest;
import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import org.hibernate.annotations.SQLDelete;
import org.hibernate.annotations.SQLRestriction;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;

@Entity
@Getter
@Table(name = "users")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@SQLDelete(sql = "UPDATE users SET deleted_at = CURRENT_TIMESTAMP WHERE user_id = ?")
@SQLRestriction("deleted_at IS NULL")
@EntityListeners(AuditingEntityListener.class)
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "user_id")
    private Long id;

    @Column(name = "email", unique = true, length = 255)
    private String email;

    @Column(name = "password", length = 255)
    private String password;

    @Column(name = "nickname", length = 100)
    private String nickname;

    @Column(name = "profile_img", length = 500)
    private String profileImg;

    @Column(name = "provider", length = 20)
    private String provider; // KAKAO, NAVER, GOOGLE, EMAIL

    // 소셜 가입 초기에는 비어있을 수 있음 -> nullable = true (기본값)
    @Column(name = "birth_date")
    private LocalDate birthDate;

    @Column(name = "birth_time")
    private LocalTime birthTime;

    @Column(name = "gender", length = 10)
    private String gender;

    @Column(name = "name_kor", length = 50)
    private String nameKor;

    @Column(name = "name_chn", length = 50)
    private String nameChn;

    @Column(name = "is_solar", nullable = false)
    private boolean isSolar = true;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "equip_east_id")
    private Character equipEast;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "equip_west_id")
    private Character equipWest;

    @CreatedDate
    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "deleted_at")
    private LocalDateTime deletedAt;

    @Builder
    public User(String email, String password, String nickname, String provider, String profileImg,
                LocalDate birthDate, LocalTime birthTime, String gender, boolean isSolar, String nameKor) {
        this.email = email;
        this.password = password;
        this.nickname = nickname;
        this.provider = provider;
        this.profileImg = profileImg; // 추가됨
        this.birthDate = birthDate;
        this.birthTime = birthTime;
        this.gender = gender;
        this.isSolar = isSolar;
        this.nameKor = nameKor;
    }

    // 기존 메서드 유지 (하위 호환성 위해)
    public void updateProfile(String nickname, String profileImg, String nameKor, String nameChn) {
        if (nickname != null) this.nickname = nickname;
        if (profileImg != null) this.profileImg = profileImg;
        if (nameKor != null) this.nameKor = nameKor;
        if (nameChn != null) this.nameChn = nameChn;
    }

    // 회원 정보 수정 메서드 (UserUpdateRequest 사용)
    public void updateUserInfo(UserUpdateRequest request) {
        if (request.getNickname() != null) this.nickname = request.getNickname();
        if (request.getProfileImg() != null) this.profileImg = request.getProfileImg();
        if (request.getNameKor() != null) this.nameKor = request.getNameKor();
        if (request.getNameChn() != null) this.nameChn = request.getNameChn();
        if (request.getGender() != null) this.gender = request.getGender();
        if (request.getBirthDate() != null) this.birthDate = request.getBirthDate();
        if (request.getBirthTime() != null) this.birthTime = request.getBirthTime();
        if (request.getIsSolar() != null) this.isSolar = request.getIsSolar();
    }

    // 소셜 로그인 업데이트 (이미 가입된 경우 정보 갱신)
    public User updateSocialInfo(String nickname, String profileImg) {
        if (nickname != null && this.nickname == null) this.nickname = nickname;
        if (profileImg != null) this.profileImg = profileImg;
        return this;
    }

    // 비밀번호 변경 편의 메서드
    public void updatePassword(String encryptedPassword) {
        this.password = encryptedPassword;
    }

    // 캐릭터 장착 메서드
    public void equipCharacter(Character character, boolean isEast) {
        if (isEast) {
            this.equipEast = character;
        } else {
            this.equipWest = character;
        }
    }
}