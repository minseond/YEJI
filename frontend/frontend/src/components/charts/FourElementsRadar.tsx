import React from 'react';
import { motion } from 'framer-motion';

interface ElementData {
    code: string;
    label: string;
    percent: number;
}

interface FourElementsRadarProps {
    data: ElementData[];
    isActive?: boolean;
}

const ELEMENT_COLORS: Record<string, string> = {
    FIRE: '#ff6b6b',      // Red
    EARTH: '#8b7355',     // Brown
    AIR: '#87ceeb',       // Sky Blue
    WATER: '#4a90e2'      // Blue
};

// Western Elements Mapping for Hanja/Icons if needed, typically:
// Fire (화), Earth (토), Air (풍), Water (수)
// But purely based on the Pie chart logic.

const LABELS: Record<string, string> = {
    FIRE: '불',
    EARTH: '흙',
    AIR: '공기',
    WATER: '물'
};

const ORDERED_CODES = ['FIRE', 'EARTH', 'AIR', 'WATER'];

const FourElementsRadar: React.FC<FourElementsRadarProps> = ({ data, isActive = true }) => {
    const size = 200;
    const center = size / 2;
    const radius = (size / 2) - 30;

    // Helper to get coordinates
    const getCoordinates = (index: number, value: number) => {
        // 4 points: 0, 90, 180, 270 degrees. 
        // Index 0 (Fire) -> Top (-PI/2)
        const angle = (Math.PI * 2 * index) / 4 - Math.PI / 2;
        const x = center + Math.cos(angle) * (radius * (value / 100));
        const y = center + Math.sin(angle) * (radius * (value / 100));
        return { x, y };
    };

    // Prepare data points
    const points = ORDERED_CODES.map((code, index) => {
        const element = data.find(d => d.code === code);
        const value = Math.max(10, element ? element.percent : 10);
        return getCoordinates(index, value);
    });

    const polygonPoints = points.map(p => `${p.x},${p.y}`).join(' ');

    // Axis lines
    const axes = ORDERED_CODES.map((code, index) => {
        const end = getCoordinates(index, 100);
        return {
            x1: center,
            y1: center,
            x2: end.x,
            y2: end.y,
            code
        };
    });

    return (
        <div className="relative w-full h-full flex items-center justify-center select-none">
            <svg width="100%" height="100%" viewBox={`0 0 ${size} ${size}`} className="overflow-visible drop-shadow-xl">
                {/* Background Grid (Diamonds/Squares) */}
                {[20, 40, 60, 80, 100].map((step, i) => {
                    const stepPoints = ORDERED_CODES.map((_, index) => {
                        const { x, y } = getCoordinates(index, step);
                        return `${x},${y}`;
                    }).join(' ');
                    return (
                        <polygon
                            key={i}
                            points={stepPoints}
                            fill="transparent"
                            stroke="rgba(255,255,255,0.1)"
                            strokeWidth="1"
                        />
                    );
                })}

                {/* Axes */}
                {axes.map((axis, i) => (
                    <line
                        key={i}
                        x1={axis.x1}
                        y1={axis.y1}
                        x2={axis.x2}
                        y2={axis.y2}
                        stroke="rgba(255,255,255,0.1)"
                        strokeWidth="1"
                    />
                ))}

                {/* Data Polygon */}
                {isActive && (
                    <motion.polygon
                        points={polygonPoints}
                        fill="rgba(99, 102, 241, 0.4)"
                        stroke="#818cf8"
                        strokeWidth="2"
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{
                            opacity: [0.4, 0.6, 0.4],
                            scale: 1,
                        }}
                        transition={{
                            opacity: { duration: 3, repeat: Infinity, ease: "easeInOut" },
                            scale: { duration: 1, ease: "easeOut" }
                        }}
                        className="drop-shadow-[0_0_15px_rgba(99,102,241,0.8)]"
                    />
                )}

                {/* Labels (Icons/Text at tips) */}
                {ORDERED_CODES.map((code, index) => {
                    const { x, y } = getCoordinates(index, 115);
                    const element = data.find(d => d.code === code);
                    const percent = element ? Math.round(element.percent) : 0;

                    return (
                        <g key={code}>
                            {/* Value Circle */}
                            <motion.circle
                                initial={{ r: 0, scale: 0 }}
                                animate={{ r: 4, scale: 1 }}
                                transition={{ duration: 0.5, delay: 0.5 + index * 0.1 }}
                                cx={points[index].x}
                                cy={points[index].y}
                                fill={ELEMENT_COLORS[code]}
                                className="drop-shadow-[0_0_8px_currentColor]"
                            />

                            {/* Tip Label Group */}
                            <foreignObject x={x - 20} y={y - 20} width={40} height={40}>
                                <div className="w-full h-full flex flex-col items-center justify-center text-center">
                                    <div
                                        className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white mb-0.5 shadow-lg border border-white/20"
                                        style={{ backgroundColor: ELEMENT_COLORS[code] }}
                                    >
                                        {/* Simple Initial or mapped label */}
                                        {LABELS[code].charAt(0)}
                                    </div>
                                    <span className="text-[10px] text-white/60 font-mono leading-none">{percent}%</span>
                                </div>
                            </foreignObject>
                        </g>
                    );
                })}
            </svg>
        </div>
    );
};

export default FourElementsRadar;
