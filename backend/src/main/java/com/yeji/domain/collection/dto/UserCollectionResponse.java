package com.yeji.domain.collection.dto;

import com.yeji.domain.collection.entity.UserCollection;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Getter;

import java.time.LocalDateTime;

@Getter
@Builder
@Schema(description = "보유 캐릭터 정보 응답")
public class UserCollectionResponse {

    @Schema(description = "보유 ID", example = "10")
    private Long collectionId;

    @Schema(description = "캐릭터 정보")
    private CharacterResponse character;

    @Schema(description = "획득 일시")
    private LocalDateTime acquiredAt;

    public static UserCollectionResponse from(UserCollection userCollection) {
        return UserCollectionResponse.builder()
                .collectionId(userCollection.getId())
                .character(CharacterResponse.from(userCollection.getCharacter()))
                .acquiredAt(userCollection.getAcquiredAt())
                .build();
    }
}