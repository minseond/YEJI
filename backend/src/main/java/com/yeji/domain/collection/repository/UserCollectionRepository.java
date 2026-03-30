package com.yeji.domain.collection.repository;

import com.yeji.domain.collection.entity.UserCollection;
import com.yeji.domain.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface UserCollectionRepository extends JpaRepository<UserCollection, Long> {

    @Query("SELECT uc FROM UserCollection uc JOIN FETCH uc.character c WHERE uc.user.id = :userId")
    List<UserCollection> findAllByUserIdWithCharacter(@Param("userId") Long userId);

    boolean existsByUserIdAndCharacterId(Long userId, Long characterId);

    Long user(User user);
}