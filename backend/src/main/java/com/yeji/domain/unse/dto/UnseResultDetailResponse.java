package com.yeji.domain.unse.dto;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import com.yeji.domain.unse.entity.UnsePair;

import java.time.LocalDateTime;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record UnseResultDetailResponse(
        Long id,
        String category,
        @JsonProperty("eastern") JsonNode eastern,
        @JsonProperty("western") JsonNode western,
        LocalDateTime created_at
) {
    public static UnseResultDetailResponse from(UnsePair r) {
        return new UnseResultDetailResponse(
                r.getId(),
                r.getCategory(),
                r.getEastern(),
                r.getWestern(),
                r.getCreatedAt()
        );
    }
}
