package com.yeji.domain.collection.service;

import com.yeji.domain.collection.dto.CharacterEquipRequest;
import com.yeji.domain.collection.dto.CharacterResponse;
import com.yeji.domain.collection.dto.UserCollectionResponse;
import com.yeji.domain.collection.entity.Character;
import com.yeji.domain.collection.entity.CharacterType;
import com.yeji.domain.collection.repository.CharacterRepository;
import com.yeji.domain.collection.repository.UserCollectionRepository;
import com.yeji.domain.user.entity.User;
import com.yeji.domain.user.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class CollectionService {
    private final CharacterRepository characterRepository;
    private final UserCollectionRepository userCollectionRepository;
    private final UserRepository userRepository;

    // COL-001 전체 캐릭터 도감 조회
    public List<CharacterResponse> getAllCharacters() {
        return characterRepository.findAllByIsActiveTrue().stream()
                .map(CharacterResponse::from)
                .collect(Collectors.toList());
    }

    // COL-002 내 보유 캐릭터 조회
    public List<UserCollectionResponse> getMyCollections(Long userId) {
        return userCollectionRepository.findAllByUserIdWithCharacter(userId).stream()
                .map(UserCollectionResponse::from)
                .collect(Collectors.toList());
    }

    // COL-003 캐릭터 상세 조회
    public CharacterResponse getCharacterDetail(Long characterId) {
        Character character = characterRepository.findById(characterId)
                .orElseThrow(() -> new IllegalArgumentException("해당 캐릭터를 찾을 수 없습니다. id=" + characterId));
        return CharacterResponse.from(character);
    }

    // COL-004 캐릭터 장착
    @Transactional
    public void equipCharacter(Long userId, CharacterEquipRequest request) {
        User user = userRepository.findById(userId)
                .orElseThrow(() -> new IllegalArgumentException("유저를 찾을 수 없습니다."));

        // 장착 해제 요청인 경우
        if (request.getCharacterId() == null) {
            user.equipCharacter(null, request.getType() == CharacterType.EAST);
            return;
        }

        Character character = characterRepository.findById(request.getCharacterId())
                .orElseThrow(() -> new IllegalArgumentException("해당 캐릭터를 찾을 수 없습니다."));

        // 유저가 해당 캐릭터를 보유하고 있는지 확인
        boolean hasCharacter = userCollectionRepository.existsByUserIdAndCharacterId(userId, request.getCharacterId());
        if (!hasCharacter) {
            throw new IllegalArgumentException("보유하지 않은 캐릭터는 장착할 수 없습니다.");
        }

        // 캐릭터 타입이 슬롯과 일치하는지 확인 (기획에 따라 다를 수 있으나, 보통 동양 슬롯엔 동양 캐릭터)
        // 만약 타입 교차 장착이 가능하다면 이 검증은 제거해도 됨. 현재는 엄격하게 체크.
        if (character.getType() != request.getType()) {
            throw new IllegalArgumentException("해당 슬롯에 맞지 않는 캐릭터 타입입니다.");
        }

        user.equipCharacter(character, request.getType() == CharacterType.EAST);
    }
}
