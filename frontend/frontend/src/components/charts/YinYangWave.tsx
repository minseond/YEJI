import React from 'react';
import { motion } from 'framer-motion';

interface YinYangWaveProps {
    yin: number; // Percentage 0-100
    yang: number; // Percentage 0-100
}

const YinYangWave: React.FC<YinYangWaveProps> = ({ yin, yang }) => {
    const total = yin + yang;
    const yinPct = total === 0 ? 50 : (yin / total) * 100;

    return (
        <div className="w-full flex flex-col gap-2">
            <div className="relative w-full h-16 rounded-full overflow-hidden border border-white/10 bg-zinc-900 shadow-[inset_0_2px_10px_rgba(0,0,0,0.5)]">
                {/* Yin (Black) is background */}

                {/* Yang (White) Fill */}
                <motion.div
                    className="absolute inset-y-0 right-0 bg-gray-100 flex items-center"
                    initial={{ width: '50%' }}
                    animate={{ width: `${100 - yinPct}%` }}
                    transition={{ duration: 1, ease: "easeOut" }}
                >
                    {/* Waving Interface */}
                    <div className="absolute left-0 top-0 bottom-0 w-[20px] -translate-x-1/2 h-full z-10 overflow-visible">
                        <svg viewBox="0 0 20 100" className="h-full w-full overflow-visible" preserveAspectRatio="none">
                            <motion.path
                                d="M10,0 Q20,25 10,50 Q0,75 10,100 L20,100 L20,0 Z"
                                fill="#f3f4f6" // matches bg-gray-100
                                animate={{
                                    d: [
                                        "M10,0 Q18,25 10,50 Q2,75 10,100 L20,100 L20,0 Z",
                                        "M10,0 Q2,25 10,50 Q18,75 10,100 L20,100 L20,0 Z",
                                        "M10,0 Q18,25 10,50 Q2,75 10,100 L20,100 L20,0 Z"
                                    ]
                                }}
                                transition={{
                                    repeat: Infinity,
                                    duration: 2,
                                    ease: "linear"
                                }}
                            />
                        </svg>
                    </div>
                </motion.div>

                {/* Text Labels Overlay */}
                <div className="absolute inset-0 flex justify-between items-center px-6 pointer-events-none">
                    <div className="flex flex-col items-center">
                        <span className="text-[10px] text-white/40 uppercase tracking-widest">YIN (음)</span>
                        <span className="text-lg font-bold text-white font-mono">{Math.round(yinPct)}%</span>
                    </div>
                    <div className="flex flex-col items-center">
                        <span className="text-[10px] text-black/40 uppercase tracking-widest">YANG (양)</span>
                        <span className="text-lg font-bold text-black font-mono">{Math.round(100 - yinPct)}%</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default YinYangWave;
