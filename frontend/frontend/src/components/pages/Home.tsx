import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Scroll, Eye } from 'lucide-react';
import FortuneReadingPage from './FortuneReadingPage';
import FortuneTeaserModal from '../features/FortuneTeaserModal';
import { useCharacterSettings, getSDCharacterImage } from '../../utils/character';

interface ServiceItem {
    id: string;
    title: string;
    desc: string;
    type: 'active' | 'coming-soon';
    bgImage: string;
    color: string;
}

const Home = ({
    onThemeChange,
    onMenuVisibilityChange,
    onStartCinematic
}: {
    onThemeChange?: (theme: string) => void;
    onMenuVisibilityChange?: (visible: boolean) => void;
    onStartCinematic?: () => void;
}) => {
    const navigate = useNavigate();
    const location = useLocation();
    const [view, setView] = useState<'home' | 'reading'>('home');
    const [hoveredId, setHoveredId] = useState<string | null>(null);
    const [showFortuneModal, setShowFortuneModal] = useState(false);
    const [showCardModal, setShowCardModal] = useState(false);
    const [readingMode, setReadingMode] = useState<'saju' | 'daily'>('saju');
    const [isNavigating, setIsNavigating] = useState(false); // Transition State
    const [transitionDialogue, setTransitionDialogue] = useState("");
    const [transitionImage, setTransitionImage] = useState("");
    const charSettings = useCharacterSettings();

    useEffect(() => {
        onThemeChange?.('fusion');
        onMenuVisibilityChange?.(true); // Ensure Navbar is visible when visiting Home

        // Check for state to auto-open Saju
        if (location.state?.showSaju) {
            handleFortuneSelect('saju');
            // Clear state to prevent re-opening on back navigation
            window.history.replaceState({}, document.title);
        }
    }, [onThemeChange, onMenuVisibilityChange, location.state]);

    const services: ServiceItem[] = [
        {
            id: 'fortune',
            title: '오늘의 운세',
            desc: '오늘의 기운을 미리 확인해보세요',
            type: 'active',
            bgImage: '/assets/bg/fortune_bg_oriental.png',
            color: 'from-amber-900/80 to-stone-900/80'
        },
        {
            id: 'cards',
            title: '카드 점괘',
            desc: '타로와 화투로 보는 신비한 점괘',
            type: 'active',
            bgImage: '/assets/bg/card_bg_oriental.png',
            color: 'from-purple-900/80 to-slate-900/80'
        },
        {
            id: 'compatibility',
            title: '궁합',
            desc: '천생연분일까? 두 사람의 운명 확인',
            type: 'active',
            bgImage: '/assets/bg/todayfortune.png',
            color: 'from-pink-900/80 to-rose-900/80'
        }
    ];

    const handleFortuneSelect = (mode: 'saju' | 'daily') => {
        if (mode === 'daily') {
            navigate('/today');
            return;
        }
        setReadingMode(mode);
        setShowFortuneModal(false);
        setView('reading');
        onMenuVisibilityChange?.(false);
    };

    return (
        <div className="min-h-screen w-full relative bg-[#0a0a0c] overflow-hidden text-white font-['Hahmlet'] font-bold">
            <AnimatePresence mode="wait">
                {view === 'home' ? (
                    <motion.div
                        key="home"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0, x: -20 }}
                        className="min-h-screen flex flex-col items-center justify-center p-4 md:p-12 relative z-10"
                    >
                        {/* 1. 배경 레이어: main.png 배경 */}
                        <div className="absolute inset-0 z-0 pointer-events-none">
                            <img
                                src="/assets/bg/main.png"
                                alt="Background"
                                className="w-full h-full object-cover brightness-[0.3]"
                            />
                            <div className="absolute inset-0 bg-black/60" />
                        </div>

                        {/* 2. 콘텐츠 레이어: z-index를 높여 배경보다 위에 둠 */}
                        {/* 2. 콘텐츠 레이어: Immersive Card Select Layout */}



                        <div className="relative z-20 w-full max-w-[1600px] min-h-[65vh] pointer-events-auto pt-20 flex flex-col lg:flex-row gap-6 items-stretch justify-center">

                            {services.map((item) => (
                                <motion.div
                                    key={item.id}
                                    layout
                                    onMouseEnter={() => setHoveredId(item.id)}
                                    onMouseLeave={() => setHoveredId(null)}
                                    onClick={() => {
                                        if (item.id === 'fortune') {
                                            handleFortuneSelect('daily');
                                        } else if (item.id === 'cards') {
                                            /* Navigate to Full Feature Card Reading Page */
                                            navigate('/card-reading');
                                        } else if (item.id === 'compatibility') {
                                            // INK WIPE TRANSITION START
                                            const dialogues = [
                                                "인연이란 참 신기한 것이지요...",
                                                "후후, 누구와의 궁합이 그리 궁금하실까요?",
                                                "운명의 붉은 실은 어디로 이어져 있을까요?",
                                                "두 분의 앞날을 제가 살짝 엿보아 드리지요.",
                                                "떨리는 마음, 그 설렘이 느껴지는군요."
                                            ];
                                            const images = [
                                                getSDCharacterImage('east', charSettings.east, 'loading'),
                                                getSDCharacterImage('east', charSettings.east, 'loading2'),
                                                getSDCharacterImage('east', charSettings.east, 'loading3'),
                                                getSDCharacterImage('east', charSettings.east, 'loading4'),
                                                getSDCharacterImage('east', charSettings.east, 'loading5'),
                                                getSDCharacterImage('east', charSettings.east, 'loading6')
                                            ].filter(img => img !== '');

                                            setTransitionDialogue(dialogues[Math.floor(Math.random() * dialogues.length)]);
                                            setTransitionImage(images[Math.floor(Math.random() * images.length)]);
                                            setIsNavigating(true);
                                            onMenuVisibilityChange?.(false); // Hide Navbar immediately
                                            // Optional: Play a sound effect here if available
                                            setTimeout(() => {
                                                navigate('/compatibility');
                                            }, 2500); // Increased duration by 1s (1.5s -> 2.5s)
                                        }
                                    }}
                                    className={`relative rounded-[2rem] border border-white/10 overflow-hidden transition-all duration-700 ease-[cubic-bezier(0.25,1,0.5,1)] group
                                        ${item.type === 'active' ? 'cursor-pointer hover:shadow-[0_0_50px_rgba(255,255,255,0.1)]' : 'opacity-50 grayscale cursor-default'}
                                        ${hoveredId === item.id ? 'flex-[4]' : 'flex-1'}
                                        ${hoveredId && hoveredId !== item.id ? 'opacity-50 blur-[2px]' : 'opacity-100'}
                                        min-w-[120px] lg:min-w-[240px]
                                    `}
                                >
                                    {/* Card Background */}
                                    <div className="absolute inset-0 z-0">
                                        <div className={`absolute inset-0 bg-gradient-to-br ${item.color} opacity-80 mix-blend-multiply transition-opacity duration-500`} />
                                        <div className={`w-full h-full transition-transform duration-[1.5s] ${(item.id === 'fortune' || item.id === 'cards') ? 'scale-x-[-1]' : ''}`}>
                                            <img
                                                src={item.bgImage || '/assets/bg/fortune_bg_oriental.png'}
                                                alt={item.title}
                                                className="w-full h-full object-cover opacity-40 group-hover:opacity-60 group-hover:scale-110 transition-all duration-[1.5s]"
                                            />
                                        </div>
                                    </div>

                                    {/* Dev Badge Removed */}

                                    {/* Default Content (Title Only) */}
                                    <div className={`absolute inset-0 flex flex-col items-center justify-center transition-all duration-500 z-10
                                        ${hoveredId === item.id ? 'opacity-0 translate-y-20 pointer-events-none' : 'opacity-100 translate-y-0'}
                                    `}>
                                        <h3 className="text-4xl md:text-5xl font-['Hahmlet'] text-white/90 tracking-[0.3em] vertical-rl lg:horizontal-tb drop-shadow-2xl whitespace-nowrap">
                                            {item.title}
                                        </h3>
                                        <div className="mt-8 w-[1px] h-24 bg-gradient-to-b from-white/50 to-transparent shadow-[0_0_15px_rgba(255,255,255,0.3)]" />
                                    </div>

                                    {/* Expanded Content Overlay */}
                                    <AnimatePresence mode="wait">
                                        {hoveredId === item.id && (
                                            <motion.div
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: 1 }}
                                                exit={{ opacity: 0 }}
                                                transition={{ duration: 0.5, delay: 0.1 }}
                                                className="absolute inset-0 z-20 flex flex-col justify-between p-0 overflow-hidden"
                                            >
                                                {/* Cinematic Overlay - Reduced Opacity for Clarity */}
                                                <div className="absolute inset-0 bg-black/10 z-0" />
                                                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/30 z-0" />

                                                {/* Character Visuals */}
                                                {/* Character Visuals Removed as per request */}

                                                {/* Top: Cinematic Title */}
                                                <div className="relative z-20 pt-24 flex flex-col items-center">
                                                    <motion.h3
                                                        initial={{ y: -50, opacity: 0, scale: 0.9 }}
                                                        animate={{ y: 0, opacity: 1, scale: 1 }}
                                                        transition={{ delay: 0.3, duration: 0.6 }}
                                                        className={`text-6xl md:text-8xl font-black tracking-tighter drop-shadow-2xl text-transparent bg-clip-text
                                                            ${item.id === 'fortune' ? 'bg-gradient-to-b from-amber-100 to-amber-500' : ''}
                                                            ${item.id === 'cards' ? 'bg-gradient-to-b from-purple-100 to-purple-500' : ''}
                                                            ${item.id === 'compatibility' ? 'bg-gradient-to-b from-rose-100 to-rose-400' : ''}
                                                        `}
                                                    >
                                                        {item.title}
                                                    </motion.h3>
                                                    <motion.div
                                                        initial={{ width: 0 }}
                                                        animate={{ width: 100 }}
                                                        transition={{ delay: 0.8, duration: 0.5 }}
                                                        className={`h-1 mt-6 shadow-[0_0_20px_rgba(255,255,255,0.5)] rounded-full
                                                            ${item.id === 'fortune' ? 'bg-amber-500' : ''}
                                                            ${item.id === 'cards' ? 'bg-purple-500' : ''}
                                                            ${item.id === 'compatibility' ? 'bg-rose-500' : ''}
                                                        `}
                                                    />
                                                </div>

                                                {/* Dev Badge Removed from here */}

                                                {/* Bottom: Action Area */}
                                                <div className="relative z-20 pb-24 pt-32 flex flex-col items-center justify-center w-full grow bg-gradient-to-t from-black/90 via-black/40 to-transparent">
                                                    <motion.p
                                                        initial={{ opacity: 0, y: 20 }}
                                                        animate={{ opacity: 1, y: 0 }}
                                                        transition={{ delay: 0.5 }}
                                                        className="text-white/90 text-xl md:text-2xl font-light mb-8 max-w-xl text-center leading-relaxed drop-shadow-lg"
                                                    >
                                                        {item.desc}
                                                    </motion.p>

                                                    <motion.div
                                                        initial={{ opacity: 0 }}
                                                        animate={{ opacity: 1 }}
                                                        transition={{ delay: 1, duration: 1 }}
                                                        className="flex flex-col items-center"
                                                    >
                                                        <div className={`w-1 h-16 bg-gradient-to-b from-transparent to-transparent
                                                            ${item.id === 'fortune' ? 'via-amber-500/50' : ''}
                                                            ${item.id === 'cards' ? 'via-purple-500/50' : ''}
                                                            ${item.id === 'compatibility' ? 'via-rose-500/50' : ''}
                                                        `} />
                                                    </motion.div>
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </motion.div>
                            ))}
                        </div>

                        {/* 운세 선택 모달 */}
                        <AnimatePresence>
                            {showFortuneModal && (
                                <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        onClick={() => setShowFortuneModal(false)}
                                        className="absolute inset-0 bg-black/80 backdrop-blur-sm cursor-pointer"
                                    />
                                    <motion.div
                                        initial={{ scale: 0.9, opacity: 0 }}
                                        animate={{ scale: 1, opacity: 1 }}
                                        exit={{ scale: 0.9, opacity: 0 }}
                                        className="relative bg-[#1a1a1a] p-8 rounded-3xl w-full max-w-lg border border-white/10 text-center z-110"
                                    >
                                        <div className="absolute top-2 right-4 text-xs font-mono text-white/30 border border-white/20 px-2 py-1 rounded">
                                            DEV MODE
                                        </div>
                                        <h2 className="text-3xl font-['Hahmlet'] mb-8 text-amber-200">
                                            [개발용] 운세 모드 선택
                                        </h2>
                                        <div className="grid grid-cols-2 gap-4">
                                            <button onClick={() => handleFortuneSelect('saju')} className="p-6 bg-white/5 border border-white/10 rounded-2xl hover:border-amber-500 hover:bg-amber-500/5 transition-all group cursor-pointer">
                                                <Scroll size={32} className="mx-auto text-amber-500 mb-2 group-hover:scale-110 transition-transform" />
                                                <div className="font-bold">사주팔자</div>
                                            </button>
                                            <button onClick={() => handleFortuneSelect('daily')} className="p-6 bg-white/5 border border-white/10 rounded-2xl hover:border-indigo-500 hover:bg-indigo-500/5 transition-all group cursor-pointer">
                                                <Eye size={32} className="mx-auto text-indigo-500 mb-2 group-hover:scale-110 transition-transform" />
                                                <div className="font-bold">오늘의 운세</div>
                                            </button>
                                        </div>
                                    </motion.div>
                                </div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                ) : (
                    <motion.div
                        key="reading"
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -20 }}
                    >
                        <FortuneReadingPage
                            mode={readingMode}
                            onBack={() => {
                                setView('home');
                                onMenuVisibilityChange?.(true);
                            }} />
                    </motion.div>
                )}
            </AnimatePresence>

            <FortuneTeaserModal
                isOpen={showCardModal}
                onClose={() => setShowCardModal(false)}
            />

            {/* Ink Wipe Transition Overlay */}
            <AnimatePresence>
                {isNavigating && (
                    <motion.div
                        className="fixed inset-0 z-[9999] pointer-events-none flex items-center justify-center bg-transparent"
                        initial={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        {/* Ink Blot Expanding */}
                        <motion.div
                            initial={{ scale: 0, opacity: 0 }}
                            animate={{ scale: 20, opacity: 1 }}
                            transition={{ duration: 1.5, ease: [0.7, 0, 0.3, 1] }}
                            className="w-32 h-32 bg-black rounded-full mix-blend-multiply filter blur-sm"
                            style={{
                                backgroundImage: "url('https://www.transparenttextures.com/patterns/black-ink.png')", // Optional texture
                            }}
                        />

                        {/* Text: Character & Dialogue */}
                        <motion.div
                            className="absolute z-10 flex flex-col items-center justify-center bottom-0 w-full pb-20 md:pb-32"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.6, duration: 0.8 }}
                        >
                            {/* Speech Bubble */}
                            <motion.div
                                initial={{ scale: 0.8, opacity: 0, y: 20 }}
                                animate={{ scale: 1, opacity: 1, y: 0 }}
                                transition={{ delay: 0.8, type: "spring", stiffness: 200 }}
                                className="relative bg-white/10 backdrop-blur-md border border-white/20 px-8 py-4 rounded-2xl mb-6 w-auto max-w-3xl text-center shadow-[0_0_30px_rgba(255,255,255,0.1)]"
                            >
                                <p className="text-amber-100 font-['Gowun_Batang'] text-xl font-bold tracking-wider leading-relaxed whitespace-nowrap">
                                    "{transitionDialogue}"
                                </p>
                                {/* Triangle tail */}
                                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-white/10 border-r border-b border-white/20 transform rotate-45 backdrop-blur-md" />
                            </motion.div>

                            {/* Character Image */}
                            <motion.img
                                src={transitionImage}
                                alt="Loading Character"
                                initial={{ y: 50, opacity: 0 }}
                                animate={{ y: 0, opacity: 1 }}
                                transition={{ delay: 0.5, duration: 0.8, ease: "easeOut" }}
                                className="h-64 md:h-80 w-auto object-contain drop-shadow-[0_0_30px_rgba(0,0,0,0.8)] filter brightness-110"
                            />
                        </motion.div>

                        {/* Full Screen Blackout to ensure coverage */}
                        <motion.div
                            className="absolute inset-0 bg-black -z-10"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ delay: 0.5, duration: 0.5 }}
                        />
                    </motion.div>
                )}
            </AnimatePresence>


        </div>
    );
};

export default Home;