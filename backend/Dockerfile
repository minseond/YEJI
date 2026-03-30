# Build stage
FROM eclipse-temurin:21-jdk AS builder

WORKDIR /app

# Gradle wrapper 복사
COPY gradlew .
COPY gradle gradle
COPY build.gradle .
COPY settings.gradle .

# 의존성 캐싱을 위해 먼저 다운로드
RUN chmod +x ./gradlew
RUN ./gradlew dependencies --no-daemon || true

# 소스 코드 복사 및 빌드
COPY src src
RUN ./gradlew bootJar --no-daemon -x test

# Runtime stage
FROM eclipse-temurin:21-jre

WORKDIR /app

# 빌드된 JAR 복사
COPY --from=builder /app/build/libs/*.jar app.jar

# JVM 옵션 (Java 21 호환성)
ENV JAVA_OPTS="--enable-native-access=ALL-UNNAMED \
    --add-opens=java.base/java.lang=ALL-UNNAMED \
    --add-opens=java.base/sun.nio.ch=ALL-UNNAMED \
    --add-opens=java.base/java.io=ALL-UNNAMED"

EXPOSE 8080

ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar app.jar"]
