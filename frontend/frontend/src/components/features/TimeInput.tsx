import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, HelpCircle, ChevronUp, ChevronDown } from 'lucide-react';

interface TimeInputProps {
    onSelect: (hour: string, minute: string, period: 'AM' | 'PM' | '') => void;
    onUnknown?: () => void;
    initialHour?: number;
    onClose?: () => void;
}

const ITEM_HEIGHT = 60;
const VISIBLE_ITEMS = 3;
const CONTAINER_HEIGHT = ITEM_HEIGHT * VISIBLE_ITEMS;

const TimeInput = ({ onSelect, onUnknown, onClose, initialHour = 12 }: TimeInputProps) => {
    // State
    const [selectedHour, setSelectedHour] = useState<number>(initialHour);
    const [isMoluHovered, setIsMoluHovered] = useState(false);

    // Refs for Scroll & Drag
    const scrollRef = useRef<HTMLDivElement>(null);
    const isDragging = useRef(false);
    const startScrollTop = useRef(0);
    const startY = useRef(0);
    const lastY = useRef(0);
    const lastTime = useRef(0);
    const velocity = useRef(0);
    const momentumId = useRef<number | null>(null);
    const isDragClick = useRef(false);

    // Initial Scroll Position
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = selectedHour * ITEM_HEIGHT;
        }
    }, []);

    // Handle Scroll
    const handleScroll = () => {
        if (!scrollRef.current) return;
        const index = Math.round(scrollRef.current.scrollTop / ITEM_HEIGHT);
        const hour = Math.min(Math.max(index, 0), 23); // 0 to 23
        if (hour !== selectedHour) {
            setSelectedHour(hour);
        }
    };

    // Momentum Loop
    const momentumLoop = () => {
        if (!scrollRef.current) return;
        scrollRef.current.scrollTop -= velocity.current;
        velocity.current *= 0.95; // Friction

        if (Math.abs(velocity.current) < 0.5) {
            if (momentumId.current) cancelAnimationFrame(momentumId.current);
            momentumId.current = null;
            scrollRef.current.style.scrollSnapType = 'y mandatory';
            return;
        }
        momentumId.current = requestAnimationFrame(momentumLoop);
    };

    // Confirm Selection
    const handleConfirm = () => {
        onSelect(selectedHour.toString(), '00', '');
    };

    const hours = Array.from({ length: 24 }, (_, i) => i);

    return (
        <div className="relative w-full h-[600px] overflow-hidden select-none flex flex-col items-center justify-center bg-transparent">

            {/* Title */}
            <div className="absolute top-12 md:top-24 z-30 text-center">
                <h2 className="text-3xl font-serif text-white/90 drop-shadow-lg tracking-widest font-bold">생시 입력</h2>

            </div>

            {/* Close Button - 콘텐츠 영역 우상단 */}
            {onClose && (
                <button
                    onClick={onClose}
                    className="absolute top-12 right-[calc(50%-120px)] z-40 w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 border border-white/20 text-white/60 hover:text-white backdrop-blur-md transition-all flex items-center justify-center"
                >
                    <X size={20} />
                </button>
            )}

            {/* Scroll Container */}
            <div className="relative z-20 flex flex-col items-center gap-2 mb-8">

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
                    className="text-white/40 hover:text-white/80 transition-colors"
                >
                    <ChevronUp size={24} />
                </button>

                <div className="relative w-40 h-[180px]">

                    {/* Selection Indicator (Optional - Subtle) */}
                    {/* <div className="absolute top-1/2 left-0 w-full h-[60px] -translate-y-1/2 border-y border-white/10 bg-white/5 pointer-events-none rounded-lg" /> */}

                    <div
                        ref={scrollRef}
                        onScroll={handleScroll}
                        className="w-full h-full overflow-y-auto no-scrollbar snap-y snap-mandatory touch-pan-y cursor-grab active:cursor-grabbing"
                        // Mouse Events
                        onMouseDown={(e) => {
                            if (momentumId.current) { cancelAnimationFrame(momentumId.current); momentumId.current = null; }
                            isDragging.current = true;
                            isDragClick.current = false;
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
                            const deltaY = y - lastY.current;
                            const deltaTime = now - lastTime.current;
                            if (deltaTime > 0) velocity.current = deltaY * 1.5;
                            const walk = (y - startY.current) * 1.5;
                            scrollRef.current.scrollTop = startScrollTop.current - walk;
                            lastY.current = y;
                            lastTime.current = now;
                            if (Math.abs(y - startY.current) > 5) isDragClick.current = true;
                        }}
                        onMouseUp={() => { isDragging.current = false; momentumLoop(); }}
                        onMouseLeave={() => { if (isDragging.current) { isDragging.current = false; momentumLoop(); } }}
                    >
                        <div style={{ height: (CONTAINER_HEIGHT - ITEM_HEIGHT) / 2 }} />
                        {hours.map(h => (
                            <div key={h} className="w-full h-[60px] flex items-center justify-center snap-center" onClick={() => {
                                if (!isDragClick.current && scrollRef.current) {
                                    scrollRef.current.style.scrollSnapType = 'y mandatory';
                                    scrollRef.current.scrollTo({ top: h * ITEM_HEIGHT, behavior: 'smooth' });
                                }
                            }}>
                                <span className={`font-serif font-bold transition-all duration-300 ${h === selectedHour ? 'text-5xl text-white drop-shadow-lg scale-110' : 'text-3xl text-white/30 scale-90'}`}>
                                    {h}
                                </span>
                            </div>
                        ))}
                        <div style={{ height: (CONTAINER_HEIGHT - ITEM_HEIGHT) / 2 }} />
                    </div>
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
                    className="text-white/40 hover:text-white/80 transition-colors"
                >
                    <ChevronDown size={24} />
                </button>
            </div>

            {/* Bottom Actions - 세로 배치 */}
            <div className="absolute bottom-8 z-30 flex flex-col items-center gap-4">
                {/* Unknown Time Button - 확인 버튼 위에 */}
                <div className="relative">
                    <button
                        onMouseEnter={() => setIsMoluHovered(true)}
                        onMouseLeave={() => setIsMoluHovered(false)}
                        onClick={onUnknown}
                        className="w-14 h-14 rounded-full bg-white/5 hover:bg-white/10 border border-white/20 text-white/60 hover:text-white backdrop-blur-md transition-all flex items-center justify-center relative shadow-lg"
                        title="모르겠어요"
                    >
                        <HelpCircle size={24} />
                    </button>
                    <AnimatePresence>
                        {isMoluHovered && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.8, x: 10 }}
                                animate={{ opacity: 1, scale: 1, x: 0 }}
                                exit={{ opacity: 0, scale: 0.8, x: 10 }}
                                className="absolute left-full top-1/2 -translate-y-1/2 ml-3 bg-black/80 px-3 py-1.5 rounded-lg whitespace-nowrap border border-white/10 backdrop-blur-md pointer-events-none"
                            >
                                <span className="text-xs text-white/80 font-['Gowun_Batang']">시간을 몰라요</span>
                                <div className="absolute -left-1 top-1/2 -translate-y-1/2 w-2 h-2 bg-black/80 rotate-45 border-l border-b border-white/10"></div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* 확인 버튼 */}
                <button
                    onClick={handleConfirm}
                    className="px-12 py-4 bg-white/10 hover:bg-white/20 border border-white/30 rounded-full text-white font-serif text-xl tracking-widest backdrop-blur-md shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_40px_rgba(255,255,255,0.3)] hover:scale-105 active:scale-95 transition-all"
                >
                    확인
                </button>
            </div>

            <motion.div
                className="absolute top-[65%] pointer-events-none"
                initial={{ opacity: 0 }}
                animate={{ opacity: 0.4 }}
            >

            </motion.div>

        </div>
    );
};

export default TimeInput;
