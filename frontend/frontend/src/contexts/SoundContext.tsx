import React, { createContext, useContext, useState, useEffect } from 'react';

interface SoundContextType {
    volume: number;
    isMuted: boolean;
    setVolume: (v: number) => void;
    setIsMuted: (m: boolean) => void;
}

const SoundContext = createContext<SoundContextType | undefined>(undefined);

export const SoundProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [volume, setVolume] = useState(() => {
        const saved = localStorage.getItem('yeji_volume');
        return saved ? parseFloat(saved) : 0.5;
    });

    const [isMuted, setIsMuted] = useState(() => {
        const saved = localStorage.getItem('yeji_muted');
        return saved === 'true';
    });

    useEffect(() => {
        localStorage.setItem('yeji_volume', volume.toString());
    }, [volume]);

    useEffect(() => {
        localStorage.setItem('yeji_muted', isMuted.toString());
    }, [isMuted]);

    return (
        <SoundContext.Provider value={{ volume, isMuted, setVolume, setIsMuted }}>
            {children}
        </SoundContext.Provider>
    );
};

export const useSoundSettings = () => {
    const context = useContext(SoundContext);
    if (!context) {
        throw new Error('useSoundSettings must be used within a SoundProvider');
    }
    return context;
};
