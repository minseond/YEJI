import React from 'react';
import { motion } from 'framer-motion';

export const RADAR_LABELS = [
    { key: 'communication', label: '소통 지수', color: '#94a3b8' },
    { key: 'stability', label: '안정 지수', color: '#f59e0b' },
    { key: 'growth', label: '성장 지수', color: '#10b981' },
    { key: 'passion', label: '열정 지수', color: '#ef4444' },
    { key: 'flexibility', label: '유연 지수', color: '#3b82f6' }
];

const RadarChart = ({ data, highlightKey }: { data: Record<string, number>, highlightKey?: string }) => {
    const size = 300;
    const center = size / 2;
    const radius = 100;
    const labels = RADAR_LABELS;

    const getPoint = (index: number, value: number) => {
        const angle = (Math.PI * 2 * index) / 5 - Math.PI / 2;
        const dist = (value / 100) * radius;
        return {
            x: center + Math.cos(angle) * dist,
            y: center + Math.sin(angle) * dist
        };
    };

    const dataPoints = labels.map((l, i) => getPoint(i, data[l.key]));
    const dataPath = dataPoints.map(p => `${p.x},${p.y}`).join(' ');

    return (
        <div className="relative">
            <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="overflow-visible">
                <defs>
                    {labels.map(l => (
                        <radialGradient key={`grad-${l.key}`} id={`grad-${l.key}`} cx="50%" cy="50%" r="50%">
                            <stop offset="0%" stopColor={l.color} stopOpacity="0.4" />
                            <stop offset="100%" stopColor={l.color} stopOpacity="0.1" />
                        </radialGradient>
                    ))}
                </defs>
                {[25, 50, 75, 100].map(level => (
                    <polygon
                        key={level}
                        points={labels.map((_, i) => {
                            const p = getPoint(i, level);
                            return `${p.x},${p.y}`;
                        }).join(' ')}
                        className="fill-none stroke-amber-500/10 stroke-[0.5]"
                    />
                ))}
                <motion.polygon
                    points={dataPath}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 1 }}
                    fill={highlightKey ? `url(#grad-${highlightKey})` : 'rgba(251, 191, 36, 0.2)'}
                    stroke={highlightKey ? RADAR_LABELS.find(l => l.key === highlightKey)?.color : '#f59e0b'}
                    strokeWidth="2"
                    style={{ filter: highlightKey ? `drop-shadow(0 0 8px ${RADAR_LABELS.find(l => l.key === highlightKey)?.color})` : 'none' }}
                />
                {labels.map((l, i) => {
                    const p = getPoint(i, 130);
                    const isHighlighted = highlightKey === l.key;
                    return (
                        <foreignObject key={i} x={p.x - 40} y={p.y - 20} width="80" height="40">
                            <div className={`text-center transition-all ${isHighlighted ? 'scale-110' : 'opacity-60'}`}>
                                <div className="text-[10px] font-bold" style={{ color: l.color }}>{l.label}</div>
                                <div className="text-white font-bold">{data[l.key]}</div>
                            </div>
                        </foreignObject>
                    );
                })}
            </svg>
        </div>
    );
};

export default RadarChart;
