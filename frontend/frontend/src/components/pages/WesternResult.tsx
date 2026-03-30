import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Headphones, CheckCircle2, Star, Moon, Sun } from 'lucide-react';

import SpotlightSection from '../ui/SpotlightSection';

import FourElementsVisual from '../charts/FourElementsVisual';
import ConstellationViewer from '../features/ConstellationViewer';
import AnimatedBubble from '../common/AnimatedBubble';

const ZODIAC_ENGLISH_MAP: Record<string, string> = {
    '물병자리': 'Aquarius',
    '물고기자리': 'Pisces',
    '양자리': 'Aries',
    '황소자리': 'Taurus',
    '쌍둥이자리': 'Gemini',
    '게자리': 'Cancer',
    '사자자리': 'Leo',
    '처녀자리': 'Virgo',
    '천칭자리': 'Libra',
    '전갈자리': 'Scorpio',
    '사수자리': 'Sagittarius',
    '염소자리': 'Capricorn',
};

import { THEMES, type WesternFortuneDataV2 } from '../../data/types';
import {
    WEST_ELEMENTS,
    WEST_MODALITIES,
    genWestElementDialogue,
    genWestModalityDialogue,
    genWestKeywordDialogue,
    getWestZodiacDialogue,
    getWestZodiacDesc,
    WEST_KEYWORDS
} from '../../utils/domainMapping';
import { getCharacterImage, getCharacterName, useCharacterSettings } from '../../utils/character';

import ParticleBackground, { type ParticleType } from '../effects/ParticleBackground';

interface WesternResultProps {
    data: WesternFortuneDataV2;
    isActive: boolean;
    // Lifted State Methods
    revealStep: number;
    setRevealStep: React.Dispatch<React.SetStateAction<number>>;
    sentenceIndex: number;
    setSentenceIndex: React.Dispatch<React.SetStateAction<number>>;
    isRevealing: boolean;
    setIsRevealing: React.Dispatch<React.SetStateAction<boolean>>;
    manualBubbleText: string | null;
    setManualBubbleText: React.Dispatch<React.SetStateAction<string | null>>;
    MAX_STEPS: number;
}

// Helper: Keyword Icon Mapper
const getKeywordIcon = (code: string | undefined) => {
    if (!code) return <Star size={16} />;
    if (code.includes('EMPATHY') || code.includes('HEAL')) return <CheckCircle2 size={16} />;
    if (code.includes('INTUITION') || code.includes('SPIRIT')) return <Sparkles size={16} />;
    if (code.includes('IMAGINATION') || code.includes('DREAM')) return <Moon size={16} />;
    if (code.includes('LEAD') || code.includes('SUN')) return <Sun size={16} />;
    return <Star size={16} />;
};

