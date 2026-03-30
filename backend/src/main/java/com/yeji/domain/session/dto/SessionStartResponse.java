package com.yeji.domain.session.dto;

import java.time.Instant;
import java.util.List;

public record SessionStartResponse(
        String session_id,
        Long user_id,
        List<ServiceItem> services,
        Message welcome_message
) {
    public record ServiceItem(String id, String label, String icon, String description) {}
    public record Message(String id, String character, String type, String content, Instant timestamp) {}
}
