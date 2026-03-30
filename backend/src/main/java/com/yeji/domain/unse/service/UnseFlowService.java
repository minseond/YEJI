package com.yeji.domain.unse.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import com.yeji.domain.saju.entity.SajuResult;
import com.yeji.domain.saju.repository.SajuResultRepository;
import com.yeji.domain.session.model.SessionPhase;
import com.yeji.domain.session.model.UserSession;
import com.yeji.domain.session.service.SessionService;
import com.yeji.domain.unse.dto.flow.UnseGreetingResponse;
import com.yeji.domain.unse.dto.request.UnseGenerateRequest;
import com.yeji.domain.unse.entity.UnsePair;
import com.yeji.domain.unse.repository.UnsePairRepository;
import com.yeji.domain.unse.service.ai.UnseAiClient;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.time.LocalDateTime;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;

@Slf4j
@Service
@RequiredArgsConstructor
public class UnseFlowService {

    private final SessionService sessionService;
    private final UserRepository userRepository;
    private final SajuResultRepository sajuResultRepository;
    private final UnseAiClient unseAiClient;
    private final ObjectMapper objectMapper;
    private final UnsePairRepository unsePairRepository;
    private final TransactionTemplate transactionTemplate;

    public UnseGreetingResponse greetingAndBindSession(Long userId, UnseGenerateRequest request) {
        UserSession session = sessionService.getRequired(request.sessionId(), userId);

        session.setUnseCategory(request.category());
        session.setUnseForceRegenerate(Boolean.TRUE.equals(request.forceRegenerate()));

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        String birthDate = resolveBirthDate(user);
        String birthTime = resolveBirthTime(user);

        // 캐릭터 코드 갱신
        if (request.char1Code() != null && !request.char1Code().isBlank()) {
            session.setChar1Code(request.char1Code());
        }
        if (request.char2Code() != null && !request.char2Code().isBlank()) {
            session.setChar2Code(request.char2Code());
        }

        String categoryUpper = normalizeCategoryUpper(session.getUnseCategory());
        String char1Code = safeChar(session.getChar1Code(), "SOISEOL");
        String char2Code = safeChar(session.getChar2Code(), "STELLA");

        JsonNode greetingJson = unseAiClient.greeting(birthDate, birthTime, categoryUpper, char1Code, char2Code);

        String aiSessionId = safeText(greetingJson, "/session_id");
        if (aiSessionId == null || aiSessionId.isBlank()) {
            throw new RuntimeException("AI session_id missing in greeting");
        }

        session.setAiSessionId(aiSessionId);
        session.setPhase(SessionPhase.FORTUNE_READY);

        // ✅ 덮어쓰기 정책: 동기화 + 트랜잭션 보장
        synchronized (this) {
            transactionTemplate.executeWithoutResult(status -> {
                UnsePair pair = resolveOrCreatePair(user, categoryUpper);
                session.setResultId(pair.getId());
            });
        }

        sessionService.save(session);

        return objectMapper.convertValue(greetingJson, UnseGreetingResponse.class);
    }

    public SseEmitter openChatTurnStream(String backendSessionId, Long userId, String message) {
        UserSession session = sessionService.getRequired(backendSessionId, userId);
        SseEmitter emitter = new SseEmitter(0L);

        final String aiSessionIdSnapshot = session.getAiSessionId();
        final String char1Snapshot = safeChar(session.getChar1Code(), "SOISEOL");
        final String char2Snapshot = safeChar(session.getChar2Code(), "STELLA");

        CompletableFuture.runAsync(() -> {
            try {
                if (aiSessionIdSnapshot == null || aiSessionIdSnapshot.isBlank()) {
                    sendError(emitter, "AI session_id missing");
                    completeSafely(emitter);
                    return;
                }

                unseAiClient.streamChatTurn(aiSessionIdSnapshot, message, char1Snapshot, char2Snapshot, false)
                        .doOnNext(ev -> {
                            try { sendJson(emitter, "message", ev); } catch (Exception ignored) {}
                        })
                        .doOnError(err -> {
                            log.error("AI Stream Error: {}", err.getMessage());
                            sendError(emitter, err.getMessage());
                            completeSafely(emitter);
                        })
                        .doOnComplete(() -> completeSafely(emitter))
                        .subscribe();

            } catch (Exception e) {
                log.error("SSE Exception", e);
                sendError(emitter, e.getMessage());
                completeSafely(emitter);
            }
        });

        return emitter;
    }




