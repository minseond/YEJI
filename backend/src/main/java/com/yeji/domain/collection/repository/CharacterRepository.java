package com.yeji.domain.collection.repository;

import com.yeji.domain.collection.entity.Character;
import com.yeji.domain.collection.entity.CharacterType;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CharacterRepository extends JpaRepository<Character, Long> {
    List<Character> findAllByIsActiveTrue();
    List<Character> findAllByTypeAndIsActiveTrue(CharacterType type);
}