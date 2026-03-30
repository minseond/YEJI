import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scroll, Sparkles, ArrowLeft } from 'lucide-react';
import ParticleBackground from '../effects/ParticleBackground';

// Components
// (Unused ThreeDTiltCard and FourElementsRadar removed)

// Types & Utils
import { type DualFortuneResultV2 } from '../../data/types';
import {
    getGanjiMeaning,
    getDailyZodiacFortune,
    getDailyLuckyInfoUnified,
    getDailyWesternFortune,
    getCurrentSunSign
} from '../../utils/domainMapping';
import { getCharacterImage, getCharacterName, useCharacterSettings, getDuoOutroScript } from '../../utils/character';
import AnimatedBubble from '../common/AnimatedBubble';

// Types for the result data (Daily)
export interface DailyFortuneResult {
    type: string;
    score: number | string;
    summary: string;
    keywords?: string[];
    explanation: string;
    luckyItem?: string;
    details?: { title: string, description: string }[]; // Added for detailed breakdown
}

interface TodayFortuneResultProps {
    fortuneType: string;
    eastResult: DailyFortuneResult;
    westResult: DailyFortuneResult;
    staticResult: DualFortuneResultV2; // Full Integrated Report Data
    onBack: () => void;
    onSaveAndExit?: () => void;
    mode?: 'default' | 'history';
}

