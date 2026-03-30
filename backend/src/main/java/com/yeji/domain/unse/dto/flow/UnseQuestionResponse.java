package com.yeji.domain.unse.dto.flow;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.databind.JsonNode;
import com.yeji.domain.unse.dto.flow.UnseFlowModels.Message;
import com.yeji.domain.unse.dto.flow.UnseFlowModels.SessionState;

import java.util.List;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record UnseQuestionResponse(
        SessionState session,
        int free_limit,
        //무료 3회 넘어서 FP 차감 발생했는지 표시
        boolean charged,
        List<Message> messages,
        JsonNode answer,
        String next_action
) {}
