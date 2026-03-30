import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { X } from 'lucide-react';

const SCROLL_IMAGE = "/assets/images/scroll_blank.png";

interface ScrollNameInputProps {
    onConfirm: (name: string) => void;
    initialName?: string;
    onClose?: () => void;
}

const ScrollNameInput = ({ onConfirm, initialName = "", onClose }: ScrollNameInputProps) => {
    const [name, setName] = useState(initialName);
    const [step, setStep] = useState<'input' | 'writing' | 'stamped'>('input');

    const handleConfirm = () => {
        if (!name.trim()) return;
        setStep('writing');

        // Simulate writing duration
        setTimeout(() => {
            setStep('stamped');
            // Wait for stamp to settle then finish
            setTimeout(() => {
                onConfirm(name);
            }, 500);
        }, 400);
    };

    return (
        <motion.div
            className="relative w-[300px] h-[500px] md:w-[450px] md:h-[700px] flex items-center justify-center z-50 pointer-events-auto"
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.8, opacity: 0, transition: { duration: 0.5 } }}
        >
            {/* Close Button - 콘텐츠 영역 우상단 */}
            {onClose && (
                <button
                    onClick={onClose}
                    className="absolute top-12 right-4 z-50 w-10 h-10 rounded-full bg-black/20 hover:bg-black/40 border border-white/20 text-white/60 hover:text-white backdrop-blur-md transition-all flex items-center justify-center"
                >
                    <X size={20} />
                </button>
            )}

            {/* Scroll Background Image - Screen Blend Mode to remove Black BG */}
            <img
                src={SCROLL_IMAGE}
                alt="Scroll"
                className="absolute inset-0 w-full h-full object-contain drop-shadow-2xl mix-blend-screen"
            />

            {/* Input Area - Horizontal Writing */}
            <div className="relative z-10 flex flex-col items-center justify-center gap-4 h-[70%] w-full pt-4">
                <div className="relative w-full flex justify-center">
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && step === 'input' && handleConfirm()}
                        placeholder=""
                        className="w-[60%] bg-transparent border-b-2 border-transparent focus:border-[#5d4037]/30 text-center text-4xl md:text-5xl font-serif text-[#3e2723] focus:outline-none transition-colors py-2 tracking-widest placeholder:text-[#3e2723]/20"
                        autoFocus
                        disabled={step !== 'input'}
                    />

                    {/* Brush Animation Overlay */}
                    <AnimatePresence>
                        {step === 'writing' && (
                            <motion.img
                                src="/assets/images/brush.png"
                                alt="Brush"
                                className="absolute top-[-50%] z-50 w-24 md:w-32 pointer-events-none drop-shadow-xl"
                                initial={{ x: -20, opacity: 0, scale: 0.8 }}
                                animate={{
                                    x: [-10, 50, 20, 100, 60, 140], // Rapid scribble
                                    y: [0, -10, 10, -5, 5, 0], // Vertical jitter
                                    rotate: [-10, 15, -15, 10, -5, 0], // Aggressive tilt
                                    opacity: [0, 1, 1, 1, 1, 0],
                                    scale: [0.8, 1.1, 0.9, 1.2, 1, 0.8]
                                }}
                                transition={{ duration: 0.4, ease: "linear" }}
                            />
                        )}
                    </AnimatePresence>
                </div>

                {/* Button / Stamp Container - Fixed Height to prevent layout shift */}
                <div className="h-20 flex items-center justify-center relative w-full">
                    <AnimatePresence mode="wait">
                        {step === 'input' && name && (
                            <motion.button
                                key="button"
                                initial={{ opacity: 0, scale: 0.8 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0 }}
                                onClick={handleConfirm}
                                className="relative group"
                            >
                                {/* Wax Seal Visual - Pre-stamp state */}
                                <div className="w-16 h-16 rounded-full bg-gradient-to-br from-[#8a1c1c] to-[#5e1212] shadow-[0_4px_6px_rgba(0,0,0,0.3),inset_0_-4px_4px_rgba(0,0,0,0.2)] flex items-center justify-center border-[3px] border-[#a13b3b]/50 group-hover:scale-105 transition-transform cursor-pointer">
                                    {/* Inner Ring */}
                                    <div className="w-12 h-12 rounded-full border border-[#4a0f0f]/50 flex items-center justify-center opacity-70">
                                        <div className="w-8 h-8 rounded-full border border-[#4a0f0f]/30" />
                                    </div>
                                    <div className="absolute top-2 left-3 w-4 h-2 bg-white/20 rounded-full blur-[1px]" />
                                </div>
                            </motion.button>
                        )}

                        {step === 'stamped' && (
                            <motion.div
                                key="stamp"
                                className="relative z-20 pointer-events-none"
                                initial={{ scale: 3, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                transition={{ type: 'spring', damping: 12, stiffness: 200 }}
                            >
                                {/* Stamped Wax Seal */}
                                <div className="w-20 h-20 rounded-full bg-[#8a1c1c] shadow-lg flex items-center justify-center mix-blend-multiply opacity-90">
                                    <div className="w-16 h-16 rounded-full border border-[#4a0f0f]/50 flex items-center justify-center">
                                        <div className="w-10 h-10 rounded-full border border-[#4a0f0f]/30" />
                                    </div>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </motion.div>
    );
};

export default ScrollNameInput;
