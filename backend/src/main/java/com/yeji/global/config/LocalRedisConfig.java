package com.yeji.global.config;

import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Profile;
import redis.embedded.RedisServer;

import java.io.IOException;

@Slf4j
@Configuration
@Profile("test") // 실제 배포 시에는 dev를 없에야함
public class LocalRedisConfig {

    @Value("${spring.data.redis.port}")
    private int redisPort;

    private RedisServer redisServer;

    @PostConstruct
    public void startRedis() throws IOException {
        try {
            // it.ozimov 버전 사용 시 빌더 패턴
            redisServer = RedisServer.builder()
                    .port(redisPort)
                    .setting("maxmemory 128M") // 메모리 제한
                    .build();

            redisServer.start();
            log.info("✅ Embedded Redis Started on port {}", redisPort);
        } catch (Exception e) {
            // 로컬 개발 중 재시작 시 포트 충돌이 나도 앱이 죽지 않도록 예외 처리
            log.warn("Embedded Redis Start Failed (Port maybe in use): {}", e.getMessage());
        }
    }

    @PreDestroy
    public void stopRedis() {
        if (redisServer != null && redisServer.isActive()) {
            try {
                redisServer.stop();
                log.info("✅ Embedded Redis Stopped");
            } catch (Exception e) {
                log.error("Embedded Redis Stop Failed: {}", e.getMessage());
            }
        }
    }
}