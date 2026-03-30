import { useState, useEffect, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, Info, X, Heart, Coins, Activity, GraduationCap, Briefcase } from 'lucide-react';

import { useCollection } from '../../contexts/CollectionContext';
import { useCharacterSettings, getCharacterName } from '../../utils/character';
import { useSound } from '../../hooks/useSound';
import MAJOR_ARCANA, { type TarotCard, shuffleDeck } from '../../data/tarotCards';
import { HWATU_CARDS } from '../../data/hwatuCards';
import { getHwatuImage } from '../../utils/getHwatuImage';
import { createCardReading, type CardResultDetailResponse, type CardCreateReadingRequest } from '../../api/card';
import MysticScatteredDeck from '../tarot/MysticScatteredDeck';
import HwatuStepResult from '../results/HwatuStepResult';
import HwatuStoryResult from '../results/HwatuStoryResult';
import HwatuSummaryResult from '../results/HwatuSummaryResult';
import TarotResultView from '../results/TarotResultView';
import TarotStepResult from '../results/TarotStepResult';
import { getTarotImage } from '../../utils/tarotAssets';

// Mock Hwatu Assets removed - using dynamic new URL() mapping instead

type Phase = 'intro' | 'selection' | 'input' | 'card-selection' | 'shuffling' | 'result';

interface SelectedCardResult {
    card: TarotCard;
    isReversed: boolean;
    stepTitle: string;
}

const WEST_STEPS = [
    { id: 'past', title: '과거 (Past)', desc: '당신의 무의식 속에 잠재된 경험과 그로부터 비롯된 현재의 뿌리를 상상하며 첫 번째 카드를 선택하세요.' },
    { id: 'present', title: '현재 (Present)', desc: '지금 이 순간 당신을 둘러싼 에너지와 마주하고 있는 진실을 투영하는 두 번째 카드를 고르세요.' },
    { id: 'future', title: '미래 (Future)', desc: '현재의 기운이 이어져 도달하게 될 방향과 당신이 맞이하게 될 새로운 가능성을 담은 마지막 카드를 선택하세요.' }
];

const EAST_STEPS = [
    { id: 'step1', title: '본인 및 현재상태', desc: '현재 당신의 상황과 마음가짐을 투영하는 화투 패를 선택하세요.' },
    { id: 'step2', title: '상대 및 환경', desc: '당신을 둘러싼 주변의 기운과 외부적인 영향을 상징하는 패를 고르세요.' },
    { id: 'step3', title: '과정 및 관계', desc: '사건의 흐름과 인연의 고리를 보여줄 운명의 패를 찾으세요.' },
    { id: 'step4', title: '결과 및 조언', desc: '이 모든 것의 결말과, 당신에게 필요한 지혜가 담긴 마지막 패를 선택하세요.' }
];

const LOADING_MESSAGES = [
    "손은 눈보다 빠르니까...\n지금 눈 깜빡이면 운명 바뀝니다.",
    "화투 패가 자꾸 손에서 미끄러져요.\n예지가 핸드크림을 너무 발랐나 봐요;;",
    "로딩이 길어지는 건 그만큼 당신의 운명이 스펙터클하다는 증거!",
    "결과 나오기 3초 전... 아니 5초 전...\n에잇, 정성껏 뽑고 있습니다!",
    "운명의 실타래가 너무 엉켜서\n예지가 지금 이빨로 풀고 있어요.",
    "결과 나오기 직전인데... 예지가 화장실 급하대요.\n3초만 참아줘요.",
    "사실 지금 예지가 화투 그림 감상하느라 일 안 하고 있어요.\n제가 혼내는 중!"
];

const WEST_LOADING_MESSAGES = [
    "반짝이는 별들 사이에서\n당신의 조각을 찾아내고 있어요.",
    "수정구에 안개가 자욱하네요...\n곧 당신의 운명이 선명해질 거예요.",
    "카드가 운명의 소리를 들려주고 있어요.\n잠시만 더 귀를 기울여볼까요?",
    "우주의 에너지를 가득 모으는 중입니다.\n깊은 숨을 한번 들이마셔 보세요.",
    "당신의 과거와 현재, 그리고 미래가\n아름다운 궤도를 그리기 시작했어요.",
    "별의 목소리를 정성껏 해석하고 있습니다.\n곧 신비로운 이야기를 들려드릴게요!",
    "운명의 지도가 조금 복잡하네요.\n조심스럽게 별자리를 연결하는 중입니다."
];

const CATEGORIES = [
    { id: 'LOVE', name: '연애', icon: Heart, color: 'text-stone-800', bg: 'bg-rose-500/10', border: 'border-rose-500/30' },
    { id: 'MONEY', name: '재물', icon: Coins, color: 'text-stone-800', bg: 'bg-amber-500/10', border: 'border-amber-500/30' },
    { id: 'HEALTH', name: '건강', icon: Activity, color: 'text-stone-800', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' },
    { id: 'STUDY', name: '학업', icon: GraduationCap, color: 'text-stone-800', bg: 'bg-blue-500/10', border: 'border-blue-500/30' },
    { id: 'CAREER', name: '직장', icon: Briefcase, color: 'text-stone-800', bg: 'bg-indigo-500/10', border: 'border-indigo-500/30' },
];

const ParticleBackground = ({ theme }: { theme?: 'west' | 'east' }) => {
    const particles = Array.from({ length: 20 });
    return (
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
            {particles.map((_, i) => (
                <motion.div
                    key={i}
                    initial={{
                        x: Math.random() * 100 + '%',
                        y: Math.random() * 100 + '%',
                        opacity: 0,
                        scale: Math.random() * 0.5 + 0.2
                    }}
                    animate={{
                        y: [null, '-20%', '-40%'],
                        x: [null, (Math.random() - 0.5) * 30 + 'px'],
                        opacity: [0, 0.3, 0],
                        rotate: theme === 'east' ? [0, 90, 180] : 0
                    }}
                    transition={{
                        duration: Math.random() * 15 + 15,
                        repeat: Infinity,
                        ease: "linear",
                        delay: Math.random() * 10
                    }}
                    className={`absolute w-1 h-1 blur-[1px] ${theme === 'east'
                        ? 'bg-rose-400/20 rounded-[100%_0%_100%_0%]'
                        : 'bg-purple-300/20 rounded-full shadow-[0_0_10px_rgba(168,85,247,0.3)]'
                        }`}
                />
            ))}
        </div>
    );
};

const FilmicOverlay = () => (
    <div className="absolute inset-0 z-[100] pointer-events-none overflow-hidden">
        <div className="absolute inset-0 opacity-[0.02] bg-[url('https://grainy-gradients.vercel.app/noise.svg')] bg-repeat mix-blend-overlay" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(0,0,0,0.3)_120%)] shadow-[inset_0_0_100px_rgba(0,0,0,0.4)]" />
    </div>
);

const TypewriterText = ({ text, speed = 50, delay = 400 }: { text: string; speed?: number; delay?: number }) => {
    const [count, setCount] = useState(0);

    useEffect(() => {
        let isCancelled = false;
        let intervalId: any;

        setCount(0);

        const timeoutId = setTimeout(() => {
            if (isCancelled) return;

            intervalId = setInterval(() => {
                setCount((prev) => {
                    if (prev < text.length) return prev + 1;
                    clearInterval(intervalId);
                    return prev;
                });
            }, speed);
        }, delay);

        return () => {
            isCancelled = true;
            clearTimeout(timeoutId);
            if (intervalId) clearInterval(intervalId);
        };
    }, [text, speed, delay]);

    return <span>{text.slice(0, count)}</span>;
};

// HWATU_RESULT_DATA removed - replaced by hwatuResultData memo

