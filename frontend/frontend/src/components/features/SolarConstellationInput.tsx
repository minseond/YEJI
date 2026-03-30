import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { X, ChevronUp, ChevronDown } from 'lucide-react';
import ConstellationViewer from './ConstellationViewer';

interface SolarConstellationInputProps {
    onSelect: (month: string, day: string) => void;
    initialMonth?: number;
    initialDay?: number;
    year?: number;
    onClose?: () => void;
}

const ZODIAC_SIGNS = [
    { name: 'Capricorn', kor: '염소자리', start: { m: 12, d: 22 }, end: { m: 1, d: 19 } },
    { name: 'Aquarius', kor: '물병자리', start: { m: 1, d: 20 }, end: { m: 2, d: 18 } },
    { name: 'Pisces', kor: '물고기자리', start: { m: 2, d: 19 }, end: { m: 3, d: 20 } },
    { name: 'Aries', kor: '양자리', start: { m: 3, d: 21 }, end: { m: 4, d: 19 } },
    { name: 'Taurus', kor: '황소자리', start: { m: 4, d: 20 }, end: { m: 5, d: 20 } },
    { name: 'Gemini', kor: '쌍둥이자리', start: { m: 5, d: 21 }, end: { m: 6, d: 21 } },
    { name: 'Cancer', kor: '게자리', start: { m: 6, d: 22 }, end: { m: 7, d: 22 } },
    { name: 'Leo', kor: '사자자리', start: { m: 7, d: 23 }, end: { m: 8, d: 22 } },
    { name: 'Virgo', kor: '처녀자리', start: { m: 8, d: 23 }, end: { m: 9, d: 22 } },
    { name: 'Libra', kor: '천칭자리', start: { m: 9, d: 23 }, end: { m: 10, d: 23 } },
    { name: 'Scorpio', kor: '전갈자리', start: { m: 10, d: 24 }, end: { m: 11, d: 22 } },
    { name: 'Sagittarius', kor: '사수자리', start: { m: 11, d: 23 }, end: { m: 12, d: 21 } },
];

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

const getZodiac = (m: number, d: number) => {
    if ((m === 12 && d >= 22) || (m === 1 && d <= 19)) {
        return ZODIAC_SIGNS[0]; // Capricorn
    }
    return ZODIAC_SIGNS.find(z => {
        if (z.name === 'Capricorn') return false;
        if (m === z.start.m && d >= z.start.d) return true;
        if (m === z.end.m && d <= z.end.d) return true;
        return false;
    }) || ZODIAC_SIGNS[1];
};

const getBirthstone = (m: number) => BIRTHSTONES.find(b => b.month === m) || BIRTHSTONES[0];

const ITEM_HEIGHT = 60;
const VISIBLE_ITEMS = 3;
const CONTAINER_HEIGHT = ITEM_HEIGHT * VISIBLE_ITEMS;

