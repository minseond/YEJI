package com.yeji.domain.collection.entity;

import jakarta.persistence.*;
import lombok.AccessLevel;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Entity
@Table(name = "characters")
public class Character {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    @Column(name = "character_id")
    private Long id;

    @Column(nullable = false, length = 50)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private CharacterType type;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private CharacterGrade grade;

    @Column(name = "image_url", length = 500)
    private String imageUrl;

    @Column(name = "model_url", length = 500)
    private String modelUrl;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(name = "is_active", nullable = false)
    private boolean isActive;

    @Builder
    public Character(String name, CharacterType type, CharacterGrade grade, String imageUrl, String modelUrl, String description, boolean isActive) {
        this.name = name;
        this.type = type;
        this.grade = grade;
        this.imageUrl = imageUrl;
        this.modelUrl = modelUrl;
        this.description = description;
        this.isActive = isActive;
    }
}