import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

interface BirthstoneRouletteProps {
    onSelect: (month: number) => void;
    onClose?: () => void;
}

const BIRTHSTONES = [
    { month: 1, name: 'Garnet', kor: '가넷', meaning: '진실, 우정', color: '#B22222' },
    { month: 2, name: 'Amethyst', kor: '자수정', meaning: '평화, 성실', color: '#9966CC' },
    { month: 3, name: 'Aquamarine', kor: '아쿠아마린', meaning: '총명, 용기', color: '#7FFFD4' },
    { month: 4, name: 'Diamond', kor: '다이아몬드', meaning: '불멸, 고귀', color: '#E0E0E0' },
    { month: 5, name: 'Emerald', kor: '에메랄드', meaning: '행복, 행운', color: '#50C878' },
    { month: 6, name: 'Pearl', kor: '진주', meaning: '순결, 부귀', color: '#F5F5F5' },
    { month: 7, name: 'Ruby', kor: '루비', meaning: '사랑, 평화', color: '#E0115F' },
    { month: 8, name: 'Peridot', kor: '페리도트', meaning: '화목, 해로', color: '#B9F276' },
    { month: 9, name: 'Sapphire', kor: '사파이어', meaning: '성실, 진실', color: '#0F52BA' },
    { month: 10, name: 'Opal', kor: '오팔', meaning: '희망, 순결', color: '#EECFA1' },
    { month: 11, name: 'Topaz', kor: '토파즈', meaning: '건강, 희망', color: '#FFC87C' },
    { month: 12, name: 'Turquoise', kor: '터키석', meaning: '성공, 승리', color: '#40E0D0' },
];

const RADIUS = 250; // Radius of the circle
const GEM_SIZE = 120; // Adjust this value to change the size of the gems

const BirthstoneRoulette = ({ onSelect, onClose }: BirthstoneRouletteProps) => {
    const [hoveredMonth, setHoveredMonth] = useState<number | null>(null);

    const activeStone = hoveredMonth ? BIRTHSTONES.find(s => s.month === hoveredMonth) : null;

    return (
        <div className="relative w-full h-[600px] flex flex-col items-center justify-center">
            {/* Removed Title as requested to verify spacing */}

            <div className="relative w-[600px] h-[600px] rounded-full flex items-center justify-center">

                {/* Central Info Display */}
                <div className="absolute inset-0 flex items-center justify-center z-0 pointer-events-none">
                    <AnimatePresence mode="wait">
                        {activeStone ? (
                            <motion.div
                                key={activeStone.month}
                                initial={{ opacity: 0, scale: 0.9, y: 10 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.9, y: -10 }}
                                transition={{ duration: 0.15, ease: "easeOut" }}
                                className="flex flex-col items-center text-center"
                            >
                                <div className="text-5xl font-serif font-bold text-[#e0c097] mb-2 tracking-[0.1em] drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]">
                                    {new Date(2000, activeStone.month - 1).toLocaleString('en-US', { month: 'long' }).toUpperCase()}
                                </div>
                                <div
                                    className="text-2xl font-serif mb-6 tracking-[0.3em] uppercase border-b border-white/20 pb-2 drop-shadow-md"
                                    style={{ color: activeStone.color, textShadow: `0 0 10px ${activeStone.color}80` }}
                                >
                                    {activeStone.name}
                                </div>
                                <div className="text-white/60 text-lg font-serif italic font-light tracking-wide">
                                    "{activeStone.meaning}"
                                </div>
                            </motion.div>
                        ) : (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="text-white/30 font-serif text-xl"
                            >
                                {/* Empty state */}
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Decorative Ring (Subtle) */}
                <div className="absolute inset-0 m-auto w-[500px] h-[500px] border border-white/5 rounded-full pointer-events-none" />

                {BIRTHSTONES.map((stone, index) => {
                    // Position calculations for 2D Circle
                    // Place 1 at Top (-90 deg). User wants 1 shifted right (+30 deg) -> -60 deg.
                    const angleDeg = (index * 30) - 60;
                    const angleRad = angleDeg * (Math.PI / 180);

                    const x = Math.cos(angleRad) * RADIUS;
                    const y = Math.sin(angleRad) * RADIUS;

                    return (
                        <Item
                            key={stone.month}
                            month={stone.month}
                            x={x}
                            y={y}
                            onSelect={() => onSelect(stone.month)}
                            onHover={(isHover) => setHoveredMonth(isHover ? stone.month : null)}
                        />
                    );
                })}
            </div>

            {/* Close Button - Bottom Center */}
            {onClose && (
                <div className="absolute bottom-10 z-[60]">
                    <button
                        onClick={onClose}
                        className="w-16 h-16 rounded-full bg-white/10 hover:bg-white/20 border border-white/30 text-white/80 hover:text-white backdrop-blur-md transition-all flex items-center justify-center group shadow-lg"
                    >
                        <X size={24} />
                    </button>
                </div>
            )}
        </div>
    );
};

const Item = ({ month, x, y, onSelect, onHover }: { month: number, x: number, y: number, onSelect: () => void, onHover: (v: boolean) => void }) => {
    const [imgError, setImgError] = useState(false);
    const [hover, setHover] = useState(false);

    // Gem fallback logic (same as before)
    const GEM_COLORS = [
        'bg-red-900', 'bg-purple-900', 'bg-blue-300', 'bg-white',
        'bg-green-600', 'bg-gray-200', 'bg-red-600', 'bg-green-400',
        'bg-blue-800', 'bg-pink-400', 'bg-yellow-500', 'bg-blue-500'
    ];
    const fallbackColor = GEM_COLORS[(month - 1) % GEM_COLORS.length];

    const handleHoverStart = () => {
        setHover(true);
        onHover(true);
    };

    const handleHoverEnd = () => {
        setHover(false);
        onHover(false);
    };

    const HIT_SIZE = GEM_SIZE * 0.5; // Trigger area is 50% of visual size

    return (
        <motion.div
            className="absolute flex flex-col items-center justify-center cursor-pointer group rounded-full"
            style={{
                x: x,
                y: y,
                left: '50%',
                top: '50%',
                marginLeft: -HIT_SIZE / 2,
                marginTop: -HIT_SIZE / 2,
                width: HIT_SIZE,
                height: HIT_SIZE
            }}
            whileHover={{ scale: 1.5, zIndex: 50 }}
            onClick={onSelect}
            onHoverStart={handleHoverStart}
            onHoverEnd={handleHoverEnd}
        >
            {/* Glow Effect only on Hover */}
            {hover && (
                <motion.div
                    layoutId="glow"
                    className="absolute bg-white/40 blur-xl rounded-full pointer-events-none"
                    style={{ width: GEM_SIZE, height: GEM_SIZE }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.2 }}
                />
            )}

            {/* Container: Transparent by default, Remove borders/bg unless Error */}
            <div
                className={`absolute flex items-center justify-center transition-all duration-300 pointer-events-none ${imgError ? `rounded-full ${fallbackColor} border border-white/20` : ''}`}
                style={{ width: GEM_SIZE, height: GEM_SIZE }}
            >
                {!imgError ? (
                    <img
                        src={`/assets/birthstones/${month}_gem.png`}
                        alt={`${month}월`}
                        className="w-full h-full object-contain filter drop-shadow-[0_0_5px_rgba(255,255,255,0.3)]"
                        onError={() => setImgError(true)}
                    />
                ) : (
                    <span className="text-white font-bold text-lg drop-shadow-md">{month}</span>
                )}
            </div>

            {/* Removed Text Label Below as requested */}
        </motion.div>
    );
};

export default BirthstoneRoulette;
