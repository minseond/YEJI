package com.yeji.domain.unse.dto.flow;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.yeji.domain.unse.dto.flow.UnseFlowModels.CooldownInfo;
import com.yeji.domain.unse.dto.flow.UnseFlowModels.Message;
import com.yeji.domain.unse.dto.flow.UnseFlowModels.SessionState;

import java.util.List;

@JsonInclude(JsonInclude.Include.NON_NULL)
public record UnsePromptResponse(
        SessionState session,
        //최근 12시간 이내 생성 여부/남은 시간
        CooldownInfo cooldown,
        //"지금 분석중" 이런 메시지
        List<Message> messages,
        //스트림 열기
        String next_action,
        String hint
) {}
