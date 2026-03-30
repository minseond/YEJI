import React, { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Flame, Droplets, Mountain, Wind } from 'lucide-react';

interface ElementData {
    code: string;
    label: string;
    percent: number;
}

interface FourElementsVisualProps {
    data: ElementData[];
    isActive?: boolean;
}

// Element Configs: Colors and Icons
const ELEMENT_CONFIG: Record<string, { color: string, bg: string, icon: any, label: string }> = {
    FIRE: {
        color: '#ef4444', // red-500
        bg: 'rgba(239, 68, 68, 0.2)',
        icon: Flame,
        label: 'Fire'
    },
    EARTH: {
        color: '#d97706', // amber-600
        bg: 'rgba(217, 119, 6, 0.2)',
        icon: Mountain, // lucide doesn't have explicit earth/soil icon, mountain is close
        label: 'Earth'
    },
    AIR: {
        color: '#0ea5e9', // sky-500
        bg: 'rgba(14, 165, 233, 0.2)',
        icon: Wind,
        label: 'Air'
    },
    WATER: {
        color: '#3b82f6', // blue-500
        bg: 'rgba(59, 130, 246, 0.2)',
        icon: Droplets,
        label: 'Water'
    }
};

const FourElementsVisual: React.FC<FourElementsVisualProps> = ({ data, isActive = true }) => {
    // 1. Find dominant element
    const sortedData = useMemo(() => {
        return [...data].sort((a, b) => b.percent - a.percent);
    }, [data]);

    const dominant = sortedData[0];

    // Determine effect type based on dominant element
    const getEffectComponent = (code: string) => {
        switch (code) {
            case 'FIRE':
                return (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden rounded-2xl">
                        {/* Fire particles/glow */}
                        <motion.div
                            animate={{
                                opacity: [0.4, 0.8, 0.4],
                                scale: [1, 1.1, 1],
                            }}
                            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute w-64 h-64 bg-red-500/20 blur-[60px] rounded-full"
                        />
                        <motion.div
                            animate={{ y: [-10, 10, -10] }}
                            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute bottom-0 w-full h-1/2 bg-gradient-to-t from-red-600/10 to-transparent"
                        />
                    </div>
                );
            case 'WATER':
                return (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden rounded-2xl">
                        <motion.div
                            animate={{
                                opacity: [0.3, 0.6, 0.3],
                                scale: [1, 1.05, 1],
                            }}
                            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute w-64 h-64 bg-blue-500/20 blur-[60px] rounded-full"
                        />
                        <motion.div
                            animate={{ y: [0, 10, 0] }}
                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute bottom-0 w-full h-1/2 bg-gradient-to-t from-blue-600/10 to-transparent"
                        />
                    </div>
                );
            case 'EARTH':
                return (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden rounded-2xl">
                        <motion.div
                            animate={{
                                opacity: [0.3, 0.5, 0.3],
                            }}
                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute w-64 h-64 bg-amber-700/20 blur-[60px] rounded-full"
                        />
                        <div className="absolute bottom-0 w-full h-1/3 bg-gradient-to-t from-amber-900/20 to-transparent" />
                    </div>
                );
            case 'AIR':
                return (
                    <div className="absolute inset-0 flex items-center justify-center pointer-events-none overflow-hidden rounded-2xl">
                        <motion.div
                            animate={{
                                opacity: [0.3, 0.6, 0.3],
                                rotate: [0, 5, -5, 0]
                            }}
                            transition={{ duration: 5, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute w-64 h-64 bg-sky-300/20 blur-[60px] rounded-full"
                        />
                        <motion.div
                            animate={{ x: [-20, 20, -20] }}
                            transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute inset-0 bg-gradient-to-tr from-transparent via-sky-400/5 to-transparent"
                        />
                    </div>
                );
            default:
                return null;
        }
    };

    const DominantConfig = ELEMENT_CONFIG[dominant.code] || ELEMENT_CONFIG.FIRE;
    const DominantIcon = DominantConfig.icon;

    return (
        <div className="w-full h-full flex flex-col relative overflow-hidden rounded-2xl bg-black/20">
            {/* Backgroud Effect for Dominant */}
            {isActive && getEffectComponent(dominant.code)}

            {/* Main Visual Area (Center) */}
            <div className="flex-1 relative flex flex-col items-center justify-center z-10 p-6 min-h-0">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ duration: 1, delay: 0.2 }}
                    className="relative"
                >
                    <div className="absolute inset-0 blur-3xl opacity-60 scale-150" style={{ backgroundColor: DominantConfig.color }} />
                    <DominantIcon
                        size={140}
                        color={DominantConfig.color}
                        className="relative z-10 drop-shadow-[0_0_40px_rgba(255,255,255,0.6)]"
                    />
                </motion.div>
                <motion.h3
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.4 }}
                    className="text-5xl font-bold mt-8 font-serif text-white uppercase tracking-widest drop-shadow-lg"
                >
                    {DominantConfig.label}
                </motion.h3>
                <div className="flex items-center gap-2 mt-2">
                    <span className="h-px w-8 bg-white/30" />
                    <motion.p
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 0.8 }}
                        transition={{ delay: 0.5 }}
                        className="text-sm text-white/70 uppercase tracking-[0.2em] font-light"
                    >
                        Dominant Element
                    </motion.p>
                    <span className="h-px w-8 bg-white/30" />
                </div>
            </div>

            {/* Bottom Stats Row */}
            <div className="h-20 bg-black/40 backdrop-blur-md border-t border-white/10 flex items-center justify-around px-2 z-20">
                {data.map((item) => {
                    const config = ELEMENT_CONFIG[item.code] || ELEMENT_CONFIG.FIRE;
                    const Icon = config.icon;
                    const isDominant = item.code === dominant.code;

                    return (
                        <div key={item.code} className="flex flex-col items-center justify-center p-2">
                            <div className={`p-1.5 rounded-full mb-1 ${isDominant ? 'bg-white/10' : 'bg-transparent'}`}>
                                <Icon
                                    size={16}
                                    color={isDominant ? config.color : 'rgba(255,255,255,0.4)'}
                                    className={isDominant ? 'animate-pulse' : ''}
                                />
                            </div>
                            <div className="flex items-baseline gap-0.5">
                                <span className={`text-sm font-bold font-mono ${isDominant ? 'text-white' : 'text-white/50'}`}>
                                    {Math.round(item.percent)}
                                </span>
                                <span className="text-[10px] text-white/30">%</span>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default FourElementsVisual;
