import { useState, memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Heart, Coins, Activity, GraduationCap, Briefcase } from 'lucide-react';

interface FortuneSelectionProps {
    onSelect: (question: string) => void;
    onHover?: (id: string | null) => void;
    disabled?: boolean;
}

const fortuneTypes = [
    {
        id: 'love',
        title: "연애운",
        subtitle: "Love",
        desc: "나의 인연과 사랑의 흐름을 알아봅니다.",
        icon: Heart,
        color: "rose",
        gradientFrom: "rgba(244, 63, 94, 0.4)", // rose-500
        question: "저의 연애운과 새로운 인연에 대해 알려주세요. 제가 주의해야 할 점이나 좋은 시기가 있을까요?"
    },
    {
        id: 'wealth',
        title: "재물운",
        subtitle: "Wealth",
        desc: "재물의 흐름과 풍요의 기운을 확인합니다.",
        icon: Coins,
        color: "amber",
        gradientFrom: "rgba(245, 158, 11, 0.4)", // amber-500
        question: "이번 달, 그리고 앞으로의 금전적인 흐름은 어떨까요? 재물운을 높이기 위한 조언이 필요합니다."
    },
    {
        id: 'health',
        title: "건강운",
        subtitle: "Health",
        desc: "신체의 기운과 활력을 점검해봅니다.",
        icon: Activity,
        color: "emerald",
        gradientFrom: "rgba(16, 185, 129, 0.4)", // emerald-500
        question: "저의 건강 상태와 컨디션 관리에 대해 조언해 주세요. 특별히 조심해야 할 부분이 있을까요?"
    },
    {
        id: 'academic',
        title: "학업운",
        subtitle: "Study",
        desc: "학업 성취와 지혜의 길을 밝혀봅니다.",
        icon: GraduationCap,
        color: "blue",
        gradientFrom: "rgba(59, 130, 246, 0.4)", // blue-500
        question: "학업이나 시험 준비에 있어서 좋은 성과를 낼 수 있을까요? 집중력을 높이는 방법이 궁금합니다."
    },
    {
        id: 'career',
        title: "직업운",
        subtitle: "Career",
        desc: "일과 성공, 승진의 기회를 엿봅니다.",
        icon: Briefcase,
        color: "violet",
        gradientFrom: "rgba(139, 92, 246, 0.4)", // violet-500
        question: "직장에서의 성취와 발전 가능성이 궁금합니다. 커리어 성장을 위해 어떤 태도가 필요할까요?"
    },
];

const FortuneSelection = memo(({ onSelect, onHover, disabled = false }: FortuneSelectionProps) => {
    const [hoveredId, setHoveredId] = useState<string | null>(null);

    const handleHover = (id: string | null) => {
        if (disabled) return;
        setHoveredId(id);
        if (onHover) onHover(id);
    };

    const radius = 220; // Radius of the circle

    return (
        <div className={`absolute inset-0 z-20 flex flex-col items-center justify-center pointer-events-none ${disabled ? 'cursor-wait' : ''}`}>
            {/* Title - Moved up */}
            <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="absolute inset-0 flex flex-col items-center justify-center z-30 pointer-events-none pt-10"
            >
                <h2 className={`text-4xl md:text-5xl font-['Gowun_Batang'] mb-2 transition-all duration-300 ${hoveredId ? 'text-black drop-shadow-md' : 'text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-indigo-200 drop-shadow-sm'}`}>
                    운명의 갈래
                </h2>

            </motion.div>

            {/* Circular Container (The Round Table) */}
            <div className={`relative w-[300px] h-[300px] md:w-[500px] md:h-[500px] flex items-center justify-center header-hidden mt-20 ${disabled ? 'pointer-events-none' : 'pointer-events-auto'}`}>
                {/* Table Decoration line */}
                <div className="absolute inset-0 rounded-full border border-white/5 opacity-50" />

                {fortuneTypes.map((item, index) => {
                    const isHovered = hoveredId === item.id;
                    const count = fortuneTypes.length;
                    const angle = (index * (360 / count)) - 90; // Start from top (-90 degrees)
                    const radian = (angle * Math.PI) / 180;

                    const x = Math.cos(radian) * radius;
                    const y = Math.sin(radian) * radius;

                    return (
                        <motion.button
                            key={item.id}
                            disabled={disabled}
                            initial={{ opacity: 0 }}
                            animate={{
                                opacity: 1,
                                scale: isHovered ? 1.1 : 1,
                                width: isHovered ? 160 : 110,
                                height: isHovered ? 160 : 110,
                                backgroundColor: isHovered ? 'rgba(20, 20, 20, 0.95)' : 'rgba(255, 255, 255, 0.05)',
                                borderColor: isHovered ? 'rgba(255, 255, 255, 0.6)' : 'rgba(255, 255, 255, 0.15)',
                                borderWidth: isHovered ? '2px' : '1px',
                            }}
                            onHoverStart={() => handleHover(item.id)}
                            onHoverEnd={() => handleHover(null)}
                            onClick={() => onSelect(item.id)}
                            className={`absolute flex flex-col items-center justify-center overflow-hidden shadow-lg`}
                            style={{
                                x: x,
                                y: y,
                                borderRadius: '50%',
                                zIndex: isHovered ? 50 : 10,
                            }}
                            transition={{
                                type: "spring",
                                stiffness: 300,
                                damping: 20,
                                opacity: { duration: 0.5, delay: index * 0.1 } // Staggered fade in
                            }}
                        >
                            {/* Background Gradient on Hover */}
                            <motion.div
                                className="absolute inset-0"
                                style={{
                                    background: `linear-gradient(to bottom right, ${item.gradientFrom}, transparent, transparent)`
                                }}
                                initial={{ opacity: 0 }}
                                animate={{ opacity: isHovered ? 1 : 0 }}
                            />

                            {/* Icon & Text Container */}
                            <motion.div
                                className="relative z-10 flex flex-col items-center justify-center gap-2"
                            >
                                <item.icon
                                    size={isHovered ? 36 : 32}
                                    className={`transition-colors duration-300 ${isHovered ? `text-${item.color}-200` : `text-white/30`}`}
                                />

                                {/* Title - Always visible but styled better on hover */}
                                <motion.span
                                    animate={{
                                        opacity: 1,
                                        y: isHovered ? 0 : 5,
                                        scale: isHovered ? 1.1 : 1
                                    }}
                                    className={`text-sm font-['Gowun_Batang'] whitespace-nowrap ${isHovered ? 'text-white font-bold' : 'text-white/40'}`}
                                >
                                    {item.title}
                                </motion.span>

                                {/* Simple "Select" text on hover only */}
                                <AnimatePresence>
                                    {isHovered && (
                                        <motion.span
                                            initial={{ opacity: 0, height: 0 }}
                                            animate={{ opacity: 1, height: 'auto' }}
                                            exit={{ opacity: 0, height: 0 }}
                                            className={`text-[10px] text-${item.color}-300 font-light tracking-widest uppercase`}
                                        >
                                            SELECT
                                        </motion.span>
                                    )}
                                </AnimatePresence>
                            </motion.div>
                        </motion.button>
                    );
                })}
            </div>
        </div>
    );
});

export default FortuneSelection;
