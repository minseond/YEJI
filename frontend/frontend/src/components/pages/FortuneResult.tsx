
import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scroll, Headphones, FastForward, LogOut, Sparkles } from 'lucide-react';

import SpotlightSection from '../ui/SpotlightSection';

import ParticleBackground, { type ParticleType } from '../effects/ParticleBackground';

import AnimatedBubble from '../common/AnimatedBubble';

import { type DualFortuneResultV2, type SajuDataV2, type WesternFortuneDataV2 } from '../../data/types';
import {
    EAST_TEN_GODS,
    EAST_PILLARS,
    genEastPillarDialogue,
    genEastElementDialogue,
    genEastYinYangDialogue,
    getEastYinYangSummary,
    genEastTenGodDialogue,
    genEastTenGodSummaryDialogue,
    getTenGodIntro
} from '../../utils/domainMapping';
import { getCharacterImage, getCharacterName, useCharacterSettings, getDuoOutroScript } from '../../utils/character';

// Import New Chart
import FiveElementsPie from '../charts/FiveElementsPie';
import WesternResult from './WesternResult';

interface UserInfo {
    name: string;
    gender: 'male' | 'female' | '';
    year: number;
    month: number;
    day: number;
    time: string;
    solarConstellation: string;
}
interface FortuneResultProps {
    fortuneResult: DualFortuneResultV2;
    userInfo: UserInfo;
    userQuestion: string;
    onBack: () => void;
    onRestart: () => void;
    onSaveAndExit: () => void;
    initialViewMode?: 'eastern' | 'western';
    mode?: 'result' | 'history';
}