    /**
     * eastern+western 둘 다 반환
     * 저장은 pair.eastern/pair.western에 최소블록으로 덮어쓰기
     */
    public JsonNode getFinalSummaryBoth(String backendSessionId, Long userId) {
        UserSession session = sessionService.getRequired(backendSessionId, userId);

        User user = userRepository.findById(userId)
                .orElseThrow(() -> new RuntimeException("User not found"));

        String categoryUpper = normalizeCategoryUpper(session.getUnseCategory());
        String categoryLower = normalizeCategoryLower(session.getUnseCategory());

        String aiSessionId = session.getAiSessionId();

        JsonNode eastern;
        JsonNode western;

        if (aiSessionId == null || aiSessionId.isBlank()) {
            ObjectNode fb = (ObjectNode) resolveHybridSummaryBoth(userId, categoryLower);
            eastern = fb.get("eastern");
            western = fb.get("western");
        } else {
            eastern = unseAiClient.getChatSummary(aiSessionId, "eastern", categoryLower);
            western = unseAiClient.getChatSummary(aiSessionId, "western", categoryLower);
        }

        // ✅ 저장용 최소 블록
        ObjectNode eastMin = extractMinimalBlock(eastern);
        ObjectNode westMin = extractMinimalBlock(western);

        // ✅ 동기화된 트랜잭션으로 저장
        synchronized (this) {
            transactionTemplate.executeWithoutResult(status -> {
                // (userId, category) 기준으로 1개만 유지: 있으면 가져오고 없으면 생성
                UnsePair pair = resolveOrCreatePair(user, categoryUpper);

                // 부분 업데이트
                pair.updateEastern(eastMin);
                pair.updateWestern(westMin);

                unsePairRepository.save(pair);

                if (session.getResultId() == null) {
                    session.setResultId(pair.getId());
                }
            });
        }

        sessionService.save(session);

        // ✅ 응답은 기존처럼 "원본 AI 응답" 그대로 내려도 되고,
        // 프론트가 최소만 원하면 eastMin/westMin으로 바꿔도 됨.
        ObjectNode root = objectMapper.createObjectNode();
        root.set("eastern", eastern);
        root.set("western", western);

        return root;
    }


    /**
     * 캐시/강제재생성 분석 조회는 그대로 유지 (저장 로직 X)
     */
    // @Transactional removed to limit scope and handle race condition
    public JsonNode getTodayAnalysis(String sessionId, Long userId, String type, String category, boolean force) {
        UserSession session = sessionService.getRequired(sessionId, userId);
        User user = userRepository.findById(userId).orElseThrow();

        String birthDate = resolveBirthDate(user);
        String birthTime = resolveBirthTime(user);
        String genderCh = resolveGender(user); // M or F

        String formattedType = normalizeType(type); // eastern or western

        // category 파라미터가 없으면 세션 카테고리를 사용
        String categoryUpper = normalizeCategoryUpper(
                (category == null || category.isBlank()) ? session.getUnseCategory() : category

        );
        log.info("[UNSE][TODAY] userId={} type={} categoryParam={} sessionCategory={} => categoryUpper={}",
                userId, formattedType, category, session.getUnseCategory(), categoryUpper);

        // fortuneId/persona는 기존 로직 유지
        String fortuneId = String.format("%s:%s:%s:%s", formattedType, birthDate, birthTime, genderCh);

        String persona = "eastern".equalsIgnoreCase(formattedType)
                ? safeChar(session.getChar1Code(), "KYLE")
                : safeChar(session.getChar2Code(), "STELLA");

        // 1) AI 호출
        JsonNode analysis = unseAiClient.getAnalysis(fortuneId, formattedType, categoryUpper, persona, force);

        // 2) 최소 블록으로 맵핑
        ObjectNode minimal = extractMinimalBlock(analysis);

        // 3,4,5) DB Update with Synchronization to prevent duplicates in parallel requests
        synchronized (this) {
            transactionTemplate.executeWithoutResult(status -> {
                // 3) pair row find or create
                UnsePair pair = resolveOrCreatePair(user, categoryUpper);

                // 4) type에 따라 부분 업데이트
                if ("eastern".equalsIgnoreCase(formattedType)) {
                    pair.updateEastern(minimal);
                } else if ("western".equalsIgnoreCase(formattedType)) {
                    pair.updateWestern(minimal);
                } else {
                    throw new RuntimeException("Invalid type: " + formattedType);
                }

                // 5) 저장 (dirty checking)
                unsePairRepository.save(pair);
                log.info("[UNSE][TODAY] saved pair: userId={} categoryUpper={} type={}", userId, categoryUpper, formattedType);
            });
        }

        // 6) 반환은 그대로(원하면 minimal만 반환해도 됨)
        return analysis;
    }


