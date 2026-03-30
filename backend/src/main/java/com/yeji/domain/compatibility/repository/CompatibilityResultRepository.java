package com.yeji.domain.compatibility.repository;

import com.yeji.domain.compatibility.entity.CompatibilityResult;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface CompatibilityResultRepository extends JpaRepository<CompatibilityResult, Long> {
    // requester의 User 엔티티 필드가 id 이므로, ByRequester_Id 로 참조
    List<CompatibilityResult> findAllByRequester_IdOrderByCreatedAtDesc(Long userId);
}