const WesternResult = ({
    data,
    isActive,
    revealStep,
    setRevealStep,
    sentenceIndex,
    setSentenceIndex,
    isRevealing,
    setIsRevealing,
    manualBubbleText,
    setManualBubbleText,
    MAX_STEPS
}: WesternResultProps) => {

    // Reactive Character Settings
    const settings = useCharacterSettings();
    const WestStarImg = getCharacterImage('west', settings.west, 'normal');
    const WestName = getCharacterName('west', settings.west);

    const [replayEndStep, setReplayEndStep] = useState<number | null>(null);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Scroll to top on mount
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTo(0, 0);
        }
    }, []);

    // Determine particle type based on dominant element
    const getParticleType = (): ParticleType => {
        if (!data || !data.stats || !data.stats.element_4_distribution) return 'western';

        // Find dominant element
        const dominant = [...data.stats.element_4_distribution].sort((a, b) => b.percent - a.percent)[0];

        switch (dominant.code) {
            case 'FIRE': return 'fire';
            case 'WATER': return 'water';
            case 'EARTH': return 'earth';
            case 'AIR': return 'air';
            default: return 'western';
        }
    };

    const particleType = getParticleType();



    // Validation
    const isDataValid = data &&
        data.stats &&
        data.stats.element_4_distribution &&
        data.stats.modality_3_distribution &&
        data.stats.keywords &&
        data.fortune_content &&
        data.fortune_content.detailed_analysis &&
        data.lucky;

    if (!isDataValid) {
        return (
            <div className="absolute inset-0 flex items-center justify-center bg-black text-white p-10 flex-col gap-4 z-50">
                <h2 className="text-2xl font-bold text-red-500">서양 데이터 오류</h2>
                <p>AI 서양 분석 결과의 형식이 올바르지 않습니다.</p>
                <div className="bg-gray-900 p-4 rounded overflow-auto max-h-[500px] w-full text-xs font-mono text-left">
                    {JSON.stringify(data, null, 2)}
                </div>
            </div>
        );
    }

    // Phase 1: Elements (Steps 1-4)
    // Phase 2: Modalities (Steps 5-7)
    // Phase 3: Keywords (Steps 8-10)
    // Phase 4: Summary (Step 11)
    // Phase 5: Lucky (Step 12)

    // Helper: Split text into sentences
    const getSentences = (text: string) => {
        if (!text) return [];
        const matches = text.match(/[^.!?]+[.!?]/g);
        return matches ? matches.map(s => s.trim()) : [text];
    };

    // Helper: Bubble Text
    const getBubbleText = () => {
        if (!data) return "";

        // 0. Intro
        if (revealStep === 0) {
            return "지금부터 서양 점성술의 시각으로 당신의 운명을 바라보겠습니다.각 항목을 클릭하여 상세한 내용을 직접 확인해보세요.";
        }

        switch (revealStep) {
            // 1. Elements (4원소) - 통합 및 간소화
            case 1: {
                // 가장 강한 원소 설명
                return genWestElementDialogue([...data.stats.element_4_distribution].sort((a, b) => b.percent - a.percent)[0].code, "");
            }

            // 2. Main Sign (별자리) - 원소 다음으로 배치
            case 2: {
                const signName = data.stats?.main_sign?.name || '';
                return getWestZodiacDialogue(signName);
            }

            // 3. Modalities (3양태)
            case 3: return genWestModalityDialogue([...data.stats.modality_3_distribution].sort((a, b) => b.percent - a.percent)[0].code);

            // 4. Keywords (키워드)
            case 4: return "당신의 차트에서 발견된 핵심 키워드들을 살펴볼까요?";
            case 5: return genWestKeywordDialogue(data.stats.keywords[0]?.label, "");
            case 6: return `${data.stats.keywords_summary}`;

            // 5. Summary & Advice
            case 7: return "드디어 별들이 속삭이는 마지막 메시지에요. 당신의 차트에 담긴 수많은 별들의 이야기를 모아, 인생의 거대한 테마를 정리해 보았답니다. 특히 '별들의조언' 는 지금 당신에게 꼭 필요한 별들의 지혜이니 마음에 깊이 새겨보세요.";

            // 6. Lucky Items
            case 8: return "마지막으로, 당신을 지켜주는 별들과 공명하는 행운의 아이템들이에요! 이 색상은 당신의 오라(Aura)를 더욱 빛나게 하고, 숫자는 중요한 순간에 행운을 불러올 거예요. 마음이 지칠 땐 추천 장소를 찾아가 별들의 에너지를 가득 채워보세요.";

            default: return "분석이 끝났어요! 동양과 서양의 지혜가 당신에게 도움이 되길 바라요!";
        }
    };

    const currentFullText = manualBubbleText || getBubbleText();
    const currentSentences = getSentences(currentFullText);
    const currentBubbleText = currentSentences[sentenceIndex] || currentSentences[0] || "";

    const handleReplayExplain = (targetStep: number, endStep: number, e?: React.MouseEvent) => {
        e?.stopPropagation();
        setManualBubbleText(null);
        setIsRevealing(true);
        setRevealStep(targetStep);
        setReplayEndStep(endStep);
        setSentenceIndex(0);
    };

    // Interaction Handler
    useEffect(() => {
        if (!isActive) return;

        const handleKeyPress = (e: KeyboardEvent) => {
            if (e.code === 'Space') {
                e.preventDefault();
                if (manualBubbleText) {
                    setManualBubbleText(null);
                    return;
                }

                if (isRevealing) {
                    if (sentenceIndex < currentSentences.length - 1) {
                        setSentenceIndex(prev => prev + 1);
                    } else if (replayEndStep && revealStep >= replayEndStep) {
                        setIsRevealing(false);
                        setReplayEndStep(null);
                    } else if (revealStep === 0) {
                        // End of Intro -> Stop revealing
                        setIsRevealing(false);
                    } else if (revealStep < MAX_STEPS) {
                        setRevealStep(prev => prev + 1);
                        setSentenceIndex(0);
                    } else {
                        setIsRevealing(false);
                    }
                }
            }
        };

        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, [isActive, isRevealing, revealStep, sentenceIndex, manualBubbleText, currentSentences]);

    return (
        <div className="min-w-full h-full flex items-center justify-center p-4 md:p-8 pt-20 relative">
            {/* Ambient Background Particles based on Element */}
            <ParticleBackground type={particleType} opacity={0.6} className="z-0" />

            <div
                className="w-full max-w-6xl h-full max-h-[85vh] bg-black/40 backdrop-blur-xl border border-white/10 rounded-3xl overflow-hidden flex flex-col shadow-2xl relative"
            >
                {/* Background Layer */}
                <div
                    className="absolute inset-0 z-0 bg-cover bg-center pointer-events-none transition-all duration-500"
                    style={{ backgroundImage: "url('/assets/bg/universe.jpg')" }}
                />

                {/* Vignette Overlay */}
                <div className="absolute inset-0 z-0 pointer-events-none rounded-3xl shadow-[inset_0_0_60px_rgba(0,0,0,0.8)]" />

                <div ref={scrollRef} className="relative z-10 overflow-y-auto h-full p-6 md:p-10 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                    {/* Header: Main Sign */}
                    <div className="flex items-center gap-6 mb-8 pb-6 border-b border-white/5 relative">
                        <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${THEMES['total'].bgFrom} to-transparent border border-white/10 flex items-center justify-center shadow-lg shrink-0`}>
                            <Sparkles size={28} className="text-yellow-400 drop-shadow-[0_0_8px_rgba(250,204,21,0.5)]" />
                        </div>
                        <div>
                            <h2 className={`text-3xl md:text-4xl font-['Nanum_Brush_Script'] ${THEMES['total'].primary}`}>
                                점성술
                            </h2>
                        </div>
                    </div>

                    <div className="space-y-12 pb-20">
                        <SpotlightSection
                            isActive={isRevealing && revealStep >= 1 && revealStep <= 2}
                            isDimmed={isRevealing && (revealStep > 2 || revealStep === 0)}
                        >
                            <div className="flex items-center gap-3 mb-6">
                                <h3 className="text-white font-bold text-lg uppercase tracking-widest drop-shadow-md">1. 4원소 · 별자리</h3>
                                <button
                                    onClick={(e) => handleReplayExplain(1, 2, e)}
                                    className="relative z-10 cursor-pointer px-4 py-2 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white transition-all shadow-md flex items-center gap-2 transform hover:scale-105"
                                >
                                    <Headphones size={18} fill="currentColor" className="opacity-90" />
                                    <span className="text-sm font-bold whitespace-nowrap">해설 듣기</span>
                                </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 rounded-3xl border border-white/10 bg-black/80 shadow-inner relative">
                                {/* 1. 4원소 분포 */}
                                <SpotlightSection
                                    isActive={isRevealing && revealStep === 1}
                                    isDimmed={isRevealing && revealStep !== 1 && revealStep >= 1 && revealStep <= 2}
                                    className={`p-3 md:p-6 flex flex-col items-center border-b md:border-b-0 md:border-r border-white/10 h-full relative ${revealStep === 1 ? 'z-20' : 'z-0'}`}
                                >
                                    <div className="text-center mb-2 md:mb-4">
                                        <span className="text-[10px] text-indigo-300 font-bold uppercase tracking-widest opacity-60">Elements</span>
                                        <h4 className="text-sm md:text-lg font-bold text-white">4원소 분석</h4>
                                    </div>
                                    <div className="relative w-full min-h-[360px] h-full flex items-center justify-center p-4">
                                        <FourElementsVisual
                                            data={data.stats.element_4_distribution}
                                            isActive={!isRevealing || revealStep >= 1}
                                        />
                                    </div>
                                </SpotlightSection>

                                {/* 2. 태양 별자리 */}
                                <SpotlightSection
                                    isActive={isRevealing && revealStep === 2}
                                    isDimmed={isRevealing && revealStep !== 2 && revealStep >= 1 && revealStep <= 2}
                                    className={`p-3 md:p-6 flex flex-col items-center justify-center h-full relative ${revealStep === 2 ? 'z-20' : 'z-0'}`}
                                >
                                    <div className="text-center mb-4 md:mb-8">
                                        <span className="text-[10px] text-indigo-300 font-bold uppercase tracking-widest opacity-60">Sun Sign</span>
                                        <h4 className="text-sm md:text-lg font-bold text-white">태양 별자리</h4>
                                    </div>
                                    <div className="flex-1 flex flex-col items-center justify-center space-y-4 w-full">
                                        <div className="w-full max-w-[280px] aspect-square relative flex items-center justify-center">
                                            <ConstellationViewer zodiacName={ZODIAC_ENGLISH_MAP[data.stats.main_sign.name] || 'Aries'} />
                                        </div>
                                        <div className="text-center w-full px-4">
                                            <h5 className="text-lg md:text-2xl font-['Nanum_Brush_Script'] text-white mb-2 md:mb-3">{data.stats.main_sign.name}</h5>
                                            <div className="text-xs md:text-base text-white/80 bg-black/40 p-3 md:p-4 rounded-xl border border-white/10 max-w-[280px] md:max-w-[360px] mx-auto leading-relaxed md:leading-loose">
                                                {getWestZodiacDesc(data.stats.main_sign.name)}
                                            </div>
                                        </div>
                                    </div>
                                </SpotlightSection>
                            </div>
                        </SpotlightSection>

                        {/* 2. 양태 분석 (Separated) */}
                        <SpotlightSection
                            isActive={isRevealing && revealStep === 3}
                            isDimmed={isRevealing && (revealStep < 3 || revealStep > 3) && revealStep !== 0}
                        >
                            <div className="flex items-center gap-3 mb-6">
                                <h3 className="text-white font-bold text-lg uppercase tracking-widest drop-shadow-md">2. 양태 분석 (Modalities)</h3>
                                <button
                                    onClick={(e) => handleReplayExplain(3, 3, e)}
                                    className="relative z-10 cursor-pointer px-4 py-2 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white transition-all shadow-md flex items-center gap-2 transform hover:scale-105"
                                >
                                    <Headphones size={18} fill="currentColor" className="opacity-90" />
                                    <span className="text-sm font-bold whitespace-nowrap">해설 듣기</span>
                                </button>
                            </div>

                            <SpotlightSection
                                isActive={true}
                                isDimmed={false}
                                className="p-4 md:p-8 flex flex-col rounded-3xl border border-white/10 bg-black/80 shadow-inner relative overflow-hidden"
                            >
                                <div className="text-center mb-4 md:mb-8">
                                    <span className="text-xs text-indigo-300 font-bold uppercase tracking-widest opacity-60">Modalities Distribution</span>
                                    <h4 className="text-lg md:text-xl font-bold text-white">행동 양식 분포</h4>
                                </div>
                                <div className="grid grid-cols-3 gap-4 md:gap-8 max-w-3xl mx-auto w-full">
                                    {data.stats.modality_3_distribution.map((mod, idx) => (
                                        <div
                                            key={idx}
                                            className="flex flex-col items-center justify-center p-3 md:p-6 rounded-2xl bg-black/40 border border-white/10 relative overflow-hidden group hover:bg-white/5 transition-all"
                                        >
                                            <span className="text-[10px] md:text-sm font-bold text-white/60 mb-1 md:mb-2 uppercase tracking-wider">{mod.label}</span>
                                            <span className="text-xl md:text-3xl font-black text-indigo-400 drop-shadow-[0_0_10px_rgba(129,140,248,0.5)]">{mod.percent}%</span>
                                            <div className="absolute inset-x-0 bottom-0 h-1 bg-indigo-500/20">
                                                <div className="h-full bg-indigo-500" style={{ width: `${mod.percent}%` }} />
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <div className="mt-6 md:mt-8 p-4 md:p-6 bg-indigo-900/20 rounded-2xl border border-indigo-500/20 max-w-2xl mx-auto w-full">
                                    <p className="text-sm md:text-base text-white/90 leading-relaxed text-center font-western">
                                        "{data.stats.modality_summary}"
                                    </p>
                                </div>
                            </SpotlightSection>
                        </SpotlightSection>

                        {/* 3. Keywords Section */}
                        <SpotlightSection
                            isActive={isRevealing && revealStep >= 4 && revealStep <= 6}
                            isDimmed={isRevealing && (revealStep < 4 || revealStep > 6) && revealStep !== 0}
                        >
                            <div className="flex items-center gap-3 mb-4">
                                <h3 className="text-white font-bold text-lg uppercase tracking-widest drop-shadow-md">3. 핵심 테마</h3>
                                <button
                                    onClick={(e) => handleReplayExplain(4, 6, e)}
                                    className="relative z-10 cursor-pointer px-4 py-2 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white transition-all shadow-md flex items-center gap-2 transform hover:scale-105"
                                >
                                    <Headphones size={18} fill="currentColor" className="opacity-90" />
                                    <span className="text-sm font-bold whitespace-nowrap">해설 듣기</span>
                                </button>
                            </div>
                            <div className="rounded-2xl p-6 border border-white/5 grid grid-cols-1 md:grid-cols-2 gap-6 items-center bg-black/80 shadow-inner relative overflow-hidden">
                                <div className="grid grid-cols-2 gap-3">
                                    {data.stats.keywords.map((kw, idx) => (
                                        <div
                                            key={idx}
                                            className={`p-3 rounded-lg flex items-center gap-3 border transition-all ${revealStep === 5 && idx === 0 ? 'bg-indigo-500/30 border-indigo-500 ring-2 ring-indigo-500/50' : 'bg-black/20 border-white/5'
                                                }`}
                                        >
                                            <div className="text-indigo-400">
                                                {getKeywordIcon(kw.code)}
                                            </div>
                                            <div>
                                                <div className="text-xs text-white/40 uppercase">{kw.code}</div>
                                                <div className="font-bold text-white">{WEST_KEYWORDS[kw.code]?.label || kw.label}</div>
                                                <div className="text-[10px] text-white/60 mt-1 break-keep leading-tight">
                                                    {WEST_KEYWORDS[kw.code]?.desc}
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                                <div className={`p-4 rounded-xl border transition-colors ${revealStep === 6 ? 'bg-indigo-500/10 border-indigo-500/30' : 'bg-white/5 border-white/5'}`}>
                                    <div className="text-sm text-white font-bold mb-2 uppercase tracking-wider text-center drop-shadow-md">해석</div>
                                    <p className="text-white/90 text-lg leading-relaxed font-western text-center">
                                        "{data.stats.keywords_summary}"
                                    </p>
                                </div>
                            </div>
                        </SpotlightSection>

                        {/* 4. Final Summary */}
                        <SpotlightSection
                            isActive={isRevealing && revealStep === 7}
                            isDimmed={isRevealing && revealStep !== 7 && revealStep !== 0}
                        >
                            <div className="flex items-center gap-3 mb-4">
                                <h3 className="text-white font-bold text-lg uppercase tracking-widest drop-shadow-md">4. 별들의 지혜</h3>
                                <button
                                    onClick={(e) => handleReplayExplain(7, 7, e)}
                                    className="relative z-10 cursor-pointer px-4 py-2 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white transition-all shadow-md flex items-center gap-2 transform hover:scale-105"
                                >
                                    <Headphones size={18} fill="currentColor" className="opacity-90" />
                                    <span className="text-sm font-bold whitespace-nowrap">해설 듣기</span>
                                </button>
                            </div>
                            <div className="p-6 rounded-2xl border border-indigo-500/30 mb-8 space-y-6 bg-black/80 shadow-inner relative overflow-hidden">
                                <h4 className="text-indigo-400 font-bold mb-4 text-xl text-center">{data.fortune_content.overview}</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {data.fortune_content.detailed_analysis.map((sec, idx) => (
                                        <div key={idx} className="p-4 bg-white/5 border border-white/10 rounded-xl">
                                            <div className="text-xs text-indigo-300/70 font-bold mb-2 uppercase tracking-wider">{sec.title}</div>
                                            <p className="text-white/80 text-sm leading-relaxed font-western">
                                                {sec.content}
                                            </p>
                                        </div>
                                    ))}
                                </div>
                                <div className="p-5 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl mt-4 shadow-inner">
                                    <div className="text-sm text-white font-bold mb-3 uppercase tracking-widest text-center drop-shadow-md">별들의 조언</div>
                                    <p className="text-xl text-white leading-relaxed font-western whitespace-pre-wrap text-center font-bold">
                                        {data.fortune_content.advice}
                                    </p>
                                </div>
                            </div>
                        </SpotlightSection>

                        {/* 5. Lucky Items */}
                        <SpotlightSection
                            isActive={isRevealing && revealStep === 8}
                            isDimmed={isRevealing && revealStep !== 8 && revealStep !== 0}
                        >
                            <div className="flex items-center gap-3 mb-4">
                                <h3 className="text-white font-bold text-lg uppercase tracking-widest drop-shadow-md">5. 행운 아이템</h3>
                                <button
                                    onClick={(e) => handleReplayExplain(8, 8, e)}
                                    className="relative z-10 cursor-pointer px-4 py-2 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white transition-all shadow-md flex items-center gap-2 transform hover:scale-105"
                                >
                                    <Headphones size={18} fill="currentColor" className="opacity-90" />
                                    <span className="text-sm font-bold whitespace-nowrap">해설 듣기</span>
                                </button>
                            </div>
                            <div className="p-6 rounded-2xl border border-white/10 grid grid-cols-2 md:grid-cols-4 gap-4 text-center bg-black/80 shadow-inner relative overflow-hidden">
                                <div className="p-4 rounded-xl bg-black/20">
                                    <div className="text-xs text-white/90 font-bold uppercase mb-2 drop-shadow-sm">행운의 색</div>
                                    <div className="text-lg font-bold text-indigo-300">{data.lucky.color}</div>
                                </div>
                                <div className="p-4 rounded-xl bg-black/20">
                                    <div className="text-xs text-white/90 font-bold uppercase mb-2 drop-shadow-sm">행운의 숫자</div>
                                    <div className="text-lg font-bold text-indigo-300">{data.lucky.number}</div>
                                </div>
                                {data.lucky.item && (
                                    <div className="p-4 rounded-xl bg-black/20">
                                        <div className="text-xs text-white/90 font-bold uppercase mb-2 drop-shadow-sm">행운의 아이템</div>
                                        <div className="text-lg font-bold text-indigo-300">{data.lucky.item}</div>
                                    </div>
                                )}
                                {data.lucky.place && (
                                    <div className="p-4 rounded-xl bg-black/20">
                                        <div className="text-xs text-white/90 font-bold uppercase mb-2 drop-shadow-sm">행운의 장소</div>
                                        <div className="text-lg font-bold text-indigo-300">{data.lucky.place}</div>
                                    </div>
                                )}
                            </div>
                        </SpotlightSection>

                        <div className="h-20" />
                    </div>
                </div>
            </div>

            {/* Floating Overlays */}
            <AnimatePresence>
                {
                    (isRevealing || manualBubbleText) && (
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
                                        if (sentenceIndex < currentSentences.length - 1) {
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
                                        }
                                    }
                                }}
                            />

                            {/* Character Image */}
                            <motion.div
                                key="west-char-bubble"
                                initial={{ x: -100, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                exit={{ x: -100, opacity: 0 }}
                                className="absolute bottom-[-50px] left-[-50px] md:bottom-[-20px] md:left-[-20px] w-[150px] md:w-[200px] z-10 pointer-events-none"
                            >
                                <img src={WestStarImg} className="w-full h-full object-contain" />
                            </motion.div>

                            {/* Dialogue Bubble */}
                            <motion.div
                                className="absolute z-20 pointer-events-none"
                                initial={false}
                                animate={{
                                    top: revealStep === 1 ? '45%' :
                                        revealStep === 2 ? '35%' :
                                            revealStep === 3 ? '65%' :
                                                revealStep >= 4 && revealStep <= 6 ? '70%' : '75%',
                                    left: revealStep === 1 ? '55%' :
                                        revealStep === 2 ? '15%' :
                                            revealStep === 3 ? '10%' :
                                                revealStep >= 4 && revealStep <= 6 ? '10%' : '10%',
                                    x: '-10%',
                                }}
                                transition={{ type: "spring", stiffness: 80, damping: 20 }}
                            >
                                <AnimatedBubble
                                    theme="indigo"
                                    size="large"
                                    title={WestName}
                                    text={currentBubbleText}
                                />
                            </motion.div>

                            <div className="absolute bottom-10 left-0 right-0 text-center pointer-events-none">
                                <span className="bg-black/50 px-4 py-2 rounded-full text-white/50 text-xs animate-pulse backdrop-blur-md">
                                    {manualBubbleText ? "닫기" : revealStep < MAX_STEPS ? "탭하여 계속 설명 듣기" : "탭하여 완료"}
                                </span>
                            </div>
                        </motion.div>
                    )
                }
            </AnimatePresence>
        </div>
    );
};

export default WesternResult;
