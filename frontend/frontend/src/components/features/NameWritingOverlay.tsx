import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState } from 'react';

// You might need to adjust the path if you saved it elsewhere
const BRUSH_IMAGE = "/assets/images/brush.png";

interface NameWritingOverlayProps {
    name: string;
    onComplete: () => void;
}

const NameWritingOverlay = ({ name, onComplete }: NameWritingOverlayProps) => {
    const [step, setStep] = useState(0); // 0: Init, 1: Writing, 2: Stamp, 3: Complete

    useEffect(() => {
        // Sequence Controller
        const timeouts: NodeJS.Timeout[] = [];

        // Start Writing after paper unfolds (0.5s)
        timeouts.push(setTimeout(() => setStep(1), 800));

        // Start Stamp after writing (approx 2s for writing)
        timeouts.push(setTimeout(() => setStep(2), 2800));

        // Complete after hold (1s after stamp)
        timeouts.push(setTimeout(() => {
            setStep(3);
            setTimeout(onComplete, 800); // Allow exit animation
        }, 3800));

        return () => timeouts.forEach(clearTimeout);
    }, [onComplete]);

    return (
        <motion.div
            className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
        >
            {/* Paper / Scroll Area */}
            <motion.div
                className="relative bg-[#fdfbf7] w-80 h-[500px] md:w-96 md:h-[600px] shadow-2xl overflow-hidden flex flex-col items-center justify-center border-y-8 border-[#3e2723]"
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 600, opacity: 1, transition: { duration: 0.8, ease: "easeOut" } }}
            >
                {/* Paper Texture Overlay */}
                <div className="absolute inset-0 opacity-20 bg-[url('https://www.transparenttextures.com/patterns/aged-paper.png')] pointer-events-none" />

                {/* Vertical Text Container */}
                <div className="relative z-10 flex flex-col items-center gap-8 py-20 h-full">

                    {/* The Name - Vertical Writing */}
                    <div className="relative writing-vertical-rl text-6xl md:text-7xl font-['Gungseo', 'NanumMyeongjo', serif] text-black tracking-[0.2em] h-full max-h-[70%] flex flex-col-reverse items-center">

                        {/* Mask for Reveal Effect */}
                        <motion.div
                            className="absolute inset-0 bg-[#fdfbf7] z-20"
                            initial={{ height: "100%" }}
                            animate={{
                                height: step >= 1 ? "0%" : "100%",
                                transition: { duration: 2.0, ease: "easeInOut" }
                            }}
                            style={{ originY: 0 }}
                        />
                        {name}
                    </div>

                    {/* Stamp */}
                    <AnimatePresence>
                        {step >= 2 && (
                            <motion.div
                                className="absolute bottom-20 z-30 border-4 border-red-700 p-2 rounded-lg"
                                initial={{ scale: 3, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                transition={{ type: 'spring', damping: 12, stiffness: 200 }}
                            >
                                <div className="w-16 h-16 bg-red-700/10 flex items-center justify-center border-2 border-red-700 rounded-sm">
                                    <span className="text-red-700 font-bold font-serif text-lg transform -rotate-12">
                                        확인
                                    </span>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                </div>
                    
                {/* Moving Brush */}
                <AnimatePresence>
                    {step === 1 && (
                        <motion.img
                            src={BRUSH_IMAGE}
                            alt="Brush"
                            className="absolute z-50 w-32 md:w-48 pointer-events-none drop-shadow-2xl"
                            initial={{ top: "10%", left: "50%", opacity: 0 }}
                            animate={{
                                top: ["15%", "40%", "65%", "80%"], // Simulate vertical movement
                                left: ["55%", "48%", "52%", "50%"], // Slight natural wobble
                                rotate: [-5, 5, -5, 0],
                                opacity: 1
                            }}
                            exit={{ x: 100, y: 100, opacity: 0, transition: { duration: 0.5 } }}
                            transition={{ duration: 2.0, ease: "easeInOut" }}
                        />
                    )}
                </AnimatePresence>

            </motion.div>
        </motion.div>
    );
};

export default NameWritingOverlay;
