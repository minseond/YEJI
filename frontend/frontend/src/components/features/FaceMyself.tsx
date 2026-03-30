import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ArrowLeft } from 'lucide-react';
import ParticleBackground from '../effects/ParticleBackground';
import ScrollNameInput from './ScrollNameInput';
import YinYangGenderInput from './YinYangGenderInput';
import GapjaYearInput from './GapjaYearInput';
import SolarConstellationInput from './SolarConstellationInput';
import TimeInput from './TimeInput';
import AnimatedBubble from '../common/AnimatedBubble';

interface UserData {
    name?: string;
    gender?: string;
    birthYear?: string;
    birthMonth?: string;
    birthDay?: string;
    birthTime?: string;
}

const FaceMyself = ({ onClose, autoAdvance = false, onToggleAutoAdvance }: {
    onClose: () => void,
    autoAdvance?: boolean,
    onToggleAutoAdvance?: () => void
}) => {
    const [step, setStep] = useState<'NAME' | 'GENDER' | 'YEAR' | 'DATE' | 'TIME' | 'LOADING'>('NAME');
    const [userData, setUserData] = useState<UserData>({
        name: '김싸피',
        gender: 'male',
        birthYear: '1996',
        birthMonth: '1',
        birthDay: '1',
        birthTime: '14:00 PM'
    });

    const handleNameConfirm = (name: string) => {
        setUserData(prev => ({ ...prev, name }));
        setStep('GENDER');
    };

    const handleGenderConfirm = (gender: string) => {
        setUserData(prev => ({ ...prev, gender }));
        setStep('YEAR');
    };

    const handleYearConfirm = (year: string) => {
        setUserData(prev => ({ ...prev, birthYear: year }));
        setStep('DATE');
    };

    const handleDateConfirm = (month: string, day: string) => {
        setUserData(prev => ({ ...prev, birthMonth: month, birthDay: day }));
        setStep('TIME');
    };

    const [loadingProgress, setLoadingProgress] = useState(0);

    // Loading Simulation
    useEffect(() => {
        if (step === 'LOADING') {
            const duration = 5000; // 5 seconds
            const interval = 50;
            const steps = duration / interval;
            const increment = 100 / steps;

            const timer = setInterval(() => {
                setLoadingProgress(prev => {
                    const next = prev + increment;
                    if (next >= 100) {
                        clearInterval(timer);
                        setTimeout(onClose, 500); // Close after a short delay at 100%
                        return 100;
                    }
                    return next;
                });
            }, interval);

            return () => clearInterval(timer);
        }
    }, [step, onClose]);

    const handleTimeConfirm = (hour: string, minute: string, period: string) => {
        const timeStr = `${hour}:${minute} ${period}`;
        setUserData(prev => ({ ...prev, birthTime: timeStr }));
        setStep('LOADING');
    };

    const handleBack = () => {
        if (step === 'GENDER') setStep('NAME');
        if (step === 'YEAR') setStep('GENDER');
        if (step === 'DATE') setStep('YEAR');
        if (step === 'TIME') setStep('DATE');
    };

    return (
        <motion.div
            className="fixed inset-0 z-[100] bg-black/90 text-white font-serif flex items-center justify-center overflow-hidden"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            <ParticleBackground type="eastern" opacity={0.3} className="z-0" />

            {/* Header Controls */}
            <div className="absolute top-6 right-6 z-[20000] flex items-center gap-4">
                {step !== 'NAME' && step !== 'LOADING' && (
                    <button
                        onClick={handleBack}
                        className="text-white/50 hover:text-white flex items-center gap-1 transition-colors"
                    >
                        <ArrowLeft size={24} />
                        <span className="text-sm">이전</span>
                    </button>
                )}
                {(step === 'NAME' || step === 'GENDER') && (
                    <button
                        onClick={onClose}
                        className="text-white/50 hover:text-white transition-colors"
                    >
                        <X size={32} />
                    </button>
                )}
            </div>

            {/* Main Content Area */}
            <div className="relative z-10 w-full h-full flex items-center justify-center">
                <AnimatePresence mode="wait">
                    {step === 'NAME' && (
                        <motion.div
                            key="name"
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -20 }}
                            transition={{ duration: 0.5 }}
                        >
                            <ScrollNameInput onConfirm={handleNameConfirm} initialName={userData.name} onClose={() => setStep('NAME')} />
                        </motion.div>
                    )}

                    {step === 'GENDER' && (
                        <motion.div
                            key="gender"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.9 }}
                            transition={{ duration: 0.5 }}
                            className="w-full h-full flex items-center justify-center"
                        >
                            <YinYangGenderInput onSelect={handleGenderConfirm} />
                        </motion.div>
                    )}

                    {step === 'YEAR' && (
                        <motion.div
                            key="year"
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 1.1 }}
                            transition={{ duration: 0.6 }}
                            className="w-full h-full flex items-center justify-center"
                        >
                            <GapjaYearInput
                                onSelect={handleYearConfirm}
                                onClose={onClose}
                                initialYear={parseInt(userData.birthYear || '1990')}
                            />
                        </motion.div>
                    )}

                    {step === 'DATE' && (
                        <motion.div
                            key="date"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.5 }}
                            className="w-full h-full flex items-center justify-center"
                        >
                            {/* Pass default year if birthYear is undefined, though it should be defined by now */}
                            <SolarConstellationInput
                                year={parseInt(userData.birthYear || '2000')}
                                initialMonth={parseInt(userData.birthMonth || '1')}
                                initialDay={parseInt(userData.birthDay || '15')}
                                onSelect={handleDateConfirm}
                                onClose={onClose}
                            />
                        </motion.div>
                    )}

                    {step === 'TIME' && (
                        <motion.div
                            key="time"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.5 }}
                            className="w-full h-full flex items-center justify-center"
                        >
                            <TimeInput
                                onSelect={handleTimeConfirm}
                                onClose={onClose}
                                initialHour={parseInt(userData.birthTime?.split(':')[0] || '12')}
                            />
                        </motion.div>
                    )}

                    {step === 'LOADING' && (
                        <motion.div
                            key="loading"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex flex-col items-center justify-center gap-8"
                        >
                            {/* Title Text */}
                            <h2 className="text-2xl text-white/80 animate-pulse font-serif">
                                운명의 시간을 확인하고 있습니다...
                            </h2>

                            {/* Character & Speech Bubble Area */}
                            <div className="relative">
                                {/* Character Circle */}
                                <motion.div
                                    initial={{ scale: 0.8, rotate: -10 }}
                                    animate={{
                                        scale: [0.8, 1.0, 0.8],
                                        rotate: [-10, 10, -10]
                                    }}
                                    transition={{
                                        duration: 2,
                                        repeat: Infinity,
                                        ease: "easeInOut"
                                    }}
                                    className="w-48 h-48 rounded-full bg-white/10 border-4 border-white/20 flex items-center justify-center overflow-hidden backdrop-blur-sm relative z-10"
                                >
                                    <img
                                        src="/assets/images/butter.png"
                                        alt="Butter"
                                        className="w-full h-full object-cover"
                                    />
                                </motion.div>

                                {/* Speech Bubble */}
                                <AnimatedBubble
                                    theme="amber"
                                    size="large"
                                    title="버터"
                                    className="-top-32 -right-36"
                                    text="와 아 신나요!"
                                />
                            </div>

                            {/* Progress Bar */}
                            <div className="w-64 h-2 bg-white/10 rounded-full overflow-hidden mt-4">
                                <motion.div
                                    className="h-full bg-gradient-to-r from-amber-200 to-amber-500"
                                    initial={{ width: "0%" }}
                                    animate={{ width: `${loadingProgress}%` }}
                                    transition={{ ease: "linear" }}
                                />
                            </div>

                            <p className="text-white/40 text-sm font-mono">{Math.round(loadingProgress)}%</p>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </motion.div>
    );
};

export default FaceMyself;