const SolarConstellationInput = ({ onSelect, initialMonth = 1, initialDay = 15, year = 2000, onClose }: SolarConstellationInputProps) => {

    // --- State ---
    const [selectedMonth, setSelectedMonth] = useState(initialMonth);
    const [selectedDay, setSelectedDay] = useState(initialDay);

    // --- Derived Data ---
    const maxDays = new Date(year, selectedMonth, 0).getDate();
    const effectiveDay = Math.min(selectedDay, maxDays);
    const activeZodiac = getZodiac(selectedMonth, effectiveDay);
    const activeBirthstone = getBirthstone(selectedMonth);

    // --- Refs for Scroll & Drag (Month) ---
    const monthScrollRef = useRef<HTMLDivElement>(null);
    const isMonthDragging = useRef(false);
    const monthStartScrollTop = useRef(0);
    const monthStartY = useRef(0);
    const monthLastY = useRef(0);
    const monthLastTime = useRef(0);
    const monthVelocity = useRef(0);
    const monthMomentumId = useRef<number | null>(null);
    const isMonthDragClick = useRef(false);

    // --- Refs for Scroll & Drag (Day) ---
    const dayScrollRef = useRef<HTMLDivElement>(null);
    const isDayDragging = useRef(false);
    const dayStartScrollTop = useRef(0);
    const dayStartY = useRef(0);
    const dayLastY = useRef(0);
    const dayLastTime = useRef(0);
    const dayVelocity = useRef(0);
    const dayMomentumId = useRef<number | null>(null);
    const isDayDragClick = useRef(false);

    // Validate Day on Month Change
    useEffect(() => {
        if (selectedDay > maxDays) {
            setSelectedDay(maxDays);
            // Snap scrolling too
            if (dayScrollRef.current) {
                dayScrollRef.current.scrollTo({
                    top: (maxDays - 1) * ITEM_HEIGHT,
                    behavior: 'smooth'
                });
            }
        }
    }, [selectedMonth, maxDays, selectedDay]);

    // Initial Scroll Position
    useEffect(() => {
        if (monthScrollRef.current) {
            monthScrollRef.current.scrollTop = (initialMonth - 1) * ITEM_HEIGHT;
        }
        if (dayScrollRef.current) {
            dayScrollRef.current.scrollTop = (initialDay - 1) * ITEM_HEIGHT;
        }
    }, []);

    // --- Handlers: Month ---
    const handleMonthScroll = () => {
        if (!monthScrollRef.current) return;
        const index = Math.round(monthScrollRef.current.scrollTop / ITEM_HEIGHT);
        const mon = Math.min(Math.max(1 + index, 1), 12);
        if (mon !== selectedMonth) {
            setSelectedMonth(mon);
        }
    };

    const momentumLoopMonth = () => {
        if (!monthScrollRef.current) return;
        monthScrollRef.current.scrollTop -= monthVelocity.current;
        monthVelocity.current *= 0.95; // Friction

        if (Math.abs(monthVelocity.current) < 0.5) {
            if (monthMomentumId.current) cancelAnimationFrame(monthMomentumId.current);
            monthMomentumId.current = null;
            monthScrollRef.current.style.scrollSnapType = 'y mandatory';
            return;
        }
        monthMomentumId.current = requestAnimationFrame(momentumLoopMonth);
    };

    // --- Handlers: Day ---
    const handleDayScroll = () => {
        if (!dayScrollRef.current) return;
        const index = Math.round(dayScrollRef.current.scrollTop / ITEM_HEIGHT);
        const d = Math.min(Math.max(1 + index, 1), maxDays);
        if (d !== selectedDay) {
            setSelectedDay(d);
        }
    };

    const momentumLoopDay = () => {
        if (!dayScrollRef.current) return;
        dayScrollRef.current.scrollTop -= dayVelocity.current;
        dayVelocity.current *= 0.95;

        if (Math.abs(dayVelocity.current) < 0.5) {
            if (dayMomentumId.current) cancelAnimationFrame(dayMomentumId.current);
            dayMomentumId.current = null;
            dayScrollRef.current.style.scrollSnapType = 'y mandatory';
            return;
        }
        dayMomentumId.current = requestAnimationFrame(momentumLoopDay);
    };


    const handleConfirm = () => {
        onSelect(selectedMonth.toString(), effectiveDay.toString());
    };

    // Lists
    const months = Array.from({ length: 12 }, (_, i) => i + 1);
    const days = Array.from({ length: maxDays }, (_, i) => i + 1);

    return (
        <div className="relative w-full h-[600px] overflow-hidden select-none flex flex-col items-center justify-center">

            {/* Background Image (Static) */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[0] pointer-events-none flex items-center justify-center opacity-50 saturate-75">
                {/* Reuse Year Input Background or similar if desired, keeping empty for now or reusing specific bg logic */}
                {/* Using the Birthstone Image as faint background or just dark bg */}
                <img
                    src={`/assets/birthstones/${activeBirthstone.month}_gem.png`}
                    className="w-[500px] h-[500px] object-contain opacity-60"
                    alt=""
                />
            </div>

            {/* Close Button - 콘텐츠 영역 우상단 */}
            {onClose && (
                <button
                    onClick={onClose}
                    className="absolute top-12 right-[calc(50%-200px)] z-40 w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 border border-white/20 text-white/60 hover:text-white backdrop-blur-md transition-all flex items-center justify-center"
                >
                    <X size={20} />
                </button>
            )}

            {/* Content Container */}
            <div className="relative z-20 flex gap-4 items-center mb-12">

                {/* --- MONTH COLUMN --- */}
                <div className="flex flex-col items-center gap-2">
                    <span className="text-white/60 font-serif text-lg tracking-widest">월</span>

                    {/* Up Arrow */}
                    <button
                        onClick={() => {
                            if (monthScrollRef.current) {
                                monthScrollRef.current.style.scrollSnapType = 'y mandatory';
                                monthScrollRef.current.scrollTo({
                                    top: monthScrollRef.current.scrollTop - ITEM_HEIGHT,
                                    behavior: 'smooth'
                                });
                            }
                        }}
                        className="text-white/40 hover:text-white/80 transition-colors"
                    >
                        <ChevronUp size={24} />
                    </button>

                    <div className="relative w-32 h-[180px]">
                        <div
                            ref={monthScrollRef}
                            onScroll={handleMonthScroll}
                            className="w-full h-full overflow-y-auto no-scrollbar snap-y snap-mandatory touch-pan-y cursor-grab active:cursor-grabbing"
                            // Mouse Events for Month Momentum
                            onMouseDown={(e) => {
                                if (monthMomentumId.current) { cancelAnimationFrame(monthMomentumId.current); monthMomentumId.current = null; }
                                isMonthDragging.current = true;
                                isMonthDragClick.current = false;
                                if (monthScrollRef.current) {
                                    monthScrollRef.current.style.scrollSnapType = 'none';
                                    monthStartScrollTop.current = monthScrollRef.current.scrollTop;
                                }
                                monthStartY.current = e.pageY;
                                monthLastY.current = e.pageY;
                                monthLastTime.current = performance.now();
                                monthVelocity.current = 0;
                            }}
                            onMouseMove={(e) => {
                                if (!isMonthDragging.current || !monthScrollRef.current) return;
                                e.preventDefault();
                                const y = e.pageY;
                                const now = performance.now();
                                const deltaY = y - monthLastY.current;
                                const deltaTime = now - monthLastTime.current;
                                if (deltaTime > 0) monthVelocity.current = deltaY * 1.5;
                                const walk = (y - monthStartY.current) * 1.5;
                                monthScrollRef.current.scrollTop = monthStartScrollTop.current - walk;
                                monthLastY.current = y;
                                monthLastTime.current = now;
                                if (Math.abs(y - monthStartY.current) > 5) isMonthDragClick.current = true;
                            }}
                            onMouseUp={() => { isMonthDragging.current = false; momentumLoopMonth(); }}
                            onMouseLeave={() => { if (isMonthDragging.current) { isMonthDragging.current = false; momentumLoopMonth(); } }}
                        >
                            <div style={{ height: (CONTAINER_HEIGHT - ITEM_HEIGHT) / 2 }} />
                            {months.map(m => (
                                <div key={m} className="w-full h-[60px] flex items-center justify-center snap-center" onClick={() => {
                                    if (!isMonthDragClick.current && monthScrollRef.current) {
                                        monthScrollRef.current.style.scrollSnapType = 'y mandatory';
                                        monthScrollRef.current.scrollTo({ top: (m - 1) * ITEM_HEIGHT, behavior: 'smooth' });
                                    }
                                }}>
                                    <span className={`font-serif font-bold transition-all duration-300 ${m === selectedMonth ? 'text-5xl text-white drop-shadow-lg scale-110' : 'text-3xl text-white/30 scale-90'}`}>
                                        {m}
                                    </span>
                                </div>
                            ))}
                            <div style={{ height: (CONTAINER_HEIGHT - ITEM_HEIGHT) / 2 }} />
                        </div>
                    </div>

                    {/* Down Arrow */}
                    <button
                        onClick={() => {
                            if (monthScrollRef.current) {
                                monthScrollRef.current.style.scrollSnapType = 'y mandatory';
                                monthScrollRef.current.scrollTo({
                                    top: monthScrollRef.current.scrollTop + ITEM_HEIGHT,
                                    behavior: 'smooth'
                                });
                            }
                        }}
                        className="text-white/40 hover:text-white/80 transition-colors"
                    >
                        <ChevronDown size={24} />
                    </button>
                </div>

                {/* --- CENTER COLUMN (Constellation) --- */}
                <div className="w-[180px] h-full flex flex-col items-center justify-center pt-8">
                    <div className="w-[160px] h-[160px] relative flex items-center justify-center">
                        <ConstellationViewer zodiacName={activeZodiac.name} />
                    </div>
                    <span className="text-white text-lg font-serif mt-2">{activeZodiac.kor}</span>
                    <span className="text-sm font-light mt-1 opacity-80" style={{ color: activeBirthstone.color }}>{activeBirthstone.kor}</span>
                </div>

                {/* --- DAY COLUMN --- */}
                <div className="flex flex-col items-center gap-2">
                    <span className="text-white/60 font-serif text-lg tracking-widest">일</span>

                    {/* Up Arrow */}
                    <button
                        onClick={() => {
                            if (dayScrollRef.current) {
                                dayScrollRef.current.style.scrollSnapType = 'y mandatory';
                                dayScrollRef.current.scrollTo({
                                    top: dayScrollRef.current.scrollTop - ITEM_HEIGHT,
                                    behavior: 'smooth'
                                });
                            }
                        }}
                        className="text-white/40 hover:text-white/80 transition-colors"
                    >
                        <ChevronUp size={24} />
                    </button>

                    <div className="relative w-32 h-[180px]">
                        <div
                            ref={dayScrollRef}
                            onScroll={handleDayScroll}
                            className="w-full h-full overflow-y-auto no-scrollbar snap-y snap-mandatory touch-pan-y cursor-grab active:cursor-grabbing"
                            // Mouse Events for Day Momentum
                            onMouseDown={(e) => {
                                if (dayMomentumId.current) { cancelAnimationFrame(dayMomentumId.current); dayMomentumId.current = null; }
                                isDayDragging.current = true;
                                isDayDragClick.current = false;
                                if (dayScrollRef.current) {
                                    dayScrollRef.current.style.scrollSnapType = 'none';
                                    dayStartScrollTop.current = dayScrollRef.current.scrollTop;
                                }
                                dayStartY.current = e.pageY;
                                dayLastY.current = e.pageY;
                                dayLastTime.current = performance.now();
                                dayVelocity.current = 0;
                            }}
                            onMouseMove={(e) => {
                                if (!isDayDragging.current || !dayScrollRef.current) return;
                                e.preventDefault();
                                const y = e.pageY;
                                const now = performance.now();
                                const deltaY = y - dayLastY.current;
                                const deltaTime = now - dayLastTime.current;
                                if (deltaTime > 0) dayVelocity.current = deltaY * 1.5;
                                const walk = (y - dayStartY.current) * 1.5;
                                dayScrollRef.current.scrollTop = dayStartScrollTop.current - walk;
                                dayLastY.current = y;
                                dayLastTime.current = now;
                                if (Math.abs(y - dayStartY.current) > 5) isDayDragClick.current = true;
                            }}
                            onMouseUp={() => { isDayDragging.current = false; momentumLoopDay(); }}
                            onMouseLeave={() => { if (isDayDragging.current) { isDayDragging.current = false; momentumLoopDay(); } }}
                        >
                            <div style={{ height: (CONTAINER_HEIGHT - ITEM_HEIGHT) / 2 }} />
                            {days.map(d => (
                                <div key={d} className="w-full h-[60px] flex items-center justify-center snap-center" onClick={() => {
                                    if (!isDayDragClick.current && dayScrollRef.current) {
                                        dayScrollRef.current.style.scrollSnapType = 'y mandatory';
                                        dayScrollRef.current.scrollTo({ top: (d - 1) * ITEM_HEIGHT, behavior: 'smooth' });
                                    }
                                }}>
                                    <span className={`font-serif font-bold transition-all duration-300 ${d === selectedDay ? 'text-5xl text-white drop-shadow-lg scale-110' : 'text-3xl text-white/30 scale-90'}`}>
                                        {d}
                                    </span>
                                </div>
                            ))}
                            <div style={{ height: (CONTAINER_HEIGHT - ITEM_HEIGHT) / 2 }} />
                        </div>
                    </div>

                    {/* Down Arrow */}
                    <button
                        onClick={() => {
                            if (dayScrollRef.current) {
                                dayScrollRef.current.style.scrollSnapType = 'y mandatory';
                                dayScrollRef.current.scrollTo({
                                    top: dayScrollRef.current.scrollTop + ITEM_HEIGHT,
                                    behavior: 'smooth'
                                });
                            }
                        }}
                        className="text-white/40 hover:text-white/80 transition-colors"
                    >
                        <ChevronDown size={24} />
                    </button>
                </div>

            </div>

            {/* Bottom Info & Confirm */}
            <div className="absolute bottom-12 z-30 text-center w-full flex flex-col items-center gap-6">

                <button
                    onClick={handleConfirm}
                    className="px-12 py-4 bg-white/10 hover:bg-white/20 border border-white/30 rounded-full text-white font-serif text-xl tracking-widest backdrop-blur-md shadow-[0_0_20px_rgba(255,255,255,0.1)] hover:shadow-[0_0_40px_rgba(255,255,255,0.3)] hover:scale-105 active:scale-95 transition-all"
                >
                    확인
                </button>

                <motion.div
                    className="absolute top-[-50px] pointer-events-none"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 0.6 }}
                >
                    <p className="text-white/50 text-sm font-['Gowun_Batang']">
                        스크롤 & 드래그 하여 입력하세요
                    </p>
                </motion.div>
            </div>


        </div>
    );
};

export default SolarConstellationInput;
