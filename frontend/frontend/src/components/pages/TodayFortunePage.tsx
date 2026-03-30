import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { startSession, getTodayAnalysis, type TodayFortuneAnalysis, getUnseHistory, type UnseResultListItem } from '../../api/unse';
import { getRandomFortuneV2 } from '../../data/dummyFortuneV2';
import { ArrowLeft, ChevronRight } from 'lucide-react';
import AnimatedBubble from '../common/AnimatedBubble';
import FortuneSelection from './FortuneSelection';
import FortuneLoading from './FortuneLoading';
import TodayFortuneResult, { type DailyFortuneResult } from './TodayFortuneResult';
import { type DualFortuneResultV2 } from '../../data/types';
import { getSajuResult } from '../../api/saju'; // Real API import
import ParticleBackground from '../effects/ParticleBackground';

// Character Images
import { getCharacterImage, getCharacterName, useCharacterSettings, getSelectionIntroScript, type DuoIntroStep, type CharacterType } from '../../utils/character';

// Dynamic loading needs to happen inside component or effect, but for assets import we need to be careful.
// actually getCharacterImage is a function, so we can just use it inside component.

// Background & Dialogue Assets mapping
const SELECTION_DIALOGUES: Record<string, { east: string, west: string, bg: string }> = {
    love: {
        east: "인연의 붉은 실이 어디로 이어져 있는지 살펴볼까요?",
        west: "금성(Venus)이 당신의 사랑을 어떻게 비추고 있는지 알려드릴게요.",
        bg: "/assets/bg/love.png"
    },
    wealth: {
        east: "재물운의 흐름을 읽어 풍요의 길을 찾아봅시다.",
        west: "목성(Jupiter)의 기운이 당신의 부를 확장시킬 시기인지 확인해보죠.",
        bg: "/assets/bg/money.png"
    },
    health: {
        east: "몸과 마음의 조화가 잘 이루어지고 있는지 짚어드리겠습니다.",
        west: "태양(Sun)의 활력이 당신의 배움을 도울 것입니다.", // Fixed copy-paste error in original
        bg: "/assets/bg/health.png"
    },
    academic: {
        east: "학문의 별이 당신을 비추고 있는지 확인해봅시다.",
        west: "수성(Mercury)의 지혜가 당신의 배움을 도울 것입니다.",
        bg: "/assets/bg/study.png"
    },
    career: {
        east: "당신의 앞길에 관운이 열려있는지 살펴보겠습니다.",
        west: "토성(Saturn)이 당신의 성취와 명예를 어떻게 돕고 있는지 확인해봐요.",
        bg: "/assets/bg/job.png"
    }
};

// Extract background URLs for easier access
const SELECTION_BGS: Record<string, string> = {
    love: "/assets/bg/love.png",
    wealth: "/assets/bg/money.png",
    health: "/assets/bg/health.png",
    academic: "/assets/bg/study.png",
    career: "/assets/bg/job.png"
};

