import { motion, useMotionValue, useTransform, useAnimation } from 'framer-motion';
import { useState, useEffect, useRef } from 'react';
import TarotBack1 from '../../assets/타로카드/back1.png';
import TarotBack2 from '../../assets/타로카드/back2.png';
import TarotBack3 from '../../assets/타로카드/back3.png';

interface DraggableFanDeckProps {
    cards: any[];
    onCardPick: (index: number) => void;
    stepIndex: number;
}

const DraggableFanDeck = ({ cards, onCardPick, stepIndex }: DraggableFanDeckProps) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const x = useMotionValue(0);
    const controls = useAnimation();
    const [centerIndex, setCenterIndex] = useState(0);
    const [constraints, setConstraints] = useState({ left: 0, right: 0 });

    // Constants for the "Dynamic Focus Fan"
    const SNAP_STRENGTH = 200;
    const SNAP_DAMPING = 30;

    // Configuration based on step
    const getConfig = (step: number) => {
        const configs = [
            { spread: 80, arcStrength: 1.2, brightness: 0.8 },
            { spread: 90, arcStrength: 1.0, brightness: 1.0 },
            { spread: 85, arcStrength: 1.5, brightness: 0.9 }
        ];
        return configs[step] || configs[1];
    };
    const config = getConfig(stepIndex);

    // Dynamic constraints and initial snap
    useEffect(() => {
        if (!cards.length) return;

        const totalCards = cards.length;
        const middleIndex = Math.floor(totalCards / 2);
        const maxScroll = (totalCards - 1) * config.spread;

        setConstraints({ left: -maxScroll, right: 0 });

        // Initial Snap to middle card
        const initialX = -middleIndex * config.spread;
        x.set(initialX);
        controls.set({ x: initialX });
        setCenterIndex(middleIndex);
    }, [cards.length, config.spread]);

    const handleDrag = () => {
        const currentX = x.get();
        const nearestIndex = Math.round(Math.abs(currentX) / config.spread);
        const clampedIndex = Math.min(Math.max(nearestIndex, 0), cards.length - 1);
        if (clampedIndex !== centerIndex) {
            setCenterIndex(clampedIndex);
        }
    };

    const handleDragEnd = (_event: any, info: any) => {
        const currentX = x.get();
        const velocity = info.velocity.x;

        // Calculate projected stop position based on velocity
        const projectedX = currentX + (velocity * 0.2);
        const nearestIndex = Math.round(Math.abs(projectedX) / config.spread);
        const clampedIndex = Math.min(Math.max(nearestIndex, 0), cards.length - 1);
        const finalX = -clampedIndex * config.spread;

        controls.start({
            x: finalX,
            transition: {
                type: "spring",
                velocity: velocity,
                stiffness: SNAP_STRENGTH,
                damping: SNAP_DAMPING,
                restDelta: 0.001
            }
        });
        setCenterIndex(clampedIndex);
    };

    return (
        <div className="relative w-full h-full flex items-center justify-center" ref={containerRef}>
            {/* Ambient background glow */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_120%,rgba(168,85,247,0.15),transparent_70%)] pointer-events-none" />

            {/* Guide Text */}
            <div className="absolute top-8 md:top-12 text-purple-300/40 text-[10px] md:text-xs tracking-[0.5em] font-medium z-0 animate-pulse pointer-events-none">
                — EXPLORE YOUR DESTINY —
            </div>

            <motion.div
                className="absolute top-1/2 left-1/2 flex items-center justify-center cursor-grab active:cursor-grabbing preserve-3d py-20 px-[25vw]"
                style={{ x }}
                drag="x"
                dragConstraints={constraints}
                dragElastic={0.2}
                animate={controls}
                onDrag={handleDrag}
                onDragEnd={handleDragEnd}
            >
                {cards.map((card, i) => (
                    <Card
                        key={card.id || i}
                        index={i}
                        parentX={x}
                        onPick={() => onCardPick(i)}
                        config={config}
                        stepIndex={stepIndex}
                        isSelected={i === centerIndex}
                        totalCards={cards.length}
                    />
                ))}
            </motion.div>

            {/* Selection Indicator Overlay */}
            <div className="absolute bottom-10 md:bottom-20 pointer-events-none flex flex-col items-center gap-2">
                <div className="w-px h-12 bg-gradient-to-t from-white/40 via-white/10 to-transparent" />
                <div className="text-[10px] text-white/30 tracking-widest font-light">FOCUS</div>
            </div>
        </div>
    );
};

