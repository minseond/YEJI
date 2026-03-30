/**
 * 사운드 시스템에서 사용할 오디오 에셋 경로 관리
 */
export const AUDIO_ASSETS = {
    // 배경 음악 (Ambience / BGM)
    BGM: {
        ORIENTAL: '/assets/audio/bgm/oriental_ambience.mp3',
        DESTINY: '/assets/audio/bgm/destiny_resonance.mp3',
        EAST1: '/assets/audio/bgm/east1.mp3',
        EAST2: '/assets/audio/bgm/east2.mp3',
        WEST2: '/assets/audio/bgm/west2.mp3',
        WEST1: '/assets/audio/bgm/west1.mp3',
        WEST3: '/assets/audio/bgm/west3.mp3',
        EAST3: '/assets/audio/bgm/east3.mp3',
    },

    // 효과음 (SFX)
    SFX: {
        BRUSH_HOVER: '/assets/audio/sfx/brush_hover.mp3',
        SEAL_CLICK: '/assets/audio/sfx/클릭1.mp3',
        CARD_FLIP: '/assets/audio/sfx/클릭2.mp3',
        MAGIC_FLARE: '/assets/audio/sfx/마법.mp3',
        BUTTON_SELECT: '/assets/audio/sfx/클릭3.mp3',
        CLICK2: '/assets/audio/sfx/클릭2.mp3',
        CLICK1: '/assets/audio/sfx/클릭1.mp3',
    },

    // 캐릭터 보이스 (Voice)
    VOICE: {
        SOISEOL: {
            GREETING: '/assets/audio/voice/soiseol_greeting.mp3',
            REACTION: '/assets/audio/voice/soiseol_reaction.mp3',
            ORACLE: '/assets/audio/voice/soiseol_oracle.mp3',
            COLLECTION_CLICK: '/assets/audio/voice/soiseol/soiseol_3.wav',
            SELECTION_INTRO: '/assets/audio/voice/soiseol/soiseol_6.wav',
            CROSS_PROMO: '/assets/audio/voice/soiseol/soiseol_7.wav',
        },
        STELLA: {
            GREETING: '/assets/audio/voice/stella_greeting.mp3',
            REACTION: '/assets/audio/voice/stella_reaction.mp3',
            TAROT: '/assets/audio/voice/stella_tarot.mp3',
            INTRO: '/assets/audio/voice/stella/stella_2.wav',
            SELECTION_INTRO: '/assets/audio/voice/stella/stella_8.wav',
            COLLECTION_CLICK: '/assets/audio/voice/stella/stella_1.wav',
        }
    }
} as const;

export type SoundName =
    | keyof typeof AUDIO_ASSETS.BGM
    | keyof typeof AUDIO_ASSETS.SFX
    | `SOISEOL_${keyof typeof AUDIO_ASSETS.VOICE.SOISEOL}`
    | `STELLA_${keyof typeof AUDIO_ASSETS.VOICE.STELLA}`;
