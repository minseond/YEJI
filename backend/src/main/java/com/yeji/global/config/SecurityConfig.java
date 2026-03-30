package com.yeji.global.config;

import com.yeji.global.auth.oauth.handler.OAuth2LoginSuccessHandler;
import com.yeji.global.auth.oauth.service.CustomOAuth2UserService;
import com.yeji.global.jwt.JwtAuthenticationFilter;
import com.yeji.global.jwt.JwtTokenProvider;
import jakarta.servlet.DispatcherType;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;
import java.util.List;

@Configuration
@EnableWebSecurity
@RequiredArgsConstructor
public class SecurityConfig {

    private final JwtTokenProvider jwtTokenProvider;

    // PasswordEncoder Bean 등록
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http, CustomOAuth2UserService customOAuth2UserService, OAuth2LoginSuccessHandler oAuth2LoginSuccessHandler) throws Exception {
        http
                // CSRF 비활성화 (JWT 사용 시 필요 없음)
                .csrf(AbstractHttpConfigurer::disable)

                // Form 로그인, Basic 인증 비활성화
                .formLogin(AbstractHttpConfigurer::disable)
                .httpBasic(AbstractHttpConfigurer::disable)

                // CORS 설정
                .cors(cors -> cors.configurationSource(corsConfigurationSource()))

                // 세션 사용 안 함 (STATELESS)
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))

                .exceptionHandling(ex -> ex
                        .authenticationEntryPoint((request, response, authException) -> {
                            if (response.isCommitted()) return;
                            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                            response.setContentType(MediaType.APPLICATION_JSON_VALUE);
                            response.getWriter().write("{\"success\":false,\"message\":\"UNAUTHORIZED\"}");
                        })
                        .accessDeniedHandler((request, response, accessDeniedException) -> {
                            if (response.isCommitted()) return;
                            response.setStatus(HttpServletResponse.SC_FORBIDDEN);
                            response.setContentType(MediaType.APPLICATION_JSON_VALUE);
                            response.getWriter().write("{\"success\":false,\"message\":\"FORBIDDEN\"}");
                        })
                )
                // 요청 인가 설정
                .authorizeHttpRequests(auth -> auth
                                .requestMatchers("/error").permitAll()
                        // SSE/비동기(ASYNC) 디스패치에서 Security가 다시 막지 않도록 허용
                        .dispatcherTypeMatchers(DispatcherType.ASYNC, DispatcherType.ERROR).permitAll()
                        // Swagger 관련
                        .requestMatchers("/swagger-ui/**", "/v3/api-docs/**", "/swagger-resources/**", "/swagger-ui.html").permitAll()
                        // 로그인, 회원가입 관련 (Public)
                        .requestMatchers("/user/signup", "/user/login", "/user/token/refresh", "/user/check-email", "/user/check-nickname").permitAll()
                        // H2 콘솔
                        .requestMatchers("/h2-console/**").permitAll()
                        // 이메일 전송 관련
                        .requestMatchers("/user/email/**", "/user/password/reset").permitAll()
                        // 일단 상점은 보이게
                        .requestMatchers("/shop/products").permitAll()
                        // 나머지 요청은 인증 필요
                        .anyRequest().authenticated()
                        // SSE만 테스트로 잠깐 풀고 싶으면 아래 주석 해제
                        // .requestMatchers("/unse/stream/**").permitAll()
                )
                //OAuth2 로그인 설정
                .oauth2Login(oauth2 -> oauth2
                        .userInfoEndpoint(userInfo -> userInfo
                                .userService(customOAuth2UserService) // 사용자 정보 서비스 등록
                        )
                        .successHandler(oAuth2LoginSuccessHandler) // 성공 시 JWT 발급 및 redirect
                )

                // JWT 필터를 UsernamePasswordAuthenticationFilter 앞에 등록
                .addFilterBefore(new JwtAuthenticationFilter(jwtTokenProvider), UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    // CORS 설정 정의
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();

        // 허용할 프론트엔드 도메인들
        configuration.setAllowedOrigins(List.of(
                "http://localhost:3000",    // React 로컬
                "http://localhost:5173",    // Vite 개발 서버
                "http://127.0.0.1:5500",    // VS Code Live Server (결제 테스트용)
                "http://localhost:5500",    // VS Code Live Server (localhost로 띄울 경우)
                "https://i14a605.p.ssafy.io" // 배포 서버
        ));

        // 허용할 HTTP 메서드
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));

        // 허용할 헤더
        configuration.setAllowedHeaders(Arrays.asList("Authorization", "Content-Type"));

        // 인증 정보(쿠키, 헤더 등) 포함 허용
        configuration.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}