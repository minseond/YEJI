import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useRef } from 'react';
import { Star, Crown, Sparkles, X, Check, Shirt } from 'lucide-react';
import { jwtDecode } from 'jwt-decode';
import { getUserInfo } from '../../api/auth';

// New Characters (Ticker)
import { useSound } from '../../hooks/useSound';
import tickerNormal from '../../assets/character/west/Ticker/Ticker_normal.png';
import tickerSmile from '../../assets/character/west/Ticker/Ticker_smile.png';

// Import New Characters
import princessNormal from '../../assets/character/west/princess/princess_normal.png';
import princessSmile from '../../assets/character/west/princess/princess_smile.png';

// Updated Base Characters
import stellaNormal from '../../assets/character/west/stella/stella_normal.png';
import stellaSmile from '../../assets/character/west/stella/stella_smile.png';
import soiseolNormal from '../../assets/character/east/soiseol/soiseol_normal.png';
import soiseolSmile from '../../assets/character/east/soiseol/soiseol_smile.png';
import sinsunNormal from '../../assets/character/east/sinseon/sinseon_normal.png';
import sinsunSmile from '../../assets/character/east/sinseon/sinseon_smile.png';
import buchaeWomanNormal from '../../assets/character/east/buchae_woman/buchae_woman_normal.png';
import buchaeWomanSmile from '../../assets/character/east/buchae_woman/buchae_woman_smile.png';

// Stella Skins
import stellaSkin1 from '../../assets/character/west/stella/skin1/stella_normal.png';
import stellaSkin1Smile from '../../assets/character/west/stella/skin1/stella_smile.png';
import { getCharacterSettings, saveCharacterSettings } from '../../utils/character';