const TodayFortunePage = () => {
    const navigate = useNavigate();
    const [phase, setPhase] = useState<'intro' | 'selection' | 'outro' | 'loading' | 'result' | 'exit'>('intro');
    const [topic, setTopic] = useState<string | null>(null);
    const [hoveredItem, setHoveredItem] = useState<string | null>(null);
    const [history, setHistory] = useState<UnseResultListItem[]>([]);
    const [alreadySeen, setAlreadySeen] = useState(false);

    // Load Character Settings (Reactive)
    const settings = useCharacterSettings();
    const [eastEmotion, setEastEmotion] = useState<CharacterType>('normal');
    const [westEmotion, setWestEmotion] = useState<CharacterType>('normal');

    // Dynamic Images based on Emotion State
    const EastSajuImg = getCharacterImage('east', settings.east, eastEmotion);
    const WestStarImg = getCharacterImage('west', settings.west, westEmotion);
    const EastName = getCharacterName('east', settings.east);
    const WestName = getCharacterName('west', settings.west);

    // API State
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [fetchedSummary, setFetchedSummary] = useState<{ east: TodayFortuneAnalysis | null, west: TodayFortuneAnalysis | null }>({ east: null, west: null });
    const [loadingSummary, setLoadingSummary] = useState(false);
    const hasInitialized = useRef(false);

    // Intro Sequence State
    const [introStep, setIntroStep] = useState(0);
    const [introScript, setIntroScript] = useState<DuoIntroStep[]>([]);

    // Load Intro Script
    useEffect(() => {
        const script = getSelectionIntroScript(settings.east, settings.west);
        setIntroScript(script.length > 0 ? script : [
            { char: 'west', text: "오늘의 별들이 당신에게 어떤 이야기를 속삭일까요?", emotion: 'smile' },
            { char: 'east', text: "음양의 흐름을 통해 당신의 하루를 미리 짚어드리겠습니다.", emotion: 'normal' }
        ]);
    }, [settings.east, settings.west]);

    // Outro Sequence State (Selection -> Loading)
    const [outroStep, setOutroStep] = useState(0);

    // Loading State
    const [loadingProgress, setLoadingProgress] = useState(0);

    // Initialize Session & History
    useEffect(() => {
        if (!hasInitialized.current) {
            hasInitialized.current = true;
            startSession().then(res => {
                setSessionId(res.session_id);
            }).catch(() => { });

            // Fetch History for "Already Seen" check
            getUnseHistory().then(setHistory).catch(() => { });
        }
    }, []);

    // Intro Navigation Handler
    const handleIntroNext = useCallback(() => {
        if (phase !== 'intro') return;

        if (introStep < introScript.length) {
            setIntroStep(prev => prev + 1);
        } else {
            setPhase('selection');
        }
    }, [phase, introStep, introScript]);

    // Handle Emotion Updates based on Intro Step
    useEffect(() => {
        if (phase === 'intro' && introStep > 0 && introStep <= introScript.length) {
            const currentLine = introScript[introStep - 1]; // 1-based step maps to 0-based index
            if (currentLine.char === 'east') {
                setEastEmotion(currentLine.emotion || 'normal');
                setWestEmotion('normal'); // Reset other to normal or keep previous? Reset feels cleaner for focus.
            } else {
                setWestEmotion(currentLine.emotion || 'normal');
                setEastEmotion('normal');
            }
        } else {
            setEastEmotion('normal');
            setWestEmotion('normal');
        }
    }, [introStep, phase, introScript]);



    // Outro Navigation Handler
    const handleOutroNext = useCallback(() => {
        if (phase !== 'outro') return;

        if (outroStep < 3) {
            setOutroStep(prev => prev + 1);
        } else if (outroStep === 3) {
            setPhase('loading');
            setOutroStep(0);
        }
    }, [phase, outroStep]);

    // Keyboard Navigation for Intro and Outro
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.code === 'Space' || e.key === ' ' || e.key === 'Enter') {
                e.preventDefault();
                if (phase === 'intro') {
                    handleIntroNext();
                } else if (phase === 'outro') {
                    handleOutroNext();
                }
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [phase, handleIntroNext, handleOutroNext]);

    // Auto-advance step 0 (Entry) -> 1
    useEffect(() => {
        if (phase === 'intro' && introStep === 0) {
            const timer = setTimeout(() => setIntroStep(1), 1000); // Wait 1s then show first dialogue
            return () => clearTimeout(timer);
        }
    }, [phase, introStep]);

    // Outro Sequence Auto-advance
    useEffect(() => {
        if (phase === 'outro') {
            if (outroStep === 0) {
                // Step 0: Show East dialogue immediately
                const timer = setTimeout(() => setOutroStep(1), 100);
                return () => clearTimeout(timer);
            } else if (outroStep === 1) {
                // Step 1: East dialogue -> West dialogue (2.5s or manual skip)
                const timer = setTimeout(() => setOutroStep(2), 2500);
                return () => clearTimeout(timer);
            } else if (outroStep === 2) {
                // Step 2: West dialogue -> Screen fold (2.5s or manual skip)
                const timer = setTimeout(() => setOutroStep(3), 2500);
                return () => clearTimeout(timer);
            } else if (outroStep === 3) {
                // Trigger Greeting API
                // Start Greeting (API) - REMOVED as per user request
                /*
                if (topic && sessionId) {
                    const CATEGORY_MAP: Record<string, string> = {
                        love: 'LOVE',
                        wealth: 'MONEY',
                        health: 'HEALTH',
                        academic: 'STUDY',
                        career: 'CAREER'
                    };
                    const backendCategory = CATEGORY_MAP[topic] || 'GENERAL';
    
                    getSajuResult().then(sajuData => {
                        console.log("Fetched Saju Data for Greeting:", sajuData);
                        startGreeting({
                            session_id: sessionId,
                            category: backendCategory,
                            char1_code: settings.east.toUpperCase(),
                            char2_code: settings.west.toUpperCase(),
                        }).then(res => {
                            console.log("Greeting Received:", res);
                            setGreetingData(res);
                        }).catch(err => console.error("Greeting Failed:", err));
                    }).catch(sajuErr => {
                        console.warn("Saju Fetch Failed, continuing without context:", sajuErr);
                        startGreeting({
                            session_id: sessionId,
                            category: backendCategory,
                            char1_code: settings.east.toUpperCase(),
                            char2_code: settings.west.toUpperCase()
                        }).then(res => {
                            console.log("Greeting Received (Fallback):", res);
                            setGreetingData(res);
                        }).catch(err => console.error("Greeting Failed (Fallback):", err));
                    });
                }
                */
                const timer = setTimeout(() => {
                    setPhase('loading');
                    setOutroStep(0); // Reset for next time
                }, 1000);
                return () => clearTimeout(timer);
            }
        }
    }, [phase, outroStep, topic, sessionId]);


    // Loading Progress Simulation & Data Fetching
    useEffect(() => {
        if (phase === 'loading') {
            // Start fetching summary if not already
            if (sessionId && topic && !loadingSummary && !fetchedSummary.east && !fetchedSummary.west) {
                const CATEGORY_MAP: Record<string, string> = {
                    love: 'LOVE',
                    wealth: 'MONEY',
                    health: 'HEALTH',
                    academic: 'STUDY',
                    career: 'CAREER'
                };
                const backendCategory = CATEGORY_MAP[topic] || 'GENERAL';

                setLoadingSummary(true);

                Promise.all([
                    getTodayAnalysis(sessionId, 'east', backendCategory).catch(() => null),
                    getTodayAnalysis(sessionId, 'west', backendCategory).catch(() => null)
                ]).then(([east, west]) => {
                    setFetchedSummary({ east, west });
                    setLoadingSummary(false);
                }).catch(() => {
                    setLoadingSummary(false);
                });
            }

            setLoadingProgress(0);
            const interval = setInterval(() => {
                setLoadingProgress(prev => {
                    const next = (prev as number) + 2;
                    // If near completion but no summary data, wait
                    if (next >= 90 && loadingSummary) {
                        return 90;
                    }
                    if (next >= 100) {
                        clearInterval(interval);
                        setTimeout(() => setPhase('result'), 500);
                        return 100;
                    }
                    return next;
                });
            }, 50);
            return () => clearInterval(interval);
        }
    }, [phase, loadingSummary, sessionId, topic, fetchedSummary.east, fetchedSummary.west]);


    // Mock Data for Today's Fortune

    // Random Fortune Data
    // Real Data for Today's Fortune
    const [fortuneResult, setFortuneResult] = useState<DualFortuneResultV2 | null>(null);

    // Fetch Saju/Western Result on Mount
    useEffect(() => {
        getSajuResult().then(res => {
            // MERGE Logic: Deep merge for missing stats
            const dummy = getRandomFortuneV2();

            const mergeStats = (realStats: any, dummyStats: any) => {
                if (!realStats) return dummyStats;
                return {
                    ...dummyStats, // Start with all dummy props as base
                    ...realStats,  // Overwrite with real props
                    // Ensure specific nested objects exist by merging them individually if needed
                    five_elements: realStats.five_elements || dummyStats.five_elements,
                    ten_gods: realStats.ten_gods || dummyStats.ten_gods,
                    yin_yang_ratio: realStats.yin_yang_ratio || dummyStats.yin_yang_ratio,
                    // Western specific
                    element_4_distribution: realStats.element_4_distribution || dummyStats.element_4_distribution,
                    modality_3_distribution: realStats.modality_3_distribution || dummyStats.modality_3_distribution,
                    main_sign: realStats.main_sign || dummyStats.main_sign,
                };
            };

            const merged: DualFortuneResultV2 = {
                eastern: {
                    ...res.eastern,
                    stats: mergeStats(res.eastern?.stats, dummy.eastern.stats),
                    final_verdict: res.eastern?.final_verdict || dummy.eastern.final_verdict,
                    lucky: res.eastern?.lucky || dummy.eastern.lucky
                },
                western: {
                    ...res.western,
                    stats: mergeStats(res.western?.stats, dummy.western.stats),
                    fortune_content: res.western?.fortune_content || dummy.western.fortune_content,
                    lucky: res.western?.lucky || dummy.western.lucky
                }
            };

            setFortuneResult(merged);
        }).catch(err => {
            // Fallback to full dummy if fetch fails entirely
            setFortuneResult(getRandomFortuneV2());
        });
    }, []);

    // Transform Data for Result View
    const eastResult: DailyFortuneResult = fetchedSummary.east ? {
        type: `${topic === 'love' ? '연애운' : topic === 'wealth' ? '재물운' : topic === 'health' ? '건강운' : topic === 'academic' ? '학업운' : topic === 'career' ? '직업운' : '오늘의 운세'} (동양)`,
        score: fetchedSummary.east.score,
        summary: fetchedSummary.east.keyword,
        keywords: [],
        explanation: fetchedSummary.east.details?.map((d: any) => `${d.title}: ${d.description}`).join('\n\n') || "분석 결과가 없습니다.",
        luckyItem: fortuneResult?.eastern?.lucky?.item ?? "행운의 아이템",
        details: fetchedSummary.east.details || []
    } : {
        type: `${topic === 'love' ? '애정운' : topic === 'wealth' ? '재물운' : '오늘의 운세'} (${fortuneResult?.eastern?.element || '오행'})`,
        score: fortuneResult?.eastern?.score || 0,
        summary: fortuneResult?.eastern?.final_verdict?.summary || "운세 데이터를 불러오는 중입니다...",
        keywords: fortuneResult?.eastern?.stats?.ten_gods?.gods_list?.slice(0, 3).map((i: any) => i.label) || [],
        explanation: fortuneResult?.eastern?.final_verdict?.advice || "잠시만 기다려주세요.",
        luckyItem: fortuneResult?.eastern?.lucky?.item || "",
        details: []
    };

    const westResult: DailyFortuneResult = fetchedSummary.west ? {
        type: `${topic === 'love' ? 'Love' : topic === 'wealth' ? 'Wealth' : topic === 'health' ? 'Health' : topic === 'academic' ? 'Study' : topic === 'career' ? 'Career' : 'Fortune'} (서양)`,
        score: fetchedSummary.west.score,
        summary: fetchedSummary.west.keyword,
        keywords: [],
        explanation: fetchedSummary.west.details?.map((d: any) => `${d.title}: ${d.description}`).join('\n\n') || "No analysis available.",
        luckyItem: fortuneResult?.western?.lucky?.item ?? "Lucky Item",
        details: fetchedSummary.west.details || []
    } : {
        type: `${topic === 'love' ? 'Love' : topic === 'wealth' ? 'Wealth' : 'Fortune'} (${fortuneResult?.western?.stats?.main_sign?.name || 'Sign'})`,
        score: fortuneResult?.western?.score || 0,
        summary: fortuneResult?.western?.stats?.keywords_summary || "Loading...",
        keywords: fortuneResult?.western?.stats?.keywords?.map((k: any) => k.label) || [],
        explanation: fortuneResult?.western?.fortune_content?.advice || "Please wait...",
        luckyItem: fortuneResult?.western?.lucky?.item || "",
        details: []
    };

    const handleBack = () => {
        if (phase === 'selection') {
            navigate('/home');
        } else {
            setPhase('selection');
        }
    };

    return (
        <div className="fixed inset-0 bg-black text-white overflow-hidden z-[100]">
            {/* Header / Nav (Exit Button) - Hide in Result Phase */}
            {phase !== 'result' && (
                <div className="absolute top-0 left-0 w-full p-4 flex justify-between items-center z-[110] bg-gradient-to-b from-black/80 to-transparent pointer-events-none">
                    <button onClick={handleBack} className="text-white/60 hover:text-white flex items-center gap-2 pointer-events-auto transition-colors">
                        <ArrowLeft /> 나가기
                    </button>
                </div>
            )}

            <AnimatePresence mode="wait">
                {phase === 'intro' ? (
                    <motion.div
                        key="intro"
                        className="fixed inset-0 z-50 flex items-center justify-center bg-black cursor-pointer"
                        onClick={handleIntroNext}
                        exit={{ opacity: 0 }}
                    >
                        {/* Background */}
                        <ParticleBackground type="eastern" className="opacity-30" />

                        {/* Tap Indicator */}


                        {/* SKIP BUTTON */}
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                setPhase('selection');
                            }}
                            className="absolute top-8 right-8 z-[60] px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full text-white/80 text-sm backdrop-blur-sm transition-all flex items-center gap-2 group pointer-events-auto"
                        >
                            SKIP <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                        </button>

                        {/* Characters Container - Widened Gap */}
                        <div className="absolute inset-x-0 bottom-0 h-[80%] flex justify-center items-end px-4 md:px-20 pb-0 md:pb-10 gap-20 md:gap-80 pointer-events-none">
                            {/* West Character (Left) */}
                            <motion.div
                                initial={{ x: -100, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                transition={{ duration: 0.8, ease: "easeOut" }}
                                className="relative flex flex-col items-center"
                            >
                                <AnimatePresence mode="wait">
                                    {introStep > 0 && introScript[introStep - 1]?.char === 'west' && (
                                        <div className="absolute bottom-[50%] left-1/2 -translate-x-1/2 z-50 min-w-[300px] mb-0 font-serif font-bold">
                                            <AnimatedBubble
                                                theme="indigo"
                                                size="large"
                                                title={WestName}
                                                text={introScript[introStep - 1].text}
                                            />
                                        </div>
                                    )}
                                </AnimatePresence>
                                <motion.img
                                    src={WestStarImg}
                                    className="h-[50vh] md:h-[65vh] object-contain"
                                    initial={{ scale: 0.95 }}
                                    animate={{
                                        scale: introStep > 0 && introScript[introStep - 1]?.char === 'west' ? 1.05 : 1
                                    }}
                                    transition={{ duration: 0.3 }}
                                />
                            </motion.div>

                            {/* East Character (Right) */}
                            <motion.div
                                initial={{ x: 100, opacity: 0 }}
                                animate={{ x: 0, opacity: 1 }}
                                transition={{ duration: 0.8, ease: "easeOut" }}
                                className="relative flex flex-col items-center"
                            >
                                <AnimatePresence mode="wait">
                                    {introStep > 0 && introScript[introStep - 1]?.char === 'east' && (
                                        <div className="absolute bottom-[50%] left-1/2 -translate-x-1/2 z-50 min-w-[300px] mb-0 font-serif font-bold">
                                            <AnimatedBubble
                                                theme="amber"
                                                size="large"
                                                title={EastName}
                                                text={introScript[introStep - 1].text}
                                            />
                                        </div>
                                    )}
                                </AnimatePresence>
                                <motion.img
                                    src={EastSajuImg}
                                    className="h-[50vh] md:h-[65vh] object-contain"
                                    initial={{ scale: settings.east === 'sinseon' ? 1.045 : 0.95 }}
                                    animate={{
                                        scale: (introStep > 0 && introScript[introStep - 1]?.char === 'east' ? 1.05 : 1) * (settings.east === 'sinseon' ? 1.1 : 1)
                                    }}
                                    transition={{ duration: 0.3 }}
                                />
                            </motion.div>
                        </div>
                    </motion.div>
                ) : phase === 'selection' ? (
                    <motion.div
                        key="selection"
                        initial={{ clipPath: "circle(0% at 50% 50%)" }}
                        animate={{ clipPath: "circle(150% at 50% 50%)" }}
                        exit={{ opacity: 1 }}
                        transition={{ duration: 0 }}
                        className="absolute inset-0 z-10 bg-black"
                    >
                        {/* Base Background - Oriental Pattern */}
                        <div
                            className="absolute inset-0 bg-cover bg-center opacity-40 scale-x-[-1]"
                            style={{ backgroundImage: `url('/assets/bg/fortune_bg_oriental.png')` }}
                        />
                        <div className="absolute inset-0 bg-black/40" />

                        {/* Dynamic Hover Background */}
                        <AnimatePresence>
                            {hoveredItem && SELECTION_BGS[hoveredItem] && (
                                <motion.div
                                    key="hover-bg"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 0.5 }}
                                    className="absolute inset-0 z-0 bg-cover bg-center flex items-center justify-center pointer-events-none"
                                >
                                    <div
                                        className="w-full h-full bg-cover bg-center"
                                        style={{
                                            backgroundImage: `url('${SELECTION_BGS[hoveredItem]}')`,
                                            maskImage: 'radial-gradient(circle at center, black 0%, transparent 70%)',
                                            WebkitMaskImage: 'radial-gradient(circle at center, black 0%, transparent 70%)',
                                            filter: 'blur(8px) contrast(1.2)'
                                        }}
                                    />
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Characters with Hover Dialogues */}
                        <div className="absolute inset-x-0 bottom-0 h-[70%] flex justify-center items-end gap-48 md:gap-150 pb-0 md:pb-10 pointer-events-none z-20">
                            {/* West Character (Left) */}
                            <motion.div
                                initial={{ x: 0, opacity: 1 }}
                                animate={{ x: -30, opacity: 1 }}
                                transition={{ duration: 0.8, ease: "easeOut" }}
                                className="relative flex flex-col items-center"
                            >
                                <AnimatePresence>
                                    {hoveredItem && SELECTION_DIALOGUES[hoveredItem] && (
                                        <AnimatedBubble
                                            theme="indigo"
                                            size="large"
                                            title={WestName}
                                            className="bottom-[110%] left-1/2 -translate-x-1/2 min-w-[300px] font-serif font-bold"
                                            text={SELECTION_DIALOGUES[hoveredItem].west}
                                        />
                                    )}
                                </AnimatePresence>
                                <motion.img
                                    src={WestStarImg}
                                    className="h-[45vh] md:h-[60vh] object-contain"
                                    animate={{
                                        scale: hoveredItem ? 1.05 : 1
                                    }}
                                    transition={{ duration: 0.3 }}
                                />
                            </motion.div>

                            {/* East Character (Right) */}
                            <motion.div
                                initial={{ x: 0, opacity: 1 }}
                                animate={{ x: 30, opacity: 1 }}
                                transition={{ duration: 0.8, ease: "easeOut" }}
                                className="relative flex flex-col items-center"
                            >
                                <AnimatePresence>
                                    {hoveredItem && SELECTION_DIALOGUES[hoveredItem] && (
                                        <AnimatedBubble
                                            theme="amber"
                                            size="large"
                                            title={EastName}
                                            className="bottom-[110%] left-1/2 -translate-x-1/2 min-w-[300px] font-serif font-bold"
                                            text={SELECTION_DIALOGUES[hoveredItem].east}
                                        />
                                    )}
                                </AnimatePresence>
                                <motion.img
                                    src={EastSajuImg}
                                    className="h-[45vh] md:h-[60vh] object-contain"
                                    animate={{
                                        scale: hoveredItem ? 1.05 : 1
                                    }}
                                    transition={{ duration: 0.3 }}
                                />
                            </motion.div>
                        </div>

                        <FortuneSelection
                            onSelect={(topic) => {
                                // History Check
                                const categoryMap: Record<string, string> = {
                                    love: 'LOVE',
                                    wealth: 'MONEY',
                                    health: 'HEALTH',
                                    academic: 'STUDY',
                                    career: 'CAREER'
                                };
                                const targetCat = categoryMap[topic];

                                const today = new Date();
                                const year = today.getFullYear();
                                const month = String(today.getMonth() + 1).padStart(2, '0');
                                const day = String(today.getDate()).padStart(2, '0');
                                const todayStr = `${year}-${month}-${day}`;

                                const hasSeen = history.some(item => {
                                    return item.created_at && item.created_at.startsWith(todayStr) && item.category === targetCat;
                                });

                                if (hasSeen) {
                                    setTopic(topic);
                                    setAlreadySeen(true);
                                    setTimeout(() => navigate('/history'), 3000);
                                    return;
                                }

                                setTopic(topic);
                                setOutroStep(0);
                                setPhase('outro');
                            }}
                            onHover={(id) => setHoveredItem(id)}
                        />

                        {/* Already Seen Alert Bubble */}
                        <AnimatePresence>
                            {alreadySeen && (
                                <div className="absolute inset-0 z-50 flex items-center justify-center pointer-events-auto bg-black/60 backdrop-blur-sm animate-fade-in">
                                    <div className="absolute bottom-[50%] z-50 min-w-[320px]">
                                        <AnimatedBubble
                                            theme="indigo"
                                            size="large"
                                            title={WestName}
                                            text="이미 오늘 확인한 운세네요! 기록 보관소로 안내해 드릴게요."
                                        />
                                    </div>
                                </div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                ) : phase === 'outro' ? (
                    <motion.div
                        key="outro"
                        initial={{ opacity: 1 }}
                        animate={{
                            opacity: outroStep >= 3 ? 0 : 1,
                            clipPath: outroStep >= 3 ? "inset(0 50% 0 50%)" : "inset(0 0% 0 0%)"
                        }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: outroStep >= 3 ? 1 : 0.5 }}
                        className="absolute inset-0 z-10 bg-black cursor-pointer"
                        onClick={handleOutroNext}
                    >
                        {/* Background */}
                        <div
                            className="absolute inset-0 bg-cover bg-center opacity-40 scale-x-[-1]"
                            style={{ backgroundImage: `url('/assets/bg/fortune_bg_oriental.png')` }}
                        />
                        <div className="absolute inset-0 bg-black/40" />

                        {/* Characters moving to center with dialogues */}
                        <div className="absolute inset-x-0 bottom-0 h-[70%] flex justify-center items-end gap-16 md:gap-32 pb-0 md:pb-10 pointer-events-none z-30">
                            {/* West Character (Left) */}
                            <motion.div
                                initial={{ x: -200, opacity: 1 }}
                                animate={{ x: 0, opacity: 1 }}
                                transition={{ duration: 0.8, ease: "easeOut" }}
                                className="relative flex flex-col items-center"
                            >
                                <AnimatePresence>
                                    {outroStep === 2 && (
                                        <AnimatedBubble
                                            theme="indigo"
                                            size="large"
                                            title={WestName}
                                            className="bottom-[20%] left-1/2 -translate-x-1/2 min-w-[300px] font-serif font-bold"
                                            text="별들이 당신의 길을 비추기 시작했습니다."
                                        />
                                    )}
                                </AnimatePresence>
                                <motion.img
                                    src={WestStarImg}
                                    className="h-[50vh] md:h-[65vh] object-contain"
                                    animate={{
                                        scale: outroStep === 2 ? 1.05 : 1
                                    }}
                                />
                            </motion.div>

                            {/* East Character (Right) */}
                            <motion.div
                                initial={{ x: 200, opacity: 1 }}
                                animate={{ x: 0, opacity: 1 }}
                                transition={{ duration: 0.8, ease: "easeOut" }}
                                className="relative flex flex-col items-center"
                            >
                                <AnimatePresence>
                                    {outroStep === 1 && (
                                        <AnimatedBubble
                                            theme="amber"
                                            size="large"
                                            title={EastName}
                                            className="bottom-[20%] left-1/2 -translate-x-1/2 min-w-[300px]"
                                            text="운명의 흐름을 읽어보겠습니다."
                                        />
                                    )}
                                </AnimatePresence>
                                <motion.img
                                    src={EastSajuImg}
                                    className="h-[50vh] md:h-[65vh] object-contain"
                                    animate={{
                                        scale: outroStep > 0 && outroStep % 2 === 1 ? 1.05 : 1
                                    }}
                                />
                            </motion.div>
                        </div>
                    </motion.div>
                ) : phase === 'loading' ? (
                    <FortuneLoading
                        loadingProgress={loadingProgress}
                        mode="saju"
                        userQuestion={topic || "오늘의 운세"}
                        onComplete={() => setPhase('result')}
                    />
                ) : (
                    <>
                        {/* Persistent Background Layer for Talk & Final Transition */}
                        <AnimatePresence>
                            {(phase === 'result') && (
                                <motion.div
                                    key="persistent-bg"
                                    initial={{ scaleY: 0, opacity: 0 }}
                                    animate={{ scaleY: 1, opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
                                    className="absolute inset-0 z-0"
                                >
                                    {/* Background Image */}
                                    {topic && SELECTION_BGS[topic] && (
                                        <div
                                            className="absolute inset-0 bg-cover bg-center origin-bottom"
                                            style={{
                                                backgroundImage: `url('${SELECTION_BGS[topic]}')`,
                                                filter: 'blur(5px) brightness(0.4)'
                                            }}
                                        />
                                    )}
                                    {/* Gradient Overlay */}
                                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/50 to-transparent" />
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {/* Content Layer */}
                        <AnimatePresence mode="wait">
                            {phase === 'result' && fortuneResult ? (
                                <motion.div
                                    key="result"
                                    initial={{ opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    exit={{ opacity: 0 }}
                                    className="absolute inset-0 z-10"
                                >
                                    <TodayFortuneResult
                                        fortuneType={topic || "오늘의 운세"}
                                        eastResult={eastResult}
                                        westResult={westResult}
                                        staticResult={fortuneResult}
                                        onBack={handleBack}
                                        onSaveAndExit={() => {
                                            navigate('/home');
                                        }}
                                    />
                                </motion.div>
                            ) : null}
                        </AnimatePresence>
                    </>
                )}
            </AnimatePresence>
        </div>
    );
};

export default TodayFortunePage;
