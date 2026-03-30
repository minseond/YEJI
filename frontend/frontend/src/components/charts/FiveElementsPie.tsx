import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { EAST_ELEMENTS } from '../../utils/domainMapping';

interface ElementData {
    code: string;
    label: string;
    percent: number;
}

interface FiveElementsPieProps {
    data: ElementData[];
    isActive?: boolean;
}

const ELEMENT_COLORS: Record<string, string> = {
    WOOD: '#4caf50',
    FIRE: '#f44336',
    EARTH: '#ffb300',
    METAL: '#e0e0e0',
    WATER: '#2196f3'
};

const FiveElementsPie: React.FC<FiveElementsPieProps> = ({ data, isActive = true }) => {
    // Calculate SVG paths for pie slices
    let cumulativePercent = 0;

    const getCoordinatesForPercent = (percent: number) => {
        const x = Math.cos(2 * Math.PI * percent);
        const y = Math.sin(2 * Math.PI * percent);
        return [x, y];
    };

    return (
        <div className="w-full h-full flex flex-col items-center justify-center">
            <div className="flex-1 w-full relative min-h-0 flex items-center justify-center">
                <svg viewBox="-1.1 -1.1 2.2 2.2" className="w-full h-full -rotate-90 transform-gpu overflow-visible">
                    <AnimatePresence>
                        {isActive && data.map((slice, index) => {
                            if (slice.percent <= 0) return null;

                            const startPercent = cumulativePercent;
                            const endPercent = cumulativePercent + (slice.percent / 100);
                            cumulativePercent = endPercent;

                            const [startX, startY] = getCoordinatesForPercent(startPercent);
                            const [endX, endY] = getCoordinatesForPercent(endPercent);

                            const largeArcFlag = slice.percent / 100 > 0.5 ? 1 : 0;
                            const pathData = [
                                `M ${startX} ${startY}`,
                                `A 1 1 0 ${largeArcFlag} 1 ${endX} ${endY}`,
                                `L 0 0`,
                            ].join(' ');

                            return (
                                <motion.path
                                    key={slice.code}
                                    d={pathData}
                                    fill={ELEMENT_COLORS[slice.code]}
                                    initial={{ opacity: 0, scale: 0, rotate: -20 }}
                                    animate={{ opacity: 1, scale: 1, rotate: 0 }}
                                    exit={{ opacity: 0, scale: 0 }}
                                    transition={{
                                        delay: index * 0.1,
                                        duration: 0.8,
                                        type: "spring",
                                        stiffness: 80,
                                        damping: 15
                                    }}
                                    className="drop-shadow-[0_0_15px_rgba(255,255,255,0.15)]"
                                    style={{ transformOrigin: 'center' }}
                                />
                            );
                        })}
                    </AnimatePresence>
                    {/* Center Hole for Donut Style */}
                    <circle cx="0" cy="0" r="0.38" fill="#0c0c0c" className="relative z-10" />
                </svg>

                {/* Labels overlay */}
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-20">
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: isActive ? 1 : 0.3, y: isActive ? 0 : 10 }}
                        className="text-center"
                    >
                        <span className="block text-2xl font-bold text-white font-serif drop-shadow-sm">五行</span>
                    </motion.div>
                </div>
            </div>

            {/* Legend for context - Fixed Order: Fire, Water, Wood, Earth, Metal */}
            <div className="mt-6 flex gap-6 whitespace-nowrap z-30">
                {['FIRE', 'WATER', 'WOOD', 'EARTH', 'METAL'].map(code => {
                    const d = data.find(item => item.code === code) || { code, label: EAST_ELEMENTS[code]?.label || '', percent: 0 };
                    return (
                        <motion.div
                            key={code}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: isActive ? 1 : 0.4, y: isActive ? 0 : 10 }}
                            className="flex flex-col items-center gap-2"
                        >
                            <div className="w-4 h-4 rounded-full shadow-[0_0_8px_rgba(0,0,0,0.5)]" style={{ backgroundColor: ELEMENT_COLORS[code] }} />
                            <div className="flex flex-col items-center leading-none">
                                <span className="text-lg font-bold text-stone-700 mb-1 font-serif">
                                    {EAST_ELEMENTS[code]?.label}({EAST_ELEMENTS[code]?.hanja})
                                </span>
                                <span className="text-sm text-stone-500 font-mono font-bold">{Math.round(d.percent)}%</span>
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
};

export default FiveElementsPie;
