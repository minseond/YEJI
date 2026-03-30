import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Settings, Bell, Volume2, Smartphone, Mail } from 'lucide-react';
import { fetchSettings, updateSettings, type UserSettings } from '../../api/auth';
import { useSoundSettings } from '../../contexts/SoundContext';

interface SettingsModalProps {
    isOpen: boolean;
    onClose: () => void;
    userId: number;
}

const SettingsModal = ({ isOpen, onClose, userId }: SettingsModalProps) => {
    const { volume, setVolume, setIsMuted } = useSoundSettings();
    const [settings, setSettings] = useState<UserSettings>({
        pushEnabled: false,
        soundEnabled: false,
        vibEnabled: false,
        marketingAgreed: false
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen) {
            loadSettings();
        }
    }, [isOpen, userId]);

    const loadSettings = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await fetchSettings(userId);
            setSettings(data);

            // Sync context state with loaded settings
            if (data.soundEnabled !== undefined) {
                setIsMuted(!data.soundEnabled);
            }
        } catch (err) {
            console.error("Failed to load settings:", err);
            setError("설정을 불러오는데 실패했습니다.");
        } finally {
            setLoading(false);
        }
    };

    const handleToggle = async (key: keyof UserSettings) => {
        const newValue = !settings[key];

        // Optimistic update
        setSettings(prev => ({ ...prev, [key]: newValue }));

        // Sync with SoundContext if toggling sound
        if (key === 'soundEnabled') {
            setIsMuted(!newValue);
        }

        try {
            await updateSettings(userId, { [key]: newValue });
        } catch (err) {
            console.error(`Failed to update ${key}:`, err);
            // Revert on error
            setSettings(prev => ({ ...prev, [key]: !newValue }));
            if (key === 'soundEnabled') {
                setIsMuted(newValue); // Revert mute state too
            }
            setError("설정 변경에 실패했습니다.");
        }
    };

    const settingItems = [
        {
            key: 'pushEnabled' as keyof UserSettings,
            icon: Bell,
            title: '푸시 알림',
            description: '중요한 소식을 알림으로 받습니다'
        },
        {
            key: 'soundEnabled' as keyof UserSettings,
            icon: Volume2,
            title: '소리',
            description: '앱 내 효과음을 재생합니다'
        },
        {
            key: 'vibEnabled' as keyof UserSettings,
            icon: Smartphone,
            title: '진동',
            description: '알림 시 진동을 울립니다'
        },
        {
            key: 'marketingAgreed' as keyof UserSettings,
            icon: Mail,
            title: '마케팅 정보 수신',
            description: '이벤트 및 혜택 정보를 받습니다'
        }
    ];

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50"
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none"
                    >
                        <div className="bg-[#1a1a2e] border border-white/10 rounded-2xl w-full max-w-md max-h-[80vh] flex flex-col shadow-2xl pointer-events-auto font-gmarket">

                            {/* Header */}
                            <div className="p-5 border-b border-white/10 flex items-center justify-between">
                                <h3 className="text-xl font-bold text-white flex items-center gap-2">
                                    <Settings className="text-indigo-400" size={24} />
                                    설정
                                </h3>
                                <button
                                    onClick={onClose}
                                    className="p-1 rounded-full hover:bg-white/10 text-white/50 hover:text-white transition-colors"
                                >
                                    <X size={24} />
                                </button>
                            </div>

                            {/* Content */}
                            <div className="flex-1 overflow-y-auto p-4 custom-scrollbar">
                                {loading ? (
                                    <div className="flex flex-col items-center justify-center py-12 text-white/40 gap-3">
                                        <div className="w-8 h-8 border-2 border-white/20 border-t-indigo-500 rounded-full animate-spin" />
                                        <span className="text-sm">설정을 불러오는 중...</span>
                                    </div>
                                ) : error ? (
                                    <div className="flex flex-col items-center justify-center py-12 text-red-400 gap-3">
                                        <span>{error}</span>
                                        <button
                                            onClick={loadSettings}
                                            className="px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-sm text-white mt-2"
                                        >
                                            다시 시도
                                        </button>
                                    </div>
                                ) : (
                                    <div className="space-y-3">
                                        {settingItems.map((item) => {
                                            const Icon = item.icon;
                                            const isEnabled = settings[item.key];

                                            return (
                                                <div
                                                    key={item.key}
                                                    className="bg-white/5 border border-white/5 rounded-xl p-4 hover:bg-white/10 transition-colors"
                                                >
                                                    <div className="flex items-center justify-between">
                                                        <div className="flex items-start gap-3 flex-1">
                                                            <Icon className="text-indigo-400 mt-1" size={20} />
                                                            <div className="flex-1">
                                                                <div className="text-white font-bold mb-1">
                                                                    {item.title}
                                                                </div>
                                                                <div className="text-xs text-white/40">
                                                                    {item.description}
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Toggle Switch */}
                                                        <button
                                                            onClick={() => handleToggle(item.key)}
                                                            className={`relative w-12 h-6 rounded-full transition-colors ${isEnabled ? 'bg-indigo-500' : 'bg-white/20'
                                                                }`}
                                                        >
                                                            <motion.div
                                                                className="absolute top-1 w-4 h-4 bg-white rounded-full shadow-md"
                                                                animate={{ left: isEnabled ? '28px' : '4px' }}
                                                                transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                                                            />
                                                        </button>
                                                    </div>

                                                    {/* Volume Slider specific for Sound Setting */}
                                                    {item.key === 'soundEnabled' && isEnabled && (
                                                        <motion.div
                                                            initial={{ height: 0, opacity: 0, marginTop: 0 }}
                                                            animate={{ height: 'auto', opacity: 1, marginTop: 16 }}
                                                            exit={{ height: 0, opacity: 0, marginTop: 0 }}
                                                            className="overflow-hidden"
                                                        >
                                                            <div className="bg-black/20 rounded-lg p-3">
                                                                <div className="flex justify-between items-center mb-2">
                                                                    <span className="text-xs text-white/60 font-bold">볼륨 조절</span>
                                                                    <span className="text-xs font-mono text-white/80">{Math.round(volume * 100)}%</span>
                                                                </div>
                                                                <input
                                                                    type="range"
                                                                    min="0"
                                                                    max="1"
                                                                    step="0.01"
                                                                    value={volume}
                                                                    onChange={(e) => setVolume(Number(e.target.value))}
                                                                    className="w-full h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                                                                />
                                                            </div>
                                                        </motion.div>
                                                    )}
                                                </div>
                                            );
                                        })}
                                    </div>
                                )}
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};

export default SettingsModal;
