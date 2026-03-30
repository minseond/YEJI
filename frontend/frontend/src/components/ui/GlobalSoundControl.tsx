import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Volume2, VolumeX } from 'lucide-react';
import { useSoundSettings } from '../../contexts/SoundContext';

import { useLocation } from 'react-router-dom';

const GlobalSoundControl = () => {
    const { volume, isMuted, setVolume, setIsMuted } = useSoundSettings();
    const [isOpen, setIsOpen] = React.useState(false);
    const location = useLocation();

    // Hide if logged in (token exists) OR if not on the login page ('/')
    // We use location to trigger re-render on navigation (login/logout)
    const isAuthenticated = !!localStorage.getItem('accessToken');
    const isLoginPage = location.pathname === '/';

    if (isAuthenticated || !isLoginPage) return null;

    const toggleMute = () => {
        setIsMuted(!isMuted);
    };

    const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setVolume(Number(e.target.value));
    };

    return (
        <div className="fixed bottom-6 right-6 z-[999999] flex flex-col items-end gap-3 font-gmarket">
            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.9 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: 10, scale: 0.9 }}
                        className="bg-black/60 backdrop-blur-xl border border-white/20 p-4 rounded-2xl shadow-2xl flex flex-col gap-4 min-w-[200px]"
                    >
                        <div className="flex items-center justify-between gap-4">
                            <span className="text-xs font-bold text-white/70 uppercase tracking-widest">마스터 볼륨</span>
                            <span className="text-xs font-mono text-white">{Math.round(volume * 100)}%</span>
                        </div>

                        <input
                            type="range"
                            min="0"
                            max="1"
                            step="0.01"
                            value={volume}
                            onChange={handleVolumeChange}
                            className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-white"
                        />

                        <div className="h-px bg-white/10 w-full" />

                        <button
                            onClick={toggleMute}
                            className="flex items-center justify-between w-full group"
                        >
                            <span className="text-sm text-white/70 group-hover:text-white transition-colors">
                                {isMuted ? '음소거 해제' : '전체 음소거'}
                            </span>
                            {isMuted ? (
                                <VolumeX className="w-4 h-4 text-red-400" />
                            ) : (
                                <Volume2 className="w-4 h-4 text-indigo-400" />
                            )}
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>

            <motion.button
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.9 }}
                onClick={() => setIsOpen(!isOpen)}
                className={`p-3 rounded-full shadow-2xl border transition-all duration-300 ${isOpen
                    ? 'bg-white text-black border-white'
                    : 'bg-black/40 text-white border-white/20 backdrop-blur-md'
                    }`}
            >
                {isMuted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
            </motion.button>
        </div>
    );
};

export default GlobalSoundControl;