    // =========================================================
    // 핵심: 덮어쓰기 대상 Pair 결정
    // =========================================================

    private UnsePair resolveOrCreatePair(User user, String categoryUpper) {
        // [수정] 덮어쓰기 정책: "오늘 날짜"에 해당하는 기록이 있으면 덮어쓰고, 없으면 새로 생성
        LocalDateTime now = LocalDateTime.now();
        LocalDateTime startOfDay = now.toLocalDate().atStartOfDay();
        LocalDateTime endOfDay = now.toLocalDate().atTime(23, 59, 59);

        Optional<UnsePair> todayRecord = unsePairRepository.findTopByUser_IdAndCategoryAndCreatedAtBetweenOrderByCreatedAtDesc(
                user.getId(), categoryUpper, startOfDay, endOfDay
        );

        if (todayRecord.isPresent()) {
            return todayRecord.get();
        }

        // 없으면 생성 (빈 json 객체로 초기화)
        ObjectNode empty = objectMapper.createObjectNode();
        UnsePair created = UnsePair.builder()
                .user(user)
                .category(categoryUpper)
                .eastern(empty)
                .western(empty)
                .build();
        return unsePairRepository.save(created);
    }

    /**
     * AI 응답에서 최소 필드만 뽑는다.
     * - resp.data.score / keyword / one_liner / details 우선
     * - data 없으면 resp에서 직접 찾는다
     */
    private ObjectNode extractMinimalBlock(JsonNode resp) {
        ObjectNode block = objectMapper.createObjectNode();
        if (resp == null || resp.isNull()) return block;

        JsonNode data = resp.get("data");
        if (data == null || data.isNull()) data = resp;

        if (data.hasNonNull("score")) block.set("score", data.get("score"));
        if (data.hasNonNull("keyword")) block.set("keyword", data.get("keyword"));
        if (data.hasNonNull("one_liner")) block.set("one_liner", data.get("one_liner"));
        if (data.hasNonNull("details")) block.set("details", data.get("details"));

        return block;
    }

    // =========================================================
    // SSE helpers
    // =========================================================

    private void sendJson(SseEmitter emitter, String eventName, JsonNode payload) throws Exception {
        emitter.send(SseEmitter.event().name(eventName).data(payload.toString(), MediaType.APPLICATION_JSON));
    }

    private void sendError(SseEmitter emitter, String message) {
        try {
            ObjectNode node = objectMapper.createObjectNode();
            node.put("event", "error");
            node.put("message", message);
            node.put("timestamp", LocalDateTime.now().toString());
            sendJson(emitter, "error", node);
        } catch (Exception ignored) {}
    }

    private void completeSafely(SseEmitter emitter) {
        try { emitter.complete(); } catch (Exception ignored) {}
    }

    // =========================================================
    // misc helpers
    // =========================================================

    private String safeText(JsonNode root, String pointer) {
        if (root == null) return null;
        JsonNode n = root.at(pointer);
        return (n == null || n.isMissingNode() || n.isNull()) ? null : n.asText();
    }

    private String safeChar(String v, String def) {
        return (v == null || v.isBlank()) ? def : v;
    }

