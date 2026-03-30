import { useCallback, useEffect } from 'react';
import { AUDIO_ASSETS } from '../data/audioAssets';
import { useSoundSettings } from '../contexts/SoundContext';

// Global object to store audio instances across components
// This allows BGM management where one component can stop sounds started by another
const globalAudioRefs: { [key: string]: HTMLAudioElement } = {};

export const useSound = () => {
    const { volume, isMuted } = useSoundSettings();

    // Update volume of all active audio instances when volume or mute state changes
    useEffect(() => {
        Object.values(globalAudioRefs).forEach(audio => {
            if (isMuted) {
                audio.volume = 0;
            } else {
                // Apply the global volume to all audio instances
                // Note: This sets all to the same volume. If individual volume scales were stored,
                // we'd need to track them separately. For now, this applies the global volume uniformly.
                audio.volume = volume;
            }
        });
    }, [volume, isMuted]);

    /**
     * 사운드 재생
     * @param category BGM | SFX | VOICE
     * @param name 사운드 이름
     * @param options loop 여부 등
     */
    const play = useCallback((
        category: keyof typeof AUDIO_ASSETS,
        name: string,
        options: { loop?: boolean; subKey?: string; volume?: number } = {}
    ) => {
        if (isMuted) return;

        let soundPath = '';
        const soundKey = `${category}_${name}_${options.subKey || ''}`;

        // 경로 찾기
        if (category === 'VOICE' && options.subKey) {
            // @ts-ignore
            soundPath = AUDIO_ASSETS.VOICE[name as keyof typeof AUDIO_ASSETS.VOICE][options.subKey];
        } else {
            // @ts-ignore
            soundPath = AUDIO_ASSETS[category][name];
        }

        if (!soundPath) return;

        // 기존 오디오 객체가 없으면 생성
        if (!globalAudioRefs[soundKey]) {
            const audio = new Audio(soundPath);
            globalAudioRefs[soundKey] = audio;
        }

        const audio = globalAudioRefs[soundKey];

        // If it's already playing and looping (BGM), don't restart it
        if (options.loop && !audio.paused && audio.currentTime > 0) {
            return;
        }

        // Apply individual volume scale if provided, otherwise use global volume only
        const volumeScale = options.volume !== undefined ? options.volume : 1.0;
        audio.volume = volume * volumeScale;
        audio.loop = options.loop || false;

        // 재생 시점 초기화 (BGM이 아닐 경우)
        if (!options.loop) {
            audio.currentTime = 0;
        }

        audio.play().catch(err => {
            console.warn('Audio playback failed (interaction required):', err);
        });
    }, [volume, isMuted]);

    /**
     * 특정 사운드 정지
     */
    const stop = useCallback((category: string, name: string, subKey?: string) => {
        const soundKey = `${category}_${name}_${subKey || ''}`;
        const audio = globalAudioRefs[soundKey];
        if (audio) {
            audio.pause();
            audio.currentTime = 0;
        }
    }, []);

    /**
     * 모든 사운드 정지
     */
    const stopAll = useCallback(() => {
        Object.values(globalAudioRefs).forEach(audio => {
            audio.pause();
            audio.currentTime = 0;
        });
    }, []);

    return { play, stop, stopAll };
};