const FortuneResult = ({ fortuneResult, userInfo, userQuestion, onBack, onSaveAndExit, initialViewMode = 'eastern', mode = 'result' }: FortuneResultProps) => {

    // Reactive Character Settings
    const settings = useCharacterSettings();
    const EastSajuImg = getCharacterImage('east', settings.east, 'normal');
    const WestStarImg = getCharacterImage('west', settings.west, 'normal');
    const EastName = getCharacterName('east', settings.east);
    const WestName = getCharacterName('west', settings.west);

    // Dashboard State (no intro, go directly to dashboard)
    const [viewMode, setViewMode] = useState<'eastern' | 'western'>(initialViewMode);

    // Progressive Reveal State (Eastern)
    const [revealStep, setRevealStep] = useState((initialViewMode === 'western' || mode === 'history') ? 18 : 0);

    // Outro states
    const [showOutro, setShowOutro] = useState(false);
    const [outroDialogueStep, setOutroDialogueStep] = useState(0);
    const [showMainTransition, setShowMainTransition] = useState(false);
    const [isSwitching] = useState(false);

    // Common UI States
    const [sentenceIndex, setSentenceIndex] = useState(0);
    const [isRevealing, setIsRevealing] = useState(mode === 'history' ? false : initialViewMode === 'eastern');
    const [manualBubbleText, setManualBubbleText] = useState<string | null>(null);
    const [replayEndStep, setReplayEndStep] = useState<number | null>(null);

    const MAX_STEPS = 18;

    const handleModeSwitch = (mode: 'eastern' | 'western') => {
        if (viewMode === mode) return;
        setViewMode(mode);
        if (mode === 'western') setIsRevealing(false);
    };

    const handleOutroNext = (e?: React.MouseEvent) => {
        e?.stopPropagation();
        const outroScript = getDuoOutroScript(settings.east, settings.west);

        if (outroDialogueStep < outroScript.length - 1) {
            setOutroDialogueStep(prev => prev + 1);
        } else {
            // 대화 종료 후 그라데이션 전환 시작
            handleSaveAndExitClick();
        }
    };



    // Validation & Unwrapping
    // @ts-ignore
    const rawEastern = fortuneResult?.eastern;
    // @ts-ignore
    const eastern = (rawEastern?.data) ? rawEastern.data : rawEastern;

    // @ts-ignore
    const rawWestern = fortuneResult?.western;
    // @ts-ignore
    const western = (rawWestern?.data) ? rawWestern.data : rawWestern;

    const isDataValid = eastern && eastern.chart && eastern.stats && eastern.final_verdict;

    // Helper: Particle Type
    const getParticleType = (fortune: SajuDataV2 | WesternFortuneDataV2, type: 'eastern' | 'western'): ParticleType => {
        if (type === 'western') return 'western';

        const saju = fortune as SajuDataV2;
        if (saju.element) {
            const code = saju.element;
            if (code === 'WOOD') return 'wood';
            if (code === 'FIRE') return 'fire';
            if (code === 'EARTH') return 'earth';
            if (code === 'METAL') return 'metal';
            if (code === 'WATER') return 'water';
        }
        return 'eastern';
    };

    // Helper: Bubble Text
    const getBubbleText = () => {
        if (!eastern) return "";
        const saju = eastern;

        switch (revealStep) {
            case 0: return "자, 분석이 끝났습니다. 사주팔자(四柱八字)란 당신이 태어난 생년, 월, 일, 시라는 '네 기둥'과 '여덟 글자'에 담긴 운명의 지도를 뜻하죠. 각 부분을 클릭해서 더 자세한 내용을 확인해보세요.";

            // Year
            case 1: return EAST_PILLARS['year'].context;
            case 2: return genEastPillarDialogue('year', `${saju.chart.year.gan}${saju.chart.year.ji}`);

            // Month
            case 3: return EAST_PILLARS['month'].context;
            case 4: return genEastPillarDialogue('month', `${saju.chart.month.gan}${saju.chart.month.ji}`);

            // Day
            case 5: return EAST_PILLARS['day'].context;
            case 6: return genEastPillarDialogue('day', `${saju.chart.day.gan}${saju.chart.day.ji}`);

            // Hour
            case 7: return EAST_PILLARS['hour'].context;
            case 8: return genEastPillarDialogue('hour', `${saju.chart.hour.gan}${saju.chart.hour.ji}`);

            // Elements
            case 9: return genEastElementDialogue(saju.element, '');

            // Yin Yang
            case 10: return genEastYinYangDialogue(Math.round(saju.stats.yin_yang_ratio.yin), 100 - Math.round(saju.stats.yin_yang_ratio.yin), saju.stats.yin_yang_ratio.summary);

            case 11: return getTenGodIntro();
            case 12: {
                // Top 1
                const sorted = [...saju.stats.ten_gods.gods_list].sort((a, b) => b.percent - a.percent);
                return genEastTenGodDialogue(1, sorted[0].code);
            }
            case 13: {
                // Top 2
                const sorted = [...saju.stats.ten_gods.gods_list].sort((a, b) => b.percent - a.percent);
                return genEastTenGodDialogue(2, sorted[1].code);
            }
            case 14: {
                // Top 3
                const sorted = [...saju.stats.ten_gods.gods_list].sort((a, b) => b.percent - a.percent);
                if (sorted[2].percent > 0) return genEastTenGodDialogue(3, sorted[2].code);
                return "나머지 기운들도 당신의 삶을 다채롭게 채워주고 있습니다.";
            }

            case 15: return genEastTenGodSummaryDialogue(saju.stats.ten_gods.summary);
            case 16: return "자, 이제 사주 전체의 흐름을 갈무리하는 천기누설(天機漏洩)입니다. 당신이 타고난 '강(強)'점은 세상에 나아가는 무기로 삼고, '약(弱)'점은 미리 살펴 조심하는 지혜가 필요합니다. 이 조언들은 단순한 말이 아니라, 당신의 운명을 더욱 단단하게 만드는 전략임을 명심하세요.";

            case 17: return "마지막으로, 당신에게 부족한 기운을 채워줄 귀한 처방전입니다. 이는 단순한 미신이 아니라, 무너진 오행의 균형을 바로잡는 실질적인 개운법(開運法)입니다. 중요한 날에는 이 색상의 옷을 입거나 숫자를 활용하고, 마음이 어지러울 때는 추천 장소에서 기운을 맑게 씻어내 보세요.";
            case 18: return "이제 모든 비밀이 밝혀졌습니다. 자유롭게 둘러보며 서양 별자리 운세도 확인해보세요.";
            default: return "결과를 확인해보세요.";
        }
    };

    // Helper: Split text into sentences (ending with . ! ?)
    const getSentences = (text: string) => {
        if (!text) return [];
        // Match sequences of characters ending with . ! ? or end of string
        // We look for patterns like "...니다." or "...가?"
        // This simple regex handles common Korean sentence endings.
        const matches = text.match(/[^.!?]+[.!?]/g);
        return matches ? matches.map(s => s.trim()) : [text];
    };

    const currentFullText = manualBubbleText || getBubbleText();
    const currentSentences = getSentences(currentFullText);
    const currentBubbleText = currentSentences[sentenceIndex] || currentSentences[0] || "";

    const handleReplayExplain = (targetStep: number, endStep: number, e: React.MouseEvent) => {
        e.stopPropagation();
        setManualBubbleText(null);
        setIsRevealing(true);
        setRevealStep(targetStep);
        setReplayEndStep(endStep);
        setSentenceIndex(0);
    };


    // Handle Reveal Step Auto-Scroll if needed? 
    // Usually handled by the layout ref or just CSS scroll-behavior.

    // --- WESTERN STATE (Lifted) ---
    const [westRevealStep, setWestRevealStep] = useState(0);
    const [westSentenceIndex, setWestSentenceIndex] = useState(0);
    const [westIsRevealing, setWestIsRevealing] = useState(true);
    const [westManualBubbleText, setWestManualBubbleText] = useState<string | null>(null);
    // Exit Transition State
    const [showExitGradient, setShowExitGradient] = useState(false);
    const WEST_MAX_STEPS = 8; // Simplified: Elements, Sign, Modalities, Keywords(3), Summary, Lucky

    const handleSaveAndExitClick = () => {
        // Trigger smooth gradient exit
        setShowExitGradient(true);
        setTimeout(() => {
            if (onSaveAndExit) onSaveAndExit();
        }, 1500); // Wait for animation
    };


    // Unified Next Step Handler (dashboard only, no intro)
    const handleGlobalNext = () => {
        // Dashboard mode only
        if (viewMode === 'western') return;

        if (manualBubbleText) {
            setManualBubbleText(null);
            return;
        }

        if (isRevealing) {
            const fullText = getBubbleText();
            const sentences = getSentences(fullText);

            if (sentenceIndex < sentences.length - 1) {
                setSentenceIndex(prev => prev + 1);
            } else {
                // Move to next step or finish
                if (replayEndStep && revealStep >= replayEndStep) {
                    setIsRevealing(false);
                    setReplayEndStep(null);
                } else if (revealStep === 0) {
                    // End of Intro -> Stop revealing
                    setIsRevealing(false);
                } else if (revealStep < MAX_STEPS) {
                    setRevealStep(prev => prev + 1);
                    setSentenceIndex(0);
                } else {
                    // All steps done
                    setIsRevealing(false);
                }
            }
        }
    }


    // Keyboard Listener (Space)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.code === 'Space') {
                e.preventDefault(); // Prevent scrolling
                handleGlobalNext();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isRevealing, manualBubbleText, revealStep, sentenceIndex, viewMode]);



    if (!isDataValid) {
        return (
            <div className="absolute inset-0 flex items-center justify-center bg-black text-white p-10 flex-col gap-4">
                <h2 className="text-2xl font-bold text-red-500">데이터 오류</h2>
                <p>AI 분석 결과의 형식이 올바르지 않습니다.</p>
                <div className="bg-gray-900 p-4 rounded overflow-auto max-h-[500px] w-full text-xs font-mono text-left">
                    {JSON.stringify(fortuneResult, null, 2)}
                </div>
                <button onClick={onBack} className="px-4 py-2 bg-white/10 rounded-full hover:bg-white/20">돌아가기</button>
            </div>
        );
    }

    return (
        <>
            {/* RESULT PHASE - Swipeable 3D Cards (No intro, direct dashboard) */}
            <AnimatePresence>
                {fortuneResult && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="fixed inset-0 z-[9999] flex flex-col bg-black overflow-hidden"
                    >
                        {/* Background Effects - Using saju_east/west images */}
                        <div className="absolute inset-0 z-0">
                            {/* Background Image */}
                            <div
                                className="absolute inset-0 bg-cover bg-center blur-sm brightness-[0.25]"
                                style={{
                                    backgroundImage: `url('/assets/bg/${viewMode === 'eastern' ? 'saju_east' : 'saju_west'}.png')`
                                }}
                            />
                            {/* Dark overlay */}
                            <div className="absolute inset-0 bg-black/40" />
                            {/* Particle effects on top */}
                            {viewMode === 'eastern' && (
                                <ParticleBackground
                                    type={getParticleType(eastern, 'eastern')}
                                    className="opacity-30"
                                />
                            )}
                        </div>

                        {/* Top Bar removed, moved to bottom */}

                        {/* Top Bar (Restored to Top) */}
                        <div className="absolute top-0 left-0 right-0 p-6 z-[120] flex justify-center items-center bg-gradient-to-b from-black via-black/50 to-transparent pointer-events-none">
                            {/* Original Nav Buttons Removed as requested */}

                            {/* Skip Button - Shared for Both Modes */}
                            {((viewMode === 'eastern' && isRevealing) || (viewMode === 'western' && westIsRevealing)) && (
                                <button
                                    onClick={() => {
                                        if (viewMode === 'eastern') {
                                            setIsRevealing(false);
                                            setRevealStep(MAX_STEPS);
                                            setSentenceIndex(0);
                                        } else {
                                            setWestIsRevealing(false);
                                            setWestRevealStep(WEST_MAX_STEPS);
                                            setWestSentenceIndex(0);
                                        }
                                    }}
                                    className="bg-white/10 hover:bg-white/20 border border-white/20 text-white backdrop-blur-md rounded-full px-5 py-2.5 flex items-center gap-2 transition-all shadow-[0_0_15px_rgba(255,255,255,0.1)] group pointer-events-auto"
                                >
                                    <FastForward size={16} className="text-white group-hover:scale-110 transition-transform" fill="currentColor" />
                                    <span className="text-xs font-bold uppercase tracking-widest">넘기기</span>
                                </button>
                            )}
                        </div>

                        {/* Floating Action Button: Save & Exit / Back */}
                        {/* Floating Action Button: Save & Exit / Back */}
                        <AnimatePresence>
                            {((viewMode === 'eastern' && !isRevealing && !manualBubbleText) ||
                                (viewMode === 'western' && !westIsRevealing && !westManualBubbleText)) && (
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        exit={{ opacity: 0, y: 20 }}
                                        className="absolute bottom-10 left-0 right-0 z-[200] flex justify-center gap-4 pointer-events-none"
                                    >

                                        <button
                                            onClick={handleSaveAndExitClick}
                                            className={`pointer-events-auto flex items-center gap-3 px-8 py-4 ${mode === 'history' ? 'bg-gradient-to-r from-stone-600 to-stone-800 hover:from-stone-500 hover:to-stone-700' : 'bg-gradient-to-r from-amber-600 to-amber-800 hover:from-amber-500 hover:to-amber-700'} text-white rounded-full font-bold shadow-lg transition-all transform hover:scale-105 active:scale-95`}
                                        >
                                            {mode === 'history' ? <LogOut size={20} className="rotate-180" /> : <LogOut size={20} />}
                                            <span className="text-lg tracking-wider">{mode === 'history' ? '히스토리로 돌아가기' : '저장 및 종료'}</span>
                                        </button>
                                    </motion.div>
                                )}
                        </AnimatePresence>

                        {/* Floating Mode Toggle - Bottom Right (Restored) */}
                        {!isRevealing && !manualBubbleText && (
                            <div className="fixed bottom-24 right-8 z-[100] bg-black/40 p-1.5 rounded-full flex gap-1 backdrop-blur-xl border border-white/10 shadow-2xl scale-125 origin-bottom-right group hover:bg-black/60 transition-all">
                                {/* Tab Switcher Background */}
                                <motion.div
                                    className={`absolute inset-y-1.5 rounded-full shadow-lg ${viewMode === 'western' ? 'bg-indigo-600/80' : 'bg-amber-600/80'}`}
                                    initial={false}
                                    animate={{
                                        left: viewMode === 'eastern' ? '6px' : 'calc(50% + 2px)',
                                        width: 'calc(50% - 8px)'
                                    }}
                                    transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
                                />

                                <button
                                    onClick={() => handleModeSwitch('eastern')}
                                    disabled={isSwitching}
                                    className={`relative z-10 px-6 py-2.5 rounded-full text-[10px] font-black uppercase tracking-tighter transition-colors duration-300 flex flex-col items-center min-w-[100px] justify-center leading-none
                                        ${viewMode === 'eastern' ? 'text-white' : 'text-white/40 hover:text-white/70'}
                                        ${isSwitching ? 'opacity-50' : ''}
                                    `}
                                >
                                    <Scroll size={16} className="mb-1" />
                                    <span className="font-['JoseonPalace']">사주팔자</span>
                                </button>
                                <button
                                    onClick={() => handleModeSwitch('western')}
                                    disabled={isSwitching}
                                    className={`relative z-10 px-6 py-2.5 rounded-full text-[10px] font-black uppercase tracking-tighter transition-colors duration-300 flex flex-col items-center min-w-[100px] justify-center leading-none
                                        ${viewMode === 'western' ? 'text-white' : 'text-white/40 hover:text-white/70'}
                                        ${isSwitching ? 'opacity-50' : ''}
                                    `}
                                >
                                    <Sparkles size={16} className="mb-1" />
                                    <span className="font-['GmarketSans']">점성술</span>
                                </button>
                            </div>
                        )}



                        {/* User Metadata - Subtly at bottom left */}
                        <div className="absolute bottom-6 left-10 z-50 text-white/20 text-[10px] uppercase tracking-[0.2em] pointer-events-none">
                            {userInfo.name} • {userQuestion || "Full Destiny Report"}
                        </div>

                        {/* Content Container */}
                        <div className="flex-1 w-full h-full relative z-20">
                            <AnimatePresence mode="wait">
                                {viewMode === 'eastern' && (
                                    <motion.div
                                        key="eastern"
                                        initial={{ opacity: 0, scale: 0.98 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        exit={{ opacity: 0, scale: 1.02 }}
                                        transition={{ duration: 0.3, ease: "easeOut" }}
                                        className="min-w-full h-full flex items-center justify-center p-4 md:p-8 pt-20 relative"
                                    >
                                        <div
                                            className="w-full max-w-6xl h-full max-h-[85vh] bg-[#f4efe4] border border-[#d7ccc8] rounded-3xl overflow-hidden flex flex-col shadow-2xl"
                                        >
                                            <div className="overflow-y-auto h-full p-6 md:p-10 scrollbar-thin scrollbar-thumb-stone-300 scrollbar-track-transparent">
                                                <div className="flex items-center gap-6 mb-8 pb-6 border-b border-stone-300 relative">
                                                    <div className={`w-16 h-16 rounded-2xl bg-stone-200 border border-stone-300 flex items-center justify-center shadow-md shrink-0`}>
                                                        <span className="text-3xl font-serif font-bold text-stone-700">東</span>
                                                    </div>
                                                    <div>
                                                        <div className="flex gap-2 mb-1">


                                                        </div>
                                                        <h2 className="text-3xl md:text-4xl font-['Nanum_Brush_Script'] text-stone-900">
                                                            사주 팔자
                                                        </h2>
                                                    </div>
                                                </div>

                                                <div className="space-y-12 pb-20">


                                                    <SpotlightSection
                                                        isActive={isRevealing && revealStep === 1}
                                                        isDimmed={isRevealing && (revealStep > 8 || revealStep === 0)}
                                                    >
                                                        <div className="flex items-center gap-3 mb-4">
                                                            <h3 className="text-stone-500 text-sm uppercase tracking-widest font-bold">1. 사주 팔자 </h3>
                                                            <button
                                                                onClick={(e) => handleReplayExplain(1, 8, e)}
                                                                className="relative z-10 cursor-pointer px-4 py-2 rounded-full bg-amber-600 hover:bg-amber-700 text-white transition-all shadow-md flex items-center gap-2 transform hover:scale-105"
                                                            >
                                                                <Headphones size={18} fill="currentColor" className="opacity-90" />
                                                                <span className="text-sm font-bold whitespace-nowrap font-eastern">해설 듣기</span>
                                                            </button>
                                                        </div>
                                                        <div className="grid grid-cols-4 gap-2 md:gap-4 p-4 rounded-2xl bg-cover bg-center border border-[#d7ccc8] shadow-inner relative overflow-hidden" style={{ backgroundImage: "url('/assets/bg/hanji.png')" }}>

                                                            {['year', 'month', 'day', 'hour'].map((pillarKey) => {
                                                                const pillarTargetMap: Record<number, string> = {
                                                                    1: 'year', 2: 'year',
                                                                    3: 'month', 4: 'month',
                                                                    5: 'day', 6: 'day',
                                                                    7: 'hour', 8: 'hour'
                                                                };

                                                                const isActive = isRevealing && pillarTargetMap[revealStep] === pillarKey;
                                                                const isDimmed = isRevealing && revealStep >= 1 && revealStep <= 8 && !isActive;

                                                                // @ts-ignore
                                                                const pillar = eastern.chart[pillarKey];
                                                                const labels: Record<string, string> = { year: "년주", month: "월주", day: "일주", hour: "시주" };

                                                                // 한글 발음 매핑
                                                                const GAN_MAP: Record<string, string> = { '甲': '갑', '乙': '을', '丙': '병', '丁': '정', '戊': '무', '己': '기', '庚': '경', '辛': '신', '壬': '임', '癸': '계' };
                                                                const JI_MAP: Record<string, string> = { '子': '자', '丑': '축', '寅': '인', '卯': '묘', '辰': '진', '巳': '사', '午': '오', '未': '미', '申': '신', '酉': '유', '戌': '술', '亥': '해' };

                                                                const ganKorean = GAN_MAP[pillar.gan] || pillar.gan;
                                                                const jiKorean = JI_MAP[pillar.ji] || pillar.ji;

                                                                const getElementColor = (code: string) => {
                                                                    if (code.includes('WOOD')) return 'text-green-700';
                                                                    if (code.includes('FIRE')) return 'text-red-700';
                                                                    if (code.includes('EARTH')) return 'text-amber-700';
                                                                    if (code.includes('METAL')) return 'text-slate-600';
                                                                    if (code.includes('WATER')) return 'text-blue-700';
                                                                    return 'text-stone-800';
                                                                };

                                                                return (
                                                                    <SpotlightSection
                                                                        key={pillarKey}
                                                                        isActive={isActive}
                                                                        isDimmed={isDimmed}
                                                                        className="rounded-xl relative z-10"
                                                                    >
                                                                        <div className={`p-3 rounded-xl flex flex-col items-center gap-2 transition-all duration-300 ${isActive ? 'bg-[#e7e0d3] shadow-md scale-105 ring-2 ring-stone-400/30' : 'bg-transparent'}`}>
                                                                            <span className={`text-[12px] font-eastern ${isActive ? 'text-stone-900 font-bold' : 'text-stone-500'}`}>{labels[pillarKey]}</span>

                                                                            <div className={`text-xl md:text-2xl font-serif font-bold ${getElementColor(pillar.element_code)} flex flex-col items-center leading-none gap-2 py-1`}>
                                                                                {/* 천간 */}
                                                                                <div className="flex items-center gap-2">
                                                                                    <span className="text-xs md:text-sm font-eastern text-stone-400 w-4 text-center">{ganKorean}</span>
                                                                                    <span className="text-2xl md:text-3xl drop-shadow-sm">{pillar.gan}</span>
                                                                                </div>
                                                                                {/* 지지 */}
                                                                                <div className="flex items-center gap-2">
                                                                                    <span className="text-xs md:text-sm font-eastern text-stone-400 w-4 text-center">{jiKorean}</span>
                                                                                    <span className="text-2xl md:text-3xl drop-shadow-sm">{pillar.ji}</span>
                                                                                </div>
                                                                            </div>


                                                                        </div>
                                                                    </SpotlightSection>
                                                                )
                                                            })}
                                                        </div>
                                                    </SpotlightSection>

                                                    <SpotlightSection
                                                        isActive={isRevealing && revealStep >= 9 && revealStep <= 10}
                                                        isDimmed={isRevealing && (revealStep < 9 || revealStep > 10) && revealStep !== 0}
                                                    >
                                                        <div className="flex items-center gap-3 mb-6">
                                                            <h3 className="text-stone-500 text-sm uppercase tracking-widest font-bold">2. 오행 · 음양</h3>
                                                            <button
                                                                onClick={(e) => handleReplayExplain(9, 10, e)}
                                                                className="relative z-10 cursor-pointer px-4 py-2 rounded-full bg-amber-600 hover:bg-amber-700 text-white transition-all shadow-md flex items-center gap-2 transform hover:scale-105"
                                                            >
                                                                <Headphones size={18} fill="currentColor" className="opacity-90" />
                                                                <span className="text-sm font-bold whitespace-nowrap font-eastern">해설 듣기</span>
                                                            </button>
                                                        </div>

                                                        <div className="grid grid-cols-1 md:grid-cols-2 rounded-3xl border border-[#d7ccc8] shadow-md relative bg-cover bg-center" style={{ backgroundImage: "url('/assets/bg/hanji.png')" }}>
                                                            {/* 1. 오행 분포 */}
                                                            <SpotlightSection
                                                                isActive={isRevealing && revealStep === 9}
                                                                isDimmed={isRevealing && revealStep !== 9 && revealStep >= 1 && revealStep <= 15}
                                                                className="p-3 md:p-6 md:py-8 min-h-[300px] h-full flex flex-col items-center justify-start border-b md:border-b-0 md:border-r border-white/10"
                                                            >
                                                                <div className="w-full text-center mb-2 md:mb-4">
                                                                    <span className="text-lg md:text-xl uppercase font-bold text-amber-600 font-eastern">오행 분포</span>
                                                                </div>
                                                                <div className="relative w-full aspect-square max-w-[240px] md:max-w-[280px] flex items-center justify-center">
                                                                    <FiveElementsPie
                                                                        data={eastern.stats.five_elements.elements_list}
                                                                        isActive={!isRevealing || revealStep >= 9}
                                                                    />
                                                                </div>
                                                            </SpotlightSection>

                                                            {/* 2. 음양 밸런스 */}
                                                            <SpotlightSection
                                                                isActive={isRevealing && revealStep === 10}
                                                                isDimmed={isRevealing && revealStep !== 10 && revealStep >= 1 && revealStep <= 15}
                                                                className="p-3 md:p-6 md:py-8 min-h-[300px] h-full flex flex-col justify-start"
                                                            >
                                                                <div className="w-full text-center mb-3 md:mb-6">
                                                                    <span className="text-lg md:text-xl uppercase font-bold text-amber-600 font-eastern">음양 밸런스</span>
                                                                </div>
                                                                <div className="space-y-3 px-1 md:px-2 flex-1 flex flex-col justify-center">
                                                                    <div className="flex justify-between items-end text-xs md:text-sm text-stone-600">
                                                                        <div className="flex flex-col">
                                                                            <span className="text-[8px] md:text-[10px] uppercase text-stone-400">陰(음)</span>
                                                                            <span className="text-sm md:text-xl font-black">{Math.round(eastern.stats.yin_yang_ratio.yin)}%</span>
                                                                        </div>
                                                                        <div className="flex flex-col items-end">
                                                                            <span className="text-[8px] md:text-[10px] uppercase text-stone-400">陽(양)</span>
                                                                            <span className="text-sm md:text-xl font-black">{100 - Math.round(eastern.stats.yin_yang_ratio.yin)}%</span>
                                                                        </div>
                                                                    </div>
                                                                    <div className="h-6 md:h-8 flex rounded-full overflow-hidden bg-stone-200/50 border border-stone-300/50 p-1 shadow-inner relative">
                                                                        <motion.div
                                                                            initial={{ width: 0 }}
                                                                            animate={{ width: `${Math.round(eastern.stats.yin_yang_ratio.yin)}%` }}
                                                                            className="h-full bg-stone-800 rounded-l-full shadow-lg relative z-0"
                                                                        />
                                                                        <motion.div
                                                                            initial={{ width: 0 }}
                                                                            animate={{ width: `${100 - Math.round(eastern.stats.yin_yang_ratio.yin)}%` }}
                                                                            className="h-full bg-white border-l-0 rounded-r-full shadow-lg relative z-0"
                                                                        />
                                                                    </div>
                                                                    <div className="p-3 md:p-4 rounded-xl bg-amber-100/50 border border-amber-600/20 text-center shadow-sm">
                                                                        <p className="text-xs md:text-base leading-snug md:leading-relaxed text-stone-900 font-bold whitespace-pre-wrap font-eastern">
                                                                            {getEastYinYangSummary(Math.round(eastern.stats.yin_yang_ratio.yin), 100 - Math.round(eastern.stats.yin_yang_ratio.yin))}
                                                                        </p>
                                                                    </div>
                                                                </div>
                                                            </SpotlightSection>
                                                        </div>
                                                    </SpotlightSection>

                                                    {/* 3. 십신 분석 */}
                                                    <SpotlightSection
                                                        isActive={isRevealing && revealStep >= 11 && revealStep <= 15}
                                                        isDimmed={isRevealing && (revealStep < 11 || revealStep > 15) && revealStep !== 0}
                                                    >
                                                        <div className="flex items-center gap-3 mb-6">
                                                            <h3 className="text-stone-500 text-sm uppercase tracking-widest font-bold font-eastern">3. 십신 분석</h3>
                                                            <button
                                                                onClick={(e) => handleReplayExplain(11, 15, e)}
                                                                className="relative z-10 cursor-pointer px-4 py-2 rounded-full bg-amber-600 hover:bg-amber-700 text-white transition-all shadow-md flex items-center gap-2 transform hover:scale-105"
                                                            >
                                                                <Headphones size={18} fill="currentColor" className="opacity-90" />
                                                                <span className="text-sm font-bold whitespace-nowrap font-eastern">해설 듣기</span>
                                                            </button>
                                                        </div>

                                                        {/* 십신 분석 컨테이너 */}
                                                        <div className="p-3 md:p-6 flex flex-col rounded-3xl border border-[#d7ccc8] shadow-md bg-cover bg-center" style={{ backgroundImage: "url('/assets/bg/hanji.png')" }}>
                                                            <div className="w-full text-center mb-2 md:mb-4">
                                                                <h4 className="text-sm md:text-lg font-bold text-stone-800 font-eastern">주요 십신 특성</h4>
                                                            </div>
                                                            <div className="grid grid-cols-3 gap-2 md:gap-4 flex-1 items-stretch">
                                                                {eastern.stats.ten_gods.gods_list
                                                                    .sort((a: any, b: any) => b.percent - a.percent)
                                                                    .slice(0, 3)
                                                                    .map((god: any, idx: number) => {
                                                                        const isCurrentGod =
                                                                            (revealStep === 12 && idx === 0) ||
                                                                            (revealStep === 13 && idx === 1) ||
                                                                            (revealStep === 14 && idx === 2);

                                                                        const rankColors = ["text-yellow-600", "text-stone-500", "text-amber-800"];
                                                                        const rankColor = rankColors[idx];
                                                                        const rankLabels = ["第一", "第二", "第三"];
                                                                        const rankLabel = rankLabels[idx];

                                                                        return (
                                                                            <div key={god.code} className={`p-2 md:p-4 rounded-xl border transition-all flex flex-col items-center justify-center text-center ${isCurrentGod ? 'bg-amber-100 border-amber-500 shadow-lg scale-[1.05] ring-1 ring-amber-400' : 'bg-white border-stone-300 shadow-md hover:bg-stone-50'}`}>
                                                                                <span className={`text-lg md:text-xl font-black font-serif mb-1 ${rankColor}`}>{rankLabel}</span>
                                                                                <div className="text-sm md:text-base font-bold text-stone-900 font-eastern leading-tight">{EAST_TEN_GODS[god.code]?.label || god.label}</div>
                                                                            </div>
                                                                        );
                                                                    })}
                                                            </div>
                                                        </div>

                                                        {/* Summary Paragraph (Ten Gods) */}
                                                        <div className="mt-4 p-4 bg-[#e7e0d3] rounded-2xl border border-[#d7ccc8]/50 text-center shadow-sm">
                                                            <p className="text-stone-800 text-base md:text-lg font-bold font-eastern leading-relaxed italic">
                                                                "{eastern.stats.ten_gods.summary}"
                                                            </p>
                                                        </div>
                                                    </SpotlightSection>

                                                    <SpotlightSection
                                                        isActive={isRevealing && revealStep >= 16}
                                                        isDimmed={isRevealing && revealStep >= 1 && revealStep <= MAX_STEPS && revealStep !== 16}
                                                    >
                                                        <div className="flex items-center gap-3 mb-4">
                                                            <h3 className="text-stone-500 text-sm uppercase tracking-widest font-bold">4. 천기누설 </h3>
                                                            <button
                                                                onClick={(e) => handleReplayExplain(16, 16, e)}
                                                                className="relative z-10 cursor-pointer px-4 py-2 rounded-full bg-amber-600 hover:bg-amber-700 text-white transition-all shadow-md flex items-center gap-2 transform hover:scale-105"
                                                            >
                                                                <Headphones size={18} fill="currentColor" className="opacity-90" />
                                                                <span className="text-sm font-bold whitespace-nowrap font-eastern">해설 듣기</span>
                                                            </button>
                                                        </div>
                                                        <div className="p-6 rounded-2xl bg-cover bg-center border border-[#d7ccc8] mb-8 space-y-6 shadow-md relative overflow-hidden" style={{ backgroundImage: "url('/assets/bg/hanji.png')" }}>

                                                            <h4 className="text-stone-900 font-bold mb-4 text-xl text-center relative z-10 font-serif">{eastern.final_verdict.summary}</h4>

                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative z-10">
                                                                <div className="p-4 bg-indigo-50 border border-indigo-100 rounded-xl shadow-sm">
                                                                    <div className="text-md text-indigo-800 font-bold mb-2 uppercase tracking-wider">강(強)</div>
                                                                    <p className="text-stone-800 text-base leading-relaxed font-bold font-eastern">
                                                                        {eastern.final_verdict.strength}
                                                                    </p>
                                                                </div>
                                                                <div className="p-4 bg-red-50 border border-red-100 rounded-xl shadow-sm">
                                                                    <div className="text-md text-red-800 font-bold mb-2 uppercase tracking-wider">약(弱)</div>
                                                                    <p className="text-stone-800 text-base leading-relaxed font-bold font-eastern">
                                                                        {eastern.final_verdict.weakness}
                                                                    </p>
                                                                </div>
                                                            </div>

                                                            <div className="p-4 bg-[#e7e0d3] border border-[#d7ccc8] rounded-xl mt-4 relative z-10">
                                                                <div className="text-sm text-stone-600 font-bold mb-2 uppercase tracking-wider text-center">조언(勸告)</div>
                                                                <p className="text-stone-900 text-xl leading-relaxed font-eastern whitespace-pre-wrap text-center font-bold">
                                                                    {eastern.final_verdict.advice}
                                                                </p>
                                                            </div>
                                                        </div>
                                                    </SpotlightSection>

                                                    {eastern.lucky && (
                                                        <SpotlightSection
                                                            isActive={isRevealing && revealStep === 17}
                                                            isDimmed={isRevealing && revealStep >= 1 && revealStep <= MAX_STEPS && revealStep !== 17}
                                                        >
                                                            <div className="flex items-center gap-3 mb-4">
                                                                <h3 className="text-stone-500 text-sm uppercase tracking-widest font-bold">5. 행운의 요소 </h3>
                                                                <button
                                                                    onClick={(e) => handleReplayExplain(17, 17, e)}
                                                                    className="relative z-10 cursor-pointer px-4 py-2 rounded-full bg-amber-600 hover:bg-amber-700 text-white transition-all shadow-md flex items-center gap-2 transform hover:scale-105"
                                                                >
                                                                    <Headphones size={18} fill="currentColor" className="opacity-90" />
                                                                    <span className="text-sm font-bold whitespace-nowrap font-eastern">해설 듣기</span>
                                                                </button>
                                                            </div>
                                                            <div className="p-6 rounded-2xl bg-cover bg-center border border-[#d7ccc8] grid grid-cols-3 gap-4 text-center shadow-inner relative overflow-hidden" style={{ backgroundImage: "url('/assets/bg/hanji.png')" }}>

                                                                <div className="p-4 rounded-xl bg-white/50 border border-white/40 shadow-sm relative z-10">
                                                                    <div className="text-xl font-serif text-stone-600 font-bold mb-1">색(色)</div>
                                                                    <div className="text-lg font-bold text-stone-800">{eastern.lucky.color}</div>
                                                                </div>
                                                                <div className="p-4 rounded-xl bg-white/50 border border-white/40 shadow-sm relative z-10">
                                                                    <div className="text-xl font-serif text-stone-600 font-bold mb-1">수(數)</div>
                                                                    <div className="text-lg font-bold text-stone-800">{eastern.lucky.number}</div>
                                                                </div>
                                                                <div className="p-4 rounded-xl bg-white/50 border border-white/40 shadow-sm relative z-10">
                                                                    <div className="text-xl font-serif text-stone-600 font-bold mb-1">장소(地)</div>
                                                                    <div className="text-lg font-bold text-stone-800">{eastern.lucky.place}</div>
                                                                </div>
                                                            </div>
                                                        </SpotlightSection>
                                                    )}
                                                </div>
                                                <div className="h-20" />
                                            </div>
                                        </div>

                                        <AnimatePresence>
                                            {(isRevealing || manualBubbleText) && (
                                                <motion.div
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    exit={{ opacity: 0 }}
                                                    className="absolute inset-0 z-50 pointer-events-none"
                                                >
                                                    <div
                                                        className="absolute inset-0 pointer-events-auto cursor-pointer"
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            if (manualBubbleText) {
                                                                setManualBubbleText(null);
                                                            } else if (isRevealing) {
                                                                const sentences = getSentences(getBubbleText());
                                                                if (sentenceIndex < sentences.length - 1) {
                                                                    setSentenceIndex(prev => prev + 1);
                                                                } else if (replayEndStep && revealStep >= replayEndStep) {
                                                                    setIsRevealing(false);
                                                                    setReplayEndStep(null);
                                                                } else if (revealStep === 0) {
                                                                    setIsRevealing(false);
                                                                } else if (revealStep < MAX_STEPS) {
                                                                    setRevealStep(prev => prev + 1);
                                                                    setSentenceIndex(0);
                                                                } else {
                                                                    setIsRevealing(false);
                                                                    setSentenceIndex(0);
                                                                }
                                                            }
                                                        }}
                                                    />
                                                    <motion.div
                                                        key="east-char-bubble"
                                                        initial={{ x: 100, opacity: 0 }}
                                                        animate={{ x: 0, opacity: 1 }}
                                                        exit={{ x: 100, opacity: 0 }}
                                                        className="absolute bottom-[-50px] right-[-50px] md:bottom-[-20px] md:right-[-20px] w-[150px] md:w-[200px] z-10 pointer-events-none"
                                                    >
                                                        <img src={EastSajuImg} className="w-full h-full object-contain scale-x-100" />
                                                    </motion.div>
                                                    <motion.div
                                                        className="absolute z-20 pointer-events-none"
                                                        initial={false}
                                                        animate={{
                                                            // Dynamic positioning
                                                            top: revealStep === 0 ? '50%' :
                                                                (revealStep >= 1 && revealStep <= 8) ? '63%' :
                                                                    (revealStep === 9 || revealStep === 10) ? '35%' :
                                                                        (revealStep >= 11 && revealStep <= 15) ? '65%' :
                                                                            (revealStep === 16) ? '69%' :
                                                                                (revealStep === 17) ? '65%' :
                                                                                    '50%',
                                                            left: (revealStep >= 1 && revealStep <= 2) ? '20%' :
                                                                (revealStep >= 3 && revealStep <= 4) ? '35%' :
                                                                    (revealStep >= 5 && revealStep <= 6) ? '50%' :
                                                                        (revealStep >= 7 && revealStep <= 8) ? '65%' :
                                                                            (revealStep === 9) ? '55%' :
                                                                                (revealStep === 10) ? '18%' :
                                                                                    '12%',
                                                            x: (revealStep >= 1 && revealStep <= 8) ? '-50%' : '0%',
                                                        }}
                                                        transition={{ type: "spring", stiffness: 80, damping: 20 }}
                                                    >
                                                        <AnimatedBubble
                                                            theme="amber"
                                                            size="large"
                                                            title={EastName}
                                                            text={currentBubbleText}
                                                        />
                                                    </motion.div>
                                                    <div className="absolute bottom-10 left-0 right-0 text-center pointer-events-none">
                                                        <span className="bg-black/50 px-4 py-2 rounded-full text-white/50 text-xs animate-pulse backdrop-blur-md">
                                                            {manualBubbleText ? "닫기" : revealStep < MAX_STEPS ? "탭하여 계속 설명 듣기" : "탭하여 완료"}
                                                        </span>
                                                    </div>
                                                </motion.div>
                                            )}
                                        </AnimatePresence>

                                        {/* Navigation Button to West */}
                                        {!isRevealing && !manualBubbleText && (
                                            <motion.div
                                                initial={{ opacity: 0, y: 20 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                className="absolute bottom-8 right-8 z-[60]"
                                            >

                                            </motion.div>
                                        )}

                                    </motion.div>
                                )}

                                {/* Slide 2: Western (Astrology) */}
                                {viewMode === 'western' && western && (
                                    <motion.div
                                        key="western"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.5 }}
                                        className="w-full h-full flex items-center justify-center relative"
                                    >
                                        <WesternResult
                                            data={western}
                                            isActive={viewMode === 'western'}
                                            revealStep={westRevealStep}
                                            setRevealStep={setWestRevealStep}
                                            sentenceIndex={westSentenceIndex}
                                            setSentenceIndex={setWestSentenceIndex}
                                            isRevealing={westIsRevealing}
                                            setIsRevealing={setWestIsRevealing}
                                            manualBubbleText={westManualBubbleText}
                                            setManualBubbleText={setWestManualBubbleText}
                                            MAX_STEPS={WEST_MAX_STEPS}
                                        />


                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>


            {/* Internal Outro Overlay */}
            <AnimatePresence>
                {showOutro && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[10000] flex items-center justify-center p-8 overflow-hidden"
                    >
                        {/* Background Image Layer (Requested by User: Input background) */}
                        <div
                            className="absolute inset-0 bg-cover bg-center brightness-[0.3]"
                            style={{ backgroundImage: "url('/assets/login_page/back3.png')" }}
                        />
                        <div className="absolute inset-0 bg-black/60 shadow-inner" />
                        <div className="relative w-full max-w-4xl flex items-end justify-center gap-8 md:gap-70 h-[65vh]">
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
                            initial={{ scaleX: 0 }}
                            animate={{ scaleX: 1 }}
                            transition={{ duration: 0.8, ease: [0.43, 0.13, 0.23, 0.96] }}
                            className="absolute inset-0 bg-black origin-center"
                        />
                    </motion.div>
                )}
            </AnimatePresence>
            {/* Exit Gradient Transition */}
            <AnimatePresence>
                {showExitGradient && (
                    <motion.div
                        className="fixed inset-0 z-[10000] pointer-events-none flex flex-col items-center justify-center"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 1.0, ease: "easeInOut" }}
                    >
                        {/* Multi-layer gradient for richness */}
                        <div className="absolute inset-0 bg-gradient-to-b from-black via-slate-900 to-black opacity-90" />
                        <motion.div
                            className="absolute inset-0 bg-gradient-to-r from-indigo-900/50 via-purple-900/50 to-amber-900/50 mix-blend-overlay"
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            transition={{ duration: 1.5 }}
                        />

                        {/* Optional: Closing Text or subtle effect */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5, duration: 0.8 }}
                            className="relative z-10 text-white/50 text-xl font-light tracking-[0.5em] font-serif"
                        >
                            운명의 흐름을 마음에 담습니다...
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </>
    );
};

export default FortuneResult;
