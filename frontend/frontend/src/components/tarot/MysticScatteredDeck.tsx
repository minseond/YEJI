import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useMemo } from 'react';
import TarotBack1 from '../../assets/타로카드/back1.png';
import TarotBack2 from '../../assets/타로카드/back2.png';
import TarotBack3 from '../../assets/타로카드/back3.png';

interface MysticScatteredDeckProps {
    cards: any[];
    onCardPick: (index: number) => void;
    stepIndex: number;
}

const MysticScatteredDeck = ({ cards, onCardPick, stepIndex }: MysticScatteredDeckProps) => {
    const [isScattered, setIsScattered] = useState(false);
    const tarotBackImages = [TarotBack1, TarotBack2, TarotBack3];
    const cardBack = tarotBackImages[stepIndex] || TarotBack1;

    // Generate stable random positions for the scatter effect
    const scatteredPositions = useMemo(() => {
        return cards.map((_, i) => ({
            id: i,
            x: (Math.random() - 0.5) * 85, // -42.5% to 42.5% of width
            y: (Math.random() - 0.5) * 45 + 10, // Shifted down and range reduced to avoid header
            rotate: (Math.random() - 0.5) * 40, // -20 to 20 degrees
            initialDelay: i * 0.02
        }));
    }, [cards.length]);

    useEffect(() => {
        // Initial shuffle for 1.2 seconds, then scatter
        const timer = setTimeout(() => setIsScattered(true), 1200);
        return () => clearTimeout(timer);
    }, []);

    return (
        <div className="relative w-full h-[55vh] flex items-center justify-center overflow-visible select-none -mt-10">
            {/* Ambient Background Effect */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(139,92,246,0.1),transparent_70%)] pointer-events-none" />

            <AnimatePresence>
                {cards.map((card, i) => {
                    const pos = scatteredPositions[i];
                    return (
                        <motion.div
                            key={card.id || i}
                            initial={{ x: 0, y: 0, rotate: 0, scale: 0.8, opacity: 0 }}
                            animate={isScattered ? {
                                x: `${pos.x}vw`,
                                y: `${pos.y}vh`,
                                rotate: pos.rotate,
                                scale: 1,
                                opacity: 1,
                                transition: {
                                    type: "spring",
                                    stiffness: 70,
                                    damping: 14,
                                    delay: pos.initialDelay
                                }
                            } : {
                                x: 0,
                                y: 0,
                                rotate: (i % 2 === 0 ? 5 : -5),
                                scale: 0.95,
                                opacity: 1,
                                transition: { duration: 0.5 }
                            }}
                            whileHover={isScattered ? {
                                scale: 1.2,
                                zIndex: 100,
                                rotate: 0,
                                filter: "brightness(1.2) drop-shadow(0 0 30px rgba(167, 139, 250, 0.6))",
                                transition: { duration: 0.2 }
                            } : {}}
                            whileTap={isScattered ? { scale: 0.95 } : {}}
                            onClick={() => isScattered && onCardPick(i)}
                            className="absolute w-20 h-30 md:w-28 md:h-42 rounded-xl shadow-2xl cursor-pointer group preserve-3d"
                            style={{ zIndex: i }}
                        >
                            <div className="w-full h-full relative rounded-xl overflow-hidden border border-white/10 bg-gray-950">
                                <img
                                    src={cardBack}
                                    alt="Tarot Back"
                                    className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                                />

                                {/* Mystical Glowing Border */}
                                <div className="absolute inset-0 border border-purple-500/20 rounded-xl" />
                                <div className="absolute inset-0 bg-gradient-to-tr from-purple-500/10 via-transparent to-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                                {/* Inner Shadow for depth */}
                                <div className="absolute inset-x-0 bottom-0 h-1/2 bg-gradient-to-t from-black/40 to-transparent pointer-events-none" />
                            </div>
                        </motion.div>
                    );
                })}
            </AnimatePresence>

            {/* Instruction removed per request */}
        </div>
    );
};

export default MysticScatteredDeck;
