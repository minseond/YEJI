import { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

import { getSajuAnalysis } from '../../api/saju';
import { type DualFortuneResultV2 } from '../../data/types';
import { getGapjaInfo } from '../../utils/gapja';
import ParticleBackground from '../effects/ParticleBackground';
import AnimatedBubble from '../common/AnimatedBubble';

import { getUserInfo, updateProfile, type UserUpdateRequest } from '../../api/auth';
import { jwtDecode } from 'jwt-decode';

// Character Images
import { getCharacterImage, getCharacterName, useCharacterSettings, getCharacterSajuIntro, getDuoIntroScript, getDuoOutroScript, getCharacterInputScript, type DuoIntroStep, type CharacterType } from '../../utils/character';

// Sub-components
import FortuneLoading from './FortuneLoading';
import FortuneResult from './FortuneResult';
import FortuneSelection from './FortuneSelection';


// Feature Components for Input Flow
import ScrollNameInput from '../features/ScrollNameInput';
import YinYangGenderInput from '../features/YinYangGenderInput';
import GapjaYearInput from '../features/GapjaYearInput';
import SolarConstellationInput from '../features/SolarConstellationInput';
import TimeInput from '../features/TimeInput';

// Types
type Phase = 'intro' | 'saju_intro' | 'fortune_intro' | 'fortune_selection' | 'fortune_outro' | 'saju_outro' | 'input_info' | 'input_question' | 'loading' | 'debate' | 'result';

interface UserInfo {
    name: string;
    gender: 'male' | 'female' | '';
    year: number;
    month: number;
    day: number;
    time: string;
    solarConstellation: string;
}

const FortuneReadingPage = ({ mode, onBack }: { mode: 'saju' | 'daily'; onBack: () => void }) => {
    // Reactive Character Settings
    const settings = useCharacterSettings();
    const [eastEmotion, setEastEmotion] = useState<CharacterType>('normal');
    const [westEmotion, setWestEmotion] = useState<CharacterType>('normal');

    const EastSajuImg = getCharacterImage('east', settings.east, eastEmotion);
    const WestStarImg = getCharacterImage('west', settings.west, westEmotion);
    const EastName = getCharacterName('east', settings.east);
    const WestName = getCharacterName('west', settings.west);
    const navigate = useNavigate();
    // Skip 'intro' landing page -> Start immediately based on mode
    const [phase, setPhase] = useState<Phase>(() => mode === 'saju' ? 'saju_intro' : 'fortune_intro');
    const [fortuneResult, setFortuneResult] = useState<DualFortuneResultV2 | null>(null);

    // API Status Ref (Start request immediately on button click, check result in loading phase)
    const sajuApiState = useRef<{ status: 'idle' | 'loading' | 'success' | 'error', data: DualFortuneResultV2 | null }>({ status: 'idle', data: null });

    // Q&A State
    const [userQuestion, setUserQuestion] = useState("");

    // Dynamic Intro Script Scope (Moved up for access in effects)
    const [duoScript, setDuoScript] = useState<DuoIntroStep[]>([]);
    const [duoOutroScript, setDuoOutroScript] = useState<DuoIntroStep[]>([]);

    useEffect(() => {
        setDuoScript(getDuoIntroScript(settings.east, settings.west));
        setDuoOutroScript(getDuoOutroScript(settings.east, settings.west));
    }, [settings.east, settings.west]);

    // Intro Sequence State
    const [introStep, setIntroStep] = useState(0);
    const [sajuIntroStep, setSajuIntroStep] = useState(0);
    const [fortuneIntroStep, setFortuneIntroStep] = useState(0);
    const [fortuneOutroStep, setFortuneOutroStep] = useState(0);
    const [debateStep, setDebateStep] = useState(0); // 0: Start, 1: East, 2: West, 3: Choice
    const [sajuOutroStep, setSajuOutroStep] = useState(0);

    // Selection Phase State
    const [selectionHover, setSelectionHover] = useState<string | null>(null);

    // Emotion Sync Effect
    useEffect(() => {
        let targetEmotion: CharacterType | undefined;
        let targetChar: 'east' | 'west' | undefined;

        if (phase === 'saju_intro') {
            const index = sajuIntroStep - 3;
            if (index >= 0 && index < duoScript.length) {
                const step = duoScript[index];
                targetChar = step.char;
                targetEmotion = step.emotion;
            }
        } else if (phase === 'saju_outro') {
            const index = sajuOutroStep - 1;
            if (index >= 0 && index < duoOutroScript.length) {
                const step = duoOutroScript[index];
                targetChar = step.char;
                targetEmotion = step.emotion;
            }
        }

        if (targetChar === 'east') {
            setEastEmotion(targetEmotion || 'normal');
            setWestEmotion('normal'); // Reset listener to normal
        } else if (targetChar === 'west') {
            setWestEmotion(targetEmotion || 'normal');
            setEastEmotion('normal'); // Reset listener to normal
        } else {
            // Reset to normal if no active script line (e.g. script ended, paused, or phase change)
            setEastEmotion('normal');
            setWestEmotion('normal');
        }
    }, [phase, sajuIntroStep, sajuOutroStep, duoScript, duoOutroScript]);

    // Selection Dialogues
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
            west: "태양(Sun)의 활력이 당신을 어떻게 지켜주고 있는지 볼까요?",
            bg: "/assets/bg/health.png"
        },
        academic: {
            east: "학문의 별이 당신을 비추고 있는지 확인해봅시다.",
            west: "수성(Mercury)의 지혜가 당신의 배움을 도울 것입니다.",
            bg: "/assets/bg/study.png" // Fallback or specific if added
        },
        career: {
            east: "당신의 앞길에 관운이 열려있는지 살펴보겠습니다.",
            west: "토성(Saturn)이 당신의 성취와 명예를 어떻게 돕고 있는지 확인해봐요.",
            bg: "/assets/bg/job.png"
        }
    };

    // Hover Explanation State
    const [hoveredField, setHoveredField] = useState<'name' | 'gender' | 'year' | 'date' | 'time' | null>(null);

    // Explanations Map
    // Field Mapping for East/West
    const FIELD_MAPPING: Record<string, 'east' | 'west'> = {
        name: 'east',
        year: 'east',
        time: 'east',
        gender: 'west',
        date: 'west'
    };

    const DEFAULT_EXPLANATIONS: Record<string, string> = {
        name: "이름의 획수와 소리에도 깊은 운명이 깃들어 있답니다.",
        gender: "남성과 여성, 그 에너지의 차이가 운명의 방향을 결정하죠.",
        year: "태어난 해는 당신의 뿌리와 근본을 의미해요.",
        date: "태어난 날짜로 당신의 태양 별자리와 본질을 알 수 있죠.",
        time: "태어난 시가 있어야만 비로소 사주팔자가 완성된답니다."
    };

    const getExplanationText = (field: string) => {
        const side = FIELD_MAPPING[field];
        if (!side) return "";
        const charId = side === 'east' ? settings.east : settings.west;
        return getCharacterInputScript(side, charId, field) || DEFAULT_EXPLANATIONS[field] || "";
    };

    // Helper for Zodiac (Declared early to use in useEffect)
    const getZodiacName = (m: number, d: number) => {
        const signs = [
            { name: '물병자리', start: { m: 1, d: 20 }, end: { m: 2, d: 18 } },
            { name: '물고기자리', start: { m: 2, d: 19 }, end: { m: 3, d: 20 } },
            { name: '양자리', start: { m: 3, d: 21 }, end: { m: 4, d: 19 } },
            { name: '황소자리', start: { m: 4, d: 20 }, end: { m: 5, d: 20 } },
            { name: '쌍둥이자리', start: { m: 5, d: 21 }, end: { m: 6, d: 21 } },
            { name: '게자리', start: { m: 6, d: 22 }, end: { m: 7, d: 22 } },
            { name: '사자자리', start: { m: 7, d: 23 }, end: { m: 8, d: 22 } },
            { name: '처녀자리', start: { m: 8, d: 23 }, end: { m: 9, d: 22 } },
            { name: '천칭자리', start: { m: 9, d: 23 }, end: { m: 10, d: 23 } },
            { name: '전갈자리', start: { m: 10, d: 24 }, end: { m: 11, d: 22 } },
            { name: '사수자리', start: { m: 11, d: 23 }, end: { m: 12, d: 21 } },
            { name: '염소자리', start: { m: 12, d: 22 }, end: { m: 1, d: 19 } },
        ];
        if ((m === 12 && d >= 22) || (m === 1 && d <= 19)) return '염소자리';
        const found = signs.find(z => {
            if (z.name === '염소자리') return false;
            if (m === z.start.m && d >= z.start.d) return true;
            if (m === z.end.m && d <= z.end.d) return true;
            return false;
        });
        return found ? found.name : '알 수 없음';
    };

    // Input Phase State
    const [activeModal, setActiveModal] = useState<keyof UserInfo | 'date' | 'question' | null>(null);
    const [userInfo, setUserInfo] = useState<UserInfo>({
        name: 'Kim Ssafy',
        gender: 'male',
        year: 2024,
        month: 1,
        day: 1,
        time: '12:00',
        solarConstellation: 'Capricorn'
    });

    // Fetch User Info Effect
    useEffect(() => {
        const fetchUserData = async () => {
            try {
                const token = localStorage.getItem('accessToken');
                if (!token) return;

                const decoded: any = jwtDecode(token);
                const userId = decoded.userId;

                if (userId) {
                    const data = await getUserInfo(userId);

                    // Parse Date: "YYYY-MM-DD"
                    let y = 1990, m = 1, d = 1;
                    if (data.birthDate) {
                        const parts = data.birthDate.split('-');
                        if (parts.length === 3) {
                            y = parseInt(parts[0]);
                            m = parseInt(parts[1]);
                            d = parseInt(parts[2]);
                        }
                    }

                    // Parse Time: "HH:MM" or "HH:MM:SS"
                    let formattedTime: string | null = null;
                    if (data.birthTime) {
                        const timeParts = data.birthTime.split(':');
                        if (timeParts.length >= 1) {
                            const h = parseInt(timeParts[0]);
                            // Format as HH:00 (discard minutes)
                            formattedTime = `${h.toString().padStart(2, '0')}:00`;
                        }
                    }

                    setUserInfo(prev => ({
                        ...prev,
                        name: data.nameKor || data.nickname || prev.name,
                        year: y,
                        month: m,
                        day: d,
                        time: formattedTime || prev.time,
                        solarConstellation: getZodiacName(m, d)
                    }));
                }
            } catch (error) {
                console.error("Failed to pre-fill user info", error);
            }
        };

        fetchUserData();
    }, []);
    const [loadingProgress, setLoadingProgress] = useState(0);

    // Unified Next Step Handler
    const handleNextStep = useCallback(() => {
        // Delegate to handleOutroClick if in saju_outro phase


        if (phase === 'input_info' && sajuOutroStep > 0) {
            if (sajuOutroStep < 2) {
                setSajuOutroStep(prev => prev + 1);
            } else if (sajuOutroStep >= 2) {
                setPhase('loading');
                setSajuOutroStep(0);
            }
            return;
        }

        if (phase === 'saju_intro') {
            if (sajuIntroStep < 11) {
                setSajuIntroStep(prev => prev + 1);
            } else {
                setPhase('input_info');
            }
        } else if (phase === 'fortune_intro') {
            if (fortuneIntroStep < 4) { // Changed from < 5 to < 4 for 5 steps (0-4)
                setFortuneIntroStep(prev => prev + 1);
            } else {
                setPhase('fortune_selection');
            }
        } else if (phase === 'fortune_outro') {
            if (fortuneOutroStep < 4) {
                setFortuneOutroStep(prev => prev + 1);
            }
        }
    }, [phase, sajuIntroStep, sajuOutroStep, fortuneIntroStep, fortuneOutroStep]);

    // Stable handler for selection
    const handleSelect = useCallback((question: string) => {
        setUserQuestion(question);
        setFortuneOutroStep(0);
        setPhase('fortune_outro');
    }, []);

    // Stable handler for hover to prevent re-renders
    const handleSelectionHover = useCallback((id: string | null) => {
        setSelectionHover(id);
    }, []);

    // Intro Sequence Logic
    useEffect(() => {
        if (phase === 'input_question') {
            if (introStep === 0) {
                const timer = setTimeout(() => setIntroStep(1), 2000);
                return () => clearTimeout(timer);
            } else if (introStep === 1) {
                const timer = setTimeout(() => setIntroStep(2), 2000);
                return () => clearTimeout(timer);
            }
        }

        // Auto-advance for Cinematic Intro (Voice & Reveal)
        if (phase === 'saju_intro') {
            if (sajuIntroStep < 2) {
                const timer = setTimeout(() => setSajuIntroStep(prev => prev + 1), 3500);
                return () => clearTimeout(timer);
            }
            else if (sajuIntroStep === 2) {
                const timer = setTimeout(() => setSajuIntroStep(prev => prev + 1), 3000);
                return () => clearTimeout(timer);
            }
            else if (sajuIntroStep >= 11) {
                const timer = setTimeout(() => setPhase('input_info'), 1500);
                return () => clearTimeout(timer);
            }
        }

        // Fortune Intro Logic
        if (phase === 'fortune_intro') {
            if (fortuneIntroStep === 0) {
                const timer = setTimeout(() => setFortuneIntroStep(1), 1000); // Start
                return () => clearTimeout(timer);
            } else if (fortuneIntroStep === 1) {
                const timer = setTimeout(() => setFortuneIntroStep(2), 3500); // Update dialogue
                return () => clearTimeout(timer);
            } else if (fortuneIntroStep === 2) {
                const timer = setTimeout(() => setFortuneIntroStep(3), 3500); // Update dialogue
                return () => clearTimeout(timer);
            } else if (fortuneIntroStep === 3) {
                const timer = setTimeout(() => setFortuneIntroStep(4), 3500); // New dialogue
                return () => clearTimeout(timer);
            } else if (fortuneIntroStep === 4) {
                const timer = setTimeout(() => setFortuneIntroStep(5), 3500); // New dialogue
                return () => clearTimeout(timer);
            } else if (fortuneIntroStep === 4) {
                const timer = setTimeout(() => setFortuneIntroStep(5), 3500); // New dialogue
                return () => clearTimeout(timer);
            } else if (fortuneIntroStep === 5) {
                const timer = setTimeout(() => {
                    setPhase('fortune_selection');
                }, 1500); // End
                return () => clearTimeout(timer);
            }
        }

    }, [phase, introStep, sajuIntroStep, fortuneIntroStep]);

    // Fortune Outro Logic (Western/Daily Mode)
    useEffect(() => {
        if (phase === 'fortune_outro') {
            if (fortuneOutroStep === 0) {
                const timer = setTimeout(() => setFortuneOutroStep(1), 1000);
                return () => clearTimeout(timer);
            } else if (fortuneOutroStep === 1) {
                const timer = setTimeout(() => setFortuneOutroStep(2), 2500);
                return () => clearTimeout(timer);
            } else if (fortuneOutroStep === 2) {
                const timer = setTimeout(() => setFortuneOutroStep(3), 2500);
                return () => clearTimeout(timer);
            } else if (fortuneOutroStep === 3) {
                const timer = setTimeout(() => setFortuneOutroStep(4), 2500);
                return () => clearTimeout(timer);
            } else if (fortuneOutroStep === 4) {
                const timer = setTimeout(() => {
                    setPhase('loading');
                }, 1000);
                return () => clearTimeout(timer);
            }
        }
    }, [phase, fortuneOutroStep]);

    // Saju Outro Logic (Unified Animation)
    useEffect(() => {
        if (phase === 'saju_outro') {
            if (duoOutroScript.length === 0) {
                const timer = setTimeout(() => navigate('/'), 2000);
                return () => clearTimeout(timer);
            }

            if (sajuOutroStep === 0) {
                // Start outro sequence
                const timer = setTimeout(() => setSajuOutroStep(1), 1000);
                return () => clearTimeout(timer);
            } else if (sajuOutroStep > 0 && sajuOutroStep < duoOutroScript.length) {
                // Continue showing dialogue
                const timer = setTimeout(() => {
                    setSajuOutroStep(prev => prev + 1);
                }, 3500);
                return () => clearTimeout(timer);
            } else if (sajuOutroStep === duoOutroScript.length) {
                // All dialogues shown, now trigger fade-out step
                const timer = setTimeout(() => {
                    setSajuOutroStep(prev => prev + 1); // Move to fade-out step
                }, 2500);
                return () => clearTimeout(timer);
            } else if (sajuOutroStep > duoOutroScript.length) {
                // Fade-out animation is playing, wait for it to complete then navigate
                const timer = setTimeout(() => {
                    navigate('/');
                }, 1500); // Wait for fade-out animation
                return () => clearTimeout(timer);
            }
        }

        // Pre-Analysis Outro Logic (input_info phase)
        if (phase === 'input_info' && sajuOutroStep > 0) {
            if (sajuOutroStep === 1) {
                // Step 1: Start immediately
                const timer = setTimeout(() => setSajuOutroStep(2), 100);
                return () => clearTimeout(timer);
            } else if (sajuOutroStep === 2) {
                // Step 2: Grayscale/Dim before closing (Short delay)
                const timer = setTimeout(() => setSajuOutroStep(3), 500);
                return () => clearTimeout(timer);
            } else if (sajuOutroStep === 3) {
                // Step 3: "Folding" animation (clipPath) takes 2.5s in CSS
                // Wait for animation to finish before switching phase
                const timer = setTimeout(() => {
                    setPhase('loading');
                    setSajuOutroStep(0);
                }, 2400); // Slightly less than 2.5s to ensure smooth swap
                return () => clearTimeout(timer);
            }
        }

    }, [sajuOutroStep, phase, duoOutroScript, navigate]);



    // Keyboard Navigation (Spacebar)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.code === 'Space' || e.key === ' ' || e.key === 'Enter') {
                // Handle in Intro Phases
                if (phase === 'saju_intro' || phase === 'fortune_intro') {
                    // Prevent default only if not interacting with inputs (simple check)
                    e.preventDefault();
                    handleNextStep();
                }
                // Handle in Saju Outro
                if (phase === 'saju_outro') {
                    e.preventDefault();
                    handleNextStep();
                }
                // Handle in Saju Outro (Analysis Result Loading Sequence)
                if (phase === 'input_info' && sajuOutroStep > 0) {
                    e.preventDefault();
                    handleNextStep();
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [phase, handleNextStep, sajuOutroStep, duoOutroScript, navigate]);

    // Loading Logic
    useEffect(() => {
        if (phase === 'loading') {
            // Loading Animation Timer (Unified for all modes as per request)
            const duration = 5000; // Increased to 5s as per user request
            const interval = 50;
            const steps = duration / interval;
            const increment = 100 / steps;

            const timer = setInterval(() => {
                setLoadingProgress(prev => {
                    // STALL LOGIC: If SAJU mode, wait for API result
                    if (mode === 'saju') {
                        if (prev >= 90 && sajuApiState.current.status !== 'success') {
                            // If error occurred, stop loading and go back
                            if (sajuApiState.current.status === 'error') {
                                clearInterval(timer);
                                alert("운세 분석 중 오류가 발생했습니다. 다시 시도해주세요.");
                                setPhase('input_info');
                                return 0;
                            }
                            // Stall at 90%
                            return 90;
                        }
                    }

                    const next = prev + increment;
                    if (next >= 100) {
                        clearInterval(timer);
                        setTimeout(() => {
                            // COMPLETE
                            if (mode === 'saju') {
                                if (sajuApiState.current.data) {
                                    // console.log("--> [FortunePage] Setting Result:", sajuApiState.current.data);
                                    setFortuneResult(sajuApiState.current.data);
                                    setPhase('result');
                                } else {
                                    console.error("--> [FortunePage] Data is missing even though status is success");
                                    alert("데이터를 불러오지 못했습니다.");
                                    setPhase('input_info');
                                }
                            } else {
                                // Daily/Fortune Mode (Requires API or implementation)
                                console.warn("Daily mode currently disabled or requires API");
                                alert("오늘의 운세 기능은 준비 중입니다.");
                                setPhase('input_info');
                                // const result = getRandomFortuneV2();
                                // setFortuneResult(result);
                                // setPhase('debate');
                                // setDebateStep(0);
                            }
                            clearInterval(timer); // Ensure clear interval happens
                        }, 500);
                        return 100;
                    }
                    return next;
                });
            }, interval);
            return () => clearInterval(timer);
        }
    }, [phase, mode]);

    // Dynamic Intro Text
    // State moved to top
    // Effect moved to top

    const PRE_INTRO_TEXT = [
        { text: getCharacterSajuIntro('west', settings.west), char: "west", font: "font-serif text-indigo-300" },
        // ... (Keep existing if needed for PRE_INTRO part (voice over), but strictly speaking we might not need it if replacing entirely. 
        // The user said "replace saju_intro part". The voice over part (lines 998-1015) uses PRE_INTRO_TEXT.
        // We can keep it or replace it. I'll keep PRE_INTRO_TEXT for the "voice over" cinematic start if generic, but maybe replace rendering logic later)
        { text: getCharacterSajuIntro('east', settings.east), char: "east", font: "font-['JoseonPalace'] text-amber-200" }
    ];


    const handleSkip = (e: React.MouseEvent) => {
        e.stopPropagation();
        if (phase === 'saju_intro') {
            setPhase('input_info');
        } else if (phase === 'input_info' && sajuOutroStep > 0) {
            // Skip directly to loading
            setPhase('loading');
        }
    };

    const handleStartIntro = () => {
        setIntroStep(0);
        if (mode === 'saju') {
            setSajuIntroStep(0);
            setPhase('saju_intro');
        } else {
            setPhase('input_question');
        }
    };

    const handleConfirmAnalysis = () => {
        if (mode === 'saju') {
            // 1. Trigger UI transition immediately (Step 1 of Outro)
            setSajuOutroStep(1);

            // 2. Start API Request in the background
            sajuApiState.current = { status: 'loading', data: null };

            // Run async logic without blocking the main thread
            (async () => {
                try {
                    // Sync current UI info to Backend User Profile
                    const updateData: UserUpdateRequest = {
                        nameKor: userInfo.name,
                        gender: userInfo.gender === 'male' ? 'M' : 'F',
                        birthDate: `${userInfo.year}-${String(userInfo.month).padStart(2, '0')}-${String(userInfo.day).padStart(2, '0')}`,
                        birthTime: (userInfo.time && userInfo.time !== '알 수 없음') ? (() => {
                            const timePart = userInfo.time.split(' ')[0]; // e.g., "7:00" or "18:00"
                            const [h, m] = timePart.split(':');
                            return `${h.padStart(2, '0')}:${(m || '00').padStart(2, '0')}`;
                        })() : undefined,
                        isSolar: true
                    };

                    await updateProfile(updateData);

                    // Trigger Saju Analysis
                    const data = await getSajuAnalysis();
                    sajuApiState.current = { status: 'success', data };
                } catch (err: any) {
                    console.error("--> [FortunePage] background API Error:", err);
                    sajuApiState.current = { status: 'error', data: null };

                    // Handle session expiry globally
                    if (err.response?.status === 401) {
                        alert("세션이 만료되었습니다. 다시 로그인해주세요.");
                        navigate('/');
                    }
                }
            })();
        } else {
            setPhase('loading');
        }
    };

    const fieldIsActive = (char: 'east' | 'west') => hoveredField && FIELD_MAPPING[hoveredField] === char;



    const renderModalContent = () => {
        switch (activeModal) {
            case 'name':
                return (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm">
                        <ScrollNameInput
                            onConfirm={(val) => {
                                setUserInfo(prev => ({ ...prev, name: val }));
                                setActiveModal(null);
                            }}
                            initialName={userInfo.name}
                            onClose={() => setActiveModal(null)}
                        />
                    </div>
                );
            case 'gender':
                return (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm">
                        <YinYangGenderInput
                            onSelect={(val) => {
                                setUserInfo(prev => ({ ...prev, gender: val === '남성' ? 'male' : 'female' }));
                                setActiveModal(null);
                            }}
                            onClose={() => setActiveModal(null)}
                        />
                    </div>
                );
            case 'year':
                return (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm">
                        <GapjaYearInput
                            onSelect={(val) => {
                                setUserInfo(prev => ({ ...prev, year: parseInt(val) }));
                                setActiveModal(null);
                            }}
                            initialYear={userInfo.year ? userInfo.year : 1990}
                            onClose={() => setActiveModal(null)}
                        />
                    </div>
                );
            case 'date':
                return (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm">
                        <SolarConstellationInput
                            initialMonth={userInfo.month ? userInfo.month : 1}
                            initialDay={userInfo.day ? userInfo.day : 15}
                            year={userInfo.year ? userInfo.year : 2000}
                            onSelect={(m, d) => {
                                setUserInfo(prev => ({ ...prev, month: parseInt(m), day: parseInt(d) }));
                                setActiveModal(null);
                            }}
                            onClose={() => setActiveModal(null)}
                        />
                    </div>
                );
            case 'time':
                return (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                        <div className="w-full max-w-lg h-[700px] rounded-3xl overflow-hidden shadow-2xl relative">
                            <TimeInput
                                onSelect={(hour, min, period) => {
                                    setUserInfo(prev => ({ ...prev, time: `${hour}:${min} ${period} ` }));
                                    setActiveModal(null);
                                }}
                                onUnknown={() => {
                                    setUserInfo(prev => ({ ...prev, time: '알 수 없음' }));
                                    setActiveModal(null);
                                }}
                                onClose={() => setActiveModal(null)}
                            />
                        </div>
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div className="fixed inset-0 z-50 bg-black text-white overflow-hidden flex flex-col font-sans">
            {/* Header / Nav (Only show during input phases if needed) */}
            {(phase !== 'loading' && phase !== 'result') && (
                <div className="absolute top-0 left-0 w-full p-4 flex justify-between items-center z-50 bg-gradient-to-b from-black/80 to-transparent pointer-events-none">

                </div>
            )}

            {/* Modal Layer */}
            <AnimatePresence>
                {activeModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0, pointerEvents: 'none' }}
                        transition={{ duration: 0.3 }}
                        className="fixed inset-0 z-[100]"
                    >
                        {renderModalContent()}
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Content Area */}
            <div className="flex-1 relative flex flex-col items-center justify-center p-4">

                {/* 1. Global Background Layer (for Selection & Outro) */}
                <AnimatePresence>
                    {(phase === 'fortune_selection' || phase === 'fortune_outro') && (
                        <motion.div
                            initial={{ opacity: 0, clipPath: "inset(0 0% 0 0%)" }}
                            animate={{
                                opacity: (phase === 'fortune_outro' && fortuneOutroStep >= 4) ? 0 : 1,
                                clipPath: (phase === 'fortune_outro' && fortuneOutroStep >= 4) ? "inset(0 50% 0 50%)" : "inset(0 0% 0 0%)"
                            }}
                            exit={{ opacity: 0 }}
                            transition={{ duration: 1, ease: "easeInOut" }}
                            className="absolute inset-0 z-0 bg-black"
                        >
                            {/* Default BG */}
                            <div className="absolute inset-0 bg-cover bg-center opacity-60 scale-x-[-1] blur-[2px]" style={{ backgroundImage: `url('/assets/bg/fortune_bg_oriental.png')` }} />

                            {/* Hover Dynamic BG */}
                            <AnimatePresence>
                                {selectionHover && SELECTION_DIALOGUES[selectionHover] && (
                                    <motion.div
                                        key={selectionHover}
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.5 }}
                                        className="absolute inset-0 bg-cover bg-center opacity-80 scale-x-[-1] blur-sm transition-all duration-700"
                                        style={{
                                            backgroundImage: `url('${SELECTION_DIALOGUES[selectionHover].bg}')`,
                                            maskImage: 'radial-gradient(circle, black 30%, transparent 80%)',
                                            WebkitMaskImage: 'radial-gradient(circle, black 30%, transparent 80%)'
                                        }}
                                    />
                                )}
                            </AnimatePresence>
                            <div className="absolute inset-0 bg-black/30" />
                        </motion.div>
                    )}
                </AnimatePresence>


                {/* INTRO PHASE (Landing) */}
                <AnimatePresence>
                    {phase === 'intro' && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 1.1 }}
                            className="text-center space-y-8 max-w-lg z-10"
                        >
                            <ParticleBackground type="eastern" className="opacity-30" />
                            <div className="flex justify-center gap-8 mb-8 relative">
                                <div className="text-center group">
                                    <div className="w-24 h-24 rounded-full bg-amber-900/50 border-2 border-amber-500/50 flex items-center justify-center mb-2 mx-auto group-hover:scale-110 transition-transform duration-500 overflow-hidden">
                                        <img src="/assets/images/east.png" alt="East" className="w-full h-full object-cover object-top opacity-80" />
                                    </div>
                                    <p className="font-['Gowun_Batang'] text-amber-200">{EastName}</p>
                                </div>
                                <div className="text-center group">
                                    <div className="w-24 h-24 rounded-full bg-indigo-900/50 border-2 border-indigo-500/50 flex items-center justify-center mb-2 mx-auto group-hover:scale-110 transition-transform duration-500 overflow-hidden">
                                        <img src="/assets/images/west.png" alt="West" className="w-full h-full object-cover object-top opacity-80" />
                                    </div>
                                    <p className="font-['Gowun_Batang'] text-indigo-200">{WestName}</p>
                                </div>
                            </div>
                            <h1 className="text-4xl font-['Nanum_Brush_Script'] bg-gradient-to-r from-amber-200 to-indigo-200 bg-clip-text text-transparent">운명의 대토론</h1>
                            <p className="text-white/60 font-light leading-relaxed">
                                당신의 사주 정보를 바탕으로<br />
                                동서양의 현자들이 운명을 논합니다.
                            </p>
                            <button
                                onClick={handleStartIntro}
                                className="px-10 py-3 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full transition-all hover:scale-105 active:scale-95 backdrop-blur-sm"
                            >
                                바로 분석하기
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* UNIFIED CHARACTER DISPLAY (Intro & Selection & Outro & Debate) */}
                <AnimatePresence>
                    {(phase === 'fortune_intro' || phase === 'fortune_selection' || phase === 'fortune_outro') && (
                        <div
                            className={`absolute inset-0 z-10 flex items-end pointer-events-none transition-all duration-1000 ease-in-out
                                ${(phase === 'fortune_intro' || phase === 'fortune_outro') ? 'justify-center gap-16 md:gap-32 pb-16' : 'justify-between px-4 md:px-40 pb-0'}
                            `}
                        >
                            {/* West Character (Left/Center-Left) */}
                            <motion.div
                                layout
                                initial={{ opacity: 0, x: -50 }}
                                animate={{
                                    opacity: (phase === 'fortune_intro' && fortuneIntroStep >= 1) ? 1 :
                                        (phase === 'fortune_outro' && fortuneOutroStep >= 4) ? 0 : 1,
                                    x: 0,
                                    scale: (phase === 'fortune_intro' && (fortuneIntroStep === 1 || fortuneIntroStep === 3)) ||
                                        (phase === 'fortune_outro' && (fortuneOutroStep === 0 || fortuneOutroStep === 2))
                                        ? 1.05 : 1,
                                    filter: "none"
                                }}
                                exit={{ opacity: 0, x: -100 }}
                                transition={{ duration: 0.5, layout: { duration: 1.2, type: "spring", bounce: 0.2 } }}
                                className="relative flex flex-col items-center"
                            >
                                <AnimatePresence mode="wait">
                                    {/* Intro Bubble */}
                                    {phase === 'fortune_intro' && (fortuneIntroStep === 1 || fortuneIntroStep === 3) && (
                                        <AnimatedBubble
                                            key="west-intro"
                                            theme="indigo"
                                            size="large"
                                            title={WestName}
                                            className="bottom-[110%] left-1/2 -translate-x-1/2 min-w-[300px]"
                                            text={fortuneIntroStep === 1 ? `"오늘의 별들이 당신에게\n어떤 이야기를 속삭일까요?"` : `"우주의 흐름은 매 순간 변하니,\n지금 이 순간이 가장 중요합니다."`}
                                        />
                                    )}
                                    {/* Selection Bubble */}
                                    {phase === 'fortune_selection' && selectionHover && SELECTION_DIALOGUES[selectionHover] && (
                                        <AnimatedBubble
                                            key="west-selection"
                                            theme="indigo"
                                            size="large"
                                            title={WestName}
                                            className="bottom-96 left-0 md:left-auto min-w-[200px] md:min-w-[250px] mb-20"
                                            text={SELECTION_DIALOGUES[selectionHover].west}
                                        />
                                    )}
                                    {/* Outro Bubble - Step 2 */}
                                    {phase === 'fortune_outro' && fortuneOutroStep === 2 && (
                                        <AnimatedBubble
                                            key="west-outro"
                                            theme="indigo"
                                            size="large"
                                            title={WestName}
                                            className="bottom-[110%] left-1/2 -translate-x-1/2 min-w-[300px]"
                                            text={'“별들이 당신의 길을 비추기 시작했습니다.”'}
                                        />
                                    )}

                                </AnimatePresence>
                                <motion.div
                                    layout
                                    className={`relative transition-all duration-1000 ${(phase === 'fortune_intro' || phase === 'fortune_outro') ? 'w-[300px] h-[400px]' : 'w-[180px] h-[280px] md:w-[260px] md:h-[400px]'} contrast-125 brightness-110`}
                                >
                                    <img src={WestStarImg} className="w-full h-full object-contain drop-shadow-[0_0_30px_rgba(99,102,241,0.6)]" />
                                </motion.div>
                            </motion.div>

                            {/* East Character (Right/Center-Right) */}
                            <motion.div
                                layout
                                initial={{ opacity: 0, x: 50 }}
                                animate={{
                                    opacity: (phase === 'fortune_intro' && fortuneIntroStep >= 2) ? 1 :
                                        (phase === 'fortune_outro' && fortuneOutroStep >= 4) ? 0 : 1,
                                    x: 0,
                                    scale: (phase === 'fortune_intro' && (fortuneIntroStep === 2 || fortuneIntroStep === 4 || fortuneIntroStep === 5)) ||
                                        (phase === 'fortune_outro' && (fortuneOutroStep === 0 || fortuneOutroStep === 1 || fortuneOutroStep === 3))
                                        ? 1.05 : 1,
                                    filter: "none"
                                }}
                                exit={{ opacity: 0, x: 100 }}
                                transition={{ duration: 0.5, layout: { duration: 1.2, type: "spring", bounce: 0.2 } }}
                                className="relative flex flex-col items-center"
                            >
                                <AnimatePresence mode="wait">
                                    {/* Intro Bubble */}
                                    {phase === 'fortune_intro' && (fortuneIntroStep === 2 || fortuneIntroStep === 4 || fortuneIntroStep === 5) && (
                                        <AnimatedBubble
                                            key="east-intro"
                                            theme="amber"
                                            size="large"
                                            title={EastName}
                                            className="bottom-[110%] left-1/2 -translate-x-1/2 min-w-[300px]"
                                            text={fortuneIntroStep === 2 ? `"음양의 흐름을 통해\n당신의 하루를 미리 짚어드리겠습니다."` : fortuneIntroStep === 4 ? `"준비되셨다면,\n당신의 하루를 펼쳐보겠습니다."` : `"자, 어떤 운명이 기다리고 있을지\n확인해 봅시다."`}
                                        />
                                    )}
                                    {/* Selection Bubble */}
                                    {phase === 'fortune_selection' && selectionHover && SELECTION_DIALOGUES[selectionHover] && (
                                        <AnimatedBubble
                                            key="east-selection"
                                            theme="amber"
                                            size="large"
                                            title={EastName}
                                            className="bottom-96 right-0 md:right-auto min-w-[200px] md:min-w-[250px] mb-20"
                                            text={SELECTION_DIALOGUES[selectionHover].east}
                                        />
                                    )}
                                    {/* Outro Bubble - Step 1 */}
                                    {phase === 'fortune_outro' && fortuneOutroStep === 1 && (
                                        <AnimatedBubble
                                            key="east-outro"
                                            theme="amber"
                                            size="large"
                                            title={EastName}
                                            className="bottom-[110%] left-1/2 -translate-x-1/2 min-w-[300px]"
                                            text={'“운명의 흐름을 읽어보겠습니다.”'}
                                        />
                                    )}
                                    {/* Outro Bubble - Step 3 (Final) */}
                                    {phase === 'fortune_outro' && fortuneOutroStep === 3 && (
                                        <AnimatedBubble
                                            key="east-outro-final"
                                            theme="amber"
                                            size="large"
                                            title={EastName}
                                            className="bottom-[110%] left-1/2 -translate-x-1/2 min-w-[300px]"
                                            text={'“자, 그대에게 깃든 기운을 확인해봅시다.”'}
                                        />
                                    )}

                                </AnimatePresence>
                                <motion.div
                                    layout
                                    className={`relative transition-all duration-1000 ${(phase === 'fortune_intro' || phase === 'fortune_outro') ? 'w-[300px] h-[400px]' : 'w-[180px] h-[280px] md:w-[260px] md:h-[400px]'} contrast-125 brightness-110`}
                                >
                                    <img src={EastSajuImg} className="w-full h-full object-contain drop-shadow-[0_0_30px_rgba(251,191,36,0.6)]" />
                                </motion.div>
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>

                {/* FORTUNE INTRO & OUTRO PHASE - Click Overlay */}
                <AnimatePresence>
                    {(phase === 'fortune_intro' || phase === 'fortune_outro') && (
                        <div className="absolute inset-0 z-20 flex flex-col items-center justify-center p-4 pointer-events-none">
                            <motion.div
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                className="absolute inset-0 pointer-events-auto"
                            >
                                {/* Removed dark overlay */}
                                {/* Click Handler Overlay */}
                                <div className="absolute inset-0 z-50 cursor-pointer" onClick={handleNextStep} />
                            </motion.div>

                            {/* Empty container to maintain layout structure if needed, or just remove */}
                        </div>
                    )}
                </AnimatePresence>

                {/* Interaction Blocker during Transition */}
                {/* Interaction Blocker during Transition (Removed as cinematic handles it) */}




                {/* DEBATE CHOICE OVERLAY (After Debate) */}
                <AnimatePresence>
                    {phase === 'debate' && debateStep === 3 && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm"
                        >
                            <h2 className="text-3xl md:text-5xl font-['Gowun_Batang'] text-white font-bold mb-12 drop-shadow-lg">
                                토론이 종료되었습니다.
                            </h2>
                            <div className="flex gap-8 pointer-events-auto">
                                <button
                                    onClick={() => {
                                        setUserQuestion(""); // Clear previous
                                        setActiveModal('question');
                                    }}
                                    className="px-10 py-4 rounded-full bg-white/10 hover:bg-white/20 border border-white/30 backdrop-blur-md text-white text-xl font-bold transition-all hover:scale-105 hover:shadow-[0_0_30px_rgba(255,255,255,0.3)]"
                                >
                                    추가 질문하기
                                </button>
                                <button
                                    onClick={() => setPhase('result')}
                                    className="px-10 py-4 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white text-xl font-bold shadow-lg shadow-indigo-900/50 transition-all hover:scale-110 hover:shadow-[0_0_40px_rgba(99,102,241,0.6)]"
                                >
                                    결과 확인하기
                                </button>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* QUESTION MODAL */}
                <AnimatePresence>
                    {activeModal === 'question' && (
                        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                            <motion.div
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.9 }}
                                className="bg-gray-900 border border-white/20 rounded-2xl p-8 max-w-lg w-full shadow-2xl space-y-6"
                            >
                                <>
                                    <h3 className="text-2xl font-['Gowun_Batang'] text-white mb-4">무엇이 궁금하신가요?</h3>
                                    <textarea
                                        className="w-full bg-black/50 border border-white/10 rounded-xl p-4 text-white resize-none h-32 focus:outline-none focus:border-indigo-500 transition-colors"
                                        placeholder="질문을 입력해주세요..."
                                        onKeyDown={(e) => {
                                            if (e.key === 'Enter' && !e.shiftKey) {
                                                e.preventDefault();
                                                const val = e.currentTarget.value;
                                                if (val.trim()) {
                                                    setUserQuestion(val.trim());
                                                    setDebateStep(0);
                                                    setPhase('debate');
                                                    setActiveModal(null);
                                                }
                                            }
                                        }}
                                        id="q-input"
                                    />
                                    <div className="flex justify-end gap-3">
                                        <button
                                            onClick={() => setActiveModal(null)}
                                            className="px-6 py-2 rounded-lg text-white/60 hover:text-white"
                                        >
                                            취소
                                        </button>
                                        <button
                                            onClick={() => {
                                                const input = document.getElementById('q-input') as HTMLTextAreaElement;
                                                if (input && input.value.trim()) {
                                                    setUserQuestion(input.value.trim());
                                                    setDebateStep(0);
                                                    setPhase('debate');
                                                    setActiveModal(null);
                                                }
                                            }}
                                            className="px-6 py-2 bg-indigo-600 rounded-lg text-white hover:bg-indigo-500"
                                        >
                                            질문하기
                                        </button>
                                    </div>
                                </>
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>

                {/* FORTUNE SELECTION PHASE (New Immersive) */}


                {/* FORTUNE SELECTION PHASE (New Immersive) */}
                <AnimatePresence>
                    {phase === 'fortune_selection' && (
                        <div className="absolute inset-0 flex items-center justify-center">
                            {/* Selection Menu (Centered) */}
                            <FortuneSelection
                                onSelect={handleSelect}
                                onHover={handleSelectionHover}
                            />
                        </div>
                    )}
                </AnimatePresence>

                {/* SAJU INTRO & INPUT CHARACTERS */}
                <AnimatePresence>
                    {((mode === 'saju') && (phase === 'saju_intro' || phase === 'input_info' || phase === 'saju_outro')) && (
                        <div className="absolute inset-0 z-20 overflow-hidden flex flex-col items-center justify-center">
                            {/* Click Handler & Skip Button */}
                            {((phase === 'saju_intro' && sajuOutroStep === 0)) && (
                                <>
                                    <div className="absolute inset-0 z-50 cursor-pointer" onClick={handleNextStep} />
                                    <button onClick={handleSkip} className="absolute top-8 right-8 z-[60] px-4 py-2 bg-white/10 hover:bg-white/20 border border-white/20 rounded-full text-white/80 text-sm backdrop-blur-sm transition-all flex items-center gap-2 group">
                                        SKIP <ChevronRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                                    </button>
                                </>
                            )}

                            {/* Cinematic Pre-Intro Voice Over */}
                            <AnimatePresence mode="wait">
                                {(phase === 'saju_intro' && sajuIntroStep < 2) && (
                                    <div className="absolute inset-0 z-40 flex items-center justify-center bg-black pointer-events-none">
                                        <motion.p
                                            key={sajuIntroStep}
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, y: -10 }}
                                            transition={{ duration: 0.8 }}
                                            className={`text-2xl md:text-3xl font-bold tracking-widest px-4 text-center ${PRE_INTRO_TEXT[sajuIntroStep]?.font || "text-white"}`}
                                        >
                                            {PRE_INTRO_TEXT[sajuIntroStep]?.text}
                                        </motion.p>
                                        <div className="absolute bottom-20 animate-bounce text-white/50 text-sm">
                                            ▼ 화면을 클릭하세요
                                        </div>
                                    </div>
                                )}
                            </AnimatePresence>

                            {/* Background Layer */}
                            <motion.div
                                initial={{ clipPath: "inset(0 50% 0 50%)", opacity: 0 }}
                                animate={{
                                    clipPath: (phase === 'saju_outro' && sajuOutroStep >= duoOutroScript.length) ? "inset(0 50% 0 50%)" :
                                        (phase === 'input_info' && sajuOutroStep >= 3) ? "inset(0 50% 0 50%)" :
                                            ((phase === 'input_info' || sajuIntroStep >= 2) ? "inset(0 0% 0 0%)" : "inset(0 50% 0 50%)"),
                                    opacity: (phase === 'saju_outro' && sajuOutroStep >= duoOutroScript.length) ? 0 :
                                        (phase === 'input_info' && sajuOutroStep >= 3) ? 0 :
                                            ((phase === 'input_info' || sajuIntroStep >= 2) ? 1 : 0)
                                }}
                                transition={{ duration: (phase === 'saju_outro' && sajuOutroStep >= duoOutroScript.length) ? 1.2 : 2.5, ease: "easeInOut" }}
                                className="absolute inset-0 z-0 pointer-events-none"
                            >
                                <div className="absolute inset-0 bg-cover bg-center bg-no-repeat" style={{ backgroundImage: `url('/assets/login_page/back2.png')` }} />
                                <div className="absolute inset-0 bg-cover bg-center bg-no-repeat w-full h-full" style={{ backgroundImage: `url('/assets/login_page/back3.png')`, maskImage: 'linear-gradient(to right, black 30%, transparent 70%)', WebkitMaskImage: 'linear-gradient(to right, black 30%, transparent 70%)' }} />
                                <div className="absolute inset-0 bg-gradient-to-r from-slate-900/40 via-transparent to-amber-900/30 mix-blend-overlay" />
                                <div className="absolute inset-0 bg-black/20 backdrop-blur-[2px]" />
                            </motion.div>

                            <div className="max-w-full w-full flex flex-col items-center relative h-[500px] justify-center pointer-events-none">
                                <div className={`flex justify-center items-end ${(phase === 'input_info' && sajuOutroStep === 0) ? 'gap-0 md:gap-[600px]' : (phase === 'saju_outro' || sajuOutroStep > 0) ? 'gap-0 md:gap-56' : 'gap-0 md:gap-24'} w-full z-10 mt-10 transition-all duration-1000 ease-in-out`}>
                                    <motion.div
                                        initial={{ opacity: 0, y: 50, x: 0 }}
                                        animate={{
                                            opacity: (phase === 'saju_outro') ? 1 :
                                                (sajuOutroStep === 3) ? 0 :
                                                    (phase === 'input_info' || sajuIntroStep === 11) ? (hoveredField && FIELD_MAPPING[hoveredField] === 'west' ? 1 : (sajuOutroStep > 0 ? 1 : 0.4)) :
                                                        (sajuIntroStep >= 2 ? 1 : 0),
                                            y: (phase === 'saju_outro') ? 0 :
                                                (sajuOutroStep === 3) ? 50 :
                                                    (phase === 'input_info' || sajuIntroStep >= 2) ? 0 : 50,
                                            x: (hoveredField && FIELD_MAPPING[hoveredField] === 'west') ? 30 : 0,
                                            scale: (phase === 'saju_outro' && duoOutroScript[sajuOutroStep - 1]?.char === 'west') ? 1.05 :
                                                (sajuOutroStep === 1 && phase === 'input_info') ? 1.05 :
                                                    (hoveredField && FIELD_MAPPING[hoveredField] === 'west') ? 1.05 : 1,
                                            filter: (phase === 'saju_outro') ? (duoOutroScript[sajuOutroStep - 1]?.char === 'west' ? "none" : "grayscale(80%)") :
                                                (sajuOutroStep > 0 && phase === 'input_info') ? (sajuOutroStep === 1 ? "none" : "grayscale(80%)") :
                                                    (phase === 'input_info' || sajuIntroStep === 11) ? (hoveredField && FIELD_MAPPING[hoveredField] === 'west' ? "none" : "grayscale(80%)") :
                                                        ([4, 6, 8, 10].includes(sajuIntroStep) ? "brightness(1.1)" : "brightness(0.9)")
                                        }}
                                        transition={{ duration: 0.4, ease: "easeOut" }}
                                        className="relative flex flex-col items-center"
                                    >
                                        <AnimatePresence>

                                            {(fieldIsActive('west') && sajuOutroStep === 0) && <AnimatedBubble theme="indigo" size="large" title={WestName} className="bottom-16 left-1/2 -translate-x-1/2" text={hoveredField ? getExplanationText(hoveredField) : ""} />}

                                            {/* Dynamic Duo Intro */}
                                            {(phase === 'saju_intro' && [4, 6, 8, 10].includes(sajuIntroStep)) && (
                                                <AnimatedBubble
                                                    theme="indigo"
                                                    size="large"
                                                    title={WestName}
                                                    className="bottom-16 left-1/2 -translate-x-1/2"
                                                    text={duoScript[sajuIntroStep - 3]?.text || "..."}
                                                />
                                            )}

                                            {/* Final Outro Bubbles for West - Only in saju_outro phase now */}
                                            {((phase === 'saju_outro') && duoOutroScript[sajuOutroStep - 1] && duoOutroScript[sajuOutroStep - 1].char === 'west') && (
                                                <AnimatedBubble
                                                    theme="indigo"
                                                    size="large"
                                                    title={WestName}
                                                    className="bottom-16 left-1/2 -translate-x-1/2"
                                                    text={duoOutroScript[sajuOutroStep - 1].text}
                                                />
                                            )}
                                        </AnimatePresence>
                                        <div className="w-[200px] h-[300px] md:w-[350px] md:h-[450px] relative z-0">
                                            <img src={WestStarImg} alt="West Star" className="w-full h-full object-contain drop-shadow-[0_0_15px_rgba(0,0,0,0.5)]" />
                                        </div>
                                    </motion.div>

                                    <motion.div
                                        initial={{ opacity: 0, y: 50, x: 0 }}
                                        animate={{
                                            opacity: (phase === 'saju_outro') ? 1 :
                                                (sajuOutroStep === 3) ? 0 :
                                                    (phase === 'input_info' || sajuIntroStep === 11) ? (hoveredField && FIELD_MAPPING[hoveredField] === 'east' ? 1 : (sajuOutroStep > 0 ? 1 : 0.4)) :
                                                        (sajuIntroStep >= 2 ? 1 : 0),
                                            y: (phase === 'saju_outro') ? 0 :
                                                (sajuOutroStep === 3) ? 50 :
                                                    (phase === 'input_info' || sajuIntroStep >= 2) ? 0 : 50,
                                            x: (hoveredField && FIELD_MAPPING[hoveredField] === 'east') ? -30 : 0,
                                            scale: (phase === 'saju_outro' && duoOutroScript[sajuOutroStep - 1]?.char === 'east') ? 1.05 :
                                                (sajuOutroStep === 2) ? 1.05 :
                                                    (hoveredField && FIELD_MAPPING[hoveredField] === 'east') ? 1.05 : 1,
                                            filter: (phase === 'saju_outro') ? (duoOutroScript[sajuOutroStep - 1]?.char === 'east' ? "none" : "grayscale(80%)") :
                                                (sajuOutroStep > 0) ? (sajuOutroStep === 2 ? "none" : "grayscale(80%)") :
                                                    (phase === 'input_info' || sajuIntroStep === 11) ? (hoveredField && FIELD_MAPPING[hoveredField] === 'east' ? "none" : "grayscale(80%)") :
                                                        ([3, 5, 7, 9].includes(sajuIntroStep) ? "brightness(1.1)" : "brightness(0.9)")
                                        }}
                                        transition={{ duration: 0.4, ease: "easeOut" }}
                                        className="relative flex flex-col items-center"
                                    >
                                        <AnimatePresence>

                                            {(fieldIsActive('east') && sajuOutroStep === 0) && <AnimatedBubble theme="amber" size="large" title={EastName} className="bottom-16 left-1/2 -translate-x-1/2" text={hoveredField ? getExplanationText(hoveredField) : ""} />}

                                            {/* Dynamic Duo Intro: East Speaks on ODD indices (0, 2, 4, 6) => Steps 3, 5, 7, 9 */}
                                            {(phase === 'saju_intro' && [3, 5, 7, 9].includes(sajuIntroStep)) && (
                                                <AnimatedBubble
                                                    theme="amber"
                                                    size="large"
                                                    title={EastName}
                                                    className="bottom-16 left-1/2 -translate-x-1/2"
                                                    text={duoScript[sajuIntroStep - 3]?.text || "..."}
                                                />
                                            )}

                                            {/* Final Outro Bubbles for East - Only in saju_outro phase now */}
                                            {((phase === 'saju_outro') && duoOutroScript[sajuOutroStep - 1] && duoOutroScript[sajuOutroStep - 1].char === 'east') && (
                                                <AnimatedBubble
                                                    theme="amber"
                                                    size="large"
                                                    title={EastName}
                                                    className="bottom-16 left-1/2 -translate-x-1/2"
                                                    text={duoOutroScript[sajuOutroStep - 1].text}
                                                />
                                            )}
                                        </AnimatePresence>
                                        <div className="w-[200px] h-[300px] md:w-[350px] md:h-[450px] relative z-0">
                                            <img src={EastSajuImg} alt="East Saju" className="w-full h-full object-contain drop-shadow-[0_0_15px_rgba(0,0,0,0.5)]" />
                                        </div>
                                    </motion.div>
                                </div>
                            </div>
                        </div>
                    )}
                </AnimatePresence>

                {/* INPUT DASHBOARD PHASE */}
                <AnimatePresence>
                    {phase === 'input_info' && sajuOutroStep === 0 && (
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 1.05 }}
                            className="w-full max-w-sm bg-black/40 backdrop-blur-xl border border-white/10 rounded-2xl p-6 shadow-2xl z-20"
                        >
                            <h2 className="text-xl font-['Gowun_Batang'] text-center mb-6 text-amber-100">사주 정보 확인</h2>
                            <div className="space-y-3 mb-6">
                                <div onClick={() => setActiveModal('name')} onMouseEnter={() => setHoveredField('name')} onMouseLeave={() => setHoveredField(null)} className="p-4 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 cursor-pointer transition-all flex justify-between items-center group">
                                    <span className="text-white/40 text-xs">이름</span>
                                    <span className="text-base font-bold group-hover:text-amber-300 transition-colors">{userInfo.name}</span>
                                </div>
                                <div onMouseEnter={() => setHoveredField('gender')} onMouseLeave={() => setHoveredField(null)} className="p-4 bg-white/5 rounded-xl border border-white/10 transition-all">
                                    <span className="text-white/40 text-xs block mb-2">성별</span>
                                    <div className="flex gap-2">
                                        <button
                                            onClick={() => setUserInfo(prev => ({ ...prev, gender: 'male' }))}
                                            className={`flex-1 py-2 px-4 rounded-lg font-bold text-sm transition-all ${userInfo.gender === 'male' ? 'bg-blue-500/80 text-white' : 'bg-white/10 text-white/60 hover:bg-white/20'}`}
                                        >
                                            남성
                                        </button>
                                        <button
                                            onClick={() => setUserInfo(prev => ({ ...prev, gender: 'female' }))}
                                            className={`flex-1 py-2 px-4 rounded-lg font-bold text-sm transition-all ${userInfo.gender === 'female' ? 'bg-pink-500/80 text-white' : 'bg-white/10 text-white/60 hover:bg-white/20'}`}
                                        >
                                            여성
                                        </button>
                                    </div>
                                </div>
                                <div onClick={() => setActiveModal('year')} onMouseEnter={() => setHoveredField('year')} onMouseLeave={() => setHoveredField(null)} className="p-4 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 cursor-pointer transition-all flex justify-between items-center group">
                                    <span className="text-white/40 text-xs">생년</span>
                                    <span className="text-base font-bold group-hover:text-amber-300 transition-colors">{userInfo.year}년 ({userInfo.year ? getGapjaInfo(userInfo.year).korGanji : ''}년)</span>
                                </div>
                                <div onClick={() => setActiveModal('date')} onMouseEnter={() => setHoveredField('date')} onMouseLeave={() => setHoveredField(null)} className="p-4 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 cursor-pointer transition-all flex justify-between items-center group">
                                    <span className="text-white/40 text-xs">월일</span>
                                    <span className="text-base font-bold group-hover:text-amber-300 transition-colors">{userInfo.month}월 {userInfo.day}일 ({getZodiacName(userInfo.month, userInfo.day)})</span>
                                </div>
                                <div onClick={() => setActiveModal('time')} onMouseEnter={() => setHoveredField('time')} onMouseLeave={() => setHoveredField(null)} className="p-3 bg-white/5 hover:bg-white/10 rounded-xl border border-white/10 cursor-pointer transition-all flex justify-between items-center group">
                                    <span className="text-white/40 text-[13px]">시간</span>
                                    <span className="text-base font-bold group-hover:text-amber-300 transition-colors">{userInfo.time}</span>
                                </div>
                            </div>
                            <button onClick={handleConfirmAnalysis} className="w-full py-3.5 rounded-xl bg-gradient-to-r from-amber-700 to-amber-600 hover:from-amber-600 hover:to-amber-500 text-white font-bold text-base shadow-lg shadow-amber-900/40 transition-all hover:scale-105 active:scale-95">
                                사주 보기
                            </button>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* INPUT QUESTION PHASE */}
                <AnimatePresence>
                    {phase === 'input_question' && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="absolute inset-0 z-20 flex flex-col items-center justify-center p-4 bg-black/60 backdrop-blur-md"
                        >
                            <div className="max-w-4xl w-full flex flex-col items-center">
                                <div className="flex justify-center items-end gap-4 md:gap-16 mb-12 h-64 md:h-80 relative">
                                    <motion.div animate={{ opacity: introStep >= 0 ? 1 : 0.3, scale: introStep === 0 ? 1.1 : 1, y: introStep === 0 ? -20 : 0 }} className="relative flex flex-col items-center">
                                        <AnimatePresence>{introStep === 0 && <AnimatedBubble theme="amber" size="large" title={EastName} className="bottom-20 left-1/2 -translate-x-1/2" text={`"오늘 당신을 감싸고 있는 기운을...\n한번 살펴볼까요?"`} />}</AnimatePresence>
                                        <div className="w-32 h-32 md:w-48 md:h-48 rounded-full border-4 border-amber-600/50 bg-amber-900/20 overflow-hidden shadow-[0_0_30px_rgba(217,119,6,0.3)]"><img src="/assets/images/east.png" alt="East" className="w-full h-full object-cover" /></div>
                                    </motion.div>
                                    <motion.div animate={{ opacity: introStep >= 1 || introStep === 2 ? 1 : 0.3, scale: introStep === 1 ? 1.1 : 1, y: introStep === 1 ? -20 : 0 }} className="relative flex flex-col items-center">
                                        <AnimatePresence>{introStep === 1 && <AnimatedBubble theme="indigo" size="large" title={WestName} className="bottom-20 left-1/2 -translate-x-1/2" text={`"별들의 목소리를 들어볼까요?"`} />}</AnimatePresence>
                                        <div className="w-32 h-32 md:w-48 md:h-48 rounded-full border-4 border-indigo-500/50 bg-indigo-900/20 overflow-hidden shadow-[0_0_30px_rgba(99,102,241,0.3)]"><img src="/assets/images/west.png" alt="West" className="w-full h-full object-cover" /></div>
                                    </motion.div>
                                </div>
                                <AnimatePresence>
                                    {introStep === 2 && (
                                        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="w-full max-w-lg space-y-6">
                                            <div className="text-center"><h3 className="text-xl font-['Gowun_Batang'] text-white mb-2">무엇이 궁금하신가요?</h3><p className="text-white/50 text-xs">구체적으로 물어보실수록 더 정확한 답변을 드릴 수 있습니다.</p></div>
                                            <div className="relative">
                                                <textarea value={userQuestion} onChange={(e) => setUserQuestion(e.target.value)} placeholder="예: 오늘 중요한 미팅이 있는데 잘 될까요?" className="w-full h-32 bg-white/5 border border-white/20 rounded-xl px-6 py-4 text-white placeholder:text-white/20 focus:outline-none focus:border-amber-500/50 focus:bg-white/10 transition-all font-sans text-base resize-none custom-scrollbar" onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && userQuestion.trim()) { e.preventDefault(); setPhase('loading'); } }} />
                                                <button onClick={() => { if (userQuestion.trim()) setPhase('loading'); }} disabled={!userQuestion.trim()} className="absolute right-4 bottom-4 px-6 py-2 bg-white/10 hover:bg-white/20 rounded-lg text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed">질문하기</button>
                                            </div>
                                            <div className="flex flex-wrap justify-center gap-2 max-w-2xl mx-auto">
                                                {[{ tag: "오늘의 총운", question: "오늘 하루 저의 전반적인 운세 흐름이 궁금합니다. 특별한 일이 생길까요?" }, { tag: "이달의 재물운", question: "이번 달 저의 금전적인 흐름은 어떨까요?" }].map((item) => (
                                                    <button key={item.tag} onClick={() => setUserQuestion(item.question)} className="px-4 py-2 rounded-full bg-white/5 border border-white/5 hover:bg-white/10 hover:border-white/20 text-xs text-white/60 transition-all hover:scale-105">#{item.tag}</button>
                                                ))}
                                            </div>
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* LOADING PHASE */}
                <AnimatePresence>
                    {phase === 'loading' && (
                        <FortuneLoading
                            loadingProgress={loadingProgress}
                            mode="saju"
                            userQuestion={userQuestion}
                            onComplete={() => { }} // No-op for saju mode, handled by effect
                        />
                    )}
                </AnimatePresence>

                {/* RESULT PHASE */}
                <AnimatePresence>
                    {phase === 'result' && fortuneResult && (
                        <FortuneResult
                            fortuneResult={fortuneResult}
                            userInfo={userInfo}
                            userQuestion={userQuestion}
                            onBack={onBack}
                            onSaveAndExit={() => {
                                navigate('/');
                            }}
                            onRestart={() => setPhase('input_info')}
                        />
                    )}
                </AnimatePresence>

                {/* Saju Outro Overlay (Re-appears over result or takes over?) */}
                {/* Since result might be unmounted when phase changes, characters need to be visible. */}
                {/* Characters logic at lines 984+ checks for phase. Check if 'saju_outro' is included. */}
                {/* Need to ensure characters stay visible or re-appear during saju_outro */}
            </div>
        </div>
    );
};

export default FortuneReadingPage;