const Card = ({ index, parentX, onPick, config, stepIndex, isSelected, totalCards }: any) => {
    const tarotBackImages = [TarotBack1, TarotBack2, TarotBack3];
    const cardBack = tarotBackImages[stepIndex] || TarotBack1;

    // Mathematical arc and magnification calculations
    // Distance from center focus (0)
    const distance = useTransform(parentX, (val: number) => {
        const myX = index * config.spread;
        return Math.abs(myX + val);
    });

    // 1. Position: Arc math
    const xPos = index * config.spread;
    const y = useTransform(distance, [0, 600], [-80, 200]); // Lift center card

    // 2. Rotation: Fan math
    const rotate = useTransform(parentX, (val: number) => {
        const myX = index * config.spread;
        const delta = myX + val;
        return (delta / 100) * 12 * config.arcStrength;
    });

    // 3. Magnification: Scale up as it hits center
    const scale = useTransform(distance, [0, 200, 500], [1.3, 0.9, 0.75]);

    // 4. Visual depth: Z-Index and Effects
    const zIndex = useTransform(distance, [0, 500], [100, 0]);
    const brightness = useTransform(distance, [0, 300], [1.2, 0.6]);
    const blur = useTransform(distance, [0, 400], [0, 4]);

    // Entrance Animation Config
    const entranceDelay = (index * 0.05); // Staggered entry

    return (
        <motion.div
            initial={{ opacity: 0, scale: 0, y: 300, rotate: 0 }}
            animate={{
                opacity: 1,
                scale: 1,
                y: 0, // Reset to 0 so the 'style.y' (the fan arc) can take over
                transition: {
                    delay: entranceDelay,
                    duration: 0.8,
                    type: "spring",
                    stiffness: 100,
                    damping: 15
                }
            }}
            style={{
                x: xPos,
                y,
                rotate,
                scale,
                zIndex,
                filter: useTransform([brightness, blur], ([br, bl]: any) => `brightness(${br}) blur(${bl}px)`),
                position: 'absolute',
                transformOrigin: 'bottom center'
            }}
            whileHover={{
                zIndex: 110,
                scale: 1.25,
                y: -120, // More lift to see the card clearly
                transition: { duration: 0.2 }
            }}
            whileTap={{ scale: 1.15 }}
            onClick={onPick}
            className={`w-32 h-48 md:w-44 md:h-64 rounded-xl shadow-[0_10px_40px_rgba(0,0,0,0.5)] cursor-pointer group transition-shadow duration-500
                ${isSelected ? 'shadow-[0_0_50px_rgba(168,85,247,0.4)] ring-2 ring-purple-400/30' : ''}`}
        >
            <div className="w-full h-full relative rounded-xl overflow-hidden border border-white/10 bg-gray-900">
                <img
                    src={cardBack}
                    alt="Tarot Back"
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                />

                {/* Decorative Overlays */}
                <div className="absolute inset-0 bg-gradient-to-tr from-purple-500/10 via-transparent to-white/5 pointer-events-none" />
                <div className={`absolute inset-0 transition-opacity duration-300 ${isSelected ? 'opacity-10' : 'opacity-0'} bg-white pointer-events-none`} />

                {/* Edge Lighting */}
                <div className="absolute inset-0 border border-white/5 rounded-xl pointer-events-none" />
                <div className="absolute top-0 left-0 w-full h-1/2 bg-gradient-to-b from-white/10 to-transparent pointer-events-none" />
            </div>

            {/* Shadow decoration beneath card */}
            <motion.div
                className="absolute -bottom-8 left-1/2 -translate-x-1/2 w-4/5 h-4 bg-black/40 blur-xl rounded-full -z-10"
                style={{ opacity: useTransform(distance, [0, 300], [1, 0]) }}
            />
        </motion.div>
    );
};

export default DraggableFanDeck;