    private String resolveBirthDate(User user) {
        if (user.getBirthDate() != null) return user.getBirthDate().toString();
        JsonNode inputData = sajuResultRepository.findByUser_Id(user.getId()).map(SajuResult::getInputData).orElse(null);
        String picked = pick(inputData, "birth_date", "birthDate");
        if (picked != null) return picked;
        throw new RuntimeException("Birth date missing");
    }

    private String resolveBirthTime(User user) {
        if (user.getBirthTime() != null) return user.getBirthTime().toString();
        JsonNode inputData = sajuResultRepository.findByUser_Id(user.getId()).map(SajuResult::getInputData).orElse(null);
        return Optional.ofNullable(pick(inputData, "birth_time", "birthTime")).orElse("00:00");
    }

    private String pick(JsonNode node, String... keys) {
        if (node == null || node.isNull()) return null;
        for (String k : keys) {
            JsonNode v = node.get(k);
            if (v != null && !v.isNull() && v.isTextual()) return v.asText();
        }
        return null;
    }

    private String resolveGender(User user) {
        if (user.getGender() != null) {
            String g = user.getGender().trim().toUpperCase();
            if (g.startsWith("M")) return "M";
            if (g.startsWith("F")) return "F";
            if (g.startsWith("W")) return "F";
        }
        JsonNode inputData = sajuResultRepository.findByUser_Id(user.getId()).map(SajuResult::getInputData).orElse(null);
        String picked = pick(inputData, "gender");
        if (picked != null) {
            String g = picked.trim().toUpperCase();
            if (g.startsWith("M")) return "M";
            if (g.startsWith("F") || g.startsWith("W")) return "F";
        }
        return "M";
    }

    private String normalizeCategoryUpper(String raw) {
        return (raw == null || raw.isBlank()) ? "GENERAL" : raw.trim().toUpperCase();

    }

    private String normalizeCategoryLower(String raw) {
        if (raw == null || raw.isBlank()) return "total";
        return switch (raw.trim().toUpperCase()) {
            case "GENERAL", "TOTAL" -> "total";
            case "LOVE" -> "love";
            case "MONEY", "WEALTH" -> "wealth";
            case "CAREER" -> "career";
            case "HEALTH" -> "health";
            case "STUDY" -> "study";
            default -> "total";
        };
    }

    private String normalizeType(String type) {
        if (type == null || type.isBlank()) return "eastern";
        String t = type.trim().toLowerCase();
        return switch (t) {
            case "east", "eastern" -> "eastern";
            case "west", "western" -> "western";
            default -> t;
        };
    }

    // =========================================================
    // fallback (기존 유지)
    // =========================================================

    private JsonNode resolveHybridSummary(Long userId, String type, String category) {
        Optional<SajuResult> sajuOpt = sajuResultRepository.findByUser_Id(userId);
        ObjectNode root = objectMapper.createObjectNode();
        ObjectNode fortune = root.putObject("fortune");

        if (sajuOpt.isPresent()) {
            JsonNode analysis = sajuOpt.get().getAnalysisResult();
            if ("eastern".equalsIgnoreCase(type)) {
                int score = analysis.path("eastern").path("score").asInt(50);
                fortune.put("score", score);
            } else {
                int score = analysis.path("western").path("score").asInt(50);
                fortune.put("score", score);
            }
        } else {
            fortune.put("score", 50);
        }

        fortune.put("one_line", "AI 연결이 지연되고 있습니다.");
        fortune.put("detail", "현재 AI 서버와의 연결이 원활하지 않아 간략한 분석 결과만 제공됩니다. 상세한 운세 풀이를 보시려면 잠시 후 다시 시도해주세요.");

        var array = fortune.putArray("keywords");
        array.add("분석 대기");
        array.add("연결 지연");

        return root;
    }

    private JsonNode resolveHybridSummaryBoth(Long userId, String category) {
        JsonNode eastern = resolveHybridSummary(userId, "eastern", category);
        JsonNode western = resolveHybridSummary(userId, "western", category);

        ObjectNode root = objectMapper.createObjectNode();
        root.set("eastern", eastern);
        root.set("western", western);
        return root;
    }
}
