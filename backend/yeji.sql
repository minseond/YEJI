/* ================================================= */
/* 1. 도감 및 캐릭터 (Collection & Meta) */
/* ================================================= */
CREATE table if not exists  characters (
                                           character_id SERIAL PRIMARY KEY,
                                           name VARCHAR(50) NOT NULL,
    type VARCHAR(20) NOT NULL,
    grade VARCHAR(20) NOT NULL DEFAULT 'COMMON',
    image_url VARCHAR(500),
    model_url VARCHAR(500),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
    );

COMMENT ON TABLE characters IS '캐릭터 도감 메타 정보';
COMMENT ON COLUMN characters.character_id IS '캐릭터 ID';
COMMENT ON COLUMN characters.name IS '캐릭터명 (산신령, 멀린 등)';
/* ================================================= */
/* 2. 유저 및 설정 (Users & Settings) */
/* ================================================= */
CREATE TABLE users (
                       user_id BIGSERIAL PRIMARY KEY,
                       email VARCHAR(255) UNIQUE,
                       password VARCHAR(255),
                       nickname VARCHAR(100),
                       profile_img VARCHAR(500),
                       provider VARCHAR(20),
                       birth_date DATE,
                       name_kor VARCHAR(50),
                       name_chn VARCHAR(50),
                       birth_time TIME,
                       gender VARCHAR(10),
                       is_solar BOOLEAN NOT NULL DEFAULT TRUE,
                       equip_east_id INT,
                       equip_west_id INT,
                       created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                       deleted_at TIMESTAMP DEFAULT NULL,
                       CONSTRAINT fk_user_eq_east FOREIGN KEY (equip_east_id) REFERENCES characters (character_id) ON DELETE SET NULL,
                       CONSTRAINT fk_user_eq_west FOREIGN KEY (equip_west_id) REFERENCES characters (character_id) ON DELETE SET NULL
);

