package com.yeji.domain.unse.dto.flow;

import com.fasterxml.jackson.annotation.JsonInclude;

import java.time.Instant;

public class UnseFlowModels {

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record SessionState(
            String session_id,
            Long user_id,
            String phase,
            int turn_count,
            int question_count
    ) {}

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record Message(
            String id,
            String character,
            String type,
            String content,
            Instant timestamp,
            Object meta
    ) {}

    @JsonInclude(JsonInclude.Include.NON_NULL)
    public record CooldownInfo(
            boolean has_cooldown,
            long remaining_seconds,
            Integer fp_cost
    ) {}
}