const CardReadingPage = ({ onMenuVisibilityChange }: { onMenuVisibilityChange?: (visible: boolean) => void }) => {
    const navigate = useNavigate();
    const { equippedEast, equippedWest } = useCollection();
    const characterSettings = useCharacterSettings(); // Get character settings from localStorage
    const equippedEastId = characterSettings.east; // 'buchae_woman', 'soiseol', 'sinseon'
    const equippedWestId = characterSettings.west; // Western character ID

    // Helper: Map character ID to SD character folder name (East)
    const getSDCharacterName = (id: string): string => {
        let name = getCharacterName('east', id).replace(/\s/g, '');
        if (name === '홍주') name = '홍설';
        return name || '소이설';
    };

    // Helper: Map western character ID to SD character folder name
    const getSDWestCharacterName = (id: string): string => {
        let name = getCharacterName('west', id).replace(/\s/g, '');
        return name || '넬';
    };

    // Helper: Get character image path from public folder
    const getEastCharacterImage = (type: string = 'normal'): string => {
        const path = `/assets/character/east/${equippedEastId}/${equippedEastId}_${type}.png`;
        return path;
    };

    // Helper: Get SD character image path (East)
    const getSDCharacterImage = (type: string = 'normal'): string => {
        const sdName = getSDCharacterName(equippedEastId);
        const path = `/assets/character/SD캐릭터/동양/${sdName}/${sdName}_${type}.png`;
        return path;
    };

    // Helper: Get western character image path from public folder
    const getWestCharacterImage = (type: string = 'normal'): string => {
        const path = `/assets/character/west/${equippedWestId}/${equippedWestId}_${type}.png`;
        return path;
    };

    // Helper: Get SD western character image path
    const getSDWestCharacterImage = (type: string = 'normal'): string => {
        const sdName = getSDWestCharacterName(equippedWestId);
        const path = `/assets/character/SD캐릭터/서양/${sdName}/${sdName}_${type}.png`;
        return path;
    };

    const [phase, setPhase] = useState<Phase>('intro');
    const [resultSubStep, setResultSubStep] = useState(0); // 0-3: Individual cards, 4: Summary Result
    const [hoveredChar, setHoveredChar] = useState<'west' | 'east' | null>(null);
    const [selectedSide, setSelectedSide] = useState<'west' | 'east' | null>(null);
    const [userQuestion, setUserQuestion] = useState('');
    const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
    const { play, stop } = useSound();

    const [currentStepIndex, setCurrentStepIndex] = useState(0);
    const [selectedCards, setSelectedCards] = useState<number[]>([]);
    const [hwatuDeck, setHwatuDeck] = useState<{ id: number; rotate: number; x: number; y: number; isPicked?: boolean }[]>([]);
    const [availableCards, setAvailableCards] = useState<TarotCard[]>([]);
    const [selectedCardResults, setSelectedCardResults] = useState<SelectedCardResult[]>([]);
    const [loadingMsgIndex, setLoadingMsgIndex] = useState(0);
    const [showHwatuInfo, setShowHwatuInfo] = useState(false);
    const [showTarotInfo, setShowTarotInfo] = useState(false);
    const [backendResult, setBackendResult] = useState<CardResultDetailResponse | null>(null);
    const [currentPose, setCurrentPose] = useState('normal');
    const [isMinimumWaitDone, setIsMinimumWaitDone] = useState(false);

    // Asset rotation and forced delay logic for shuffling phase
    useEffect(() => {
        if (phase === 'shuffling') {
            setIsMinimumWaitDone(false);
            const duration = 7000 + Math.random() * 2000; // 7-9 seconds
            const waitTimer = setTimeout(() => setIsMinimumWaitDone(true), duration);

            const CHARACTER_POSES = ['normal', 'smile', 'suprize', 'thinking', 'explain', 'annoying', 'angry'];
            const rotationInterval = setInterval(() => {
                const nextPose = CHARACTER_POSES[Math.floor(Math.random() * CHARACTER_POSES.length)];
                const messagePool = selectedSide === 'west' ? WEST_LOADING_MESSAGES : LOADING_MESSAGES;
                const nextMsg = Math.floor(Math.random() * messagePool.length);
                setCurrentPose(nextPose);
                setLoadingMsgIndex(nextMsg);
            }, 3000);

            return () => {
                clearTimeout(waitTimer);
                clearInterval(rotationInterval);
            };
        }
    }, [phase]);

    // Transition to result when both API is ready and wait is done
    useEffect(() => {
        if (phase === 'shuffling' && backendResult && isMinimumWaitDone) {
            setPhase('result');
        }
    }, [phase, backendResult, isMinimumWaitDone]);

    // Mapped Hwatu Result Data
    const hwatuResultData = useMemo(() => {
        if (selectedSide !== 'east' || selectedCards.length < 4) return null;

        const aiData = backendResult?.aiReading?.data;

        if (!aiData) return null; // STRICT: If no API data, return null to show loading

        const cards = [1, 2, 3, 4].map((pos, idx) => {
            const rawAiCards = aiData?.cards || [];

            // Priority 1: Match by 'position' field (1-indexed)
            let aiCard = rawAiCards.find(c => {
                const p = c.position !== undefined ? c.position : c.position_label;
                return Number(p) === pos;
            });

            // Priority 2: Use direct index if position matching fails but array has data
            if (!aiCard && rawAiCards[idx]) {
                const p = rawAiCards[idx].position !== undefined ? rawAiCards[idx].position : rawAiCards[idx].position_label;
                if (isNaN(Number(p)) || Number(p) === pos) {
                    aiCard = rawAiCards[idx];
                }
            }

            // Priority 3: If position matching failed, maybe match by the code we SENT for this position

            // Determine the final 'effective' API code (1-48) to show the image
            // We prioritize the code returned by AI to ensure image-text consistency
            // Determine the final 'effective' API code (0-47) to show the image
            // We prioritize the code returned by AI to ensure image-text consistency
            let cardIndex = selectedCards[idx] !== undefined ? selectedCards[idx] : 0;
            if (aiCard) {
                const aiCode = aiCard.card_code !== undefined ? aiCard.card_code : aiCard.cardCode;
                if (aiCode !== undefined) {
                    cardIndex = Number(aiCode);
                }
            }

            // Metadata lookup (0-indexed)
            const cardInfo = HWATU_CARDS[cardIndex];
            const imgPath = getHwatuImage(cardIndex);

            return {
                name: aiCard?.card_name || cardInfo?.name || '알 수 없는 패',
                img: imgPath,
                type: aiCard?.position_label || EAST_STEPS[idx].title,
                desc: aiCard?.keywords?.join(', ') || '분석 중...',
                detailedDesc: aiCard?.interpretation || '상세 해석을 불러오는 중입니다...'
            };
        });

        // Defensive extraction of report from backendResult.aiReading
        let extractedReport = '운명이 그대에게 속삭이는 소리를 듣고 있습니다...';
        let extractedSummary = '백엔드 AI의 정밀 분석 결과입니다.';
        let extractedKeyword = '운수대통';

        if (aiData?.summary) {
            const s = aiData.summary;
            extractedReport = `${s.flow_analysis}\n\n[조언]\n${s.advice}`;
            extractedSummary = s.overall_theme;

            // Extract a concise keyword
            // Priority 1: Use first keyword of the first card (Main subject)
            // Priority 2: Use first keyword of the summary if shorter than 5 chars
            // Priority 3: Default '천기누설' or '운수대통'
            if (aiData.cards && aiData.cards.length > 0 && aiData.cards[0].keywords && aiData.cards[0].keywords.length > 0) {
                extractedKeyword = aiData.cards[0].keywords[0];
            } else if (s.overall_theme.length < 10) {
                extractedKeyword = s.overall_theme;
            } else {
                extractedKeyword = '운명의 흐름';
            }
        } else if (backendResult?.aiReading) {
            const ai = backendResult.aiReading;
            if (ai.data?.message) extractedReport = ai.data.message;
            else if (ai.message) extractedReport = ai.message;
            else if (typeof ai === 'string') extractedReport = ai;
        }

        return {
            cards,
            summary: {
                keyword: extractedKeyword,
                summary: extractedSummary,
                report: extractedReport,
                lucky: aiData?.lucky ? {
                    color: aiData.lucky.color || aiData.lucky.luckyColor || '황금색',
                    number: aiData.lucky.number || aiData.lucky.luckyNumber || '7',
                    direction: aiData.lucky.direction || aiData.lucky.luckyDirection || '동쪽',
                    timing: aiData.lucky.timing || aiData.lucky.luckyTime || '오전',
                    element: aiData.lucky.element || '木 (나무)'
                } : undefined
            }
        };
    }, [selectedSide, selectedCards, backendResult]);

    // Memoized data for HwatuSummaryResult to avoid object-literal re-creation
    const hwatuSummaryProps = useMemo(() => {
        if (!hwatuResultData) return null;
        return {
            cards: hwatuResultData.cards,
            keyword: hwatuResultData.summary.keyword,
            summary: hwatuResultData.summary.summary,
            report: hwatuResultData.summary.report,
            lucky: hwatuResultData.summary.lucky,
            vibe: '운명의 결'
        };
    }, [hwatuResultData]);

    // Mapped Tarot Result Data for Step-by-Step
    const tarotResultData = useMemo(() => {
        if (selectedSide !== 'west' || selectedCardResults.length < 3) return null;

        const aiData = backendResult?.aiReading?.data;

        if (!aiData) return null; // STRICT: If no API data, return null to show loading

        // Map selected cards (0, 1, 2)
        const cards = selectedCardResults.map((res, idx) => {
            // Priority 1: Match AI data by position (1-indexed) or use array index as fallback
            const rawAiCards = aiData?.cards || [];
            let aiCard = rawAiCards.find(c => {
                const p = c.position !== undefined ? c.position : c.position_label;
                return Number(p) === idx + 1;
            });

            // Priority 2: If position match failed, try matching by the expected order (idx)
            if (!aiCard && rawAiCards[idx]) {
                const p = rawAiCards[idx].position !== undefined ? rawAiCards[idx].position : rawAiCards[idx].position_label;
                // Only take it if it doesn't explicitly conflict with another position
                if (isNaN(Number(p)) || Number(p) === idx + 1) {
                    aiCard = rawAiCards[idx];
                }
            }

            // Priority 3: Fallback to matching by code and position if previous failed
            if (!aiCard) {
                aiCard = rawAiCards.find(c => {
                    const code = c.card_code !== undefined ? c.card_code : c.cardCode;
                    return Number(code) === res.card.number && Number(c.position) === idx + 1;
                });
            }

            // Determine final card code and orientation from AI or fallback to original pick
            const aiCode = aiCard ? (aiCard.card_code ?? aiCard.cardCode) : undefined;
            const effectiveCode = aiCode !== undefined ? aiCode : res.card.number;

            const aiReversed = aiCard ? (aiCard.is_reversed ?? aiCard.isReversed) : undefined;
            const effectiveReversed = aiReversed !== undefined ? !!aiReversed : res.isReversed;

            const positionLabel = aiCard ? (aiCard.position_label || aiCard.positionLabel) : res.stepTitle;
            const cardName = aiCard ? (aiCard.card_name || aiCard.cardName) : res.card.name;

            return {
                name: cardName || res.card.name,
                img: getTarotImage(effectiveCode),
                type: positionLabel || res.stepTitle, // e.g. "과거", "현재", "미래"
                desc: aiCard?.keywords?.join(', ') || res.card.name,
                detailedDesc: aiCard?.interpretation || (effectiveReversed ? res.card.reversedMeaning : res.card.uprightMeaning),
                keywords: aiCard?.keywords || (effectiveReversed ? res.card.reversedKeywords : res.card.uprightKeywords),
                isReversed: effectiveReversed
            };
        });

        return { cards };
    }, [selectedSide, selectedCardResults, backendResult]);

    useEffect(() => {
        onMenuVisibilityChange?.(false);
        return () => onMenuVisibilityChange?.(true);
    }, [onMenuVisibilityChange]);

    useEffect(() => {
        const handleMouseMove = (e: MouseEvent) => {
            setMousePos({ x: e.clientX, y: e.clientY });
        };
        window.addEventListener('mousemove', handleMouseMove);
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            stop('BGM', 'WEST1');
            stop('BGM', 'EAST1');
            stop('BGM', 'EAST2');
        };
    }, [stop]);

    useEffect(() => {
        if (selectedSide === 'west') {
            play('BGM', 'WEST1', { loop: true, volume: 0.3 });
            stop('BGM', 'EAST1');
            stop('BGM', 'EAST2');
        } else if (selectedSide === 'east') {
            play('BGM', 'EAST2', { loop: true, volume: 0.3 });
            stop('BGM', 'WEST1');
            stop('BGM', 'EAST1');
        } else {
            stop('BGM', 'WEST1');
            stop('BGM', 'EAST1');
            stop('BGM', 'EAST2');
        }
    }, [selectedSide, play, stop]);

    useEffect(() => {
        if (phase === 'shuffling') {
            const interval = setInterval(() => {
                setLoadingMsgIndex(prev => {
                    let nextIndex;
                    do {
                        nextIndex = Math.floor(Math.random() * LOADING_MESSAGES.length);
                    } while (nextIndex === prev);
                    return nextIndex;
                });
            }, 3000);
            return () => clearInterval(interval);
        } else {
            setLoadingMsgIndex(0);
        }
    }, [phase]);

    // Loading Character Pose Cycling
    useEffect(() => {
        if (phase === 'shuffling' && selectedSide === 'east') {
            const poses = ['normal', 'smile', 'angry', 'annoying', 'explain', 'suprize', 'thinking'];
            const interval = setInterval(() => {
                setCurrentPose(prev => {
                    let nextPose;
                    do {
                        nextPose = poses[Math.floor(Math.random() * poses.length)];
                    } while (nextPose === prev);
                    return nextPose;
                });
            }, 3000);
            return () => clearInterval(interval);
        } else {
            setCurrentPose('normal');
        }
    }, [phase, selectedSide]);

    useEffect(() => {
        if (phase === 'intro') {
            const timer = setTimeout(() => {
                setPhase('selection');
            }, 1500);
            return () => clearTimeout(timer);
        }
    }, [phase]);

    const handleBack = useCallback(() => {
        if (phase === 'input') {
            setPhase('selection');
            setSelectedSide(null);
            setUserQuestion('');
        } else if (phase === 'card-selection') {
            if (currentStepIndex > 0) {
                setCurrentStepIndex(prev => prev - 1);
                // Also remove the last selected card
                setSelectedCards(prev => prev.slice(0, -1));
                if (selectedSide === 'east') {
                    // Restore the last picked card's state in Hwatu deck
                    const lastCardId = selectedCards[selectedCards.length - 1];
                    setHwatuDeck(prev => prev.map(card =>
                        card.id === lastCardId ? { ...card, isPicked: false } : card
                    ));
                } else {
                    // West (Tarot)
                    const lastResult = selectedCardResults[selectedCardResults.length - 1];
                    setAvailableCards(prev => [...prev, lastResult.card]);
                    setSelectedCardResults(prev => prev.slice(0, -1));
                }
            } else {
                setPhase('input');
                setSelectedCards([]);
            }
        } else if (phase === 'result') {
            if (selectedSide === 'east') {
                if (resultSubStep > 0) {
                    setResultSubStep(prev => prev - 1);
                } else {
                    setPhase('card-selection');
                    setCurrentStepIndex(EAST_STEPS.length - 1);
                }
            } else {
                // Tarot result back... (Reset to selection for now or handle sub-steps if any)
                setPhase('card-selection');
            }
        } else {
            stop('BGM', 'WEST1');
            stop('BGM', 'EAST1');
            stop('BGM', 'EAST2');
            navigate('/');
        }
    }, [phase, currentStepIndex, selectedCards, selectedSide, selectedCardResults, resultSubStep, navigate, stop]);

    // Hwatu Phase Transition: Shuffling -> Result
    useEffect(() => {
        if (selectedSide === 'east' && phase === 'shuffling' && backendResult) {
            // Enforce a minimum loading duration of 5-7 seconds to simulate deep analysis
            const randomDelay = Math.floor(Math.random() * 2000) + 5000;

            const timer = setTimeout(() => {
                setPhase('result');
            }, randomDelay);
            return () => clearTimeout(timer);
        }
    }, [selectedSide, phase, backendResult]);

    const handleSelect = (side: 'west' | 'east') => {
        setSelectedSide(side);
        if (side === 'west') play('SFX', 'WARP_ENTER');
        else play('SFX', 'INK_SPLASH');
        setPhase('input');
    };

    const handleCardPick = async (index: number) => {
        const steps = selectedSide === 'west' ? WEST_STEPS : EAST_STEPS;
        // Don't auto-add to selectedCards here, logic differs by side now

        if (selectedSide === 'west') {
            const newSelected = [...selectedCards, index];
            setSelectedCards(newSelected);

            play('SFX', 'CARD_FLIP');
            const pickedCard = availableCards[index];
            const isReversed = Math.random() < 0.5;
            const result: SelectedCardResult = {
                card: pickedCard,
                isReversed,
                stepTitle: steps[currentStepIndex].title
            };
            setSelectedCardResults([...selectedCardResults, result]);
            const remainingCards = availableCards.filter(c => c.id !== pickedCard.id);
            setAvailableCards(remainingCards);

            if (currentStepIndex < steps.length - 1) {
                setCurrentStepIndex(prev => prev + 1);
            } else {
                setPhase('shuffling');
                setResultSubStep(0);

                // Actual API Call for Tarot
                try {
                    const response = await createCardReading({
                        category: 'TARO',
                        topic: userQuestion,
                        cards: (selectedCardResults.concat(result) as SelectedCardResult[]).map((res, i) => ({
                            cardCode: res.card.number,
                            position: i + 1,
                            isReversed: res.isReversed
                        }))
                    });
                    setBackendResult(response);
                } catch (error) {
                    console.error("Failed to create Tarot reading:", error);
                }
            }
        } else {
            play('SFX', 'CARD_FLIP');

            // 1. Visual Update
            setHwatuDeck(prev => prev.map(card =>
                card.id === index ? { ...card, isPicked: true } : card
            ));

            const logicalId = predecidedCards[currentStepIndex];
            // Update selectedCards so result page can map it
            const updatedSelectedCards = [...selectedCards, logicalId];
            setSelectedCards(updatedSelectedCards);

            if (currentStepIndex < steps.length - 1) {
                setCurrentStepIndex(prev => prev + 1);
            } else {
                // Last card picked
                setPhase('shuffling');
                setResultSubStep(0);
            }
        }
    };

    const [predecidedCards, setPredecidedCards] = useState<number[]>([]);

    const handleStartReading = async (topicId: string) => {
        setUserQuestion(topicId);
        if (selectedSide === 'west') {
            const deck = shuffleDeck(MAJOR_ARCANA);
            setAvailableCards(deck);
            setSelectedCardResults([]);
            setPhase('card-selection');
            setCurrentStepIndex(0);
            setSelectedCards([]);
        } else {
            // Hwatu: Prefetch Logic
            // 1. Generate 4 unique random logical IDs immediately
            const generatedIds: number[] = [];
            while (generatedIds.length < 4) {
                const r = Math.floor(Math.random() * 48);
                if (!generatedIds.includes(r)) generatedIds.push(r);
            }
            setPredecidedCards(generatedIds);

            // 2. Prepare visual deck
            const ids = Array.from({ length: 48 }, (_, i) => i);
            for (let i = ids.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [ids[i], ids[j]] = [ids[j], ids[i]];
            }
            const shuffledDeck = ids.map((id, i) => ({
                id,
                rotate: (i % 7) * 4 - 12 + (Math.random() * 6 - 3),
                x: (i % 8) * 4 - 16 + (Math.random() * 4 - 2),
                y: (i % 5) * 4 - 10 + (Math.random() * 4 - 2),
                isPicked: false
            }));
            setHwatuDeck(shuffledDeck);

            // Audio setup
            stop('BGM', 'WEST1');
            // stop('BGM', 'EAST2'); // Keep playing

            setPhase('card-selection');
            setCurrentStepIndex(0);
            setSelectedCards([]);

            // 3. Fire API Request IMMEDIATELY (Async)
            try {
                // Note: We don't set isProcessing=true here because we want user to interact.
                // We'll accept the result whenever it comes.
                const requestPayload: CardCreateReadingRequest = {
                    category: 'HWATU',
                    topic: topicId,
                    cards: generatedIds.map((cardId, i) => ({
                        cardCode: cardId,
                        position: i + 1,
                        isReversed: false
                    }))
                };
                // Fire and forget - let the promise resolve and update state
                createCardReading(requestPayload).then(response => {
                    setBackendResult(response);
                }).catch(err => {
                    console.error("Prefetch failed:", err);
                });

            } catch (error) {
                console.error("Failed to initiate prefetch:", error);
            }
        }
    };


    const handleRestartHwatu = useCallback(() => {
        setResultSubStep(5);
    }, []);

    const handleExit = useCallback(() => {
        navigate('/');
    }, [navigate]);

    return (
        <div className="fixed inset-0 z-50 bg-black text-white selection:bg-purple-500/30 overflow-hidden flex flex-col font-sans">
            <FilmicOverlay />

            {/* Top Navigation - Only for selection/intro */}
            {(phase === 'intro' || phase === 'selection') && (
                <div className="absolute top-0 left-0 w-full p-6 flex justify-between items-center z-50 pointer-events-none">
                    <motion.button
                        whileHover={{ scale: 1.05, backgroundColor: 'rgba(0,0,0,0.8)' }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleBack}
                        className="text-white/60 hover:text-white flex items-center gap-3 pointer-events-auto bg-black/40 px-6 py-2.5 rounded-full border border-white/5 backdrop-blur-2xl transition-all shadow-2xl"
                    >
                        <ArrowLeft size={18} />
                        <span className="text-sm tracking-widest uppercase font-['Hahmlet']">
                            뒤로가기
                        </span>
                    </motion.button>
                </div>
            )}

            <div className="absolute inset-0 z-0">
                <div className="absolute inset-0 bg-[url('/assets/bg/fortune_bg_oriental.png')] bg-cover bg-center opacity-[0.15] grayscale contrast-125" />
                <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/60" />

                <motion.div
                    animate={{ opacity: [0.3, 0.5, 0.3], scale: [1, 1.1, 1] }}
                    transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
                    className={`absolute inset-0 blur-[120px] pointer-events-none opacity-40 transition-colors duration-1000 ${selectedSide === 'west' ? 'bg-purple-900/40' : (selectedSide === 'east' ? 'bg-amber-900/40' : 'bg-transparent')}`}
                />
                <div className="absolute inset-0 bg-gradient-to-b from-black/40 via-transparent to-black/40" />
                <ParticleBackground theme={selectedSide || undefined} />

                <div
                    className="absolute inset-0 z-0 pointer-events-none transition-opacity duration-500"
                    style={{ background: `radial-gradient(600px circle at ${mousePos.x}px ${mousePos.y}px, rgba(255,255,255,0.07), transparent 40%)` }}
                />

                <AnimatePresence>
                    {hoveredChar === 'west' && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-gradient-to-r from-purple-950/40 to-transparent" />
                    )}
                    {hoveredChar === 'east' && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="absolute inset-0 bg-gradient-to-l from-amber-950/40 to-transparent" />
                    )}
                </AnimatePresence>
            </div>

            <AnimatePresence>
                {phase === 'intro' && (
                    <motion.div className="absolute inset-0 z-50 overflow-hidden pointer-events-none">
                        <motion.div initial={{ x: 0 }} exit={{ x: '-100%' }} transition={{ duration: 1.8, ease: [0.7, 0, 0.3, 1] }} className="absolute top-0 left-0 w-[50.5%] h-full bg-black border-r border-white/10 z-10" />
                        <motion.div initial={{ x: 0 }} exit={{ x: '100%' }} transition={{ duration: 1.8, ease: [0.7, 0, 0.3, 1] }} className="absolute top-0 right-0 w-[50.5%] h-full bg-black border-l border-white/10 z-10" />
                        <div className="absolute inset-0 flex flex-col items-center justify-center z-20">
                            <motion.h1 initial={{ y: 20, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={{ opacity: 0, scale: 0.9, y: -20 }} transition={{ duration: 0.8 }} className="text-4xl md:text-6xl font-['Hahmlet'] text-transparent bg-clip-text bg-gradient-to-b from-amber-100 to-amber-600 mb-4">운명의 문을 엽니다</motion.h1>
                            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0, y: 10 }} transition={{ delay: 0.2, duration: 0.8 }} className="text-white/50 font-['Hahmlet'] tracking-[0.5em] text-sm md:text-base ml-2">당신의 질문에 답할 카드를 선택하세요</motion.p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence mode="wait">
                {phase === 'selection' && (
                    <motion.div key="selection-portal" initial={{ opacity: 0, filter: "blur(20px)" }} animate={{ opacity: 1, filter: "blur(0px)" }} exit={{ opacity: 0, transition: { duration: 0 } }} className="relative z-10 flex-1 flex flex-col md:flex-row items-stretch justify-center w-full bg-black/20">
                        <div className={`flex-1 relative group cursor-pointer overflow-hidden border-r border-white/5 transition-all duration-700 ${selectedSide ? (selectedSide === 'west' ? 'flex-[10] z-20' : 'flex-[0] opacity-0') : ''}`} onMouseEnter={() => { setHoveredChar('west'); play('SFX', 'BRUSH_HOVER'); }} onMouseLeave={() => setHoveredChar(null)} onClick={() => handleSelect('west')}>
                            <ParticleBackground theme="west" />
                            <motion.div className="absolute inset-0 z-0" animate={{ scale: selectedSide === 'west' ? 1.5 : (hoveredChar === 'west' ? 1.02 : 1), x: (mousePos.x - (typeof window !== 'undefined' ? window.innerWidth : 0) / 2) * 0.01 }} transition={{ duration: selectedSide === 'west' ? 1.5 : 0.8, ease: "easeInOut" }}>
                                <motion.div animate={{ opacity: hoveredChar === 'west' ? 0.5 : 0.1 }} style={{ background: 'radial-gradient(circle, rgba(168, 85, 247, 0.4) 0%, transparent 70%)' }} className="absolute inset-0 pointer-events-none z-10" />
                                <motion.img src={getWestCharacterImage('normal')} alt="Tarot Oracle" animate={{ scale: selectedSide === 'west' ? 1.5 : 0.90, filter: hoveredChar === 'west' || selectedSide === 'west' ? 'grayscale(0%) brightness(1.1)' : 'grayscale(100%) brightness(0.4) blur(2px)' }} transition={{ duration: 0.8 }} className="w-full h-full object-contain object-center opacity-90 transition-all duration-700 -translate-y-5" />
                                <div className="absolute inset-0 bg-gradient-to-r from-purple-950/80 via-black/20 to-transparent" />
                            </motion.div>
                            <div className="relative z-20 h-full flex flex-col items-center justify-center p-12 text-center">
                                <motion.div animate={{ y: hoveredChar === 'west' ? -15 : 0, opacity: selectedSide === 'west' ? 0 : 1 }} className="space-y-4 transition-opacity duration-300">
                                    <h2 className="text-7xl md:text-9xl font-['Hahmlet'] text-white opacity-90 tracking-[0.3em] font-light italic mix-blend-plus-lighter">TAROT</h2>
                                    {equippedWest && <div className="text-purple-300 text-xs tracking-[0.5em] font-['Hahmlet'] opacity-40 uppercase">{equippedWest.name} Deck</div>}
                                </motion.div>
                            </div>
                        </div>

                        {!selectedSide && (
                            <div className="hidden md:block absolute left-1/2 top-1/4 bottom-1/4 w-[1px] bg-gradient-to-b from-transparent via-white/20 to-transparent z-30 pointer-events-none">
                                <motion.div animate={{ top: ['0%', '100%'], opacity: [0, 1, 0] }} transition={{ duration: 3, repeat: Infinity, ease: "linear" }} className="absolute w-[3px] -left-[1px] h-20 bg-white shadow-[0_0_15px_white]" />
                            </div>
                        )}

                        <div className={`flex-1 relative group cursor-pointer overflow-hidden transition-all duration-700 ${selectedSide ? (selectedSide === 'east' ? 'flex-[10] z-20' : 'flex-[0] opacity-0') : ''}`} onMouseEnter={() => { setHoveredChar('east'); play('SFX', 'BRUSH_HOVER'); }} onMouseLeave={() => setHoveredChar(null)} onClick={() => handleSelect('east')}>
                            <ParticleBackground theme="east" />
                            <motion.div className="absolute inset-0 z-0" animate={{ scale: selectedSide === 'east' ? 1.5 : (hoveredChar === 'east' ? 1.02 : 1), x: (mousePos.x - (typeof window !== 'undefined' ? window.innerWidth : 0) / 2) * 0.01 }} transition={{ duration: selectedSide === 'east' ? 1.5 : 0.8, ease: "easeInOut" }}>
                                <motion.div animate={{ opacity: hoveredChar === 'east' ? 0.4 : 0.1 }} style={{ background: 'radial-gradient(circle, rgba(251, 191, 36, 0.4) 0%, transparent 70%)' }} className="absolute inset-0 pointer-events-none z-10" />
                                <motion.img src={getEastCharacterImage('normal')} alt="Hwatu Master" animate={{ scale: selectedSide === 'east' ? 1.5 : 0.95, filter: hoveredChar === 'east' || selectedSide === 'east' ? 'grayscale(0%) brightness(1.1)' : 'grayscale(100%) brightness(0.4) blur(2px)' }} transition={{ duration: 0.8 }} className="w-full h-full object-contain object-center opacity-90 transition-all duration-700" />
                                <div className="absolute inset-0 bg-gradient-to-l from-amber-950/80 via-black/20 to-transparent" />
                            </motion.div>
                            <div className="relative z-20 h-full flex flex-col items-center justify-center p-12 text-center">
                                <motion.div animate={{ y: hoveredChar === 'east' ? -15 : 0, opacity: selectedSide === 'east' ? 0 : 1 }} className="space-y-4 transition-opacity duration-300">
                                    <h2 className="text-7xl md:text-9xl font-['Hahmlet'] font-light text-white opacity-90 tracking-[0.2em] italic mix-blend-plus-lighter py-4">화투</h2>
                                    {equippedEast && <div className="text-amber-300 text-xs tracking-[0.5em] font-['Hahmlet'] opacity-40 uppercase">{equippedEast.name} Edition</div>}
                                </motion.div>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {phase === 'input' && selectedSide && (
                <motion.div key="input-phase" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="relative flex-1 flex flex-col w-full h-full">
                    {/* Top Navigation */}
                    <div className="absolute top-8 left-8 right-8 z-[200] flex justify-between items-center pointer-events-none">
                        <motion.button
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            onClick={handleBack}
                            className={`pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full backdrop-blur-xl border transition-all shadow-lg font-['Hahmlet']
                                ${selectedSide === 'west'
                                    ? 'bg-purple-950/60 border-purple-400/40 text-purple-100 hover:bg-purple-900/80 shadow-purple-500/10'
                                    : 'bg-stone-900/60 border-amber-900/40 text-amber-100 hover:bg-stone-800/80 shadow-amber-900/10'
                                }`}
                        >
                            <ArrowLeft size={20} />
                            <span className="text-sm font-medium">뒤로가기</span>
                        </motion.button>

                        <motion.button
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            onClick={() => navigate('/')}
                            className={`pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full backdrop-blur-xl border transition-all shadow-lg font-['Hahmlet']
                                ${selectedSide === 'west'
                                    ? 'bg-purple-950/60 border-purple-400/40 text-purple-100 hover:bg-purple-900/80 shadow-purple-500/10'
                                    : 'bg-stone-900/60 border-amber-900/40 text-amber-100 hover:bg-stone-800/80 shadow-amber-900/10'
                                }`}
                        >
                            <span className="text-sm font-medium">나가기</span>
                            <X size={20} />
                        </motion.button>
                    </div>

                    <div className="flex-1 flex flex-col items-center justify-end pb-10 md:pb-20 relative overflow-hidden">
                        <div className={`absolute z-20 pointer-events-none transition-all duration-1000 ${selectedSide === 'west' ? 'left-0 md:left-10 bottom-20 md:bottom-15 w-[60vh] h-[70vh] md:w-[70vh] md:h-[80vh]' : 'right-0 md:right-10 bottom-20 md:bottom-15 w-[60vh] h-[70vh] md:w-[70vh] md:h-[80vh]'}`}>
                            <motion.img
                                initial={{ opacity: 0, y: 50 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 1, delay: 0.2 }}
                                src={selectedSide === 'west' ? getWestCharacterImage('normal') : getEastCharacterImage('normal')}
                                alt="Oracle"
                                className={`w-full h-full object-contain object-bottom drop-shadow-2xl brightness-110 ${selectedSide === 'west' ? 'scale-100' : 'scale-110'}`}
                            />
                        </div>
                        {/* Guide Character (Master Sinseon) - Small Helper Version */}
                        {selectedSide === 'east' && (
                            <motion.div
                                initial={{ opacity: 0, x: -100, y: -50, rotate: -15, scale: 0.8 }}
                                animate={{ opacity: 1, x: 0, y: 0, rotate: 0, scale: 1 }}
                                transition={{
                                    delay: 1.2,
                                    duration: 1,
                                    type: "spring",
                                    stiffness: 50,
                                    damping: 15
                                }}
                                className="absolute left-[-20px] md:left-[-40px] bottom-40 flex flex-col items-center pointer-events-auto z-40 rotate-12"
                            >
                                {/* Small Info Bubble - Folded Paper Style */}
                                <motion.div
                                    initial={{ opacity: 0, y: 10, scale: 0.8 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    transition={{ delay: 2, duration: 0.5 }}
                                    className="relative mb-4 p-5 bg-[#fdfaf3] border-2 border-amber-900/30 shadow-2xl flex flex-col items-center gap-3 w-52 text-center overflow-hidden"
                                    style={{ clipPath: 'polygon(0% 0%, 85% 0%, 100% 15%, 100% 100%, 0% 100%)' }}
                                >
                                    {/* Paper Fold Corner */}
                                    <div className="absolute top-0 right-0 w-8 h-8 bg-amber-100/50 border-l-2 border-b-2 border-amber-900/20" />

                                    <div className="text-stone-800 text-sm font-bold font-['Hahmlet'] leading-snug">
                                        화투 점괘에 대해<br />알려드릴까요?
                                    </div>
                                    <button
                                        onClick={() => setShowHwatuInfo(true)}
                                        className="px-4 py-1.5 bg-amber-900/90 text-amber-100 rounded-lg text-xs font-bold hover:bg-amber-900 transition-all flex items-center gap-1.5 group shadow-inner"
                                    >
                                        <Info size={12} className="group-hover:rotate-12 transition-transform" />
                                        자세히 보기
                                    </button>
                                    {/* Bubble Triangle */}
                                    <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-[#fdfaf3] border-r-2 border-b-2 border-amber-900/30 rotate-45 rounded-sm" />
                                </motion.div>

                                <motion.img
                                    animate={{ y: [0, -8, 0] }}
                                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                                    src={getSDCharacterImage('normal')}
                                    alt="Guide Sinseon"
                                    className="w-40 h-40 md:w-56 md:h-56 object-contain drop-shadow-xl"
                                />
                            </motion.div>
                        )}

                        {/* Tarot Guide Character (Ticker) - Symmetrical to Hwatu */}
                        {selectedSide === 'west' && (
                            <motion.div
                                initial={{ opacity: 0, x: 100, y: -50, rotate: 15, scale: 0.8 }}
                                animate={{ opacity: 1, x: 0, y: 0, rotate: 0, scale: 1 }}
                                transition={{
                                    delay: 1.2,
                                    duration: 1,
                                    type: "spring",
                                    stiffness: 50,
                                    damping: 15
                                }}
                                className="absolute right-[-20px] md:right-[-40px] bottom-40 flex flex-col items-center pointer-events-auto z-40 -rotate-12"
                            >
                                {/* Cosmic Info Bubble */}
                                <motion.div
                                    initial={{ opacity: 0, y: 10, scale: 0.8 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    transition={{ delay: 2, duration: 0.5 }}
                                    className="relative mb-4 p-5 bg-purple-900/80 border-2 border-purple-400/30 shadow-[0_0_20px_rgba(168,85,247,0.3)] backdrop-blur-xl flex flex-col items-center gap-3 w-52 text-center rounded-2xl border-t-purple-300/50"
                                >
                                    <div className="text-purple-100 text-sm font-bold font-['Hahmlet'] leading-snug">
                                        타로 점술에 대해<br />알려드릴까요?
                                    </div>
                                    <button
                                        onClick={() => setShowTarotInfo(true)}
                                        className="px-4 py-1.5 bg-purple-600/90 text-white rounded-lg text-xs font-bold hover:bg-purple-500 transition-all flex items-center gap-1.5 group shadow-[0_0_10px_purple]"
                                    >
                                        <Info size={12} className="group-hover:rotate-12 transition-transform" />
                                        자세히 보기
                                    </button>
                                    {/* Bubble Triangle */}
                                    <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-purple-900/80 border-r-2 border-b-2 border-purple-400/30 rotate-45 rounded-sm" />
                                </motion.div>

                                <motion.img
                                    animate={{ y: [0, -8, 0] }}
                                    transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                                    src={getWestCharacterImage('loading')}
                                    alt="Guide Ticker"
                                    className="w-40 h-40 md:w-56 md:h-56 object-contain drop-shadow-[0_0_30px_rgba(168,85,247,0.4)] scale-x-[-1]"
                                />
                            </motion.div>
                        )}
                        <div className={`relative z-30 w-full max-w-5xl mx-auto px-4 md:px-0 flex flex-col gap-4 transition-all duration-700 ${selectedSide === 'west' ? 'md:translate-x-100 md:-translate-y-10' : 'md:translate-x-40 md:-translate-y-10'}`}>
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.8 }}
                                className={`relative rounded-2xl backdrop-blur-md flex items-center transition-all duration-500
                                    ${selectedSide === 'west'
                                        ? 'p-4 md:p-5 min-h-[80px] max-w-[400px] bg-purple-900/60 border-2 border-purple-500/50 shadow-[0_0_20px_rgba(168,85,247,0.2)] ml-0'
                                        : 'p-4 md:p-5 min-h-[80px] max-w-[400px] bg-[#f5f5f0]/90 border-4 border-double border-amber-900 shadow-xl ml-0'
                                    }`}
                            >
                                <div className={`absolute -top-5 left-8 px-6 py-2 rounded-full font-bold uppercase tracking-widest text-sm shadow-lg ${selectedSide === 'west' ? 'bg-purple-600 text-white border border-purple-400' : 'bg-[#5c4033] text-amber-100 border border-[#8b4513]'}`}>
                                    {selectedSide === 'west' ? getCharacterName('west', equippedWestId) : getCharacterName('east', equippedEastId)}
                                </div>
                                <div className={`font-bold leading-relaxed w-full transition-all
                                    ${selectedSide === 'west'
                                        ? "text-lg md:text-xl text-purple-100 font-['Hahmlet']"
                                        : "text-lg md:text-xl text-stone-900 font-['Hahmlet']"
                                    }
                                `}>
                                    <TypewriterText key={selectedSide} text={selectedSide === 'west' ? "궁금한 운명을 선택하세요" : "그대의 운명 중... 무엇을 살펴볼까요?"} speed={50} delay={1000} />
                                </div>
                                <motion.div animate={{ y: [0, 5, 0] }} transition={{ repeat: Infinity, duration: 1 }} className={`absolute bottom-4 right-6 text-2xl ${selectedSide === 'west' ? 'text-purple-400' : 'text-amber-800'}`}>▼</motion.div>
                            </motion.div>

                            {/* Category Selection */}
                            <div className="flex flex-col gap-3 mt-6 ml-4">
                                {CATEGORIES.map((cat, idx) => (
                                    <motion.button
                                        key={cat.id}
                                        initial={{ opacity: 0, x: selectedSide === 'west' ? 50 : -50 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        transition={{
                                            delay: 2.5 + (idx * 0.1),
                                            type: "spring",
                                            stiffness: 100,
                                            damping: 15
                                        }}
                                        whileHover={{ scale: 1.05, x: selectedSide === 'west' ? -10 : 10 }}
                                        whileTap={{ scale: 0.95 }}
                                        onClick={() => handleStartReading(cat.id)}
                                        className={`w-full max-w-[200px] h-16 group flex items-center gap-4 px-6 rounded-2xl border-2 border-double backdrop-blur-xl transition-all duration-300
                                            ${selectedSide === 'west'
                                                ? 'bg-purple-900/60 border-purple-500/50 hover:border-purple-400 shadow-lg hover:shadow-purple-500/20'
                                                : 'bg-[#fdfaf3]/95 border-amber-900/30 hover:border-amber-900 shadow-lg hover:shadow-amber-900/20'
                                            }`}
                                    >
                                        <div className={`p-2 rounded-full group-hover:scale-110 transition-transform ${selectedSide === 'west' ? 'bg-purple-500/10' : 'bg-amber-900/5'}`}>
                                            <cat.icon size={24} className={cat.color} />
                                        </div>
                                        <span className={`text-lg font-bold font-['Hahmlet'] ${selectedSide === 'west' ? 'text-purple-100' : 'text-stone-900'}`}>
                                            {cat.name}
                                        </span>
                                    </motion.button>
                                ))}
                            </div>
                        </div>
                    </div>
                </motion.div>
            )}

            {phase === 'card-selection' && selectedSide && (
                <div className="relative z-10 flex-1 flex flex-col items-center justify-center w-full h-full overflow-hidden">
                    {/* Top Navigation */}
                    <div className="absolute top-8 left-8 right-8 z-[200] flex justify-between items-center pointer-events-none">
                        <motion.button
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            onClick={handleBack}
                            className={`pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full backdrop-blur-xl border transition-all shadow-lg font-['Hahmlet']
                                ${selectedSide === 'west'
                                    ? 'bg-purple-950/60 border-purple-400/40 text-purple-100 hover:bg-purple-900/80 shadow-purple-500/10'
                                    : 'bg-stone-900/60 border-amber-900/40 text-amber-100 hover:bg-stone-800/80 shadow-amber-900/10'
                                }`}
                        >
                            <ArrowLeft size={20} />
                            <span className="text-sm font-medium">뒤로가기</span>
                        </motion.button>

                        <motion.button
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            onClick={() => navigate('/')}
                            className={`pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full backdrop-blur-xl border transition-all shadow-lg font-['Hahmlet']
                                ${selectedSide === 'west'
                                    ? 'bg-purple-950/60 border-purple-400/40 text-purple-100 hover:bg-purple-900/80 shadow-purple-500/10'
                                    : 'bg-stone-900/60 border-amber-900/40 text-amber-100 hover:bg-stone-800/80 shadow-amber-900/10'
                                }`}
                        >
                            <span className="text-sm font-medium">나가기</span>
                            <X size={20} />
                        </motion.button>
                    </div>

                    {(() => {
                        const steps = selectedSide === 'west' ? WEST_STEPS : EAST_STEPS;
                        const currentStep = steps[currentStepIndex];
                        return (
                            <>
                                <motion.div key={`step-${currentStepIndex}`} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} className="text-center mt-12 mb-4">
                                    <h2 className={`text-4xl md:text-6xl tracking-[0.2em] mb-4 font-['GmarketSans'] font-bold text-center
                                        ${selectedSide === 'west' ? 'text-purple-200' : 'text-stone-200'}
                                    `}>
                                        {currentStep.title.split(' (')[0]}
                                    </h2>
                                    <p className="text-white/60 tracking-widest font-['GmarketSans'] font-medium mb-2 text-sm md:text-base px-10 break-keep">{currentStep.desc}</p>
                                    <motion.div
                                        animate={{ opacity: [0.4, 1, 0.4] }}
                                        transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                                        className="mt-4"
                                    >
                                        <span className={`text-xs md:text-sm tracking-[0.4em] font-['GmarketSans'] font-medium uppercase ${selectedSide === 'west' ? 'text-purple-400/80' : 'text-amber-400/80'}`}>
                                            카드를 선택하세요
                                        </span>
                                    </motion.div>
                                </motion.div>

                                <div className="flex-1 w-full relative flex items-center justify-center pointer-events-none overflow-visible min-h-[400px]">
                                    {selectedSide === 'west' ? (
                                        <div className="pointer-events-auto w-full h-full flex items-center justify-center">
                                            <MysticScatteredDeck cards={availableCards} onCardPick={handleCardPick} stepIndex={currentStepIndex} />
                                        </div>
                                    ) : (
                                        <div className="relative w-full max-w-5xl h-full flex flex-wrap justify-center items-center content-center gap-1 md:gap-2 px-10 pointer-events-auto mt-4 overflow-visible">

                                            {hwatuDeck.map((card, i) => {
                                                return (
                                                    <motion.div
                                                        key={`hwatu-${card.id}`}
                                                        initial={{ opacity: 0, scale: 0.8 }}
                                                        animate={{
                                                            opacity: card.isPicked ? 0 : 1,
                                                            scale: card.isPicked ? 2 : 1,
                                                            rotate: card.isPicked ? 45 : card.rotate,
                                                            x: card.x,
                                                            y: card.isPicked ? -500 : card.y,
                                                            filter: card.isPicked ? "blur(10px)" : "blur(0px)"
                                                        }}
                                                        whileHover={!card.isPicked ? {
                                                            scale: 1.2,
                                                            rotate: 0,
                                                            y: -35,
                                                            zIndex: 200,
                                                            transition: { duration: 0.2 }
                                                        } : {}}
                                                        whileTap={!card.isPicked ? { scale: 0.95 } : {}}
                                                        onClick={() => !card.isPicked && handleCardPick(card.id)}
                                                        className={`w-14 h-22 md:w-16 md:h-24 bg-amber-900 border border-amber-500/40 rounded shadow-2xl flex-shrink-0 relative group 
                                                            ${card.isPicked ? 'pointer-events-none' : 'cursor-pointer'}`}
                                                        style={{
                                                            zIndex: i,
                                                            marginLeft: '-1.2rem',
                                                            marginTop: '-0.3rem'
                                                        }}
                                                    >
                                                        <div className="absolute inset-0.5 bg-red-900 border border-red-500/20 rounded flex items-center justify-center">
                                                            <div className="w-[60%] h-[80%] border border-red-500/10 rounded-full opacity-20" />
                                                        </div>
                                                        <div className="absolute inset-0 bg-white/0 group-hover:bg-white/5 transition-colors" />
                                                    </motion.div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>

                                <div className="flex items-center gap-3 mb-10 mt-auto">
                                    {steps.map((step, i) => (
                                        <div key={step.id} className="flex flex-col items-center gap-2">
                                            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }} transition={{ delay: i * 0.1, type: "spring" }} className={`relative w-2.5 h-2.5 rounded-full transition-all duration-500 ${i <= currentStepIndex ? (selectedSide === 'west' ? 'bg-purple-500' : 'bg-amber-500') : 'bg-white/10'}`}>
                                                {i === currentStepIndex && (
                                                    <motion.div animate={{ scale: [1, 2, 1], opacity: [0.6, 0, 0.6] }} transition={{ duration: 1.5, repeat: Infinity }} className={`absolute inset-0 rounded-full ${selectedSide === 'west' ? 'bg-purple-500' : 'bg-amber-500'}`} />
                                                )}
                                            </motion.div>
                                        </div>
                                    ))}
                                </div>
                            </>
                        );
                    })()}
                </div>
            )
            }

            {
                phase === 'shuffling' && (
                    <div className="relative z-10 flex-1 flex flex-col items-center justify-center w-full px-6">
                        <motion.div
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            className="relative flex flex-col items-center max-w-2xl"
                        >
                            {/* Mystical Background Glow */}
                            <motion.div
                                animate={{
                                    rotate: 360,
                                    scale: [1, 1.2, 1],
                                    opacity: [0.1, 0.2, 0.1]
                                }}
                                transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                                className={`absolute w-[150%] h-[150%] rounded-full blur-[120px] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 -z-10
                                    ${selectedSide === 'west' ? 'bg-purple-600/30' : 'bg-amber-600/30'}`}
                            />

                            <AnimatePresence mode="wait">
                                <motion.img
                                    key={currentPose}
                                    src={selectedSide === 'west' ? getSDWestCharacterImage(currentPose) : getSDCharacterImage(currentPose)}
                                    alt="Loading Character"
                                    initial={{ opacity: 0, x: 20, filter: "blur(10px)" }}
                                    animate={{ opacity: 1, x: 0, filter: "blur(0px)" }}
                                    exit={{ opacity: 0, x: -20, filter: "blur(10px)" }}
                                    transition={{ duration: 0.6, ease: "easeOut" }}
                                    className="w-64 h-64 md:w-80 md:h-80 object-contain mb-8 drop-shadow-[0_0_30px_rgba(255,255,255,0.15)]"
                                />
                            </AnimatePresence>

                            <div className="space-y-6 text-center">
                                <div className="h-20 flex items-center justify-center">
                                    <AnimatePresence mode="wait">
                                        <motion.p
                                            key={loadingMsgIndex}
                                            initial={{ opacity: 0, y: 10, filter: "blur(5px)" }}
                                            animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                                            exit={{ opacity: 0, y: -10, filter: "blur(5px)" }}
                                            transition={{ duration: 0.5 }}
                                            className="text-lg md:text-xl font-['GmarketSans'] font-medium text-white/70 text-center leading-relaxed break-keep whitespace-pre-line max-w-md"
                                        >
                                            {selectedSide === 'west'
                                                ? WEST_LOADING_MESSAGES[loadingMsgIndex]
                                                : LOADING_MESSAGES[loadingMsgIndex]}
                                        </motion.p>
                                    </AnimatePresence>
                                </div>
                            </div>

                            {/* Decorative Progress bar effect */}
                            <div className={`mt-8 w-48 h-1 rounded-full overflow-hidden bg-white/5 relative`}>
                                <motion.div
                                    initial={{ x: "-100%" }}
                                    animate={{ x: "100%" }}
                                    transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                                    className={`absolute inset-0 w-1/2 h-full bg-gradient-to-r from-transparent via-${selectedSide === 'west' ? 'purple-500' : 'amber-500'} to-transparent`}
                                />
                            </div>
                        </motion.div>
                    </div>
                )
            }

            {/* Hwatu Info Modal */}
            <AnimatePresence>
                {showHwatuInfo && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-sm"
                        onClick={() => setShowHwatuInfo(false)}
                    >
                        {/* Hwatu Modal Content */}
                        <motion.div
                            initial={{ scale: 0.9, y: 30, opacity: 0 }}
                            animate={{ scale: 1, y: 0, opacity: 1 }}
                            exit={{ scale: 0.9, y: 30, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                            className="relative w-full max-w-3xl max-h-[90vh] overflow-hidden bg-[#fdfcf5] text-stone-900 rounded-[2.5rem] shadow-[0_30px_100px_rgba(0,0,0,0.8)] border-8 border-double border-amber-900/40"
                        >
                            <div className="absolute inset-0 opacity-[0.1] pointer-events-none bg-[url('https://www.transparenttextures.com/patterns/rice-paper.png')]" />
                            <div className="relative p-8 md:p-12 border-b border-amber-900/10 flex justify-between items-center">
                                <div className="space-y-1">
                                    <div className="text-amber-800 text-sm tracking-[0.4em] font-medium font-['Hahmlet']">신비한 동양의 비책</div>
                                    <h2 className="text-4xl font-bold font-['Hahmlet'] text-amber-950">화투 점괘 안내</h2>
                                </div>
                                <button onClick={() => setShowHwatuInfo(false)} className="p-3 hover:bg-amber-900/5 rounded-full transition-colors text-amber-900/40 hover:text-amber-900"><X size={32} /></button>
                            </div>
                            <div className="relative p-8 md:p-12 overflow-y-auto max-h-[calc(90vh-160px)] space-y-10 font-['Hahmlet']">
                                <section className="space-y-4 text-stone-700 leading-relaxed bread-keep">
                                    열두 달의 자연과 삶을 담은 48장의 화투 패를 통해 그대의 운명을 짚어보는 고유의 비책입니다.
                                </section>
                                <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {[
                                        { title: '본인 및 현재상태', desc: '현재 당신이 처한 상황과 내면의 상태를 비추어봅니다. 스스로도 미처 깨닫지 못했던 당신의 본심과 기운을 확인해보세요.' },
                                        { title: '상대 및 환경', desc: '당신을 둘러싼 주변의 기운과 타인의 영향을 살펴봅니다. 지금 당신에게 영향을 미치는 외부적인 요인과 조력자 혹은 방해물을 파악합니다.' },
                                        { title: '과정 및 관계', desc: '현재의 흐름이 어떻게 이어지고 있는지, 그리고 당신과 주변의 관계가 어떻게 변화하고 있는지를 보여줍니다. 인연의 끈과 사건의 전개를 읽어냅니다.' },
                                        { title: '결과 및 조언', desc: '이 흐름이 도달할 결말과, 더 나은 운명을 위해 취해야 할 행동을 제안합니다. 위기를 기회로 바꾸고 행운을 잡을 수 있는 지혜를 드립니다.' },
                                    ].map((step, idx) => (
                                        <div key={idx} className="p-5 bg-white/50 border border-amber-900/10 rounded-2xl flex flex-col gap-2">
                                            <div className="font-bold text-amber-950 text-lg border-b border-amber-900/10 pb-2 mb-1">{step.title}</div>
                                            <div className="text-stone-700 text-sm leading-relaxed break-keep font-medium">{step.desc}</div>
                                        </div>
                                    ))}
                                </section>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Tarot Info Modal */}
            <AnimatePresence>
                {showTarotInfo && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/80 backdrop-blur-sm"
                        onClick={() => setShowTarotInfo(false)}
                    >
                        {/* Tarot Modal Content */}
                        <motion.div
                            initial={{ scale: 0.9, y: 30, opacity: 0 }}
                            animate={{ scale: 1, y: 0, opacity: 1 }}
                            exit={{ scale: 0.9, y: 30, opacity: 0 }}
                            onClick={(e) => e.stopPropagation()}
                            className="relative w-full max-w-3xl max-h-[90vh] overflow-hidden bg-gray-950 text-purple-100 rounded-[2.5rem] shadow-[0_30px_100px_rgba(168,85,247,0.3)] border-4 border-purple-500/30 backdrop-blur-2xl"
                        >
                            {/* Stars Pattern Overlay */}
                            <div className="absolute inset-0 opacity-[0.2] pointer-events-none bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-purple-500/20 via-transparent to-transparent" />

                            {/* Header */}
                            <div className="relative p-8 md:p-12 border-b border-purple-500/10 flex justify-between items-center bg-gradient-to-r from-purple-900/20 to-transparent">
                                <div className="space-y-1">
                                    <div className="text-purple-400 text-sm tracking-[0.4em] font-medium font-['Hahmlet']">신비한 서양의 지혜</div>
                                    <h2 className="text-4xl font-bold font-['Hahmlet'] text-white">타로 점술 안내</h2>
                                </div>
                                <button
                                    onClick={() => setShowTarotInfo(false)}
                                    className="p-3 hover:bg-white/5 rounded-full transition-colors text-white/40 hover:text-purple-300"
                                >
                                    <X size={32} />
                                </button>
                            </div>

                            {/* Content */}
                            <div className="relative p-8 md:p-12 overflow-y-auto max-h-[calc(90vh-160px)] space-y-10 font-['Hahmlet']">
                                <section className="space-y-4">
                                    <h3 className="text-xl font-bold text-purple-300 flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-purple-500 shadow-[0_0_10px_purple]" />
                                        타로 점술이란 무엇인가요?
                                    </h3>
                                    <p className="text-purple-100/70 leading-relaxed break-keep">
                                        타로는 78장의 카드로 구성된 상징적인 도구로, 무의식의 거울이자 우주의 질서를 담고 있습니다.
                                        우리는 그중 강력한 상징성을 가진 메이저 아르카나 22장을 사용하여 당신의 운명의 흐름을 읽어냅니다.
                                    </p>
                                </section>

                                <section className="space-y-6">
                                    <h3 className="text-xl font-bold text-purple-300 flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-purple-500 shadow-[0_0_10px_purple]" />
                                        카드 배열법 (3-Card Spread)
                                    </h3>
                                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                        {[
                                            { title: '과거 (Past)', desc: '당신의 생각과 경험이 겹겹이 쌓여 만들어진 현재의 근간이자 밑바탕입니다. 지나온 시간이 건네는 지혜를 확인해보세요.' },
                                            { title: '현재 (Present)', desc: '지금 이 순간 당신의 에너지가 머무는 곳이자, 실제 마주하고 있는 감정과 상황의 거울입니다. 현재의 진실을 대면해보세요.' },
                                            { title: '미래 (Future)', desc: '지금의 기운과 선택이 이어져 도달하게 될 지점입니다. 다가올 변화를 미리 살피고 더 나은 내일을 준비하는 이정표가 되어줄 것입니다.' },
                                        ].map((step, idx) => (
                                            <div key={idx} className="p-6 bg-purple-900/20 border border-purple-500/20 rounded-2xl flex flex-col items-center text-center gap-4 hover:border-purple-500/40 transition-colors">
                                                <div className="w-10 h-10 rounded-full bg-purple-600 shadow-[0_0_15px_purple] text-white flex items-center justify-center text-sm font-bold shrink-0">{idx + 1}</div>
                                                <div className="space-y-2">
                                                    <div className="font-bold text-white text-lg">{step.title}</div>
                                                    <div className="text-sm text-purple-200/60 break-keep">{step.desc}</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </section>

                                <section className="p-6 bg-purple-500/10 border border-purple-400/20 rounded-2xl italic text-purple-200/80 text-sm leading-relaxed break-keep text-center">
                                    "카드는 미래를 확정 짓는 도구가 아닙니다. <br />
                                    당신의 내면을 비추고, 더 나은 선택을 할 수 있도록 돕는 우주의 신호입니다. <br />
                                    깊은 호흡과 함께 진심을 다해 카드를 선택해 보세요."
                                </section>
                            </div>

                            {/* Footer Decoration */}
                            <div className="absolute inset-x-0 bottom-0 h-4 bg-gradient-to-t from-purple-500/20 to-transparent" />
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            <AnimatePresence>
                {phase === 'result' && (
                    <div className="absolute inset-0 z-50">
                        {selectedSide === 'east' && hwatuResultData ? (
                            resultSubStep < 4 ? (
                                <HwatuStepResult
                                    key={`step-${resultSubStep}`}
                                    card={hwatuResultData.cards[resultSubStep]}
                                    onNext={() => setResultSubStep(prev => prev + 1)}
                                    onPrev={() => setResultSubStep(prev => Math.max(0, prev - 1))}
                                    isFirstStep={resultSubStep === 0}
                                    isLastStep={resultSubStep === 3}
                                    onExit={() => navigate('/')}
                                />
                            ) : resultSubStep === 4 ? (
                                <HwatuStoryResult
                                    data={hwatuResultData}
                                    onRestart={handleRestartHwatu}
                                    onExit={handleExit}
                                    onBack={handleBack}
                                />
                            ) : (
                                hwatuSummaryProps && (
                                    <HwatuSummaryResult
                                        data={hwatuSummaryProps}
                                        onRestart={() => navigate('/')}
                                        onExit={() => navigate('/')}
                                        onBack={handleBack}
                                    />
                                )
                            )
                        ) : selectedSide === 'west' && tarotResultData ? (
                            resultSubStep < 3 ? (
                                tarotResultData.cards[resultSubStep] && (
                                    <TarotStepResult
                                        key={`tarot-step-${resultSubStep}`}
                                        card={tarotResultData.cards[resultSubStep]}
                                        onNext={() => setResultSubStep(prev => prev + 1)}
                                        onBack={() => {
                                            if (resultSubStep > 0) setResultSubStep(prev => prev - 1);
                                            else handleBack();
                                        }}
                                        onExit={() => navigate('/')}
                                    />
                                )
                            ) : (
                                <TarotResultView
                                    data={backendResult}
                                    onRestart={() => navigate('/')}
                                    onExit={() => navigate('/')}
                                    onBack={handleBack}
                                />
                            )
                        ) : (
                            // Loading or Error State for results
                            <div className="w-full h-full flex items-center justify-center bg-black/90">
                                <p className="text-white">결과를 불러오는 중입니다...</p>
                            </div>
                        )}
                    </div>
                )}
            </AnimatePresence>
        </div >
    );
};

export default CardReadingPage;
