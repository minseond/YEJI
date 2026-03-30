package com.yeji.domain.session.service;

import com.yeji.domain.session.dto.SessionStartResponse;
import com.yeji.domain.session.model.SessionPhase;
import com.yeji.domain.session.model.UserSession;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class SessionService {

    private final Map<String, UserSession> sessions = new ConcurrentHashMap<>();

    public SessionStartResponse start(Long userId, String char1Code, String char2Code) {
        String sessionId = "sess_" + UUID.randomUUID().toString().replace("-", "");
        UserSession session = new UserSession(sessionId, userId);

        // Set character codes if provided
        if (char1Code != null && !char1Code.isBlank()) {
            session.setChar1Code(char1Code);
        }
        if (char2Code != null && !char2Code.isBlank()) {
            session.setChar2Code(char2Code);
        }

        sessions.put(sessionId, session);

        List<SessionStartResponse.ServiceItem> services = List.of(
                new SessionStartResponse.ServiceItem("fortune", "운세", "⭐", "오늘의 운세!")
        );

        SessionStartResponse.Message welcome = new SessionStartResponse.Message(
                "msg_001",
                "시스템",
                "text",
                "안녕하세요! 오늘은 어떤 이야기를 나눠볼까요?",
                Instant.now()
        );

        return new SessionStartResponse(sessionId, userId, services, welcome);
    }

    public UserSession getRequired(String sessionId, Long userId) {
        UserSession session = sessions.get(sessionId);
        if (session == null) throw new RuntimeException("세션을 찾을 수 없습니다.");
        if (!session.getUserId().equals(userId)) throw new RuntimeException("세션 접근 권한이 없습니다.");
        return session;
    }

    public void updatePhase(String sessionId, Long userId, SessionPhase phase) {
        UserSession s = getRequired(sessionId, userId);
        s.setPhase(phase);
        save(s);
    }

    public UserSession save(UserSession session) {
        if (session == null) throw new IllegalArgumentException("session is null");
        sessions.put(session.getSessionId(), session);
        return session;
    }

    /**
     * 세션 삭제 - 필요하면 사용
     */
    public void delete(String sessionId, Long userId) {
        UserSession s = getRequired(sessionId, userId);
        sessions.remove(s.getSessionId());
    }

    /**
     * 디버깅용: 현재 세션 개수
     */
    public int size() {
        return sessions.size();
    }
}
