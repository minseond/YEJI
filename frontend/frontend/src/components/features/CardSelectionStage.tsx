import { useState, useEffect } from 'react';
import { useSound } from '../../hooks/useSound';
import { motion, AnimatePresence } from 'framer-motion';
import { MousePointer2, Sparkles, ChevronLeft, ChevronRight } from 'lucide-react';
import obangBack from '../../assets/obang_card/obang_back.jpg';
import tarotBack from '../../assets/타로카드/tarot_back2.png';

type GameType = 'tarot' | 'obang' | null;

interface CardSelectionStageProps {
    onClick: () => void;
    selectedGame?: GameType;
    onZoom?: (zooming: boolean) => void;
}

const CardSelectionStage = ({ onClick, selectedGame = 'obang', onZoom }: CardSelectionStageProps) => {
    // Shared state
    const [isFlipping, setIsFlipping] = useState(false);
    const [selectedIndex, setSelectedIndex] = useState<number | null>(null);
    const [isShuffling, setIsShuffling] = useState(false);
    // Carousel State for Obang
    const [focusedIndex, setFocusedIndex] = useState(4); // 10장 기준 중앙값(0~9)

    // Tarot specific state
    const [selectedCardId, setSelectedCardId] = useState<number | null>(null);
    const [shufflePhase, setShufflePhase] = useState<'spread' | 'stack' | 'chaos'>('spread');
    const { play } = useSound();

    const isObang = selectedGame === 'obang';

    const getInstructionText = () => {
        if (isObang) return { title: "오방신점", sub: "" };
        else return { title: "신비의 타로", sub: "당신의 운명을 이끌 카드를 선택하세요" };
    };

    const instruction = getInstructionText();

    // Obang Handler
    const handleObangClick = (index: number) => {
        if (isFlipping) return;

        setSelectedIndex(index);
        setIsFlipping(true);

        setTimeout(() => {
            onClick();
        }, 1200);
    };


    // State for visible cards (subset)
    const [visibleCards, setVisibleCards] = useState<number[]>([]);

    // Initialize or Shuffle Cards
    const shuffleCards = () => {
        if (isShuffling) return;

        setIsShuffling(true);
        // Phase 1: Chaos - Explosion (1.5s)
        setShufflePhase('chaos');

        setTimeout(() => {
            // Phase 2: Stack - Gather to center (0.8s)
            setShufflePhase('stack');

            // Regenerate cards while stacked (hidden)
            const newCards = new Set<number>();
            while (newCards.size < 22) { // Increased to 22 for fuller look
                newCards.add(Math.floor(Math.random() * 78));
            }
            setVisibleCards(Array.from(newCards));

            setTimeout(() => {
                // Phase 3: Spread - Fan out
                setShufflePhase('spread');

                setTimeout(() => {
                    setIsShuffling(false);
                }, 800);
            }, 800);
        }, 1500);
    };

    // Initial load
    useEffect(() => {
        if (!isObang) { // Only shuffle for Tarot
            play('VOICE', 'STELLA', { subKey: 'SELECTION_INTRO' });
            shuffleCards();
        }
    }, [isObang, play]);

    // Tarot Handlers
    const [isSelecting, setIsSelecting] = useState(false); // Track selection phase
    const [hoveredIndex, setHoveredIndex] = useState<number | null>(null); // Track hovered card for accordion effect

    const handleTarotClick = (cardId: number) => {
        if (isFlipping || isShuffling || isSelecting) return;

        setSelectedCardId(cardId);
        setIsFlipping(true);
        setIsSelecting(true); // Start flashy sequence
        onZoom?.(true); // Trigger parent overflow unlock

        // Wait for animation then proceed
        setTimeout(() => {
            onClick();
            onZoom?.(false); // Reset (though component unmounts usually)
        }, 2500); // Extended for effect
    };

    // Magical Burst Particles
    const MagicalParticles = ({ active }: { active: boolean }) => {
        if (!active) return null;
        return (
            <div className="absolute inset-0 pointer-events-none z-[9998] flex items-center justify-center">
                {[...Array(30)].map((_, i) => (
                    <motion.div
                        key={i}
                        className="absolute w-2 h-2 bg-yellow-200 rounded-full shadow-[0_0_10px_rgba(255,255,0,0.8)]"
                        initial={{ scale: 0, opacity: 1, x: 0, y: 0 }}
                        animate={{
                            scale: [0, 1.5, 0],
                            opacity: [1, 1, 0],
                            x: (Math.random() - 0.5) * 600,
                            y: (Math.random() - 0.5) * 600,
                            rotate: Math.random() * 360,
                        }}
                        transition={{
                            duration: 1.5,
                            ease: "easeOut",
                            delay: 0.2
                        }}
                    />
                ))}
                {/* Ring Shockwave */}
                <motion.div
                    className="absolute w-64 h-64 border-4 border-purple-400 rounded-full opacity-0"
                    initial={{ scale: 0.1, opacity: 0.8 }}
                    animate={{ scale: 4, opacity: 0, borderWidth: 0 }}
                    transition={{ duration: 1.2, ease: "easeOut" }}
                />
            </div>
        );
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className={`flex flex-col items-center gap-4 w-full h-full justify-center pointer-events-auto relative ${isSelecting ? "overflow-visible" : "overflow-hidden"} ${isObang ? "font-['Hahmlet']" : "font-gmarket"}`}
        >
            {/* Background Particles for Tarot */}
            {!isObang && (
                <div className="absolute inset-0 pointer-events-none overflow-hidden">
                    {[...Array(20)].map((_, i) => (
                        <motion.div
                            key={i}
                            className="absolute w-1 h-1 bg-purple-400 rounded-full blur-[1px]"
                            initial={{ x: Math.random() * window.innerWidth, y: Math.random() * window.innerHeight, opacity: 0 }}
                            animate={{ y: [null, Math.random() * -100], opacity: [0, 1, 0] }}
                            transition={{ duration: Math.random() * 5 + 3, repeat: Infinity, ease: "linear" }}
                        />
                    ))}
                </div>
            )}

            <MagicalParticles active={isSelecting} />

            <motion.div
                initial={{ y: -50, opacity: 0 }}
                animate={{
                    y: isSelecting || isFlipping ? -200 : 0,
                    opacity: isSelecting || isFlipping ? 0 : 1
                }}
                exit={{ y: -50, opacity: 0 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="text-center space-y-4 relative z-20 mt-12 md:mt-16"
            >
                <h2 className={`text-5xl md:text-7xl font-bold text-white drop-shadow-[0_0_25px_rgba(255,255,255,0.6)] ${isObang ? "font-['Hahmlet']" : "font-gmarket tracking-tighter"}`}>
                    {instruction.title}
                </h2>
                <p className={`text-xl md:text-2xl text-white/70 font-light tracking-widest ${isObang ? "font-['Hahmlet']" : "font-gmarket"}`}>
                    {instruction.sub}
                </p>

                {/* Instruction Moved Here for Tarot */}
                {!isObang && !isFlipping && (
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                        className="flex items-center justify-center gap-2 text-white/50 text-sm font-gmarket bg-black/40 px-6 py-2 rounded-full backdrop-blur-md border border-white/5 shadow-xl mx-auto w-fit mt-4"
                    >
                        <MousePointer2 size={14} className="animate-bounce" />
                        <span>카드를 훑어보고 직감이 이끄는 한 장을 선택하세요</span>
                    </motion.div>
                )}
            </motion.div>

            {/* Content Area */}
            <div className="relative w-full flex-1 flex items-center justify-center perspective-1000 overflow-visible">

                {isObang ? (
                    /* OBANG FAN LAYOUT (Existing) */
                    /* OBANG CAROUSEL LAYOUT - SOPHISTICATED 3D COVER FLOW */
                    <div className="relative w-full h-full flex items-center justify-center -mt-16">
                        <div className="relative w-full max-w-6xl h-[600px] flex items-center justify-center perspective-[1200px]">
                            {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map((index) => {
                                // Calculate offset with wrapping support, although logical indices are linear here.
                                // We want the focused card to be center.
                                const offset = index - focusedIndex;
                                const isActive = offset === 0;
                                const isFar = Math.abs(offset) >= 2;

                                // 3D Transform Logic
                                let x = offset * 180; // 컴팩트한 간격으로 조정
                                let z = Math.abs(offset) * -200; // Deep depth push
                                let y = isActive ? 0 : 30; // Initialize y
                                let rotateY = offset * -25; // Rotate inward (Cover flow style)

                                // Scale & Opacity
                                let scale = isActive ? 1.1 : 0.9;
                                let opacity = isActive ? 1 : isFar ? 0.3 : 0.7;
                                let brightness = isActive ? 1 : 0.5; // Dim side cards

                                // Selection Override
                                const isSelected = selectedIndex === index;
                                if (isFlipping) {
                                    if (isSelected) {
                                        x = 0;
                                        z = 100; // Popping out less to avoid clipping
                                        y = -20; // Move up slightly to center
                                        scale = 1.1; // Reduced from 1.3
                                        opacity = 1;
                                        rotateY = 180; // Flip
                                        brightness = 1.2;
                                    } else {
                                        opacity = 0;
                                        scale = 0;
                                    }
                                }

                                return (
                                    <motion.div
                                        key={index}
                                        className="absolute cursor-pointer transform-style-3d"
                                        initial={{ opacity: 0, y: 100 }}
                                        animate={{
                                            x,
                                            z,
                                            y, // Slight sink for side cards or lift for selected card
                                            rotateY,
                                            scale,
                                            opacity: isFlipping && !isSelected ? 0 : opacity,
                                            filter: `brightness(${brightness})`,
                                            zIndex: isActive ? 50 : 50 - Math.abs(offset)
                                        }}
                                        transition={{
                                            type: "spring",
                                            stiffness: 200,
                                            damping: 25,
                                            mass: 0.8
                                        }}
                                        onClick={() => {
                                            if (isActive) handleObangClick(index);
                                            else setFocusedIndex(index);
                                        }}
                                        whileHover={isActive && !isFlipping ? { scale: 1.15, filter: "brightness(1.1)" } : {}}
                                    >
                                        <div className="relative w-[220px] h-[360px] transform-style-3d group">
                                            {/* Card Container */}
                                            <div className="absolute inset-0 rounded-[20px] overflow-hidden shadow-[0_20px_50px_rgba(0,0,0,0.5)] border border-amber-500/30 bg-[#1a1a1a]">
                                                {/* Image Tag for Clarity */}
                                                <img
                                                    src={obangBack}
                                                    alt="Obang Card"
                                                    className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity"
                                                />

                                                {/* Texture Overlay */}
                                                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-white/10 mix-blend-overlay" />

                                                {/* Border Shine */}
                                                <div className="absolute inset-0 rounded-[20px] border border-white/10" />
                                            </div>

                                            {/* Glow Overlay when Active */}
                                            {isActive && !isFlipping && (
                                                <div className="absolute inset-0 -z-10 rounded-[20px] bg-amber-500/20 blur-xl animate-pulse" />
                                            )}

                                            {/* Reflection Effect */}
                                            {!isFlipping && (
                                                <div
                                                    className="absolute top-full left-0 right-0 h-[140px] origin-top transform rotate-180 opacity-40 pointer-events-none"
                                                    style={{ maskImage: "linear-gradient(transparent, black)" }} // Fade out implementation
                                                >
                                                    {/* Use a simple gradient or duplicate image for reflection.
                                                         Duplicate image is expensive, let's use a blurred gradient shape that matches the card color. */}
                                                    <div className="w-full h-full bg-gradient-to-b from-amber-900/50 to-transparent blur-md transform scale-x-90" />
                                                </div>
                                            )}
                                        </div>
                                    </motion.div>
                                );
                            })}
                        </div>

                        {/* Navigation Buttons (Only visible when not flipping) */}
                        {!isFlipping && (
                            <>
                                <button
                                    className={`absolute left-4 md:left-20 p-4 rounded-full bg-black/20 hover:bg-black/40 text-white/70 hover:text-white transition-all backdrop-blur-sm border border-white/10 ${focusedIndex === 0 ? "opacity-30 cursor-default" : "opacity-100"}`}
                                    onClick={() => setFocusedIndex(prev => Math.max(0, prev - 1))}
                                    disabled={focusedIndex === 0}
                                >
                                    <ChevronLeft size={32} />
                                </button>
                                <button
                                    className={`absolute right-4 md:right-20 p-4 rounded-full bg-black/20 hover:bg-black/40 text-white/70 hover:text-white transition-all backdrop-blur-sm border border-white/10 ${focusedIndex === 9 ? "opacity-30 cursor-default" : "opacity-100"}`}
                                    onClick={() => setFocusedIndex(prev => Math.min(9, prev + 1))}
                                    disabled={focusedIndex === 9}
                                >
                                    <ChevronRight size={32} />
                                </button>
                            </>
                        )}

                        {/* Instruction Hint */}
                        {!isFlipping && (
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: 1 }}
                                className="absolute bottom-8 text-white text-lg tracking-widest font-medium animate-pulse"
                            >
                                카드를 넘겨 마음에 드는 운명을 선택하세요
                            </motion.div>
                        )}
                    </div>
                ) : (
                    /* TAROT FAN/OVERLAP LAYOUT (Static & Elegant) */
                    <div className="w-full h-full flex flex-col items-center justify-center relative overflow-hidden">

                        {/* Fan Container */}
                        <div className="w-full h-full flex items-center justify-center perspective-1000 -translate-y-8 md:-translate-y-12">
                            <motion.div
                                className="flex items-center justify-center h-[320px] md:h-[400px] w-[90%] md:w-[80%]"
                                initial={{ opacity: 0 }}
                                animate={isFlipping ? { opacity: 0, scale: 0.95 } : { opacity: 1, scale: 1 }}
                                transition={{ duration: 0.4 }}
                            >
                                {visibleCards.map((cardId, i) => {
                                    const isSelected = selectedCardId === cardId;
                                    // Calculate rotation for fan effect
                                    const total = visibleCards.length;
                                    const center = (total - 1) / 2;

                                    // Smooth Arch Calculation
                                    const rotate = (i - center) * 2.5; // Stronger arc rotation
                                    const yOffset = Math.pow(Math.abs(i - center), 1.8) * 1.5; // Parabolic curve for y

                                    // Accordion Effect Calculation
                                    let hoverOffsetX = 0;
                                    let hoverScale = 1;

                                    if (hoveredIndex !== null && !isFlipping && !isShuffling && !isSelecting) {
                                        const dist = i - hoveredIndex;
                                        if (dist < 0) hoverOffsetX = -40; // Push left neighbors further left
                                        if (dist > 0) hoverOffsetX = 40;  // Push right neighbors further right
                                        if (dist === 0) hoverScale = 1.3; // Scale up hovered card

                                        // Ripple effect strength based on distance
                                        if (Math.abs(dist) === 1) hoverOffsetX = hoverOffsetX * 0.6;
                                    }

                                    // Random values for chaos shuffle
                                    const randX = (Math.random() - 0.5) * 800; // -400 to 400
                                    const randY = (Math.random() - 0.5) * 600; // -300 to 300
                                    const randZ = (Math.random() - 0.5) * 500; // -250 to 250
                                    const randRotate = (Math.random() - 0.5) * 720; // 2 full spins

                                    return (
                                        <motion.div
                                            key={`${cardId}-${i}`}
                                            className="relative flex-shrink-0 w-24 md:w-32 aspect-[3/5] cursor-pointer group"
                                            // Negative margin for overlap
                                            style={{
                                                marginLeft: i === 0 ? 0 : '-60px',
                                                zIndex: hoveredIndex === i ? 100 : i // Bring hovered to front
                                            }}
                                            onHoverStart={() => setHoveredIndex(i)}
                                            onHoverEnd={() => setHoveredIndex(null)}
                                            onClick={() => handleTarotClick(cardId)}

                                            initial={{ x: 0, y: 0, opacity: 0, rotate: 0, scale: 0.8 }}
                                            animate={isSelected ? {
                                                x: (center - i) * 30, // Keep in center X
                                                y: 0,
                                                scale: 1.5, // Reduced for now, will handle massiveness in selection phase
                                                rotate: 0,
                                                zIndex: 9999, // Max Z-Index
                                                opacity: 1,
                                            } : isShuffling ? (
                                                shufflePhase === 'chaos' ? {
                                                    x: randX,
                                                    y: randY,
                                                    z: randZ,
                                                    rotate: randRotate,
                                                    rotateX: Math.random() * 360,
                                                    rotateY: Math.random() * 360,
                                                    scale: 0.7,
                                                    opacity: 1,
                                                    transition: { duration: 1.5, ease: "easeInOut" }
                                                } : { // Stack phase
                                                    x: (i % 2 === 0 ? 5 : -5),
                                                    y: (i % 3 === 0 ? 3 : -3),
                                                    z: 0,
                                                    opacity: 1,
                                                    scale: 0.9,
                                                    rotate: (i % 4 === 0 ? 2 : -2),
                                                    rotateX: 0,
                                                    rotateY: 0,
                                                    zIndex: 10,
                                                    transition: { duration: 0.8, type: "spring", bounce: 0.4 }
                                                }
                                            ) : {
                                                x: hoverOffsetX, // Accordion X
                                                y: yOffset + (isSelecting ? 500 : 0) + (hoveredIndex === i ? -40 : 0), // Arch Y + Hover Lift
                                                opacity: isSelecting ? 0 : 1,
                                                scale: isSelecting ? 0.5 : hoverScale,
                                                rotate: rotate,
                                                rotateX: 0,
                                                rotateY: 0,
                                                zIndex: hoveredIndex === i ? 100 : i
                                            }}
                                        >
                                            {/* Portal Effect */}
                                            {isSelected && isSelecting && (
                                                <div className="absolute inset-0 flex items-center justify-center pointer-events-none -z-10">
                                                    {/* Void Hole */}
                                                    <motion.div
                                                        initial={{ opacity: 0, scale: 0 }}
                                                        animate={{ opacity: 1, scale: 4 }}
                                                        transition={{ duration: 1.5, ease: "easeIn" }}
                                                        className="absolute w-full h-full bg-black rounded-lg shadow-[0_0_100px_50px_rgba(0,0,0,1)]"
                                                    />
                                                </div>
                                            )}

                                            {/* Card Back */}
                                            <div
                                                className="absolute inset-0 rounded-lg bg-[#1a1a2e] border border-purple-500/30 shadow-xl group-hover:shadow-purple-500/50 transition-shadow duration-300 overflow-hidden"
                                                style={{
                                                    backgroundImage: `url(${tarotBack})`,
                                                    backgroundSize: 'cover',
                                                    backgroundPosition: 'center',
                                                    backfaceVisibility: 'hidden'
                                                }}
                                            >
                                                {/* Hover Overlay */}
                                                <div className="absolute inset-0 bg-white/0 group-hover:bg-white/10 transition-colors duration-200" />
                                                <div className="absolute inset-0 border border-white/10 group-hover:border-purple-300/50 rounded-lg transition-colors duration-300" />
                                            </div>
                                        </motion.div>
                                    );
                                })}
                            </motion.div>
                        </div>

                        {/* Shuffle Button Only */}
                        {!isFlipping && (
                            <div className="absolute bottom-6 md:bottom-10 flex flex-col items-center gap-4 z-20 pointer-events-none w-full">
                                <motion.button
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={shuffleCards}
                                    disabled={isShuffling}
                                    className={`pointer-events-auto px-8 py-3 bg-gradient-to-r from-purple-900/80 to-indigo-900/80 hover:from-purple-800 hover:to-indigo-800 border border-purple-500/30 rounded-full backdrop-blur-md text-purple-100 font-gmarket text-sm flex items-center gap-2 transition-all shadow-lg hover:shadow-purple-500/20 ${isShuffling ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
                                >
                                    <Sparkles size={16} className={isShuffling ? "animate-spin" : ""} />
                                    <span>{isShuffling ? "섞는 중..." : "덱 섞기"}</span>
                                </motion.button>
                            </div>
                        )}
                    </div>
                )}
            </div>



            <AnimatePresence>
                {isSelecting && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 1.5 }}
                        className="absolute inset-0 bg-black/80 z-[9995] pointer-events-none"
                    />
                )}
            </AnimatePresence>

            {/* White Flash Overlay for Transition */}
            <AnimatePresence>
                {isSelecting && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 1.0, delay: 0.5 }}
                        className="absolute inset-0 bg-black z-[9999] pointer-events-none rounded-3xl"
                    />
                )}
            </AnimatePresence>
        </motion.div >
    );
};

export default CardSelectionStage;
