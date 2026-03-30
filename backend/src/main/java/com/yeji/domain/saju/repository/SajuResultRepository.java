package com.yeji.domain.saju.repository;

import com.yeji.domain.saju.entity.SajuResult;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;

public interface SajuResultRepository extends JpaRepository<SajuResult, Long> {

    //유저당 1개 결과
    Optional<SajuResult> findByUser_Id(Long userId);

    //히스토리 (update 돼서 바뀌면 최신 결과만 띄우기)
    List<SajuResult> findAllByUser_IdOrderByUpdatedAtDesc(Long userId);


}
