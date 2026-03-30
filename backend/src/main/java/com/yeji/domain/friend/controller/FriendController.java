package com.yeji.domain.friend.controller;

import com.yeji.domain.friend.dto.FriendResponse;
import com.yeji.domain.friend.service.FriendService;
import com.yeji.global.dto.ApiResponse;
import com.yeji.global.jwt.AuthUser;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Tag(name = "Friend", description = "친구 API")
@RestController
@RequestMapping("/friends")
@RequiredArgsConstructor
public class FriendController {

    private final FriendService friendService;

    @Operation(summary = "FRIEND-001 친구 검색", description = "닉네임으로 유저를 검색합니다.")
    @GetMapping("/search")
    public ApiResponse<List<FriendResponse>> searchFriends(@RequestParam String keyword) {
        return ApiResponse.success(friendService.searchFriends(keyword));
    }

    @Operation(summary = "FRIEND-002 친구 요청", description = "친구 요청을 보냅니다.")
    @PostMapping("/requests")
    public ApiResponse<Void> requestFriend(@AuthenticationPrincipal AuthUser authUser,
                                           @RequestBody Map<String, Long> request) {
        friendService.requestFriend(authUser, request.get("targetUserId"));
        return ApiResponse.success(null);
    }

    @Operation(summary = "FRIEND-003 요청 처리", description = "친구 요청을 수락하거나 거절합니다. (accept: true/false)")
    @PatchMapping("/requests/{requestId}")
    public ApiResponse<Void> handleRequest(@AuthenticationPrincipal AuthUser authUser,
                                           @PathVariable Long requestId,
                                           @RequestBody Map<String, Boolean> request) {
        friendService.handleRequest(authUser, requestId, request.get("accept"));
        return ApiResponse.success(null);
    }

    @Operation(summary = "FRIEND-004 친구 목록", description = "내 친구 목록을 조회합니다.")
    @GetMapping({"", "/"})
    public ApiResponse<List<FriendResponse>> getMyFriends(@AuthenticationPrincipal AuthUser authUser) {
        return ApiResponse.success(friendService.getMyFriends(authUser));
    }

    @Operation(summary = "FRIEND-005 친구 삭제", description = "친구 관계를 끊습니다.")
    @DeleteMapping("/{friendUserId}")
    public ApiResponse<Void> deleteFriend(@AuthenticationPrincipal AuthUser authUser,
                                          @PathVariable Long friendUserId) {
        friendService.deleteFriend(authUser, friendUserId);
        return ApiResponse.success(null);
    }

    // FRIEND-006 받은 친구 요청 목록
    @Operation(summary = "FRIEND-006 받은 친구 요청 목록", description = "나에게 온 친구 요청(대기 상태) 목록을 조회합니다.")
    @GetMapping("/pending")
    public ApiResponse<List<FriendResponse>> getReceivedRequests(@AuthenticationPrincipal AuthUser authUser) {
        return ApiResponse.success(friendService.getReceivedRequests(authUser));
    }
}