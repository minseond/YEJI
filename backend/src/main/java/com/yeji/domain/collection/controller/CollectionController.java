package com.yeji.domain.collection.controller;

import com.yeji.domain.collection.dto.CharacterEquipRequest;
import com.yeji.domain.collection.dto.CharacterResponse;
import com.yeji.domain.collection.dto.UserCollectionResponse;
import com.yeji.domain.collection.service.CollectionService;
import com.yeji.global.dto.ApiResponse;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Tag(name = "Collection", description = "도감 및 캐릭터 관련 API")
@RestController
@RequestMapping("/collection")
@RequiredArgsConstructor
public class CollectionController {

    private final CollectionService collectionService;

    @Operation(summary = "전체 캐릭터 도감 조회 (COL-001)", description = "시스템에 존재하는 모든 활성화된 캐릭터 목록을 조회합니다.")
    @GetMapping("/characters")
    public ApiResponse<List<CharacterResponse>> getAllCharacters() {
        return ApiResponse.success(collectionService.getAllCharacters());
    }

    @Operation(summary = "내 보유 캐릭터 조회 (COL-002)", description = "로그인한 유저가 보유한 캐릭터 목록을 조회합니다.", security = @SecurityRequirement(name = "bearerAuth"))
    @GetMapping("/my-characters")
    public ApiResponse<List<UserCollectionResponse>> getMyCollections(@AuthenticationPrincipal AuthUser authUser) {
        return ApiResponse.success(collectionService.getMyCollections(authUser.getUserId()));
    }

    @Operation(summary = "캐릭터 상세 조회 (COL-003)", description = "특정 캐릭터의 상세 정보를 조회합니다.")
    @GetMapping("/characters/{characterId}")
    public ApiResponse<CharacterResponse> getCharacterDetail(@PathVariable Long characterId) {
        return ApiResponse.success(collectionService.getCharacterDetail(characterId));
    }

    @Operation(summary = "캐릭터 장착 (COL-004)", description = "동양/서양 슬롯에 보유한 캐릭터를 장착하거나 해제합니다.", security = @SecurityRequirement(name = "bearerAuth"))
    @PatchMapping("/equip")
    public ApiResponse<Void> equipCharacter(
            @AuthenticationPrincipal AuthUser authUser,
            @RequestBody CharacterEquipRequest request) {
        collectionService.equipCharacter(authUser.getUserId(), request);
        return ApiResponse.success(null);
    }
}