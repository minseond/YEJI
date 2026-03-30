import { useMemo, useEffect, useState } from 'react';
import { motion } from 'framer-motion';

interface FateRadarChartProps {
    stats: {
        love: number;
        money: number;
        career: number;
        health: number;
        luck: number;
    };
    color?: string;
}

const FateRadarChart = ({ stats, color = '#a855f7' }: FateRadarChartProps) => {
    // Hexagon points calculation
    const size = 200;
    const center = size / 2;
    const radius = size * 0.4;

    // 5 points for pentagon radar
    const labels = ['Love', 'Money', 'Career', 'Health', 'Luck'];
    const dataValues = [stats.love, stats.money, stats.career, stats.health, stats.luck];

    const getPoint = (value: number, index: number, max: number = 100) => {
        const angle = (Math.PI * 2 * index) / 5 - Math.PI / 2;
        const dist = (value / max) * radius;
        const x = center + dist * Math.cos(angle);
        const y = center + dist * Math.sin(angle);
        return `${x},${y}`;
    };

    const getLabelPoint = (index: number) => {
        const angle = (Math.PI * 2 * index) / 5 - Math.PI / 2;
        const dist = radius * 1.3;
        const x = center + dist * Math.cos(angle);
        const y = center + dist * Math.sin(angle);
        return { x, y };
    };

    // Animation state
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        const timer = setTimeout(() => {
            setProgress(1);
        }, 500);
        return () => clearTimeout(timer);
    }, []);

    // Dynamic points based on progress
    const points = dataValues.map((val, i) => getPoint(val * progress, i)).join(' ');
    const bgPoints = dataValues.map((_, i) => getPoint(100, i)).join(' ');

    // Levels grid
    const gridLevels = [0.2, 0.4, 0.6, 0.8, 1.0];

    return (
        <div className="relative w-full max-w-[300px] aspect-square flex items-center justify-center">
            {/* Background Glow */}
            <div className="absolute inset-0 bg-purple-500/10 blur-3xl rounded-full" />

            <svg width="100%" height="100%" viewBox={`0 0 ${size} ${size}`} className="overflow-visible">
                {/* Background Grid */}
                {gridLevels.map((level, i) => (
                    <polygon
                        key={i}
                        points={dataValues.map((_, idx) => getPoint(100 * level, idx)).join(' ')}
                        fill="none"
                        stroke="rgba(168, 85, 247, 0.2)"
                        strokeWidth="1"
                        strokeDasharray={i === 4 ? "0" : "4 2"}
                    />
                ))}

                {/* Axis Lines */}
                {dataValues.map((_, i) => {
                    const p = getPoint(100, i);
                    return (
                        <line
                            key={i}
                            x1={center}
                            y1={center}
                            x2={p.split(',')[0]}
                            y2={p.split(',')[1]}
                            stroke="rgba(168, 85, 247, 0.1)"
                            strokeWidth="1"
                        />
                    );
                })}

                {/* Data Polygon */}
                <motion.polygon
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.6, fillOpacity: 0.4 }}
                    points={points}
                    fill="url(#radarGradient)"
                    stroke={color}
                    strokeWidth="2"
                    filter="url(#glow)"
                />

                {/* Data Points */}
                {dataValues.map((val, i) => {
                    const [x, y] = getPoint(val * progress, i).split(',');
                    return (
                        <motion.circle
                            key={i}
                            initial={{ r: 0 }}
                            animate={{ r: 3 }}
                            cx={x}
                            cy={y}
                            fill="#fff"
                            stroke={color}
                            strokeWidth="2"
                        />
                    );
                })}

                {/* Labels */}
                {labels.map((label, i) => {
                    const { x, y } = getLabelPoint(i);
                    return (
                        <text
                            key={i}
                            x={x}
                            y={y}
                            textAnchor="middle"
                            dominantBaseline="middle"
                            fill="rgba(255,255,255,0.7)"
                            fontSize="10"
                            fontWeight="bold"
                            className="font-mono tracking-widest uppercase"
                        >
                            {label}
                        </text>
                    );
                })}

                {/* Gradients & Filters */}
                <defs>
                    <linearGradient id="radarGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={color} stopOpacity="0.8" />
                        <stop offset="100%" stopColor={color} stopOpacity="0.2" />
                    </linearGradient>
                    <filter id="glow">
                        <feGaussianBlur stdDeviation="2.5" result="coloredBlur" />
                        <feMerge>
                            <feMergeNode in="coloredBlur" />
                            <feMergeNode in="SourceGraphic" />
                        </feMerge>
                    </filter>
                </defs>
            </svg>
        </div>
    );
};

export default FateRadarChart;