const TodayFortuneResult = ({ fortuneType, eastResult, westResult, staticResult, onSaveAndExit, mode = 'default' }: TodayFortuneResultProps) => {
    // View mode state (no intro, go directly to result)
    const [viewMode, setViewMode] = useState<'eastern' | 'western'>('eastern');

    // Outro states
    const settings = useCharacterSettings();
    const [showOutro, setShowOutro] = useState(false);
    const [outroDialogueStep, setOutroDialogueStep] = useState(0);
    const [showMainTransition, setShowMainTransition] = useState(false);
    const [isSwitching, setIsSwitching] = useState(false);
    const [showCTA, setShowCTA] = useState(false);
    const scrollRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo({ top: 0, behavior: 'instant' });
        }
    }, [viewMode]);

    const EastSajuImg = getCharacterImage('east', settings.east, 'normal');
    const WestStarImg = getCharacterImage('west', settings.west, 'normal');
    const EastName = getCharacterName('east', settings.east);
    const WestName = getCharacterName('west', settings.west);


    const activeResult = viewMode === 'eastern' ? eastResult : westResult;
    const bgGradient = viewMode === 'eastern' ? 'from-amber-900/50 to-black' : 'from-indigo-900/50 to-black';

    // Helpers for Charts
    const eastern = staticResult.eastern;
    const western = staticResult.western;

    // Verdict Helper
    // Intro Reveal State
    const [revealStep, setRevealStep] = useState(mode === 'history' ? 4 : 0); // 0: Suspense, 1: Reveal, 2: Reaction, 3: Done
    const [revealedHistory, setRevealedHistory] = useState({
        eastern: mode === 'history',
        western: mode === 'history'
    });

    // Mode Switching Logic
    // Mode Switching Logic
    const handleModeSwitch = (mode: 'eastern' | 'western') => {
        if (viewMode === mode) return;

        setViewMode(mode);
        // If target mode hasn't been revealed yet, reset animation to 0. Otherwise set to 3 (done).
        if (!revealedHistory[mode]) {
            setRevealStep(0);
        } else {
            setRevealStep(4);
        }
    };

    const handleDismissReveal = () => {
        if (revealStep === 2) {
            // Click during first dialogue -> advance to second dialogue
            setRevealStep(3);
        } else if (revealStep === 3) {
            // Click during second dialogue -> end the reveal sequence
            setRevealStep(4);
            setRevealedHistory(prev => ({ ...prev, [viewMode]: true }));
        }
    };

    // Verdict Logic & Reactions
    const getVerdictInfo = (score: number | string, mode: 'eastern' | 'western') => {
        let numScore = 0;

        if (typeof score === 'number') {
            numScore = score;
        } else {
            const s = String(score).trim();
            // Handle Korean labels from backend
            if (s === '대길') numScore = 95;
            else if (s === '중길' || s === '길') numScore = 85;
            else if (s === '소길') numScore = 72;
            else if (s === '평') numScore = 55;
            else if (s === '소흉') numScore = 37;
            else if (s === '흉') numScore = 22;
            else if (s === '대흉') numScore = 7;
            else numScore = parseFloat(s) || 0;
        }

        if (mode === 'eastern') {
            if (numScore >= 90) return { label: '大吉', subLabel: '(대길)', fullLabel: '대길 (Great Fortune)', color: 'text-amber-400', bg: 'from-amber-500/20', effect: 'gold', emotion: 'smile' as const, reactions: ["오호… 좀처럼 보기 힘든 귀한 운세요.", "오늘은 그대가 내딛는 걸음마다 길이 열릴 것이니, 주저하지 말고 나아가시오."] };
            if (numScore >= 80) return { label: '吉', subLabel: '(길)', fullLabel: '길 (Good Fortune)', color: 'text-indigo-400', bg: 'from-indigo-500/20', effect: 'star', emotion: 'smile' as const, reactions: ["음, 길한 기운이 또렷하오.", "흐름이 좋으니, 망설였던 일이 있다면 시도해보아도 무방하겠소."] };
            if (numScore >= 65) return { label: '小吉', subLabel: '(소길)', fullLabel: '소길 (Small Luck)', color: 'text-emerald-400', bg: 'from-emerald-500/10', effect: 'none', emotion: 'explain' as const, reactions: ["소소하지만 길한 기운이 보이오.", "큰 욕심보다는 작은 기쁨에 만족하는 하루가 되시게."] };
            if (numScore >= 45) return { label: '平', subLabel: '(평)', fullLabel: '평 (Average)', color: 'text-slate-300', bg: 'from-slate-500/20', effect: 'none', emotion: 'explain' as const, reactions: ["평한 운세로다. 큰 요동은 없겠소.", "잔잔한 하루이니, 스스로를 돌보는 데 쓰시게."] };
            if (numScore >= 30) return { label: '小凶', subLabel: '(소흉)', fullLabel: '소흉 (Small Bad Luck)', color: 'text-orange-300', bg: 'from-orange-500/10', effect: 'none', emotion: 'thinking' as const, reactions: ["기운이 조금은 무겁게 느껴지오.", "익숙한 일이라도 실수를 조심하고 신중히 행동하시게."] };
            if (numScore >= 15) return { label: '凶', subLabel: '(흉)', fullLabel: '흉 (Bad Luck)', color: 'text-gray-400', bg: 'from-gray-700/20', effect: 'rain', emotion: 'annoying' as const, reactions: ["기운이 다소 흔들리고 있소.", "오늘은 나서기보다는, 조용히 흐름을 살피는 것이 상책이오."] };
            return { label: '大凶', subLabel: '(대흉)', fullLabel: '대흉 (Great Misfortune)', color: 'text-red-900', bg: 'from-red-900/20', effect: 'storm', emotion: 'suprize' as const, reactions: ["큰일이오.. 흉한 기운이 짙게 드리웠소.", "중요한 결정은 피하고, 몸과 마음을 지키는 데 힘쓰시게."] };
        } else {
            // Western Logic (Stella)
            if (numScore >= 91) return { label: 'Perfect', subLabel: `(${numScore}점)`, fullLabel: 'Perfect Alignment', color: 'text-purple-400', bg: 'from-purple-500/20', effect: 'gold', emotion: 'smile' as const, reactions: ["와! 별들이 당신을 위해 완벽하게 정렬했어요!", "직관을 믿고 리드해보세요. 우주는 당신 편이랍니다!"] };
            if (numScore >= 71) return { label: 'Lucky', subLabel: `(${numScore}점)`, fullLabel: 'Lucky Day', color: 'text-indigo-400', bg: 'from-indigo-500/20', effect: 'star', emotion: 'smile' as const, reactions: ["행운의 별이 떴군요! 기분 좋은 바람이 불어오고 있어요.", "기분 좋은 서프라이즈나 소소한 행운을 기대해봐도 좋겠어요."] };
            if (numScore >= 41) return { label: 'Normal', subLabel: `(${numScore}점)`, fullLabel: 'Normal Flow', color: 'text-teal-300', bg: 'from-teal-500/20', effect: 'none', emotion: 'explain' as const, reactions: ["평온한 하루네요. 모든 것이 균형을 이루고 있어요.", "무리하지 말고, 자연스러운 흐름에 몸을 맡겨보세요."] };
            if (numScore >= 18) return { label: 'Moody', subLabel: `(${numScore}점)`, fullLabel: 'Moody Sky', color: 'text-gray-400', bg: 'from-gray-700/20', effect: 'rain', emotion: 'annoying' as const, reactions: ["음, 별들이 오늘 좀 변덕스럽네요.", "행동하기 전에 한 번 더 생각하고, 침착함을 유지하세요."] };
            return { label: 'Chaos', subLabel: `(${numScore}점)`, fullLabel: 'Chaotic Energy', color: 'text-rose-600', bg: 'from-rose-900/20', effect: 'storm', emotion: 'suprize' as const, reactions: ["혼돈의 에너지가 소용돌이치고 있어요. 조심해야겠네요.", "안전이 최우선이에요. 이 폭풍이 얼른 지나가길 바래요.."] };
        }
    };

    const activeScore = viewMode === 'eastern' ? eastResult.score : westResult.score;
    const verdictInfo = getVerdictInfo(activeScore, viewMode);

    // Dynamic Assets for Overlay
    const overlayCharName = viewMode === 'eastern' ? EastName : WestName;
    const overlayCharId = viewMode === 'eastern' ? settings.east : settings.west;
    const overlayRegion = viewMode === 'eastern' ? 'east' : 'west';
    const overlayBgStart = viewMode === 'eastern' ? 'from-amber-900/40' : 'from-indigo-900/40';

    // Drive Reveal Animation
    // Drive Reveal Animation
    useEffect(() => {
        let timer: NodeJS.Timeout;

        if (revealStep === 0) {
            timer = setTimeout(() => setRevealStep(1), 2500);
        } else if (revealStep === 1) {
            timer = setTimeout(() => setRevealStep(2), 2000);
        } else if (revealStep === 2) {
            timer = setTimeout(() => setRevealStep(3), 4000); // Reaction 1 Duration
        } else if (revealStep === 3) {
            timer = setTimeout(() => setRevealStep(4), 4000); // Reaction 2 Duration
        }

        return () => clearTimeout(timer);
    }, [revealStep]);

    // Mark as revealed when animation finishes
    useEffect(() => {
        if (revealStep === 4 && !revealedHistory[viewMode]) {
            setRevealedHistory(prev => ({ ...prev, [viewMode]: true }));
        }
    }, [revealStep, viewMode, revealedHistory]);

    // CTA Timer
    useEffect(() => {
        let showTimer: NodeJS.Timeout;
        let hideTimer: NodeJS.Timeout;

        if (viewMode === 'eastern' && revealStep === 4 && !revealedHistory.western) {
            // Wait 2 seconds before showing
            showTimer = setTimeout(() => {
                setShowCTA(true);
                // Hide 3 seconds after showing
                hideTimer = setTimeout(() => setShowCTA(false), 3000);
            }, 2000);
        } else {
            setShowCTA(false);
        }

        return () => {
            clearTimeout(showTimer);
            clearTimeout(hideTimer);
        };
    }, [viewMode, revealStep, revealedHistory.western]);


    const verdict = {
        label: verdictInfo.label,
        subLabel: verdictInfo.subLabel,
        fullLabel: verdictInfo.fullLabel,
        color: verdictInfo.color,
        bg: verdictInfo.bg,
        effect: verdictInfo.effect
    };

    const handleOutroNext = () => {
        const outroScript = getDuoOutroScript(settings.east, settings.west);
        if (outroDialogueStep < outroScript.length - 1) {
            setOutroDialogueStep(prev => prev + 1);
        } else {
            // 대화 종료 즉시 화면 닫기 애니메이션 시작
            setShowMainTransition(true);
            setTimeout(() => {
                if (onSaveAndExit) onSaveAndExit();
            }, 1000);
        }
    };

    const handleSaveAndExitClick = () => {
        // Skip Outro, just fade out and exit
        setShowMainTransition(true);
        setTimeout(() => {
            if (onSaveAndExit) onSaveAndExit();
        }, 1000);
    };

    const getKoreanFortuneType = (type: string) => {
        const map: Record<string, string> = {
            'love': '연애운',
            'wealth': '재물운',
            'health': '건강운',
            'academic': '학업운',
            'career': '직업운',
            'today': '오늘의 운세'
        };
        return map[type.toLowerCase()] || type;
    };

    const displayTitle = getKoreanFortuneType(fortuneType);

    // Result Render
    return (
        <div className={`relative w-full h-full flex flex-col overflow-hidden bg-black`}>
            {/* Reveal Overlay (Shared for both East & West) */}
            <AnimatePresence>
                {revealStep < 4 && (
                    <motion.div
                        className={`absolute inset-0 z-[200] flex flex-col overflow-hidden ${revealStep === 0 ? 'items-center justify-center bg-black' : (viewMode === 'eastern' ? 'items-end justify-end' : 'items-start justify-end')} ${revealStep >= 2 ? 'pointer-events-auto cursor-pointer' : 'pointer-events-none'}`}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.8 }}
                        onClick={handleDismissReveal}
                    >
                        {/* Background - Fades out after Step 0 */}
                        <motion.div
                            className={`absolute inset-0 bg-gradient-to-b ${overlayBgStart} to-black`}
                            initial={{ opacity: 0.8 }}
                            animate={{ opacity: revealStep === 0 ? 0.95 : 0 }}
                            transition={{ duration: 0.8 }}
                        />

                        {revealStep === 0 && <ParticleBackground type={viewMode === 'eastern' ? 'eastern' : 'western'} className="opacity-40" />}

                        {/* Content Container */}
                        <motion.div
                            layout
                            className={`relative z-10 flex flex-col ${revealStep === 0 ? 'items-center gap-12 max-w-lg w-full p-8' : `items-center gap-4 w-auto p-4 md:p-12 mb-16 ${viewMode === 'eastern' ? 'md:mr-10' : 'md:ml-10'}`}`}
                        >

                            {/* Text Area */}
                            <div className={`${revealStep === 0 ? 'h-32' : 'mb-10 z-20'} flex items-center justify-center`}>
                                <AnimatePresence mode="wait">
                                    {revealStep === 0 && (
                                        <motion.h2
                                            key="step0"
                                            initial={{ opacity: 0, y: 20 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, scale: 0.8 }}
                                            className={`text-3xl md:text-4xl ${viewMode === 'eastern' ? 'text-amber-100' : 'text-indigo-100'} font-bold animate-pulse text-center`}
                                        >
                                            {viewMode === 'eastern' ? "운명이 가리키길..." : "별들이 속삭이길..."}
                                        </motion.h2>
                                    )}
                                    {revealStep >= 1 && (
                                        <div className="flex flex-col items-center">
                                            {/* Verdict Text */}
                                            {revealStep === 1 && (
                                                <div className="flex flex-col items-center">
                                                    <motion.h1
                                                        key="step1"
                                                        initial={{ scale: 0.5, opacity: 0, y: 50 }}
                                                        animate={{ scale: 1, opacity: 1, y: 0 }}
                                                        exit={{ opacity: 0, y: -20 }}
                                                        transition={{ type: "spring", bounce: 0.6 }}
                                                        className={`text-6xl md:text-7xl font-black ${verdictInfo.color} drop-shadow-[0_0_20px_rgba(0,0,0,0.8)] text-center stroke-white stroke-1`}
                                                        style={{ textShadow: '2px 2px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000' }}
                                                    >
                                                        {verdictInfo.label}!
                                                    </motion.h1>
                                                    {/* Sub-label for Pronunciation */}

                                                </div>
                                            )}

                                            {/* Reaction Bubble - Unified for Step 2 and 3 for smooth transition */}
                                            <AnimatePresence>
                                                {(revealStep === 2 || revealStep === 3) && verdictInfo.reactions && (
                                                    <motion.div
                                                        key="reaction-bubble-wrap"
                                                        initial={{ opacity: 0, scale: 0.8, y: 20 }}
                                                        animate={{ opacity: 1, scale: 1, y: 0 }}
                                                        exit={{ opacity: 0, scale: 0.9, y: -10 }}
                                                        transition={{ duration: 0.3 }}
                                                        className="translate-y-44 min-w-[350px] max-w-[500px]"
                                                    >
                                                        <AnimatedBubble
                                                            theme={viewMode === 'eastern' ? "amber" : "indigo"}
                                                            size="large"
                                                            title={overlayCharName}
                                                            text={verdictInfo.reactions[revealStep - 2]}
                                                            className="shadow-2xl"
                                                        />
                                                    </motion.div>
                                                )}
                                            </AnimatePresence>
                                        </div>
                                    )}
                                </AnimatePresence>
                            </div>

                            {/* Character Area */}
                            <motion.div
                                layout
                                className={`relative ${revealStep === 0 ? 'w-72 h-96 md:w-96 md:h-[500px]' : 'w-64 h-80 md:w-80 md:h-[400px]'}`}
                                transition={{ layout: { duration: 0.8, type: "spring", bounce: 0.2 } }}
                            >
                                {/* Character Image Helper */}
                                {(() => {
                                    let emotion = 'thinking'; // Default for step 0
                                    if (revealStep >= 1) emotion = verdictInfo.emotion;

                                    const img = getCharacterImage(overlayRegion as any, overlayCharId, emotion as any);

                                    return (
                                        <motion.img
                                            key={emotion} // Switch key on emotion change
                                            src={img}
                                            className="w-full h-full object-contain drop-shadow-[0_0_20px_rgba(0,0,0,0.5)]"
                                            initial={{ opacity: 0.8, y: 0 }}
                                            animate={{
                                                opacity: 1,
                                                y: revealStep === 0 ? [0, -10, 0] : 0
                                            }}
                                            transition={{
                                                opacity: { duration: 0.3 },
                                                y: revealStep === 0 ? { repeat: Infinity, duration: 2, ease: "easeInOut" } : { duration: 0.3 }
                                            }}
                                        />
                                    );
                                })()}
                            </motion.div>

                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Peeking Stella (CTA for Western Result) - Hanging from Top */}
            <AnimatePresence>
                {showCTA && (
                    <div className="fixed top-0 left-1/2 -translate-x-[200px] md:-translate-x-[360px] z-[100] pointer-events-none flex flex-col items-center">
                        {/* Hanging Character */}
                        <motion.div
                            initial={{ y: -400 }}
                            animate={{ y: -240 }}
                            exit={{ y: -400 }}
                            transition={{ type: "spring", bounce: 0.5, duration: 1 }}
                            className="relative flex flex-col items-center"
                        >
                            <img
                                src={getCharacterImage('west', settings.west, 'wink')}
                                className="w-56 h-56 md:w-80 md:h-80 object-contain drop-shadow-2xl rotate-180 scale-x-[-1] transform origin-center"
                                alt="Peeking Stella"
                            />

                            {/* Speech Bubble - Below the hanging character */}
                            <motion.div
                                initial={{ opacity: 0, scale: 0.8, y: -20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                transition={{ delay: 0.5, type: "spring" }}
                                className="relative mt-2 whitespace-nowrap z-50 -ml-8"
                            >
                                <div className="bg-white text-indigo-900 px-5 py-2.5 rounded-2xl font-bold text-sm md:text-base shadow-xl border-2 border-indigo-200 flex items-center gap-2 relative">
                                    <Sparkles size={16} className="text-indigo-500 fill-indigo-500 animate-pulse" />
                                    <span>제 것도 확인해봐요!</span>
                                    {/* Arrow pointing up to character */}
                                    <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-white rotate-45 border-t border-l border-indigo-200" />
                                </div>
                            </motion.div>
                        </motion.div>
                    </div>
                )}
            </AnimatePresence>

            {/* Background */}
            <div className="absolute inset-0 z-0">
                {/* Dynamic Mode Backgrounds */}
                <div
                    className={`absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ease-in-out ${viewMode === 'eastern' ? 'opacity-30' : 'opacity-0'}`}
                    style={{ backgroundImage: "url('/assets/bg/saju_east.png')" }}
                />
                <div
                    className={`absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ease-in-out ${viewMode === 'western' ? 'opacity-30' : 'opacity-0'}`}
                    style={{ backgroundImage: "url('/assets/bg/saju_west.png')" }}
                />

                {/* Base Gradient Overlay */}
                <div className={`absolute inset-0 bg-gradient-to-b ${bgGradient} opacity-90`} />

                {/* Particle Effect */}
                <ParticleBackground type={viewMode === 'eastern' ? 'eastern' : 'western'} className="opacity-30" />
            </div>

            {/* Top Navigation */}
            <AnimatePresence>
                {revealStep >= 4 && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="relative z-50 p-6 flex justify-end items-center backdrop-blur-sm bg-black/20 border-b border-white/5"
                    >
                        {/* Mode Toggle (Center) */}
                        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-50">
                            <div className="bg-black/40 p-1.5 rounded-full flex gap-1 backdrop-blur-xl border border-white/10 shadow-lg group hover:bg-black/60 transition-all">
                                <motion.div
                                    className={`absolute inset-y-1.5 rounded-full shadow-lg ${viewMode === 'western' ? 'bg-indigo-600/80' : 'bg-amber-600/80'}`}
                                    initial={false}
                                    animate={{
                                        left: viewMode === 'western' ? '6px' : 'calc(50% + 2px)',
                                        width: 'calc(50% - 8px)'
                                    }}
                                    transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
                                />

                                <button
                                    onClick={() => handleModeSwitch('western')}
                                    disabled={isSwitching}
                                    className={`relative z-10 px-6 py-2.5 rounded-full text-sm md:text-base font-bold transition-colors duration-300 flex items-center gap-2 min-w-[120px] md:min-w-[140px] justify-center
                                        ${viewMode === 'western' ? 'text-white' : 'text-white/40 hover:text-white/70'}
                                        ${showCTA ? 'animate-pulse ring-4 ring-yellow-400 shadow-[0_0_40px_rgba(251,191,36,1)] bg-black/80 text-yellow-300' : ''}
                                        ${!showCTA && viewMode === 'eastern' && !revealedHistory.western ? 'ring-1 ring-white/10' : ''}
                                        ${isSwitching ? 'opacity-50 cursor-not-allowed' : ''}
                                    `}
                                >
                                    <Sparkles size={16} className={showCTA ? "text-yellow-300 fill-yellow-300" : ""} />
                                    <span className="font-['GmarketSans']">점성술</span>
                                    {viewMode === 'eastern' && !revealedHistory.western && (
                                        <span className="absolute -top-1 -right-1 flex h-3 w-3">
                                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
                                            <span className="relative inline-flex rounded-full h-3 w-3 bg-yellow-500"></span>
                                        </span>
                                    )}
                                </button>
                                <button
                                    onClick={() => handleModeSwitch('eastern')}
                                    disabled={isSwitching}
                                    className={`relative z-10 px-6 py-2.5 rounded-full text-sm md:text-base font-bold transition-colors duration-300 flex items-center gap-2 min-w-[120px] md:min-w-[140px] justify-center
                                        ${viewMode === 'eastern' ? 'text-white' : 'text-white/40 hover:text-white/70'}
                                        ${isSwitching ? 'opacity-50 cursor-not-allowed' : ''}
                                    `}
                                >
                                    <Scroll size={16} />
                                    <span className="font-['JoseonPalace']">사주팔자</span>
                                </button>
                            </div>
                        </div>

                        {/* Save and Exit Button */}
                        <button
                            onClick={handleSaveAndExitClick}
                            className="flex items-center gap-2 text-white/90 hover:text-white transition-all px-6 py-2 rounded-full bg-amber-600/20 border border-amber-500/30 hover:bg-amber-600/40 hover:scale-105 pointer-events-auto"
                        >
                            <span className="font-bold">{mode === 'history' ? '목록으로' : '저장 및 나가기'}</span>
                            <ArrowLeft size={20} className="rotate-180" />
                        </button>
                    </motion.div>
                )}
            </AnimatePresence>




            {/* Main Content */}
            <div ref={scrollRef} className="relative z-10 flex-1 flex flex-col items-center justify-start p-4 md:p-8 overflow-y-auto scrollbar-hide pb-32">
                <AnimatePresence mode="wait">
                    {isSwitching ? (
                        <motion.div
                            key="switching-loader"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="w-full max-w-5xl h-[60vh] flex flex-col items-center justify-center gap-6"
                        >
                            <div className={`w-12 h-12 border-4 border-white/10 ${viewMode === 'eastern' ? 'border-t-indigo-500' : 'border-t-amber-500'} rounded-full animate-spin`} />
                            <div className="text-center space-y-2">
                                <p className={`text-xl font-bold animate-pulse ${viewMode === 'eastern' ? 'text-indigo-200' : 'text-amber-200'}`}>
                                    {viewMode === 'eastern' ? '별자리의 기운을 정렬하는 중입니다...' : '사주의 흐름을 읽어오는 중입니다...'}
                                </p>
                                <p className="text-white/30 text-sm">잠시만 기다려 주세요</p>
                            </div>
                        </motion.div>
                    ) : (
                        <motion.div
                            key={viewMode}
                            initial={{ opacity: 0, scale: 0.98 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 1.02 }}
                            transition={{ duration: 0.3, ease: "easeOut" }}
                            className="w-full max-w-5xl space-y-8"
                        >
                            {/* 1. Verdict Section (Top Dominant) */}
                            <section className={`relative w-full rounded-3xl overflow-hidden min-h-[300px] flex flex-col items-center justify-center text-center p-10 border border-white/10 shadow-2xl bg-gradient-to-br ${verdict.bg} to-transparent backdrop-blur-md`}>
                                {/* Ambient Glow */}
                                <div className={`absolute inset-0 bg-${verdict.color.split('-')[1]}-500/10 blur-[100px]`} />

                                <motion.div
                                    initial={{ scale: 0.8, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    transition={{ duration: 0.8, ease: "easeOut" }}
                                    className="relative z-10"
                                >
                                    <h2 className="text-xl md:text-2xl text-white/80 mb-4 tracking-widest uppercase">
                                        {displayTitle}
                                    </h2>
                                    <h1 className={`text-6xl md:text-8xl font-black ${verdict.color} mb-2 drop-shadow-[0_0_30px_rgba(255,255,255,0.2)]`}>
                                        {verdict.label}
                                    </h1>
                                    {verdict.subLabel && (
                                        <h3 className="text-2xl md:text-3xl font-bold text-white/80 mb-6">
                                            {verdict.subLabel}
                                        </h3>
                                    )}

                                </motion.div>
                            </section>

                            {/* 1. Daily One-liner Header (Refined for both modes) */}
                            <section className={`bg-white/5 border border-white/10 rounded-3xl p-8 backdrop-blur-md relative overflow-hidden animate-in fade-in slide-in-from-bottom-2 duration-700`}>
                                <div className={`absolute top-0 right-0 w-64 h-64 ${viewMode === 'eastern' ? 'bg-amber-600/20' : 'bg-indigo-600/20'} blur-[80px] rounded-full pointer-events-none`} />

                                <div className="flex flex-col md:flex-row items-center justify-between gap-8 relative z-10">
                                    {/* Left: Date Info */}
                                    <div className="text-center md:text-left min-w-[200px]">

                                        <div className="text-2xl md:text-3xl font-['JoseonPalace'] text-white mb-2">
                                            {new Date().toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })}
                                        </div>
                                        <div className="flex items-center justify-center md:justify-start gap-3">
                                            {viewMode === 'eastern' ? (
                                                <>
                                                    <span className="text-amber-500 font-bold text-lg">병오년(丙午年)</span>
                                                    <span className="text-white/60 text-sm border-l border-white/20 pl-3">붉은 말의 해</span>
                                                </>
                                            ) : (
                                                <>
                                                    <span className="text-indigo-400 font-bold text-lg">Season of {getCurrentSunSign().engName}</span>
                                                    <span className="text-white/60 text-sm border-l border-white/20 pl-3">{getCurrentSunSign().name}의 계절</span>
                                                </>
                                            )}
                                        </div>
                                    </div>

                                    {/* Right: User's Fortune (Zodiac/Sign) */}
                                    <div className="flex-1 bg-black/30 rounded-2xl p-6 border border-white/5 w-full">
                                        {(() => {
                                            if (viewMode === 'eastern') {
                                                const yearJi = eastern?.chart?.year?.ji || '';
                                                const HANJA_TO_ZODIAC: Record<string, string> = {
                                                    "子": "쥐", "丑": "소", "寅": "호랑이", "卯": "토끼",
                                                    "辰": "용", "巳": "뱀", "午": "말", "未": "양",
                                                    "申": "원숭이", "酉": "닭", "戌": "개", "亥": "돼지"
                                                };
                                                const ANIMAL_ICONS: Record<string, string> = {
                                                    "쥐": "🐭", "소": "🐮", "호랑이": "🐯", "토끼": "🐰",
                                                    "용": "🐲", "뱀": "🐍", "말": "🐎", "양": "🐏",
                                                    "원숭이": "🐵", "닭": "🐔", "개": "🐶", "돼지": "🐷"
                                                };
                                                const userZodiac = HANJA_TO_ZODIAC[yearJi] || "띠";
                                                const userIcon = ANIMAL_ICONS[userZodiac] || "✨";

                                                let finalScore = 50;
                                                const rawScore = eastResult.score;
                                                if (typeof rawScore === 'number') finalScore = rawScore;
                                                else {
                                                    const s = String(rawScore).trim();
                                                    if (s === '대길') finalScore = 95;
                                                    else if (s === '중길' || s === '길') finalScore = 85;
                                                    else if (s === '소길') finalScore = 72;
                                                    else if (s === '평') finalScore = 55;
                                                    else if (s === '소흉') finalScore = 37;
                                                    else if (s === '흉') finalScore = 22;
                                                    else if (s === '대흉') finalScore = 7;
                                                    else finalScore = parseFloat(s) || 50;
                                                }
                                                const zodiacFortune = getDailyZodiacFortune(userZodiac, finalScore, fortuneType);
                                                return (
                                                    <div className="flex items-start gap-5">
                                                        <div className="flex flex-col items-center gap-1 shrink-0">
                                                            <span className="text-4xl filter drop-shadow hidden md:block">{userIcon}</span>
                                                            <span className="text-xs text-white/40 uppercase tracking-widest hidden md:block">{userZodiac}</span>
                                                        </div>
                                                        <div className="space-y-2">
                                                            <div className="flex items-center gap-2">
                                                                <span className="md:hidden text-2xl">{userIcon}</span>
                                                                <h5 className="text-amber-400 font-bold text-base md:text-lg">오늘의 <span className="text-white">{userZodiac}띠</span> 운세</h5>
                                                            </div>
                                                            <p className="text-white/90 text-sm md:text-base leading-relaxed font-medium whitespace-pre-wrap">{zodiacFortune}</p>
                                                        </div>
                                                    </div>
                                                );
                                            } else {
                                                const userSign = western?.stats?.main_sign?.name || '별자리';
                                                const SIGN_ICONS: Record<string, string> = {
                                                    "양자리": "♈", "황소자리": "♉", "쌍둥이자리": "♊", "게자리": "♋",
                                                    "사자자리": "♌", "처녀자리": "♍", "천칭자리": "♎", "전갈자리": "♏",
                                                    "사수자리": "♐", "염소자리": "♑", "물병자리": "♒", "물고기자리": "♓"
                                                };
                                                const userIcon = SIGN_ICONS[userSign] || "✨";

                                                let finalScore = 50;
                                                const rawScore = westResult.score;
                                                if (typeof rawScore === 'number') finalScore = rawScore;
                                                else {
                                                    const s = String(rawScore).trim();
                                                    // Map Western labels if needed, or just use score
                                                    finalScore = parseFloat(s) || 50;
                                                }
                                                const signFortune = getDailyWesternFortune(userSign, finalScore, fortuneType);
                                                return (
                                                    <div className="flex items-start gap-5">
                                                        <div className="flex flex-col items-center gap-1 shrink-0">
                                                            <span className="text-4xl filter drop-shadow hidden md:block">{userIcon}</span>
                                                            <span className="text-xs text-white/40 uppercase tracking-widest hidden md:block">{userSign}</span>
                                                        </div>
                                                        <div className="space-y-2">
                                                            <div className="flex items-center gap-2">
                                                                <span className="md:hidden text-2xl">{userIcon}</span>
                                                                <h5 className="text-indigo-400 font-bold text-base md:text-lg">오늘의 <span className="text-white">{userSign}</span> 운세</h5>
                                                            </div>
                                                            <p className="text-white/90 text-sm md:text-base leading-relaxed font-medium whitespace-pre-wrap">{signFortune}</p>
                                                        </div>
                                                    </div>
                                                );
                                            }
                                        })()}
                                    </div>
                                </div>
                            </section>


                            {/* 2. Summary Section (Moved Up) */}
                            <section className="bg-black/40 backdrop-blur-xl border border-white/10 rounded-3xl p-8 relative overflow-hidden">
                                <div className="absolute top-0 left-0 w-2 h-full bg-gradient-to-b from-transparent via-amber-500/50 to-transparent" />
                                <h3 className="text-2xl md:text-3xl font-bold text-white leading-relaxed mb-6 text-center">
                                    "{activeResult.summary}"
                                </h3>
                                {activeResult.keywords && (
                                    <div className="flex flex-wrap gap-2 justify-center">
                                        {activeResult.keywords.map((keyword, idx) => (
                                            <span key={idx} className={`px-4 py-2 bg-white/5 rounded-full text-sm font-medium border border-white/5 ${viewMode === 'eastern' ? 'text-amber-200/80 hover:bg-amber-500/20' : 'text-indigo-200/80 hover:bg-indigo-500/20'} transition-colors`}>
                                                #{keyword}
                                            </span>
                                        ))}
                                    </div>
                                )}
                            </section>

                            {/* 3. Detailed Explanations Section - 3-column "Glass Window" Layout */}
                            <section className="grid grid-cols-3 gap-0 rounded-3xl overflow-hidden border border-white/10 bg-white/5 backdrop-blur-md">
                                {(activeResult.details && activeResult.details.length > 0) ? (
                                    activeResult.details.map((detail, idx) => (
                                        <div key={idx} className={`p-4 md:p-6 flex flex-col justify-start hover:bg-white/5 transition-colors ${idx !== 2 ? 'border-r border-white/10' : ''}`}>
                                            <h4 className={`${viewMode === 'eastern' ? 'text-amber-300' : 'text-indigo-300'} font-bold text-xs md:text-lg mb-2 text-center md:text-left`}>{detail.title}</h4>
                                            <p className="text-white/80 leading-tight md:leading-relaxed text-[10px] md:text-sm text-center md:text-justify overflow-hidden line-clamp-4 md:line-clamp-none">
                                                {detail.description}
                                            </p>
                                        </div>
                                    ))
                                ) : (
                                    /* Fallback for unstructured explanation */
                                    <div className="col-span-3 p-6">
                                        <h4 className={`${viewMode === 'eastern' ? 'text-amber-300' : 'text-indigo-300'} font-bold text-lg mb-2`}>
                                            {viewMode === 'eastern' ? '종합 해석' : 'Astrological Insight'}
                                        </h4>
                                        <p className="text-white/80 leading-relaxed text-sm md:text-base whitespace-pre-line text-justify">
                                            {activeResult.explanation}
                                        </p>
                                    </div>
                                )}
                            </section>

                            <section className="mt-12 animate-in fade-in slide-in-from-bottom-4 duration-700">
                                <div className="flex items-center gap-3 mb-6 px-4 justify-center md:justify-start">
                                    <span className="text-2xl">{viewMode === 'eastern' ? '✨' : '🌙'}</span>
                                    <h3 className={`text-xl font-bold ${viewMode === 'eastern' ? 'text-amber-200' : 'text-indigo-200'}`}>오늘의 행운 요소</h3>
                                </div>

                                <div className="grid grid-cols-3 gap-2 md:gap-4">
                                    {(() => {
                                        const seedKey = viewMode === 'eastern'
                                            ? (eastern?.chart?.year?.ji || "띠")
                                            : (western?.stats?.main_sign?.name || "별자리");

                                        const lucky = getDailyLuckyInfoUnified(viewMode, seedKey);

                                        if (viewMode === 'eastern') {
                                            return (
                                                <>
                                                    {/* Direction */}
                                                    <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md flex flex-col items-center justify-center text-center group hover:bg-white/10 transition-all cursor-default">
                                                        <div className="w-12 h-12 rounded-2xl bg-amber-500/20 flex items-center justify-center mb-3 text-2xl group-hover:scale-110 transition-transform">🧭</div>
                                                        <h4 className="text-amber-200/50 font-bold mb-1 text-xs">행운의 방향</h4>
                                                        <div className="text-lg font-bold text-white">{lucky.direction}</div>
                                                    </div>
                                                    {/* Time */}
                                                    <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md flex flex-col items-center justify-center text-center group hover:bg-white/10 transition-all cursor-default">
                                                        <div className="w-12 h-12 rounded-2xl bg-amber-500/20 flex items-center justify-center mb-3 text-2xl group-hover:scale-110 transition-transform">⏰</div>
                                                        <h4 className="text-amber-200/50 font-bold mb-1 text-xs">행운의 시간</h4>
                                                        <div className="text-lg font-bold text-white">{lucky.time}</div>
                                                    </div>
                                                    {/* Energy */}
                                                    <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md flex flex-col items-center justify-center text-center group hover:bg-white/10 transition-all cursor-default">
                                                        <div className="w-12 h-12 rounded-2xl bg-amber-500/20 flex items-center justify-center mb-3 text-2xl group-hover:scale-110 transition-transform">🧿</div>
                                                        <h4 className="text-amber-200/50 font-bold mb-1 text-xs">행운의 기운</h4>
                                                        <div className="text-sm font-bold text-white leading-tight mt-1">{lucky.energy}</div>
                                                    </div>
                                                </>
                                            );
                                        } else {
                                            return (
                                                <>
                                                    {/* Color */}
                                                    <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md flex flex-col items-center justify-center text-center group hover:bg-white/10 transition-all cursor-default">
                                                        <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center mb-3 text-2xl group-hover:scale-110 transition-transform">🎨</div>
                                                        <h4 className="text-indigo-200/50 font-bold mb-1 text-xs">행운의 색</h4>
                                                        <div className="text-lg font-bold text-white">{lucky.color}</div>
                                                    </div>
                                                    {/* Number */}
                                                    <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md flex flex-col items-center justify-center text-center group hover:bg-white/10 transition-all cursor-default">
                                                        <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center mb-3 text-2xl group-hover:scale-110 transition-transform">🔢</div>
                                                        <h4 className="text-indigo-200/50 font-bold mb-1 text-xs">행운의 숫자</h4>
                                                        <div className="text-2xl font-black text-white">{lucky.number}</div>
                                                    </div>
                                                    {/* Place */}
                                                    <div className="bg-white/5 border border-white/10 rounded-3xl p-6 backdrop-blur-md flex flex-col items-center justify-center text-center group hover:bg-white/10 transition-all cursor-default">
                                                        <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center mb-3 text-2xl group-hover:scale-110 transition-transform">📍</div>
                                                        <h4 className="text-indigo-200/50 font-bold mb-1 text-xs">행운의 장소</h4>
                                                        <div className="text-lg font-bold text-white">{lucky.place}</div>
                                                    </div>
                                                </>
                                            );
                                        }
                                    })()}
                                </div>
                            </section>



                        </motion.div>
                    )}
                </AnimatePresence>
            </div>

            {/* Internal Outro Overlay */}
            <AnimatePresence>
                {showOutro && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[200] flex items-center justify-center p-8 overflow-hidden"
                    >
                        {/* Background Image Layer (Requested by User: Input background) */}
                        <div
                            className="absolute inset-0 bg-cover bg-center brightness-[0.3]"
                            style={{ backgroundImage: "url('/assets/login_page/back3.png')" }}
                        />
                        <div className="absolute inset-0 bg-black/60 shadow-inner" />

                        <div className="relative w-full max-w-4xl flex items-end justify-center gap-8 md:gap-24 h-[60vh]">
                            {/* West Character */}
                            <motion.div
                                initial={{ x: -100, opacity: 0 }}
                                animate={{
                                    x: 0,
                                    opacity: 1,
                                    scale: getDuoOutroScript(settings.east, settings.west)[outroDialogueStep]?.char === 'west' ? 1.1 : 1,
                                    filter: getDuoOutroScript(settings.east, settings.west)[outroDialogueStep]?.char === 'west' ? "none" : "grayscale(80%) brightness(0.7)"
                                }}
                                className="w-[35%] max-w-[220px] relative z-10"
                            >
                                <img src={WestStarImg} className="w-full h-full object-contain drop-shadow-[0_0_50px_rgba(129,140,248,0.3)]" alt="West" />
                                <AnimatePresence mode="wait">
                                    {getDuoOutroScript(settings.east, settings.west)[outroDialogueStep]?.char === 'west' && (
                                        <div className="absolute bottom-[60%] left-1/2 -translate-x-1/2 z-50 min-w-[300px] mb-8">
                                            <AnimatedBubble
                                                theme="indigo"
                                                size="large"
                                                title={WestName}
                                                text={getDuoOutroScript(settings.east, settings.west)[outroDialogueStep]?.text || "..."}
                                            />
                                        </div>
                                    )}
                                </AnimatePresence>
                            </motion.div>

                            {/* East Character */}
                            <motion.div
                                initial={{ x: 100, opacity: 0 }}
                                animate={{
                                    x: 0,
                                    opacity: 1,
                                    scale: getDuoOutroScript(settings.east, settings.west)[outroDialogueStep]?.char === 'east' ? 1.1 : 1,
                                    filter: getDuoOutroScript(settings.east, settings.west)[outroDialogueStep]?.char === 'east' ? "none" : "grayscale(80%) brightness(0.7)"
                                }}
                                className="w-[35%] max-w-[220px] relative z-10"
                            >
                                <img src={EastSajuImg} className="w-full h-full object-contain drop-shadow-[0_0_50px_rgba(251,191,36,0.3)]" alt="East" />
                                <AnimatePresence mode="wait">
                                    {getDuoOutroScript(settings.east, settings.west)[outroDialogueStep]?.char === 'east' && (
                                        <div className="absolute bottom-[60%] left-1/2 -translate-x-1/2 z-50 min-w-[300px] mb-8">
                                            <AnimatedBubble
                                                theme="amber"
                                                size="large"
                                                title={EastName}
                                                text={getDuoOutroScript(settings.east, settings.west)[outroDialogueStep]?.text || "..."}
                                            />
                                        </div>
                                    )}
                                </AnimatePresence>
                            </motion.div>

                            {/* Tap Area */}
                            <div className="absolute inset-0 z-50 cursor-pointer" onClick={handleOutroNext} />

                            <div className="absolute bottom-10 left-1/2 -translate-x-1/2 text-white/40 text-sm animate-pulse tracking-widest">
                                CLICK TO CONTINUE
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Fold Animation Layer (Closing) */}
            <AnimatePresence>
                {showMainTransition && (
                    <motion.div className="fixed inset-0 z-[300] overflow-hidden pointer-events-none">
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 0.8 }}
                            className="absolute inset-0 bg-black"
                        />
                    </motion.div>
                )}
            </AnimatePresence>
        </div >
    );
};

export default TodayFortuneResult;
