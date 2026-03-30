import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronUp, ChevronDown } from 'lucide-react';
import { getGapjaInfo, type GapjaInfo } from '../../utils/gapja';

interface GapjaYearInputProps {
    onSelect: (year: string) => void;
    minYear?: number;
    maxYear?: number;
    initialYear?: number;
    onClose?: () => void;
}

const ITEM_HEIGHT = 60; // Height of each year item
const VISIBLE_ITEMS = 3; // Number of items visible at once
const CONTAINER_HEIGHT = ITEM_HEIGHT * VISIBLE_ITEMS; // 180px

const GapjaYearInput = ({
    onSelect,
    minYear = 1926,
    maxYear = 2026,
    initialYear = 1990,
    onClose
}: GapjaYearInputProps) => {

    const [selectedYear, setSelectedYear] = useState<number>(initialYear);
    const [gapjaInfo, setGapjaInfo] = useState<GapjaInfo | null>(null);
    const [confirming, setConfirming] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Direct Input State
    const [isEditing, setIsEditing] = useState(false);
    const [inputValue, setInputValue] = useState("");
    const inputRef = useRef<HTMLInputElement>(null);

    // Drag State
    const isDragging = useRef(false);
    const startY = useRef(0);
    const startScrollTop = useRef(0);
    const isDragClick = useRef(false);

    // Momentum State
    const velocity = useRef(0);
    const lastY = useRef(0);
    const lastTime = useRef(0);
    const momentumId = useRef<number | null>(null);

    const handleYearClick = (year: number) => {
        // Prevent click if it was a drag action
        if (isDragClick.current) return;

        if (year === selectedYear) {
            setIsEditing(true);
            setInputValue(year.toString());
            setTimeout(() => inputRef.current?.focus(), 0);
        } else {
            // Scroll to this item on click
            if (scrollRef.current) {
                // Ensure snap is enabled for click scroll
                scrollRef.current.style.scrollSnapType = 'y mandatory';
                scrollRef.current.scrollTo({
                    top: (year - minYear) * ITEM_HEIGHT,
                    behavior: 'smooth'
                });
            }
        }
    };

    const commitInput = () => {
        setIsEditing(false);
        const num = parseInt(inputValue, 10);
        if (!isNaN(num)) {
            const clamped = Math.max(minYear, Math.min(maxYear, num));
            // Scroll to the typed year
            if (scrollRef.current) {
                scrollRef.current.scrollTo({
                    top: (clamped - minYear) * ITEM_HEIGHT,
                    behavior: 'smooth'
                });
            }
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            commitInput();
        }
    };

    // Initial Scroll Position
    useEffect(() => {
        if (scrollRef.current) {
            const index = initialYear - minYear;
            scrollRef.current.scrollTop = index * ITEM_HEIGHT;
        }
        setGapjaInfo(getGapjaInfo(initialYear));
    }, [initialYear, minYear]);

    // Handle Scroll
    const handleScroll = () => {
        if (!scrollRef.current) return;

        const scrollTop = scrollRef.current.scrollTop;
        const index = Math.round(scrollTop / ITEM_HEIGHT);
        const year = Math.min(Math.max(minYear + index, minYear), maxYear);

        if (year !== selectedYear) {
            setSelectedYear(year);
            setGapjaInfo(getGapjaInfo(year));
        }
    };

    // Confirm Selection
    const handleConfirm = () => {
        setConfirming(true);
        setTimeout(() => {
            onSelect(selectedYear.toString());
        }, 800);
    };

    // Animal Name for Background
    const animalName = gapjaInfo ? {
        '쥐': 'rat', '소': 'ox', '호랑이': 'tiger', '토끼': 'rabbit',
        '용': 'dragon', '뱀': 'snake', '말': 'horse', '양': 'sheep',
        '원숭이': 'monkey', '닭': 'rooster', '개': 'dog', '돼지': 'pig'
    }[gapjaInfo.animal] || 'dragon' : 'dragon';

    // Generate Year List
    const years = Array.from({ length: maxYear - minYear + 1 }, (_, i) => minYear + i);

    const momentumLoop = () => {
        if (!scrollRef.current) return;

        // Apply velocity
        scrollRef.current.scrollTop -= velocity.current;

        // Friction
        velocity.current *= 0.95;

        // Stop if slow enough
        if (Math.abs(velocity.current) < 0.5) {
            if (momentumId.current) cancelAnimationFrame(momentumId.current);
            momentumId.current = null;
            // Re-enable snap to settle on an item
            scrollRef.current.style.scrollSnapType = 'y mandatory';
            return;
        }

        momentumId.current = requestAnimationFrame(momentumLoop);
    };

    return (
        <div className="relative w-full h-[600px] overflow-hidden select-none flex flex-col items-center justify-center">
            {/* 1. Background Image */}
            <motion.div
                className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[0] pointer-events-none flex items-center justify-center"
                style={{ width: '700px', height: '700px' }}
            >
                <div
                    style={{
                        width: '100%',
                        height: '100%',
                        backgroundImage: `url(/zodiac/${animalName}.png)`,
                        backgroundRepeat: 'no-repeat',
                        backgroundPosition: 'center',
                        backgroundSize: 'contain',
                        transition: 'background-image 0.5s ease-in-out' // Simple CSS transition
                    }}
                    className="opacity-40 blur-[1px] saturate-50"
                />
            </motion.div>

            {/* Close Button - 콘텐츠 영역 우상단 */}
            {onClose && (
                <button
                    onClick={onClose}
                    className="absolute top-12 right-[calc(50%-200px)] z-40 w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 border border-white/20 text-white/60 hover:text-white backdrop-blur-md transition-all flex items-center justify-center"
                >
                    <X size={20} />
                </button>
            )}



            {/* 2. Scroll List Container */}
            <div className="relative z-20 w-80 flex flex-col items-center">

                {/* Up Arrow */}
                <button
                    onClick={() => {
                        if (scrollRef.current) {
                            scrollRef.current.style.scrollSnapType = 'y mandatory';
                            scrollRef.current.scrollTo({
                                top: scrollRef.current.scrollTop - ITEM_HEIGHT,
                                behavior: 'smooth'
                            });
                        }
                    }}
                    className="text-white/40 hover:text-white/80 transition-colors mb-2"
                >
                    <ChevronUp size={28} />
                </button>

                {/* Selection Highlight Box - REMOVED */}


                {/* Scrollable Area */}
                <div
                    ref={scrollRef}
                    onScroll={handleScroll}
                    onMouseDown={(e) => {
                        if (isEditing) return;

                        // Stop any running momentum
                        if (momentumId.current) {
                            cancelAnimationFrame(momentumId.current);
                            momentumId.current = null;
                        }

                        isDragging.current = true;
                        isDragClick.current = false;

                        // Disable snap for direct tracking
                        if (scrollRef.current) {
                            scrollRef.current.style.scrollSnapType = 'none';
                            startScrollTop.current = scrollRef.current.scrollTop;
                        }

                        startY.current = e.pageY;
                        lastY.current = e.pageY;
                        lastTime.current = performance.now();
                        velocity.current = 0;
                    }}
                    onMouseMove={(e) => {
                        if (!isDragging.current || !scrollRef.current) return;
                        e.preventDefault();
                        const y = e.pageY;
                        const now = performance.now();

                        // Calculate delta
                        const deltaY = y - lastY.current;
                        const deltaTime = now - lastTime.current;

                        if (deltaTime > 0) {
                            // Instant velocity
                            velocity.current = deltaY * 1.5;
                        }

                        // Scroll Move
                        const walk = (y - startY.current) * 1.5;
                        scrollRef.current.scrollTop = startScrollTop.current - walk;

                        // Update trackers
                        lastY.current = y;
                        lastTime.current = now;

                        // Drag Click Check
                        if (Math.abs(y - startY.current) > 5) {
                            isDragClick.current = true;
                        }
                    }}
                    onMouseUp={() => {
                        isDragging.current = false;
                        momentumLoop();
                    }}
                    onMouseLeave={() => {
                        if (isDragging.current) {
                            isDragging.current = false;
                            momentumLoop();
                        }
                    }}
                    className="w-full overflow-y-auto no-scrollbar snap-y snap-mandatory touch-pan-y cursor-grab active:cursor-grabbing"
                    style={{
                        height: `${CONTAINER_HEIGHT}px`
                        // Removed scroll-behavior: smooth to prevent conflict with user scroll
                    }}
                >
                    {/* Padding to center first/last items */}
                    <div style={{ height: (CONTAINER_HEIGHT - ITEM_HEIGHT) / 2 }} />

                    {years.map((year) => (
                        <div
                            key={year}
                            className="w-full flex items-center justify-center snap-center transition-all duration-200"
                            style={{ height: `${ITEM_HEIGHT}px` }}
                            onClick={() => handleYearClick(year)}
                        >
                            {isEditing && year === selectedYear ? (
                                <input
                                    ref={inputRef}
                                    type="number"
                                    value={inputValue}
                                    onChange={(e) => setInputValue(e.target.value)}
                                    onBlur={commitInput}
                                    onKeyDown={handleKeyDown}
                                    className="w-32 bg-transparent text-5xl font-serif font-bold text-white text-center outline-none drop-shadow-lg [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                                />
                            ) : (
                                <>
                                    <span
                                        className={`font-serif font-bold transition-all duration-300 ${year === selectedYear
                                            ? 'text-5xl text-white drop-shadow-lg scale-110'
                                            : 'text-3xl text-white/30 scale-90'
                                            }`}
                                    >
                                        {year}
                                    </span>

                                </>
                            )}
                        </div>
                    ))}

                    <div style={{ height: (CONTAINER_HEIGHT - ITEM_HEIGHT) / 2 }} />
                </div>

                {/* Down Arrow */}
                <button
                    onClick={() => {
                        if (scrollRef.current) {
                            scrollRef.current.style.scrollSnapType = 'y mandatory';
                            scrollRef.current.scrollTo({
                                top: scrollRef.current.scrollTop + ITEM_HEIGHT,
                                behavior: 'smooth'
                            });
                        }
                    }}
                    className="text-white/40 hover:text-white/80 transition-colors mt-2"
                >
                    <ChevronDown size={28} />
                </button>
            </div>

            {/* 3. Bottom Info & Confirm */}
            <div className="absolute bottom-12 z-30 text-center w-full flex flex-col items-center gap-6">

                {/* Gapja Info Display */}
                <AnimatePresence mode='wait'>
                    {gapjaInfo && (
                        <motion.div
                            key={gapjaInfo.year} // Animate when info changes
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -10 }}
                            transition={{ duration: 0.2 }}
                            className="flex flex-col items-center gap-2"
                        >
                            <h3 className={`text-4xl font-serif font-bold ${gapjaInfo.element.hex} drop-shadow-md`}>
                                {gapjaInfo.korGanji} <span className="text-2xl opacity-80">({gapjaInfo.hanjaGanji})</span>
                            </h3>
                        </motion.div>
                    )}
                </AnimatePresence>

                <button
                    onClick={handleConfirm}
                    className="px-12 py-4 bg-white/10 hover:bg-white/20 border border-white/30 rounded-full text-white font-serif text-xl tracking-widest backdrop-blur-md shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_40px_rgba(255,255,255,0.3)] hover:scale-105 active:scale-95 transition-all"
                >
                    확인
                </button>
            </div>

            {/* Helper Text */}
            <motion.div
                className="absolute top-10 pointer-events-none z-20"
                animate={{ opacity: confirming ? 0 : 0.6 }}
            >
                <p className="text-white/50 text-sm font-['Gowun_Batang']">
                    스크롤 & 드래그 혹은 직접 입력하세요
                </p>
            </motion.div>

        </div>
    );
};

export default GapjaYearInput;
