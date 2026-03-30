package com.yeji.domain.user.dto;

import com.yeji.domain.user.entity.UserSettings;
import lombok.Getter;

@Getter
public class UserSettingsResponse {
    private final boolean pushEnabled;
    private final boolean marketingAgreed;
    private final boolean soundEnabled;
    private final boolean vibEnabled;

    public UserSettingsResponse(UserSettings settings) {
        this.pushEnabled = settings.isPushEnabled();
        this.marketingAgreed = settings.isMarketingAgreed();
        this.soundEnabled = settings.isSoundEnabled();
        this.vibEnabled = settings.isVibEnabled();
    }
}