CREATE TABLE user_settings (
                               user_id BIGINT PRIMARY KEY,
                               push_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                               marketing_agreed BOOLEAN NOT NULL DEFAULT FALSE,
                               sound_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                               vib_enabled BOOLEAN NOT NULL DEFAULT TRUE,
                               updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                               CONSTRAINT fk_set_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE user_characters (
                                 id BIGSERIAL PRIMARY KEY,
                                 user_id BIGINT NOT NULL,
                                 character_id INT NOT NULL,
                                 acquired_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                 CONSTRAINT uk_user_char UNIQUE (user_id, character_id),
                                 CONSTRAINT fk_uchar_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
                                 CONSTRAINT fk_uchar_char FOREIGN KEY (character_id) REFERENCES characters (character_id) ON DELETE CASCADE
);

/* ================================================= */
/* 3. 경제 시스템 (Economy) */
/* ================================================= */
CREATE TABLE user_wallet (
                             user_id BIGINT PRIMARY KEY,
                             balance INT NOT NULL DEFAULT 0,
                             updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                             CONSTRAINT fk_wallet_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE products (
                          product_id SERIAL PRIMARY KEY,
                          name VARCHAR(100),
                          price_krw INT NOT NULL DEFAULT 0,
                          fp_amount INT NOT NULL DEFAULT 0,
                          is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE service_prices (
                                service_code VARCHAR(50) PRIMARY KEY,
                                service_name VARCHAR(50) NOT NULL,
                                cost_fp INT NOT NULL DEFAULT 0,
                                description VARCHAR(255)
);

CREATE TABLE payments (
                          order_id VARCHAR(100) PRIMARY KEY,
                          user_id BIGINT NOT NULL,
                          product_id INT NOT NULL,
                          amount INT DEFAULT 0,
                          pg_provider VARCHAR(50),
                          status VARCHAR(20),
                          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          CONSTRAINT fk_pay_user FOREIGN KEY (user_id) REFERENCES users (user_id),
                          CONSTRAINT fk_pay_prod FOREIGN KEY (product_id) REFERENCES products (product_id)
);

CREATE TABLE token_history (
                               id BIGSERIAL PRIMARY KEY,
                               user_id BIGINT NOT NULL,
                               service_code VARCHAR(50),
                               amount INT NOT NULL DEFAULT 0,
                               type VARCHAR(30),
                               description VARCHAR(255),
                               reference_id VARCHAR(100),
                               reference_type VARCHAR(50), -- 예: 'EVENT', 'SHOP'
                               created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                               CONSTRAINT fk_hist_user FOREIGN KEY (user_id) REFERENCES users (user_id),
                               CONSTRAINT fk_hist_svc FOREIGN KEY (service_code) REFERENCES service_prices (service_code)
);

/* ================================================= */
/* 4. 콘텐츠 결과 (Results) - JSON 사용 */
/* ================================================= */
CREATE TABLE saju_results (
                              id              BIGSERIAL PRIMARY KEY,
                              user_id         BIGINT NOT NULL,
                              input_data      JSONB NULL,            -- Postgres는 JSONB 권장
                              analysis_result JSONB NULL,
                              score           INT NOT NULL DEFAULT 0,
                              status          VARCHAR(20) NOT NULL DEFAULT 'KEEP',
                              created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                              updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

                              CONSTRAINT uq_saju_results_user UNIQUE (user_id), -- 유저당 1개 (1:1 강제)
                              CONSTRAINT fk_saju_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- 업데이트 트리거 적용
CREATE TRIGGER trg_saju_results_update
    BEFORE UPDATE ON saju_results
    FOR EACH ROW
    EXECUTE PROCEDURE update_timestamp();

CREATE TABLE unse_results (
                              id              BIGSERIAL PRIMARY KEY,
                              user_id         BIGINT NOT NULL,
                              user_prompt     TEXT NOT NULL,
                              analysis_result JSONB NULL,
                              score           INT DEFAULT 0,
                              status          VARCHAR(20) DEFAULT 'KEEP',
                              created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

                              CONSTRAINT fk_unse_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

-- 코멘트 적용
COMMENT ON TABLE unse_results IS '운세 분석 결과';
COMMENT ON COLUMN unse_results.id IS '운세 결과 ID';
COMMENT ON COLUMN unse_results.user_id IS '유저 ID(FK)';
COMMENT ON COLUMN unse_results.user_prompt IS '사용자 입력 프롬프트 원문';
COMMENT ON COLUMN unse_results.analysis_result IS 'AI 분석 결과';


CREATE TABLE taro_results (
                              id BIGSERIAL PRIMARY KEY,
                              user_id BIGINT NOT NULL,
                              question TEXT,
                              ai_reading TEXT,
                              score INT DEFAULT 0,
                              status VARCHAR(20) DEFAULT 'KEEP',
                              created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                              CONSTRAINT fk_taro_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE taro_card_selection (
                                     id BIGSERIAL PRIMARY KEY,
                                     taro_result_id BIGINT NOT NULL,
                                     user_id BIGINT NOT NULL,
                                     card_code INT,
                                     position INT,
                                     is_reversed BOOLEAN NOT NULL DEFAULT FALSE,
                                     CONSTRAINT fk_card_res FOREIGN KEY (taro_result_id) REFERENCES taro_results (id) ON DELETE CASCADE
);

CREATE TABLE face_palm_result (
                                  id BIGSERIAL PRIMARY KEY,
                                  user_id BIGINT NOT NULL,
                                  type VARCHAR(20) NOT NULL DEFAULT 'PALM',
                                  original_img_url VARCHAR(500),
                                  result_img_url VARCHAR(500),
                                  analysis_result JSONB,
                                  score INT DEFAULT 0,
                                  status VARCHAR(20) DEFAULT 'KEEP',
                                  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                  CONSTRAINT fk_fp_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

/* ================================================= */
/* 5. 소셜 및 거래 (Social & Trade) */
/* ================================================= */
CREATE TABLE friendship (
                            id BIGSERIAL PRIMARY KEY,
                            req_id BIGINT NOT NULL,
                            rcv_id BIGINT NOT NULL,
                            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            CONSTRAINT fk_fr_req FOREIGN KEY (req_id) REFERENCES users (user_id) ON DELETE CASCADE,
                            CONSTRAINT fk_fr_rcv FOREIGN KEY (rcv_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE compatibility_results (
                                       id BIGSERIAL PRIMARY KEY,
                                       req_id BIGINT NOT NULL,
                                       target_id BIGINT,
                                       target_name VARCHAR(50),
                                       target_birth_data JSONB,
                                       relation_type VARCHAR(50),
                                       result_data JSONB,
                                       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                       CONSTRAINT fk_comp_req FOREIGN KEY (req_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE luck_transfers (
                                id BIGSERIAL PRIMARY KEY,
                                sender_id BIGINT NOT NULL,
                                receiver_id BIGINT NOT NULL,
                                transfer_type VARCHAR(20) NOT NULL,
                                origin_result_id BIGINT,
                                origin_table_type VARCHAR(20),
                                character_type INT NOT NULL DEFAULT 1,
                                message TEXT,
                                is_read BOOLEAN DEFAULT FALSE,
                                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                                CONSTRAINT fk_luck_send FOREIGN KEY (sender_id) REFERENCES users (user_id),
                                CONSTRAINT fk_luck_rcv FOREIGN KEY (receiver_id) REFERENCES users (user_id)
);

/* ================================================= */
/* 6. 이벤트 (Events) */
/* ================================================= */
-- 6-1. 이벤트 메타 정보 테이블
CREATE table if not exists events (
                                      event_id SERIAL PRIMARY KEY,
                                      title VARCHAR(100) NOT NULL,           -- 이벤트명
    type VARCHAR(20) NOT NULL,             -- 이벤트 타입 (ATTENDANCE, ROULETTE, MISSION)
    start_date TIMESTAMP NOT NULL,         -- 시작일
    end_date TIMESTAMP NOT NULL,           -- 종료일
    is_active BOOLEAN DEFAULT TRUE,        -- 활성화 여부
    reward_type VARCHAR(20),               -- 보상 타입 (FP, ITEM, COUPON)
    reward_value INT DEFAULT 0,            -- 보상 양
    daily_limit INT DEFAULT 1,             -- 일일 참여 가능 횟수
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

COMMENT ON COLUMN events.title IS '이벤트명 (예: 매일매일 출석체크)';
COMMENT ON COLUMN events.daily_limit IS '일일 참여 가능 횟수 (출석은 1, 뽑기는 3)';

-- 6-2. 유저 참여 로그 테이블
CREATE TABLE if not exists event_histories (
                                               history_id BIGSERIAL PRIMARY KEY,
                                               user_id BIGINT NOT NULL,               -- 참여한 유저
                                               event_id INT NOT NULL,                 -- 참여한 이벤트
                                               reward_amount INT,                     -- 지급된 보상량
                                               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                                               CONSTRAINT fk_evt_hist_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_evt_hist_evt FOREIGN KEY (event_id) REFERENCES events (event_id)
    );

-- 인덱스 추가 (중복 참여 체크 성능 향상)
CREATE INDEX idx_evt_hist_check ON event_histories (user_id, event_id, created_at);


-- 업데이트 트리거 적용
CREATE TRIGGER trg_saju_results_update
    BEFORE UPDATE ON saju_results
    FOR EACH ROW
    EXECUTE PROCEDURE update_timestamp();

-- 자동 갱신 시간 트리거 함수 (ON UPDATE CURRENT_TIMESTAMP 대체용)
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 이벤트 운영 예시
-- 예시: 매일 출석체크 (오늘부터 1년간, 매일 1회, 100포인트)
INSERT INTO events (title, type, start_date, end_date, is_active, reward_type, reward_value, daily_limit)
VALUES ('매일매일 출석체크', 'ATTENDANCE', NOW(), NOW() + INTERVAL '1 year', TRUE, 'FP', 100, 1);

-- 예시: 행운의 룰렛 (오늘부터 1년간, 매일 3회, 랜덤 포인트)
INSERT INTO events (title, type, start_date, end_date, is_active, reward_type, reward_value, daily_limit)
VALUES ('행운의 룰렛', 'ROULETTE', NOW(), NOW() + INTERVAL '1 year', TRUE, 'FP', 0, 3);

-- 이벤트 삭제
-- event_id가 1인 이벤트를 삭제
DELETE FROM events WHERE event_id = 1;