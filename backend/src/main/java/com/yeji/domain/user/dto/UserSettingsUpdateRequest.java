package com.yeji.domain.user.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UserSettingsUpdateRequest {
    private Boolean pushEnabled;
    private Boolean marketingAgreed;
    private Boolean soundEnabled;
    private Boolean vibEnabled;
}