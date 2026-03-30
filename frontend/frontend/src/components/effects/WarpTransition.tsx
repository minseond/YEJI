import { motion } from 'framer-motion';
import { useEffect } from 'react';

const WarpTransition = ({ onComplete }: { onComplete: () => void }) => {
    useEffect(() => {
        const timer = setTimeout(onComplete, 2200); // 2.2s duration to sync with anims
        return () => clearTimeout(timer);
    }, [onComplete]);

    return (
        <motion.div
            className="fixed inset-0 z-[100] flex items-center justify-center pointer-events-auto"
            initial={{ backgroundColor: "rgba(0,0,0,0)" }}
            animate={{ backgroundColor: ["rgba(0,0,0,0)", "rgba(0,0,0,0.8)", "rgba(0,0,0,1)"] }}
            transition={{ duration: 2.2, times: [0, 0.7, 1] }}
        >
            {/* Distortion Field - Expanding Lens */}
            <motion.div
                className="absolute z-10 rounded-full border-4 border-white/20"
                style={{
                    backdropFilter: "blur(20px) brightness(1.5) contrast(1.2)",
                    boxShadow: "inset 0 0 100px rgba(255,255,255,0.3)"
                }}
                initial={{ width: "10px", height: "10px", opacity: 0 }}
                animate={{
                    width: ["10px", "150vmax"],
                    height: ["10px", "150vmax"],
                    opacity: [0, 1, 0]
                }}
                transition={{ duration: 1.8, ease: "circIn" }}
            />

            {/* Core Singularity - Pure White Light */}
            <motion.div
                className="absolute z-20 w-2 h-2 bg-white rounded-full shadow-[0_0_50px_20px_rgba(255,255,255,1)]"
                initial={{ scale: 1, opacity: 0 }}
                animate={{
                    scale: [1, 5, 300],
                    opacity: [0, 1, 0]
                }}
                transition={{ duration: 1.5, ease: "easeIn", delay: 0.2 }}
            />

            {/* Hyperspace Streaks - Minimalist High Speed */}
            <div className="absolute inset-0 z-0 overflow-hidden">
                {[...Array(20)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="absolute top-1/2 left-1/2 w-[2px] h-[50vh] bg-gradient-to-t from-transparent via-white/80 to-transparent origin-bottom"
                        style={{
                            rotate: `${i * 18}deg`,
                            transformOrigin: '50% 100%',
                        }}
                        initial={{ opacity: 0, height: 0, translateY: -100 }}
                        animate={{
                            opacity: [0, 1, 0],
                            height: ['0vh', '80vh', '150vh'],
                            translateY: [0, 200, 1000]
                        }}
                        transition={{
                            duration: 1.2,
                            delay: Math.random() * 0.3,
                            ease: "easeIn"
                        }}
                    />
                ))}
            </div>
        </motion.div>
    );
};

export default WarpTransition;
