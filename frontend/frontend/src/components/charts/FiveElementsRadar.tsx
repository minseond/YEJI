import React from 'react';
import { motion } from 'framer-motion';
import { EAST_ELEMENTS } from '../../utils/domainMapping';

interface ElementData {
    code: string;
    label: string;
    percent: number;
}

interface FiveElementsRadarProps {
    data: ElementData[];
    isActive?: boolean;
    textColor?: string;
}

const ELEMENT_COLORS: Record<string, string> = {
    WOOD: '#4caf50',  // Green
    FIRE: '#f44336',  // Red
    EARTH: '#ffb300', // Yellow/Amber
    METAL: '#90a4ae', // Metal/Grey - Adjusted for better visibility
    WATER: '#2196f3'  // Blue
};

// Order: Wood -> Fire -> Earth -> Metal -> Water (Generative Cycle)
const ORDERED_CODES = ['WOOD', 'FIRE', 'EARTH', 'METAL', 'WATER'];

const FiveElementsRadar: React.FC<FiveElementsRadarProps> = ({ data, isActive = true, textColor = 'text-white/60' }) => {
    const size = 200;
    const center = size / 2;
    const radius = (size / 2) - 30; // Leave space for labels

    // Helper to get coordinates
    const getCoordinates = (index: number, value: number) => {
        const angle = (Math.PI * 2 * index) / 5 - Math.PI / 2; // Start from top
        const x = center + Math.cos(angle) * (radius * (value / 100));
        const y = center + Math.sin(angle) * (radius * (value / 100));
        return { x, y };
    };

    // Prepare data points for the polygon (normalized to 0-100, but ensuring minimal visibility)
    const points = ORDERED_CODES.map((code, index) => {
        const element = data.find(d => d.code === code);
        // Ensure even 0% has a tiny presence so the chart doesn't collapse fully
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
                {/* Background Grid (Pentagons) */}
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
                        fill="rgba(251, 191, 36, 0.4)" // Amber-ish fill
                        stroke="#fbbf24"
                        strokeWidth="2"
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{ opacity: 1, scale: 1 }}
                        transition={{ duration: 0 }}
                        className="drop-shadow-[0_0_10px_rgba(251,191,36,0.6)]"
                    />
                )}

                {/* Labels (Icons/Text at tips) */}
                {ORDERED_CODES.map((code, index) => {
                    const { x, y } = getCoordinates(index, 115); // Place slightly outside
                    const element = data.find(d => d.code === code);
                    const percent = element ? Math.round(element.percent) : 0;

                    return (
                        <g key={code}>
                            {/* Value Circle */}
                            <motion.circle
                                initial={{ r: 0 }}
                                animate={{ r: 4 }}
                                cx={points[index].x}
                                cy={points[index].y}
                                fill={ELEMENT_COLORS[code]}
                                className="drop-shadow-[0_0_5px_currentColor]"
                            />

                            {/* Tip Label Group */}
                            <foreignObject x={x - 20} y={y - 20} width={40} height={40}>
                                <div className="w-full h-full flex flex-col items-center justify-center text-center">
                                    <div
                                        className="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold text-white mb-0.5 shadow-lg border border-white/20"
                                        style={{ backgroundColor: ELEMENT_COLORS[code] }}
                                    >
                                        {EAST_ELEMENTS[code]?.hanja}
                                    </div>
                                    <span className={`text-[10px] ${textColor} font-mono leading-none font-bold`}>{percent}%</span>
                                </div>
                            </foreignObject>
                        </g>
                    );
                })}
            </svg>
        </div>
    );
};

export default FiveElementsRadar;