const CollectionPage = () => {
    const initialSettings = getCharacterSettings();
    const [equippedWestId, setEquippedWestId] = useState(initialSettings.west);
    const [equippedEastId, setEquippedEastId] = useState(initialSettings.east);
    const [selectionMode, setSelectionMode] = useState<'west' | 'east' | null>(null);
    const [showTutorial, setShowTutorial] = useState(false);
    const [tutorialStep, setTutorialStep] = useState(0);
    const [userNickname, setUserNickname] = useState<string>('여행자');
    const scrollContainerRef = useRef<HTMLDivElement>(null);

    // Auto-Scroll for Tutorial
    useEffect(() => {
        if (showTutorial && scrollContainerRef.current) {
            if (tutorialStep <= 2) {
                // Step 0-2: Top (Main Character)
                scrollContainerRef.current.scrollTo({ top: 0, behavior: 'smooth' });
            } else if (tutorialStep === 3) {
                // Step 3: Collection Grid (Scroll down approx 450px)
                scrollContainerRef.current.scrollTo({ top: 350, behavior: 'smooth' });
            }
        }
    }, [tutorialStep, showTutorial]);

    // Skin System State
    const [skinModalChar, setSkinModalChar] = useState<any | null>(null);
    const [equippedSkins, setEquippedSkins] = useState<Record<string, 'normal' | 'special'>>({});
    const { play } = useSound();

    // Helper to get current skin image
    // Helper to get current skin image
    const getCharBaseImage = (char: any) => {
        if (!char) return null;
        const skin = equippedSkins[char.id] || 'normal';

        if (skin === 'special') {
            // New Logic: If character has a dedicated 'specialSkin' object, use it.
            if (char.specialSkin) return char.specialSkin.base;
            // Legacy Logic: Use hoverImage as the special skin base (e.g. Smile version as Skin)
            return char.hoverImage || char.image;
        }
        return char.image;
    };

    // Helper to get current skin HOVER image
    const getCharHoverImage = (char: any) => {
        if (!char) return null;
        const skin = equippedSkins[char.id] || 'normal';

        if (skin === 'special') {
            // New Logic: Special Skin's dedicated hover image
            if (char.specialSkin) return char.specialSkin.hover;
            // Legacy Logic: Swap back to Normal Image on hover (or stay same?)
            // If the special skin is the "Smile" version, hover could be "Normal" (Swap) or just keep Smile.
            // Let's swap to be dynamic.
            return char.image;
        }

        // Normal Skin: Use standard hoverImage (Wink/Smile)
        return char.hoverImage;
    };



    // Tutorial Logic
    useEffect(() => {
        const fetchUserNickname = async () => {
            const token = localStorage.getItem('accessToken');
            if (token) {
                try {
                    const decoded: any = jwtDecode(token);
                    const userData = await getUserInfo(decoded.userId);
                    if (userData.nickname) {
                        setUserNickname(userData.nickname);
                    }
                } catch (error) {
                    console.error('Failed to fetch nickname for tutorial:', error);
                }
            }
        };

        const key = 'hasSeenCollectionTutorial';
        if (!localStorage.getItem(key)) {
            fetchUserNickname();
            const timer = setTimeout(() => setShowTutorial(true), 500);
            return () => clearTimeout(timer);
        } else {
            fetchUserNickname();
        }
    }, []);

    const handleCloseTutorial = () => {
        setShowTutorial(false);
        setTutorialStep(0);
        setSelectionMode(null);
        localStorage.setItem('hasSeenCollectionTutorial', 'true');
    };

    const handleNextStep = () => {
        if (tutorialStep < tutorialMessages.length - 1) {
            const nextStep = tutorialStep + 1;
            setTutorialStep(nextStep);

            // Step-specific interactions
            if (nextStep === 2) {
                // Simulate "Clicking" for selection mode
                setSelectionMode('west');
            } else if (nextStep === 3) {
                setSelectionMode(null);
            }
        } else {
            handleCloseTutorial();
        }
    };

    // ESC & Space Key Support for Tutorial
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                if (showTutorial) handleCloseTutorial();
                if (skinModalChar) setSkinModalChar(null);
            } else if (showTutorial && (e.code === 'Space' || e.key === ' ')) {
                e.preventDefault(); // Prevent scrolling
                handleNextStep();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [showTutorial, skinModalChar, tutorialStep]);



    const tutorialMessages = [
        {
            title: `${userNickname}님, 어서오세요!`,
            text: <>이 곳은 당신의 여정을 도와줄 신비로운 존재들을<br />기록하고 관리하는 <strong className="text-purple-300">도감</strong>이에요.</>
        },
        {
            title: "메인 캐릭터",
            text: <>맨 위에는 현재 당신과 함께하는<br /><strong className="text-white">메인 캐릭터</strong>가 자리하고 있어요.</>
        },
        {
            title: "캐릭터 교체",
            text: <>메인 캐릭터를 <strong className="text-amber-300">클릭</strong>하면<br />교체 모드로 진입한답니다!<br />원하는 캐릭터를 선택해 쉽게 바꿀 수 있어요.</>
        },
        {
            title: "동반자 목록",
            text: <>아래에는 당신의 여정을 함께할<br />다양한 친구들이 기다리고 있어요.<br />모든 캐릭터는 언제든 자유롭게 만날 수 있답니다.</>
        },
        {
            title: "준비 완료!",
            text: <>자, 이제 함께할 캐릭터를 선택하여<br />당신만의 특별한 이야기를 완성해보세요!</>
        }
    ];

    // Mock Data for Characters
    const westernChars = [
        {
            id: 'stella',
            name: '스텔라',
            role: '왕국의 점성술사',
            desc: '사파이어 왕국의 신비로운 점성술사. 별들의 궤적을 쫓으며 왕국의 운명을 예견합니다.',
            image: stellaNormal,
            hoverImage: stellaSmile,
            specialSkin: {
                name: '할로윈 스킨',
                base: stellaSkin1,
                hover: stellaSkin1Smile
            },
            type: 'western',
            unlocked: true,
            customStyle: { scale: 1.0, top: '0%' }
        },
        {
            id: 'princess',
            name: '넬',
            role: '왕실의 태양',
            desc: '사파이어 왕국의 고귀한 공주. 부드러운 미소 뒤에 백성들을 향한 뜨거운 태양의 의지를 품고 있습니다.',
            image: princessNormal,
            hoverImage: princessSmile,
            type: 'western',
            unlocked: true,
            customStyle: { scale: 1.1, top: '5%' }
        },
        {
            id: 'Ticker',
            name: '티커',
            role: '뒷골목의 술사',
            desc: '사파이어 왕국 뒷골목의 전설적인 카드 술사. 거친 삶 속에서 익힌 기막힌 손기술로 운명을 뒤바꿉니다.',
            image: tickerNormal,
            hoverImage: tickerSmile,
            type: 'western',
            unlocked: true,
            customStyle: { scale: 1.15, top: '4%' }
        },
    ];

    const orientalChars = [
        {
            id: 'soiseol',
            name: '소이설',
            role: '제국의 무녀',
            desc: '동방 제국의 영험한 무녀. 오방신의 기운을 빌려 세상의 어지러운 기운을 다스리고 앞날을 비춥니다.',
            image: soiseolNormal,
            hoverImage: soiseolSmile,
            type: 'oriental',
            unlocked: true,
            customStyle: { scale: 1.0, top: '0%' }
        },

        {
            id: 'sinseon',
            name: '청운 도사',
            role: '제국의 현자',
            desc: '동방 제국 구름 위를 정처 없이 떠도는 현자. 속세의 욕심을 버린 채 도술을 닦으며 세상의 이치를 관조합니다.',
            image: sinsunNormal,
            hoverImage: sinsunSmile,
            type: 'oriental',
            unlocked: true,
            customStyle: { scale: 1.2, top: '5%' }
        },
        {
            id: 'buchae_woman',
            name: '홍주',
            role: '제국의 춤사위',
            desc: '동방 제국 최고의 무희. 붉은 부채의 손짓 하나로 사람들의 넋을 기리고 액운을 쫓는 신비로운 여인입니다.',
            image: buchaeWomanNormal,
            hoverImage: buchaeWomanSmile,
            type: 'oriental',
            unlocked: true,
            customStyle: { scale: 1.1, top: '3%' }
        },
    ];

    const currentWest = westernChars.find(c => c.id === equippedWestId) || westernChars[0];
    const currentEast = orientalChars.find(c => c.id === equippedEastId) || orientalChars[0];

    const handleCardClick = (char: any) => {
        if (!char.unlocked) return;

        // Sound Trigger for Stella
        if (char.id === 'stella') {
            play('VOICE', 'STELLA', { subKey: 'COLLECTION_CLICK' });
        }

        if (selectionMode === 'west' && char.type === 'western') {
            setEquippedWestId(char.id);
            setSelectionMode(null);
            // Wait for explicit save or should we save here?
            // The user said "If I change it... it should be fixed... (there is a button)"
            // BUT, the selection mode flow is explicit "Change Main". 
            // So for selection mode, immediate save is probably correct/expected because you clicked "Select Main".
            // HOWEVER, the user's comment "There is a Change Main Character button" might refer to the MODAL button.
            // Let's keep immediate save for Selection Mode (as it's a direct "Select this as main" action),
            // and ALSO ensure the Modal Button saves.
            saveCharacterSettings({ west: char.id, east: equippedEastId });
        } else if (selectionMode === 'east' && char.type === 'oriental') {
            setEquippedEastId(char.id);
            setSelectionMode(null);
            saveCharacterSettings({ west: equippedWestId, east: char.id });
        } else if (!selectionMode) {
            // Open Skin Modal if not in selection mode
            setSkinModalChar(char);
        }
    };

    const GameCard = ({ char }: { char: any }) => {
        const isWestern = char.type === 'western';
        const accentColor = isWestern ? 'text-purple-400' : 'text-amber-400';
        const borderColor = isWestern ? 'border-purple-500/30' : 'border-amber-500/30';
        const glowColor = isWestern ? 'shadow-purple-500/20' : 'shadow-amber-500/20';
        const fontClass = "font-['Hahmlet']";
        const bgGradient = isWestern
            ? 'bg-gradient-to-b from-indigo-950/80 to-slate-900/90'
            : 'bg-gradient-to-b from-stone-900/80 to-neutral-900/90';

        // Selection State Styles
        const isSelected = (isWestern && equippedWestId === char.id) || (!isWestern && equippedEastId === char.id);
        const isSelectable = ((selectionMode === 'west' && isWestern) || (selectionMode === 'east' && !isWestern));
        const dimIfNotSelectable = selectionMode && !isSelectable;

        return (
            <motion.div
                layout
                onClick={() => handleCardClick(char)}
                whileHover={!dimIfNotSelectable ? { scale: 1.05, y: -5, zIndex: 10 } : {}}
                animate={{
                    opacity: dimIfNotSelectable ? 0.3 : 1,
                    scale: isSelectable && !dimIfNotSelectable ? [1, 1.02, 1] : 1,
                    borderColor: isSelected ? (isWestern ? '#a855f7' : '#f59e0b') : undefined
                }}
                transition={{
                    scale: { repeat: isSelectable ? Infinity : 0, duration: 1.5 }
                }}
                className={`relative w-full aspect-[2/3] rounded-xl border-2 ${isSelected ? (isWestern ? 'border-purple-500' : 'border-amber-500') : borderColor} ${bgGradient} overflow-hidden shadow-lg ${glowColor} ring-1 ring-white/10 group cursor-pointer transition-all duration-300 backdrop-blur-sm`}
            >
                {/* Selection Indicator Overlay */}
                {isSelectable && (
                    <div className="absolute inset-0 z-50 flex items-center justify-center bg-black/20 group-hover:bg-transparent transition-colors">
                        <div className={`px-3 py-1 rounded-full text-xs font-bold text-white shadow-lg ${isWestern ? 'bg-purple-600' : 'bg-amber-600'}`}>
                            선택 가능
                        </div>
                    </div>
                )}

                {/* Equipped Indicator */}
                {isSelected && (
                    <div className={`absolute top-2 left-2 z-40 px-2 py-0.5 rounded text-[10px] font-bold text-white shadow-sm flex items-center gap-1 font-['GmarketSansMedium'] ${isWestern ? 'bg-purple-600' : 'bg-amber-600'}`}>
                        <Crown size={10} className="text-yellow-300" />
                        MAIN
                    </div>
                )}

                {/* Card Frame/Border Decoration */}
                <div className="absolute inset-0 border-2 border-white/5 m-1 rounded-lg pointer-events-none z-20" />

                {/* Character Image */}
                <div className="absolute inset-0 z-10 flex items-center justify-center">
                    {char.image ? (
                        <div className="w-full h-full relative overflow-hidden">
                            {/* Background Glow behind character */}
                            <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-[120%] 
                                radial-gradient-center opacity-30 blur-2xl 
                                ${isWestern ? 'bg-purple-600' : 'bg-amber-600'}`}
                            />

                            {/* Base Image (Dynamic Skin) */}
                            <img
                                src={getCharBaseImage(char)}
                                alt={char.name}
                                style={{
                                    transform: `scale(${char.customStyle?.scale || 1}) translateY(${char.customStyle?.top || '0%'})`,
                                    objectPosition: char.customStyle?.objectPosition || 'top center'
                                }}
                                className={`w-full h-full object-cover transition-all duration-500 ease-out
                                    ${getCharHoverImage(char) ? 'group-hover:opacity-0 group-hover:scale-[1.02]' : 'group-hover:scale-[1.02]'}
                                `}
                            />

                            {/* Hover Image (Dynamic Skin Hover) */}
                            {getCharHoverImage(char) && (
                                <img
                                    src={getCharHoverImage(char)}
                                    alt={char.name}
                                    style={{
                                        transform: `scale(${char.customStyle?.scale || 1}) translateY(${char.customStyle?.top || '0%'})`,
                                        objectPosition: char.customStyle?.objectPosition || 'top center'
                                    }}
                                    className="absolute inset-0 w-full h-full object-cover opacity-0 group-hover:opacity-100 group-hover:scale-[1.02] transition-all duration-500 ease-out"
                                />
                            )}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center opacity-30">
                            {isWestern ? <Star size={40} /> : <Crown size={40} />}
                            <span className="text-xs mt-2 font-bold tracking-widest">NO IMAGE</span>
                        </div>
                    )}
                </div>

                {/* Info Content (Slide Up on Hover) */}
                <div className="absolute bottom-0 left-0 right-0 z-30 bg-gradient-to-t from-black via-black/90 to-transparent pt-12 pb-4 px-4 translate-y-2 group-hover:translate-y-0 transition-transform duration-300">
                    <h3 className={`text-lg font-bold text-white flex items-center gap-2 ${fontClass}`}>
                        {char.name}
                    </h3>
                    <p className={`text-[10px] font-bold uppercase tracking-wider mb-2 ${accentColor} opacity-80 ${fontClass}`}>{char.role}</p>
                    <p className={`text-xs text-white/60 line-clamp-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300 delay-100 ${fontClass}`}>
                        {char.desc}
                    </p>
                </div>
            </motion.div>
        );
    };

    return (
        <motion.div
            key="collection-page"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.5 }}
            className="w-full h-screen relative bg-black text-white font-['Hahmlet'] overflow-hidden"
        >
            {/* 1. FIXED BACKGROUND LAYER (Split 50/50) */}
            <div className={`absolute inset-0 flex w-full h-full pointer-events-none z-0 ${showTutorial ? 'brightness-50' : ''}`}>
                {/* LEFT BG */}
                <div className={`w-1/2 h-full relative border-r border-white/10 overflow-hidden transition-all duration-500 ${selectionMode === 'east' ? 'brightness-50 grayscale' : ''}`}>
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_30%,_#2e1065_0%,_#020617_70%)]" />
                    <div className="absolute inset-0 bg-[url('/textures/stardust.png')] opacity-30 mix-blend-screen animate-pulse" />
                </div>
                {/* RIGHT BG */}
                <div className={`w-1/2 h-full relative overflow-hidden transition-all duration-500 ${selectionMode === 'west' ? 'brightness-50 grayscale' : ''}`}>
                    <div className="absolute inset-0 bg-[radial-gradient(circle_at_70%_30%,_#451a03_0%,_#0c0a09_70%)]" />
                    <div className="absolute inset-0 bg-[url('/textures/hanji_pattern.png')] opacity-10 mix-blend-overlay" />
                </div>
            </div>

            {/* Development Badge Overlay Removed */}

            {/* 2. UNIFIED SCROLLABLE CONTAINER */}
            <div ref={scrollContainerRef} className="absolute inset-0 w-full h-full overflow-y-auto custom-scrollbar">
                <div className="flex w-full min-h-full">
                    {/* LEFT CONTENT */}
                    <div className="w-1/2 p-8 pt-32 pb-20">

                        {/* Equipped Slot Header - West */}
                        <div className={`mb-12 flex flex-col items-center transition-all duration-500 ${showTutorial && (tutorialStep === 1 || tutorialStep === 2) ? 'z-[61] relative scale-100' : ''}`}>

                            <div
                                onClick={() => !showTutorial && setSelectionMode(selectionMode === 'west' ? null : 'west')}
                                className={`relative w-48 aspect-[3/4] rounded-2xl border-2 border-purple-500/50 bg-gradient-to-b from-purple-900/40 to-black/80 backdrop-blur-md shadow-[0_0_30px_rgba(168,85,247,0.25)] overflow-hidden group cursor-pointer ring-4 ring-purple-500/20 group-hover:ring-purple-500/60 ring-offset-2 ring-offset-black transition-all duration-500
                                    ${selectionMode === 'west' ? 'ring-purple-500 scale-105 shadow-[0_0_60px_rgba(168,85,247,0.5)]' : ''}
                                    ${showTutorial && (tutorialStep === 1 || tutorialStep === 2) ? 'ring-orange-400 shadow-[0_0_50px_rgba(251,146,60,0.8)] scale-105' : ''}
                                `}
                            >
                                {/* Premium Glow Effect */}
                                <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-tr from-purple-500/20 via-transparent to-indigo-500/20 opacity-60 group-hover:opacity-100 transition-opacity" />
                                <div className="absolute -inset-1 bg-gradient-to-b from-white/20 to-transparent opacity-0 group-hover:opacity-50 blur-sm transition-opacity" />

                                {/* Badge */}
                                <div className={`absolute top-3 left-3 z-20 flex items-center gap-1.5 px-3 py-1 rounded-full shadow-lg border border-white/20 backdrop-blur-md transition-all duration-300 font-['GmarketSansMedium'] ${selectionMode === 'west' ? 'bg-purple-600 text-white' : 'bg-black/60 text-purple-200'}`}>
                                    <Crown size={12} className={selectionMode === 'west' ? "text-yellow-300 animate-bounce" : "text-purple-400"} />
                                    <span className="text-[10px] font-bold tracking-wider">{selectionMode === 'west' ? 'SELECTING...' : 'MAIN'}</span>
                                </div>

                                {/* Character (No Hover Swap) */}
                                <img
                                    src={getCharBaseImage(currentWest) || stellaNormal}
                                    alt={currentWest.name}
                                    className="absolute inset-0 w-full h-full object-cover object-top transition-transform duration-700 group-hover:scale-110"
                                />

                                {/* Info Overlay */}
                                <div className="absolute inset-x-0 bottom-0 p-5 bg-gradient-to-t from-purple-950 via-black/80 to-transparent translate-y-2 group-hover:translate-y-0 transition-transform duration-300 font-['Hahmlet']">
                                    <h4 className="text-xl font-bold text-white leading-tight">{currentWest.name}</h4>
                                    <p className="text-xs text-purple-300 mt-1 font-medium tracking-wide flex items-center gap-1">
                                        {currentWest.role}
                                        <Sparkles size={10} />
                                    </p>
                                </div>
                            </div>
                            {selectionMode === 'west' && (
                                <motion.p
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="text-purple-300 text-sm mt-4 font-bold animate-pulse"
                                >
                                    아래 목록에서 변경할 캐릭터를 선택하세요
                                </motion.p>
                            )}
                        </div>

                        <div className="flex items-center justify-between mb-6 opacity-100 transition-opacity border-b border-white/10 pb-4">
                            <h2 className="text-2xl font-bold text-purple-100 font-['Hahmlet'] tracking-tighter">사파이어 왕국</h2>
                        </div>

                        <div className={`grid grid-cols-2 gap-4 transition-all duration-500 p-2 rounded-xl ${showTutorial && tutorialStep === 3 ? 'z-[61] relative ring-4 ring-orange-400/80 bg-black/20 shadow-[0_0_50px_rgba(251,146,60,0.3)]' : ''}`}>
                            {westernChars.map(char => <GameCard key={char.id} char={char} />)}
                        </div>
                    </div>

                    {/* RIGHT CONTENT */}
                    <div className="w-1/2 p-8 pt-32 pb-20">

                        {/* Equipped Slot Header - East */}
                        <div className={`mb-12 flex flex-col items-center transition-all duration-500 ${showTutorial && (tutorialStep === 1 || tutorialStep === 2) ? 'z-[60] relative scale-100' : ''}`}>
                            <div
                                onClick={() => !showTutorial && setSelectionMode(selectionMode === 'east' ? null : 'east')}
                                className={`relative w-48 aspect-[3/4] rounded-2xl border-2 border-amber-500/50 bg-gradient-to-b from-amber-900/40 to-black/80 backdrop-blur-md shadow-[0_0_30px_rgba(245,158,11,0.25)] overflow-hidden group cursor-pointer ring-4 ring-amber-500/20 group-hover:ring-amber-500/60 ring-offset-2 ring-offset-black transition-all duration-500
                                    ${selectionMode === 'east' ? 'ring-amber-500 scale-105 shadow-[0_0_60px_rgba(245,158,11,0.5)]' : ''}
                                    ${showTutorial && (tutorialStep === 1 || tutorialStep === 2) ? 'ring-orange-400 shadow-[0_0_50px_rgba(251,146,60,0.8)] scale-105' : ''}
                                `}
                            >
                                {/* Premium Glow Effect */}
                                <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-tr from-amber-500/20 via-transparent to-red-500/20 opacity-60 group-hover:opacity-100 transition-opacity" />
                                <div className="absolute -inset-1 bg-gradient-to-b from-white/20 to-transparent opacity-0 group-hover:opacity-50 blur-sm transition-opacity" />

                                {/* Badge */}
                                <div className={`absolute top-3 left-3 z-20 flex items-center gap-1.5 px-3 py-1 rounded-full shadow-lg border border-white/20 backdrop-blur-md transition-all duration-300 font-['GmarketSansMedium'] ${selectionMode === 'east' ? 'bg-amber-600 text-white' : 'bg-black/60 text-amber-200'}`}>
                                    <Crown size={12} className={selectionMode === 'east' ? "text-yellow-300 animate-bounce" : "text-amber-400"} />
                                    <span className="text-[10px] font-bold tracking-wider">{selectionMode === 'east' ? 'SELECTING...' : 'MAIN'}</span>
                                </div>

                                {/* Character (No Hover Swap) */}
                                <img
                                    src={getCharBaseImage(currentEast) || soiseolNormal}
                                    alt={currentEast.name}
                                    className="absolute inset-0 w-full h-full object-cover object-top transition-transform duration-700 group-hover:scale-110"
                                />

                                {/* Info Overlay */}
                                <div className="absolute inset-x-0 bottom-0 p-5 bg-gradient-to-t from-amber-950 via-black/80 to-transparent translate-y-2 group-hover:translate-y-0 transition-transform duration-300 font-['Hahmlet']">
                                    <h4 className="text-xl font-bold text-white leading-tight">{currentEast.name}</h4>
                                    <p className="text-xs text-amber-300 mt-1 font-medium tracking-wide flex items-center gap-1">
                                        {currentEast.role}
                                        <Sparkles size={10} />
                                    </p>
                                </div>
                            </div>
                            {selectionMode === 'east' && (
                                <motion.p
                                    initial={{ opacity: 0, y: 10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    className="text-amber-300 text-sm mt-4 font-bold animate-pulse"
                                >
                                    아래 목록에서 변경할 캐릭터를 선택하세요
                                </motion.p>
                            )}
                        </div>

                        <div className="flex items-center justify-between mb-6 opacity-100 transition-opacity border-b border-white/10 pb-4">
                            <h2 className="text-2xl font-bold text-amber-100 font-['Hahmlet'] tracking-tighter">동방 제국</h2>
                        </div>

                        <div className={`grid grid-cols-2 gap-4 transition-all duration-500 p-2 rounded-xl ${showTutorial && tutorialStep === 3 ? 'z-[60] relative ring-4 ring-orange-400/80 bg-black/20 shadow-[0_0_50px_rgba(251,146,60,0.3)]' : ''}`}>
                            {orientalChars.map(char => <GameCard key={char.id} char={char} />)}
                        </div>
                    </div>
                </div>
            </div>
            {/* Temporary Tutorial Replay Button */}
            <button
                onClick={() => {
                    setShowTutorial(true);
                    setTutorialStep(0);
                }}
                className="fixed bottom-6 right-6 z-40 bg-white/10 hover:bg-white/20 text-white/50 hover:text-white px-4 py-2 rounded-full backdrop-blur-md text-xs border border-white/10 transition-colors font-bold flex items-center gap-2"
            >
                <Sparkles size={12} />
                튜토리얼 다시보기
            </button>

            {/* Tutorial Overlay */}
            <AnimatePresence>
                {showTutorial && (
                    <>
                        {/* 1. Backdrop Layer (Behind highlighted elements) */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm pointer-events-none"
                        />

                        {/* 2. Dialogue Layer (Above highlighted elements) */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            className="fixed inset-0 z-[80] pointer-events-none flex items-center justify-center p-4"
                        >
                            <div className="relative w-full max-w-7xl mx-auto h-full flex items-center justify-center">

                                {/* Dialogue Box Container - Auto Position Logic */}
                                <div className="absolute w-full h-full flex flex-col justify-center items-end px-12">
                                    <motion.div
                                        key={tutorialStep}
                                        initial={{ scale: 0.9, opacity: 0, y: 20 }}
                                        animate={{ scale: 1, opacity: 1, y: 0 }}
                                        exit={{ scale: 0.9, opacity: 0, y: 10 }}
                                        transition={{ delay: 0.1 }}
                                        className={`pointer-events-auto w-[360px] bg-black/80 border border-purple-500/30 backdrop-blur-xl p-6 rounded-2xl shadow-[0_0_50px_rgba(168,85,247,0.2)] relative transition-all duration-500 
                                            ${(tutorialStep === 1 || tutorialStep === 2) ? 'mt-[300px]' : ''}
                                            ${tutorialStep === 3 ? 'mb-auto mt-[20vh]' : ''}
                                        `}
                                    >
                                        <div className="flex justify-between items-start mb-4">
                                            <h3 className="text-xl font-bold text-indigo-300 flex items-center gap-2">
                                                <Sparkles size={18} />
                                                <span>{tutorialMessages[tutorialStep].title}</span>
                                            </h3>
                                            <span className="text-xs font-mono text-white/50 bg-white/10 px-2 py-0.5 rounded-full">
                                                STEP {tutorialStep + 1}/{tutorialMessages.length}
                                            </span>
                                        </div>

                                        <p className="text-white/90 leading-relaxed mb-6 min-h-[60px] whitespace-pre-line text-sm">
                                            {tutorialMessages[tutorialStep].text}
                                        </p>

                                        <div className="flex gap-4">
                                            {tutorialStep > 0 && (
                                                <button
                                                    onClick={() => setTutorialStep(prev => prev - 1)}
                                                    className="flex-1 bg-white/5 hover:bg-white/10 text-white/70 font-bold py-2.5 rounded-xl transition-all text-sm"
                                                >
                                                    이전
                                                </button>
                                            )}
                                            <button
                                                onClick={handleNextStep}
                                                className="flex-[2] bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-400 hover:to-amber-400 text-black font-bold py-2.5 rounded-xl transition-all shadow-lg hover:shadow-orange-500/25 animate-pulse-soft text-sm"
                                            >
                                                {tutorialStep === tutorialMessages.length - 1 ? "시작하기" : "다음"}
                                            </button>
                                        </div>

                                        {/* Speech Bubble Tail */}
                                        <div className="absolute -bottom-3 left-10 w-6 h-6 bg-black/80 border-l border-b border-purple-500/30 transform rotate-45" />
                                    </motion.div>
                                </div>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>

            {/* SKIN CHANGE MODAL */}
            <AnimatePresence>
                {skinModalChar && (
                    <>
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            exit={{ opacity: 0 }}
                            onClick={() => setSkinModalChar(null)}
                            className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-md flex items-center justify-center p-4"
                        >
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0, y: 20 }}
                                animate={{ scale: 1, opacity: 1, y: 0 }}
                                exit={{ scale: 0.9, opacity: 0, y: 20 }}
                                onClick={(e) => e.stopPropagation()}
                                className={`w-full max-w-4xl bg-[#0b0d14] border border-white/10 rounded-3xl shadow-2xl overflow-hidden flex flex-col md:flex-row relative
                                ${skinModalChar.type === 'western' ? 'shadow-purple-500/20' : 'shadow-amber-500/20'}`}
                            >
                                {/* Close Button */}
                                <button
                                    onClick={() => setSkinModalChar(null)}
                                    className="absolute top-4 right-4 z-50 p-2 rounded-full bg-black/40 hover:bg-white/10 text-white/50 hover:text-white transition-colors"
                                >
                                    <X size={24} />
                                </button>

                                {/* LEFT: PREVIEW AREA */}
                                <div className="w-full md:w-1/2 h-[400px] md:h-[500px] relative bg-gradient-to-br from-gray-900 to-black overflow-hidden flex items-center justify-center group">
                                    {/* Background Effect */}
                                    <div className={`absolute inset-0 opacity-30 ${skinModalChar.type === 'western' ? 'bg-purple-900/30' : 'bg-amber-900/30'}`} />
                                    <div className="absolute inset-0 bg-[url('/textures/stardust.png')] opacity-10 mix-blend-overlay" />

                                    {/* Character Preview */}
                                    <motion.img
                                        key={equippedSkins[skinModalChar.id] || 'normal'}
                                        initial={{ opacity: 0, scale: 1.1 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        transition={{ duration: 0.4 }}
                                        src={getCharBaseImage(skinModalChar)}
                                        alt="Preview"
                                        className="h-full w-full object-cover object-top z-10"
                                    />

                                </div>

                                {/* RIGHT: CONTROLS AREA */}
                                <div className="flex-1 p-8 md:p-12 flex flex-col">
                                    <div className="mb-8">
                                        <div className="flex items-center gap-3 mb-2">
                                            <span className={`px-2 py-0.5 text-[10px] font-bold rounded border ${skinModalChar.type === 'western' ? 'border-purple-500/50 text-purple-300' : 'border-amber-500/50 text-amber-300'}`}>
                                                {skinModalChar.role}
                                            </span>

                                        </div>
                                        <h2 className="text-4xl font-bold text-white font-serif mb-2">{skinModalChar.name}</h2>
                                        <p className="text-white/60 text-sm leading-relaxed">{skinModalChar.desc}</p>
                                    </div>

                                    {/* Skin Selection Grid */}
                                    <div className="space-y-4 flex-1">
                                        <h3 className="text-sm font-bold text-white/80 flex items-center gap-2">
                                            <Shirt size={16} />
                                            보유 스킨
                                        </h3>

                                        <div className="grid grid-cols-1 gap-4">
                                            {/* Default Skin Only */}
                                            <button
                                                onClick={() => setEquippedSkins(prev => ({ ...prev, [skinModalChar.id]: 'normal' }))}
                                                className={`relative group p-3 rounded-xl border transition-all text-left flex items-center gap-4
                                                    ${(equippedSkins[skinModalChar.id] || 'normal') === 'normal'
                                                        ? `bg-white/10 ${skinModalChar.type === 'western' ? 'border-purple-500 ring-1 ring-purple-500/50' : 'border-amber-500 ring-1 ring-amber-500/50'}`
                                                        : 'bg-white/5 border-white/5 hover:bg-white/10'
                                                    }`}
                                            >
                                                <div className="w-12 h-12 rounded-lg overflow-hidden bg-black/20 shrink-0">
                                                    <img src={skinModalChar.image} className="w-full h-full object-cover object-top" alt="Normal" />
                                                </div>
                                                <div>
                                                    <div className="text-sm font-bold text-white mb-0.5">기본 스킨</div>
                                                    <div className="text-[10px] text-white/40">Default Skin</div>
                                                </div>
                                                {(equippedSkins[skinModalChar.id] || 'normal') === 'normal' && (
                                                    <div className="absolute top-3 right-3 text-green-400">
                                                        <Check size={16} />
                                                    </div>
                                                )}
                                            </button>
                                        </div>
                                    </div>

                                    {/* Footer / Confirm Done */}
                                    <div className="mt-8 pt-6 border-t border-white/10 flex justify-between items-center">
                                        <button
                                            onClick={() => {
                                                if (skinModalChar.type === 'western') {
                                                    setEquippedWestId(skinModalChar.id);
                                                    saveCharacterSettings({ west: skinModalChar.id, east: equippedEastId });
                                                } else {
                                                    setEquippedEastId(skinModalChar.id);
                                                    saveCharacterSettings({ west: equippedWestId, east: skinModalChar.id });
                                                }
                                                setSkinModalChar(null);
                                            }}
                                            disabled={(skinModalChar.type === 'western' && equippedWestId === skinModalChar.id) || (skinModalChar.type === 'oriental' && equippedEastId === skinModalChar.id)}
                                            className={`px-6 py-3 rounded-xl font-bold transition-all flex items-center gap-2
                                                ${((skinModalChar.type === 'western' && equippedWestId === skinModalChar.id) || (skinModalChar.type === 'oriental' && equippedEastId === skinModalChar.id))
                                                    ? 'bg-white/5 text-white/30 cursor-not-allowed'
                                                    : 'bg-white/10 hover:bg-white/20 text-white border border-white/10'}`}
                                        >
                                            <Crown size={16} />
                                            {((skinModalChar.type === 'western' && equippedWestId === skinModalChar.id) || (skinModalChar.type === 'oriental' && equippedEastId === skinModalChar.id))
                                                ? "현재 메인 캐릭터"
                                                : "메인 캐릭터로 설정"}
                                        </button>

                                    </div>
                                </div>
                            </motion.div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

export default CollectionPage;
