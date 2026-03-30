import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import CardSelectionStageNew from './CardSelectionStage';
import ElementalParticles from './ElementalParticles';
import { useSound } from '../../hooks/useSound';
import { motion, AnimatePresence } from 'framer-motion';
import { X, ChevronRight, Flame, Droplet, Mountain, TreeDeciduous, Swords, Download } from 'lucide-react';
import { toPng } from 'html-to-image';
import westStar from '../../assets/character/west/stella/stella_smile.png';
import eastSaju from '../../assets/character/east/soiseol/soiseol_smile.png';
import stellaSmile from '../../assets/character/west/stella/stella_smile.png';
import soiseolSmile from '../../assets/character/east/soiseol/soiseol_smile.png';
import soiseolAnnoying from '../../assets/character/east/soiseol/soiseol_annoying.png';
import obangBackground from '../../assets/obang_card/obang_background.png';
import obangBack from '../../assets/obang_card/obang_back.jpg';
import introBackground from '../../assets/login_page/back1.jpg';
import introBackground2 from '../../assets/login_page/back2.png';
import back6 from '../../assets/login_page/back6.jpg';
import tarotCardBack from '../../assets/타로카드/tarot_back2.png';
import tarotBg from '../../assets/타로카드/tarot_background.jpg';
const sinImage = '/assets/obang_card/sin2.png';
import { tarotDeck, type TarotCard } from '../../data/tarotData';

const EastName = "소이설";
const WestName = "스텔라";

interface FortuneTeaserModalProps {
    isOpen: boolean;
    onClose: () => void;
}

// Fortune stages
type FortuneStage = 'selection' | 'intro' | 'obangGuide' | 'obangExplain' | 'tarotGuide' | 'tarotExplain' | 'cardSelection' | 'breaking' | 'card' | 'level' | 'radar' | 'oracle' | 'destiny';
type GameType = 'tarot' | 'obang' | null;

interface FortuneCard {
    id: string;
    name: string;
    title: string;
    element: string;
    elementIcon: any;
    color: string;
    bgGradient: string;
    description: string;
    reading: string; // Detailed reading for So Yi-seol
    blessing: string;
    warning: string;
    imageUrl: string;
}

interface FortuneResult {
    card: FortuneCard;
    level: string;
    levelName: string;
    levelColor: string;
    message: string;
    advice: string;
    categories: {
        wood: number;
        fire: number;
        earth: number;
        metal: number;
        water: number;
    };
    lucky: {
        color: string;
        colorHex: string;
        number: number;
        direction: string;
        item: string;
        time: string;
        guardian: string;
        action: string;
    };
}




// Fortune Cards-오방신 카드 (5장)
const fortuneCards: FortuneCard[] = [{
    id: 'wood',
    name: '청룡 (靑龍)',
    title: '동방 목신',
    element: '나무 (木)',
    elementIcon: TreeDeciduous,
    color: 'green',
    bgGradient: 'from-green-900 to-emerald-900',
    description: '새로운 시작과 성장의 기운이 강해요.',
    reading: '푸른 용이 승천하는 생동감이 느껴지네요.\n오랫동안 마음속에 품어왔던 씨앗이 드디어 싹을 틔울 시기가 찾아왔어요.\n망설이지 말고 한번 시작해보세요. 거친 바람도 결국 당신의 편이 되어줄 거랍니다.',
    blessing: '창의적인 아이디어가 샘솟고 귀인의 도움을 받습니다.',
    warning: '너무 서두르면 뿌리가 약해질 수 있습니다. 차근차근 나아가세요.',
    imageUrl: '/assets/obang_card/obang_tree2.png',
},
{
    id: 'fire',
    name: '주작 (朱雀)',
    title: '남방 화신',
    element: '불 (火)',
    elementIcon: Flame,
    color: 'red',
    bgGradient: 'from-red-900 to-orange-900',
    description: '열정과 활력이 넘치는 시기예요.',
    reading: '붉은 봉황의 날갯짓처럼 그 어느 때보다 화려한 순간이군요.\n당신의 뜨거운 열정이 주변을 환하게 비추고 있어요.\n숨기지 말고 당신의 재능을 마음껏 뽐내보세요. 모두가 당신을 주목할 거예요.',
    blessing: '명예와 인기가 높아집니다. 표현하는 만큼 얻습니다.',
    warning: '불길이 너무 거세면 자신을 태울 수 있습니다. 감정 조절이 필요합니다.',
    imageUrl: '/assets/obang_card/obang_fire2.png',
},
{
    id: 'earth',
    name: '황룡 (黃龍)',
    title: '중앙 토신',
    element: '흙 (土)',
    elementIcon: Mountain,
    color: 'yellow',
    bgGradient: 'from-amber-900 to-yellow-900',
    description: '흔들리지 않는 평안함과 안정이 찾아올 거예요.',
    reading: '넓은 대지처럼 굳건하고 포근한 기운이 당신을 감싸고 있네요.\n지금은 무리해서 높이 오르기보다 깊이 뿌리내릴 때예요.\n지금 차곡차곡 쌓아둔 신뢰와 안정은 훗날 당신의 가장 큰 자산이 될 거랍니다.',
    blessing: '재물운이 안정되고 가정에 평화가 깃듭니다.',
    warning: '변화를 두려워하면 고인 물이 될 수 있습니다. 유연함을 가지세요.',
    imageUrl: '/assets/obang_card/obang_soil2.png',
},
{
    id: 'metal',
    name: '백호 (白虎)',
    title: '서방 금신',
    element: '쇠 (金)',
    elementIcon: Swords,
    color: 'gray',
    bgGradient: 'from-slate-800 to-gray-900',
    description: '냉철한 판단과 강한 의지가 필요한 때예요.',
    reading: '흰 호랑이의 서릿발 같은 기세가 느껴져요.\n지금은 옳고 그름을 가르는 명확한 결단이 필요한 순간이에요.\n두려움 없이 끊어낼 것을 끊어낸다면, 분명 더 크고 단단한 길을 얻게 될 거예요.',
    blessing: '권위가 생기고 장애물을 돌파하는 힘을 얻습니다.',
    warning: '너무 날카로우면 주변에 상처를 줄 수 있습니다. 부드러움을 겸비하세요.',
    imageUrl: '/assets/obang_card/obang_gold2.png',
},
{
    id: 'water',
    name: '현무 (玄武)',
    title: '북방 수신',
    element: '물 (水)',
    elementIcon: Droplet,
    color: 'blue',
    bgGradient: 'from-blue-950 to-indigo-950',
    description: '흐르는 물처럼 유연하게 모든 것을 넘어설 거예요.',
    reading: '깊고 검은 물의 지혜가 조용히 흐르고 있네요.\n겉으로 드러나지 않아도, 당신의 내면은 누구보다 깊어져 있어요.\n흐름에 몸을 맡겨보세요. 결국 가장 낮은 곳에서 모든 것을 품게 될 테니까요.',
    blessing: '지혜와 통찰력이 깊어집니다. 학문과 예술에서 성공할 것입니다.',
    warning: '너무 깊이 생각하지 마세요. 때로는 직관을 믿는 것도 중요합니다.',
    imageUrl: '/assets/obang_card/obang_water2.png',
},];


// Tarot Types


interface TarotResult {
    card: TarotCard;
    advice: string;
    story: string;
    subAdvice: {
        love: string;
        work: string;
        money: string;
    }
}

// Tarot Cards Data (Major Arcana Subset)


const generateTarotFortune = (): TarotResult => {
    // Filter for Major Arcana only (Suit 'major')
    const majorArcana = tarotDeck.filter(card => card.suit === 'major');
    const shuffled = [...majorArcana].sort(() => 0.5 - Math.random());
    const selected = shuffled[0];

    // Contextual sentences based on suit
    let context = "";
    if (selected.suit === 'cups') context = "감정의 강물이 당신의 마음속으로 흘러들어오고 있어요.";
    else if (selected.suit === 'wands') context = "타오르는 불꽃처럼 당신의 의지가 시험받는 순간이네요.";
    else if (selected.suit === 'swords') context = "차가운 바람이 안개를 걷어내고 진실을 보여줄 거예요.";
    else if (selected.suit === 'pentacles') context = "단단한 대지 위에서 결실을 맺을 준비가 되었나요?";
    else context = "거대한 운명의 수레바퀴가 다시 돌아가기 시작했어요.";

    // Generate specific advice
    const loveAdvice = selected.suit === 'cups' ? "진심을 전하기에 더없이 좋은 시기예요. 마음 가는 대로 움직이세요." :
        selected.suit === 'swords' ? "상처받는 것을 두려워하지 마세요. 대화가 필요합니다." :
            "서로를 배려하는 작은 마음이 큰 변화를 만듭니다.";

    // Generate detailed reading
    const story = `
        ${context}
        ${selected.meaning}
        지금 당신에게 필요한 것은 '${selected.keyword}'의 에너지입니다.
        눈앞의 상황에 일희일비하기보다, 더 멀리 바라보는 지혜를 가져보세요.
        별들은 이미 당신이 나아갈 길을 알고 있답니다.
    `;

    return {
        card: selected,
        advice: `"${selected.keyword}"의 별빛이 당신을 비추고 있습니다.`,
        story: story.trim(),
        subAdvice: {
            love: loveAdvice,
            work: selected.suit === 'wands' || selected.suit === 'pentacles' ? "당신의 능력을 인정받을 기회가 옵니다. 적극적으로 나서세요." : "지금은 잠시 숨을 고르고 다음 기회를 준비할 때예요.",
            money: selected.suit === 'pentacles' ? "예상치 못한 행운이 따를 수 있어요. 하지만 신중함은 잃지 마세요." : "불필요한 지출을 줄이고 내실을 다지는 것이 좋습니다."
        }
    };
};

// Tone update helper-converting to polite/soft tone
const formatDialogue = (text: string) => {
    return text.replace(/합니다\./g, '해요.')
        .replace(/입니다\./g, '이에요.')
        .replace(/하옵니다\./g, '해요.')
        .replace(/이옵니다\./g, '이에요.')
        .replace(/이라네\./g, '이에요.');
};


// Generate random fortune linked to selected card
const generateFortune = (): FortuneResult => {
    const selectedCard = fortuneCards[Math.floor(Math.random() * fortuneCards.length)];

    const levels = [{ level: '대길', levelName: '大吉', color: 'from-yellow-400 via-orange-400 to-red-500' },
    { level: '중길', levelName: '中吉', color: 'from-green-400 via-emerald-400 to-teal-500' },
    { level: '소길', levelName: '小吉', color: 'from-blue-400 via-cyan-400 to-sky-500' },
    { level: '길', levelName: '吉', color: 'from-purple-400 via-pink-400 to-rose-500' },];

    const messages = [{
        text: '오늘은 당신에게 특별한 기회가 찾아옵니다.',
        detail: '특히 오후 시간대에 중요한 인연을 만날 수 있습니다. 첫인상을 소중히 여기고, 진심을 담아 대화하세요.'
    },
    {
        text: '새로운 시작을 위한 완벽한 날입니다.',
        detail: '오래 미뤄왔던 일이 있다면 지금이 바로 시작할 때입니다. 작은 것부터 하나씩 실천해보세요.'
    },
    {
        text: '주변 사람들과의 조화가 행운을 가져옵니다.',
        detail: '가족, 친구, 동료들에게 고마움을 전하세요. 당신의 진심이 더 큰 행복으로 돌아올 것입니다.'
    },
    {
        text: '인내심을 가지면 좋은 결과가 있을 것입니다.',
        detail: '지금은 준비하고 기다리는 시기입니다. 때가 되면 자연스럽게 좋은 결과가 찾아올 것입니다.'
    },];

    const advices = ['아침 일찍 일어나 명상이나 가벼운 산책을 해보세요. 맑은 공기와 함께 마음의 평화를 찾을 수 있습니다.',
        '오늘 만나는 사람들에게 진심 어린 미소를 지어보세요. 긍정적인 에너지는 전염됩니다.',
        '중요한 결정은 오후 2시에서 5시 사이에 내리는 것이 좋습니다. 이 시간대에는 직관이 가장 예리해집니다.',
        '가족이나 오랜 친구에게 연락해보세요. 소중한 인연이 행운의 열쇠가 됩니다.',
        '오늘 하루는 감사 일기를 써보세요. 작은 것에도 감사하는 마음이 더 큰 행운을 불러옵니다.',];

    // Element Mapping for consistency
    const elementMap: Record<string, { color: string; colorHex: string; direction: string; guardian: string }> = {
        wood: { color: '초록색', colorHex: '#10B981', direction: '동쪽', guardian: '청룡 (Blue Dragon)' },
        fire: { color: '붉은색', colorHex: '#EF4444', direction: '남쪽', guardian: '주작 (Vermilion Bird)' },
        earth: { color: '황금색', colorHex: '#F59E0B', direction: '중앙', guardian: '황룡 (Yellow Dragon)' },
        metal: { color: '백색', colorHex: '#E2E8F0', direction: '서쪽', guardian: '백호 (White Tiger)' },
        water: { color: '남색', colorHex: '#3B82F6', direction: '북쪽', guardian: '현무 (Black Tortoise)' },
    };

    const mapping = elementMap[selectedCard.id] || elementMap.earth;

    const selectedLevel = levels[Math.floor(Math.random() * levels.length)];
    const selectedMessage = messages[Math.floor(Math.random() * messages.length)];

    // Items that might fit any element but we can randomize them
    const items = ['붉은 실', '은빛 열쇠', '작은 거울', '백옥 구슬', '금색 동전', '나침반'];
    const actions = ['따뜻한 차 한 잔 마시기', '동쪽 하늘 바라보기', '오전 산책하기', '옛 친구에게 연락하기', '방 정리하기'];

    // Generate stats where the card's element is dominant
    const categories = {
        wood: 30 + Math.floor(Math.random() * 30),
        fire: 30 + Math.floor(Math.random() * 30),
        earth: 30 + Math.floor(Math.random() * 30),
        metal: 30 + Math.floor(Math.random() * 30),
        water: 30 + Math.floor(Math.random() * 30),
    };
    // Boost the selected element's stat
    (categories as any)[selectedCard.id] = 85 + Math.floor(Math.random() * 15);

    return {
        card: selectedCard,
        level: selectedLevel.level,
        levelName: selectedLevel.levelName,
        levelColor: selectedLevel.color,
        message: selectedMessage.text,
        advice: formatDialogue(advices[Math.floor(Math.random() * advices.length)]),
        categories,
        lucky: {
            color: mapping.color,
            colorHex: mapping.colorHex,
            number: Math.floor(Math.random() * 9) + 1,
            direction: mapping.direction,
            item: items[Math.floor(Math.random() * items.length)],
            time: ['새벽 (5-7시)', '아침 (7-9시)', '오후 (12-15시)', '저녁 (18-21시)'][Math.floor(Math.random() * 4)],
            guardian: mapping.guardian,
            action: actions[Math.floor(Math.random() * actions.length)],
        },
    };
};


// Character Intro Stage Component
const CharacterIntroStage = ({ onComplete, selectedGame }: { onComplete: () => void; selectedGame: GameType }) => {
    const [currentLineIndex, setCurrentLineIndex] = useState(0);
    const [typedText, setTypedText] = useState('');
    const [isTyping, setIsTyping] = useState(true);
    const typingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const { play } = useSound();

    const isObang = selectedGame === 'obang';

    const dialogueLines = useMemo(() => isObang ? [{ text: `반가워요... 저는 오방신의 무녀, ${EastName}이라고 해요.`, expression: 'normal' },
    { text: "당신이 이곳에 이끌린 건 단순한 우연이 아니랍니다.", expression: 'smile' },
    { text: "오방의 신비로운 기운이 당신을 감싸고 있군요...", expression: 'normal' },
    { text: "자, 이제 당신의 운명을 점쳐보도록 할까요?", expression: 'smile' }] : [{ text: `어서오세요, 별을 읽는 점성술사 ${WestName} 입니다.`, expression: 'normal' },
    { text: "카드는 당신의 과거와 현재, 그리고 미래를 비추는 거울이죠.", expression: 'smile' },
    { text: "당신의 직감을 믿고 마음을 열어보세요.", expression: 'normal' },
    { text: "별들이 속삭이는 당신의 운명을 들어볼까요?", expression: 'smile' }], [isObang]);

    // useEffect(() => {
    //     if (!isObang) {
    //         play('VOICE', 'STELLA', { subKey: 'INTRO' });
    //     }
    // }, [isObang, play]);

    useEffect(() => {
        setTypedText('');
        setIsTyping(true);
        let i = 0;
        const currentText = dialogueLines[currentLineIndex].text;

        // Clear any existing interval
        if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);

        typingIntervalRef.current = setInterval(() => {
            if (i < currentText.length) {
                setTypedText(currentText.substring(0, i + 1));
                i++;
            } else {
                if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
                setIsTyping(false);
            }
        }, 50);

        return () => {
            if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
        };
    }, [currentLineIndex, dialogueLines]);

    const handleNext = useCallback(() => {
        if (isTyping) {
            if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
            setTypedText(dialogueLines[currentLineIndex]?.text || '');
            setIsTyping(false);
        } else {
            if (currentLineIndex < dialogueLines.length - 1) {
                setCurrentLineIndex(prev => prev + 1);
            } else {
                onComplete();
            }
        }
    }, [isTyping, currentLineIndex, dialogueLines, onComplete]);

    // Keyboard Navigation Support
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.code === 'Space' || e.code === 'Enter') {
                e.preventDefault();
                handleNext();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleNext]);

    // Helper to get current character image
    const getCharacterImage = () => {
        const line = dialogueLines[currentLineIndex];
        if (!line) return isObang ? eastSaju : westStar;

        const expression = line.expression;
        if (isObang) {
            return expression === 'smile' && soiseolSmile ? soiseolSmile : eastSaju;
        } else {
            return expression === 'smile' && stellaSmile ? stellaSmile : westStar;
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-transparent cursor-pointer pointer-events-auto w-full h-full rounded-3xl overflow-hidden"
            onClick={handleNext}
        >
            {/* Background Image with Overlay */}
            <div className={`absolute inset-0 z-0 ${isObang ? 'bg-[#1a1510]' : 'bg-black'} `}>
                <img
                    src={isObang ? obangBackground : back6} // Unified Obang Background
                    alt="Intro Background"
                    className={`w-full h-full object-cover ${isObang ? 'opacity-100' : 'opacity-50'} `}
                />
                <div className={`absolute inset-0 ${isObang ? 'bg-black/70' : 'bg-purple-900/20 mix-blend-overlay'} `} />
            </div>

            <div className="relative w-full max-w-4xl h-full max-h-[90vh] flex items-end justify-center pb-10 z-10">
                {/* Character Image-Added Idle Animation */}
                <motion.div
                    key={getCharacterImage()} // Re-animate opacity on image change
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: [0, -8, 0] }}
                    exit={{ opacity: 0 }}
                    transition={{
                        opacity: { duration: 0.5 },
                        y: { duration: 4, repeat: Infinity, ease: "easeInOut" }
                    }}
                    className={`absolute bottom-0 h-[80vh] w-[80vh] z-10 pointer-events-none ${isObang ? 'right-[-25%] md:right-[-20%]' : 'left-[-15%] md:left-[-25%]'} `}
                >
                    <img
                        src={getCharacterImage()}
                        alt={isObang ? "East Saju" : "West Star"}
                        className={`w-full h-full object-contain object-bottom drop-shadow-[0_0_50px_rgba(255, 255, 255, 0.1)] ${isObang ? 'translate-x-10 md:translate-x-20' : ''} ${!isObang && 'scale-110 origin-bottom'} `}
                    />
                </motion.div>

                {/* Dialogue Box-Fixed Game Style */}
                <motion.div
                    key={currentLineIndex}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className={`absolute bottom-8 md:bottom-12 left-4 right-4 md:left-20 md:right-20 z-20 flex flex-col items-start 
                        ${isObang ? '' : 'p-6 md:p-8 rounded-xl border-2 backdrop-blur-xl shadow-2xl bg-slate-900/90 border-purple-500/50 text-white shadow-purple-900/50 gap-4'}`}
                >
                    {isObang ? (
                        // Obang Style (Hanji Texture + Double Border)
                        <div className="w-full relative bg-[#f5f0e1]/95 border-2 border-amber-900/20 p-2 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.2)] backdrop-blur-md">
                            <div className="border border-double border-amber-800/30 rounded-xl px-6 py-6 md:px-8 md:py-8 bg-[url('https://www.transparenttextures.com/patterns/natural-paper.png')] bg-blend-multiply flex flex-col items-start gap-4 relative">

                                {/* Decorative Corner (Top Right) */}
                                <div className="absolute top-4 right-4 w-10 h-10 opacity-20 bg-[url('https://www.transparenttextures.com/patterns/flower-pattern.png')] bg-contain bg-no-repeat" />

                                {/* Name Tag */}
                                <div className="inline-block px-4 py-1.5 rounded-lg border shadow-md bg-amber-800 border-amber-900 text-amber-50 mb-1 z-10">
                                    <span className="text-sm font-bold tracking-widest uppercase font-['JoseonPalace']">
                                        소이설
                                    </span>
                                </div>

                                <div className="w-full z-10">
                                    <p className="text-lg md:text-2xl leading-relaxed whitespace-pre-wrap break-keep font-['JoseonPalace'] font-medium text-stone-900">
                                        {typedText}
                                        {isTyping && <span className="animate-pulse inline-block ml-1">_</span>}
                                    </p>
                                </div>
                            </div>
                        </div>
                    ) : (
                        // Stella Style (Cosmic)
                        <>
                            {/* Character Name Tag */}
                            <div className="absolute -top-5 left-8 px-6 py-2 rounded-lg border-2 shadow-lg transform -skew-x-12 bg-indigo-600 border-purple-400 text-purple-50">
                                <span className="block transform skew-x-12 text-sm md:text-base font-bold tracking-widest uppercase font-gmarket">
                                    스텔라
                                </span>
                            </div>

                            <div className="w-full pl-2">
                                <p className="text-lg md:text-2xl leading-relaxed whitespace-pre-wrap break-keep font-gmarket font-light">
                                    {typedText}
                                    {isTyping && <span className="animate-pulse inline-block ml-1">_</span>}
                                </p>
                            </div>
                        </>
                    )}
                </motion.div>
            </div>

            {/* Skip Button-Minimalist & Sophisticated */}
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    play('SFX', 'CLICK1');
                    onComplete();
                }}
                className={`absolute bottom-12 z-50 text-white hover: text-white/80 text-sm tracking-[0.3em] font-bold uppercase transition-all duration-300 flex items-center gap-2 group hover: scale-105 ${isObang ? 'left-8 flex-row-reverse' : 'right-8'} `}
            >
                {isObang ? '건너뛰기' : 'SKIP'}
            </button>
        </motion.div>
    );
};


// Obang Guide Stage Component (Phase 1 + Stella Intrusion)
const ObangGuideStage = ({ onNext, onSwitchToTarot }: { onNext: (skip: boolean) => void; onSwitchToTarot: () => void }) => {
    const [showStella, setShowStella] = useState(false);
    const { play } = useSound();

    // Trigger Stella's appearance after 1.5 seconds
    useEffect(() => {
        const timer = setTimeout(() => {
            setShowStella(true);
            // Play Soiseol voice (soiseol_7.wav) shortly after Stella appears
            setTimeout(() => {
                play('VOICE', 'SOISEOL', { subKey: 'CROSS_PROMO' });
            }, 500);
        }, 1500);
        return () => clearTimeout(timer);
    }, []);

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-transparent pointer-events-auto"
        >
            <div className="relative w-full max-w-4xl h-full max-h-[90vh] flex items-end justify-center pb-10 z-10">
                {/* Character Image (Soiseol) */}
                <motion.div
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0, y: [0, -5, 0] }}
                    transition={{
                        opacity: { duration: 0.5 },
                        y: { duration: 4, repeat: Infinity, ease: "easeInOut" }
                    }}
                    className="absolute bottom-0 right-[-25%] md:right-[-20%] h-[80vh] w-[80vh] z-10 pointer-events-none"
                >
                    <img
                        src={showStella ? soiseolAnnoying : soiseolSmile} // Use annoying expression when Stella interrupts
                        alt="Soiseol"
                        className="w-full h-full object-contain object-bottom drop-shadow-[0_0_50px_rgba(255,255,255,0.1)] translate-x-10 md:translate-x-20"
                    />
                </motion.div>

                {/* Stella Intrusion (Left Side) */}
                <AnimatePresence>
                    {showStella && (
                        <motion.div
                            initial={{ x: '-100%', y: '15%', rotate: -45, opacity: 0 }}
                            animate={{ x: '-25%', y: '15%', rotate: 10, opacity: 1 }}
                            exit={{ x: '-100%', y: '15%', rotate: -45, opacity: 0 }}
                            transition={{ type: "spring", stiffness: 120, damping: 12, mass: 0.8 }}
                            className="absolute bottom-[-10%] left-[-35%] md:left-[-30%] h-[75vh] w-[75vh] z-30 pointer-events-none origin-bottom-left"
                        >
                            <img
                                src={stellaSmile}
                                alt="Stella"
                                className="w-full h-full object-contain object-bottom drop-shadow-[0_0_50px_rgba(79,70,229,0.3)]"
                            />

                            {/* Stella's Dialogue Bubble */}
                            <motion.div
                                initial={{ opacity: 0, scale: 0.8, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                transition={{ delay: 0.5 }}
                                className="absolute top-[15%] right-[5%] bg-indigo-950/90 border border-indigo-400/50 text-indigo-100 p-6 rounded-xl rounded-bl-none shadow-xl max-w-xs pointer-events-auto"
                            >
                                <div className="flex flex-col gap-3">
                                    <p className="text-lg font-['GmarketSansMedium'] leading-relaxed">
                                        이런 거 듣지 말고, <br />
                                        <span className="text-indigo-300 font-bold">타로</span>를 보는 게 어때요?
                                    </p>
                                    {/* Stella's Tarot Option Button-Moved inside bubble */}
                                    <motion.button
                                        initial={{ opacity: 0, y: 5 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        onClick={onSwitchToTarot}
                                        className="w-full py-2 px-3 bg-gradient-to-r from-indigo-800 to-indigo-900 border border-indigo-400/30 text-indigo-100 font-['GmarketSansMedium'] text-sm rounded-lg hover:shadow-[0_0_15px_rgba(79,70,229,0.5)] hover:scale-[1.02] hover:border-indigo-400/60 transition-all flex items-center justify-center gap-2 group/tarot mt-1"
                                    >
                                        <span>솔깃한데? 타로 볼래요</span>
                                    </motion.button>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Dialogue Box (Soiseol)-Redesigned Hanji Style */}
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className={`relative z-20 mb-20 mx-auto max-w-xl min-w-[360px] ${showStella ? 'translate-x-[10%]' : ''} transition-transform duration-500`}
                >
                    <div className="relative bg-[#f5f0e1] border-2 border-amber-900/20 p-2 rounded-2xl shadow-[0_0_50px_rgba(0,0,0,0.2)] backdrop-blur-md">
                        {/* Inner Border & Texture */}
                        <div className="border border-double border-amber-800/30 rounded-xl px-8 py-8 bg-[url('https://www.transparenttextures.com/patterns/natural-paper.png')] bg-blend-multiply flex flex-col items-center gap-6">

                            {/* Decorative Corner (Top Right) */}
                            <div className="absolute top-4 right-4 w-12 h-12 opacity-20 bg-[url('https://www.transparenttextures.com/patterns/flower-pattern.png')] bg-contain bg-no-repeat" />

                            <div className="text-center">
                                <h3 className="font-['Hahmlet'] text-4xl font-black text-amber-900 mb-3 drop-shadow-sm">
                                    잠깐!
                                </h3>
                                <p className="text-xl text-stone-800 font-['Hahmlet'] leading-relaxed word-keep">
                                    <span className="text-amber-700 font-bold border-b-2 border-amber-700/20 pb-0.5">오방신점</span>이 뭔지 궁금하신가요?
                                </p>
                            </div>

                            <div className="flex flex-col gap-3 w-full">
                                <button
                                    onClick={() => onNext(false)}
                                    disabled={!showStella}
                                    className={`w-full py-3.5 px-6 bg-gradient-to-r from-amber-800 to-amber-900 text-[#f5f0e1] font-['Hahmlet'] text-xl rounded-lg shadow-lg hover: shadow-xl hover: scale-[1.02] transition-all flex items-center justify-center gap-3 group relative overflow-hidden ${!showStella ? 'opacity-50 pointer-events-none' : ''} `}
                                >
                                    <div className="absolute inset-0 bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    <span className="tracking-wide">네, 듣고 싶어요!</span>
                                </button>

                                <button
                                    onClick={() => onNext(true)}
                                    disabled={!showStella}
                                    className={`w-full py-3.5 px-6 bg-[#f5f0e1] border border-amber-900/20 text-stone-600 font-['Hahmlet'] text-xl font-bold rounded-lg hover: bg-white transition-all flex items-center justify-center gap-2 ${!showStella ? 'opacity-50 pointer-events-none' : ''} `}
                                >
                                    <span>건너뛰기! 바로 카드뽑기</span>
                                </button>


                            </div>
                        </div>
                    </div>
                </motion.div>
            </div>
        </motion.div>
    );
};


// Obang Explain Stage-Conversational
const ObangExplainStage = ({ onComplete, onLineChange }: { onComplete: () => void; onLineChange: (index: number) => void }) => {
    // Explanation lines
    const explainLines = ["오방신점은 다섯 방위의 신들에게\n당신의 운명을 묻는 전통적인 점술이에요.",
        "청룡(靑龍), 주작(朱雀), 황룡(黃龍), 백호(白虎), 현무(玄武)...",
        "이 다섯 신수가 각자의 방위에서\n당신의 기운을 수호하고 있답니다.",
        "당신은 어떤 기운을 타고났을지, 제가 확인해드릴게요."];

    const [currentLineIndex, setCurrentLineIndex] = useState(0);
    const [typedText, setTypedText] = useState('');
    const [isTyping, setIsTyping] = useState(true);
    const typingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const { play } = useSound();

    useEffect(() => {
        setTypedText('');
        setIsTyping(true);
        let i = 0;
        const currentText = explainLines[currentLineIndex];

        // Notify parent of line change
        onLineChange(currentLineIndex);

        if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);

        typingIntervalRef.current = setInterval(() => {
            if (i < currentText.length) {
                setTypedText(currentText.substring(0, i + 1));
                i++;
            } else {
                if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
                setIsTyping(false);
            }
        }, 50);

        return () => {
            if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
        };
    }, [currentLineIndex]);

    const handleNext = useCallback(() => {
        if (isTyping) {
            if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
            setTypedText(explainLines[currentLineIndex]);
            setIsTyping(false);
        } else {
            if (currentLineIndex < explainLines.length - 1) {
                setCurrentLineIndex(prev => prev + 1);
            } else {
                onComplete();
            }
        }
    }, [isTyping, currentLineIndex, onComplete]);

    // Keyboard support
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.code === 'Space' || e.code === 'Enter') {
                e.preventDefault();
                handleNext();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleNext]);

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-transparent cursor-pointer pointer-events-auto"
            onClick={handleNext}
        >
            <div className="relative w-full max-w-4xl h-full max-h-[90vh] flex items-end justify-center pb-10 z-10">
                {/* Character Image (Soiseol) */}
                <motion.div

                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0, y: [0, -5, 0] }}
                    transition={{
                        opacity: { duration: 0.5 },
                        y: { duration: 4, repeat: Infinity, ease: "easeInOut" }
                    }}
                    className="absolute bottom-0 right-[-25%] md:right-[-20%] h-[80vh] w-[80vh] z-10 pointer-events-none"
                >
                    <img
                        src={soiseolSmile}
                        alt="Soiseol"
                        className="w-full h-full object-contain object-bottom drop-shadow-[0_0_50px_rgba(251,191,36,0.2)] translate-x-10 md:translate-x-20"
                    />
                </motion.div>

                {/* Dialogue Box (Hanji Style) */}
                <motion.div
                    key={currentLineIndex}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className="absolute bottom-12 left-4 right-4 md:left-20 md:right-20 z-20 p-6 md:p-8 rounded-xl border-2 border-amber-900/40 backdrop-blur-xl shadow-2xl flex flex-col items-start gap-4 bg-[#f8f4ed]/95 text-stone-900 shadow-[0_0_40px_rgba(0,0,0,0.3)]"
                >
                    {/* Name Tag */}
                    <div className="absolute -top-5 left-8 px-6 py-2 rounded-lg border-2 shadow-lg transform -skew-x-12 bg-amber-800 border-amber-900 text-amber-50">
                        <span className="block transform skew-x-12 text-sm md:text-base font-bold tracking-widest uppercase font-['JoseonPalace']">
                            소이설
                        </span>
                    </div>

                    <div className="w-full pl-2">
                        <p className="text-lg md:text-2xl leading-relaxed whitespace-pre-wrap break-keep font-['JoseonPalace'] font-medium">
                            {typedText}
                            {isTyping && <span className="animate-pulse inline-block ml-1">_</span>}
                        </p>
                    </div>
                </motion.div>
            </div>

            {/* Skip Button (Left Side for Obang) */}
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    play('SFX', 'CLICK1');
                    onComplete();
                }}
                className="absolute bottom-12 left-8 z-50 text-white hover:text-white/80 text-sm tracking-[0.3em] font-bold uppercase transition-all duration-300 flex items-center gap-2 group hover:scale-105 flex-row-reverse"
            >
                건너뛰기
            </button>
        </motion.div>
    );
};

// Tarot Guide Stage Component (Stella + Soiseol Intrusion)
const TarotGuideStage = ({ onNext, onSwitchToObang }: { onNext: (skip: boolean) => void; onSwitchToObang: () => void }) => {
    const [showSoiseol, setShowSoiseol] = useState(false);

    // Trigger Soiseol's appearance after 1.5 seconds
    useEffect(() => {
        const timer = setTimeout(() => {
            setShowSoiseol(true);
        }, 1500);
        return () => clearTimeout(timer);
    }, []);

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-transparent pointer-events-auto"
        >
            <div className="relative w-full max-w-4xl h-full max-h-[90vh] flex items-end justify-center pb-10 z-10">
                {/* Character Image (Stella) */}
                <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0, y: [0, -5, 0] }}
                    transition={{
                        opacity: { duration: 0.5 },
                        y: { duration: 4, repeat: Infinity, ease: "easeInOut" }
                    }}
                    className="absolute bottom-0 left-[-15%] md:left-[-25%] h-[80vh] w-[80vh] z-10 pointer-events-none"
                >
                    <img
                        src={stellaSmile}
                        alt="Stella"
                        className="w-full h-full object-contain object-bottom drop-shadow-[0_0_50px_rgba(168,85,247,0.2)] scale-110 origin-bottom"
                    />
                </motion.div>

                {/* Soiseol Intrusion (Right Side) */}
                <AnimatePresence>
                    {showSoiseol && (
                        <motion.div
                            initial={{ x: '100%', y: '15%', rotate: 45, opacity: 0 }}
                            animate={{ x: '25%', y: '15%', rotate: -10, opacity: 1 }}
                            exit={{ x: '100%', y: '15%', rotate: 45, opacity: 0 }}
                            transition={{ type: "spring", stiffness: 120, damping: 12, mass: 0.8 }}
                            className="absolute bottom-[-10%] right-[-35%] md:right-[-30%] h-[75vh] w-[75vh] z-30 pointer-events-none origin-bottom-right"
                        >
                            <img
                                src={soiseolAnnoying}
                                alt="Soiseol"
                                className="w-full h-full object-contain object-bottom drop-shadow-[0_0_50px_rgba(251,191,36,0.3)]"
                            />

                            {/* Soiseol's Dialogue Bubble-Hanji Style */}
                            <motion.div
                                initial={{ opacity: 0, scale: 0.8, y: 20 }}
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                transition={{ delay: 0.5 }}
                                className="absolute top-[0%] left-[-10%] bg-[#f5f0e1]/95 border-2 border-amber-900/20 text-stone-800 p-6 rounded-xl rounded-br-none shadow-xl max-w-xs pointer-events-auto font-['JoseonPalace']"
                            >
                                <div className="absolute -top-3 -right-3 w-8 h-8 rounded-full border-4 border-[#f5f0e1] bg-amber-800 shadow-md flex items-center justify-center">
                                    <span className="text-[#f5f0e1] text-xs font-bold">★</span>
                                </div>
                                <div className="flex flex-col gap-3">
                                    <p className="text-lg leading-relaxed font-bold">
                                        이런 거 듣지 말고, <br />
                                        <span className="text-amber-700 font-black text-xl">오방신점</span>을 보는 게 어때요?
                                    </p>
                                    {/* Soiseol's Obang Option Button-Moved inside bubble */}
                                    <motion.button
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        onClick={onSwitchToObang}
                                        className="w-full py-2 px-3 bg-gradient-to-r from-amber-800 to-amber-950 border border-amber-500/30 text-amber-50 font-['JoseonPalace'] text-base rounded-lg hover:shadow-[0_0_15px_rgba(251,191,36,0.3)] hover:scale-[1.02] transition-all flex items-center justify-center gap-2 mt-1"
                                    >
                                        <span>솔깃한데? 오방신점 볼래요</span>
                                    </motion.button>
                                </div>
                            </motion.div>
                        </motion.div>
                    )}
                </AnimatePresence>

                {/* Dialogue Box (Stella)-Magical Midnight Style */}
                <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.2 }}
                    className={`relative z-20 mb-20 mx-auto max-w-xl min-w-[360px] ${showSoiseol ? 'translate-x-[-10%]' : ''} transition-transform duration-500`}
                >
                    <div className="relative bg-slate-950/80 border-2 border-purple-500/30 p-8 rounded-xl shadow-[0_0_40px_rgba(168,85,247,0.2)] backdrop-blur-2xl flex flex-col items-center gap-6 text-white">

                        {/* Name Tag */}
                        <div className="absolute -top-5 left-8 px-6 py-2 rounded-lg border-2 shadow-lg transform -skew-x-12 bg-gradient-to-r from-purple-800 to-indigo-800 border-purple-400 text-purple-50">
                            <span className="block transform skew-x-12 text-sm md:text-base font-bold tracking-widest uppercase font-gmarket">
                                스텔라
                            </span>
                        </div>

                        <h3 className="font-gmarket text-2xl md:text-3xl font-bold text-purple-200 mb-2 text-center break-keep">
                            타로 카드에 대해 알려드릴까요?
                        </h3>

                        <div className="flex flex-col gap-3 w-full font-gmarket">
                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => onNext(false)}
                                disabled={!showSoiseol}
                                className={`w-full py-3 px-6 bg-gradient-to-r from-indigo-800 to-purple-800 text-white text-xl rounded-lg shadow-lg border border-purple-400/30 transition-all flex items-center justify-center gap-2 group ${!showSoiseol ? 'opacity-50 pointer-events-none' : ''} `}
                            >
                                <span className="font-medium">네, 설명 들을래요!</span>
                            </motion.button>

                            <motion.button
                                whileHover={{ scale: 1.02 }}
                                whileTap={{ scale: 0.98 }}
                                onClick={() => onNext(true)}
                                disabled={!showSoiseol}
                                className={`w-full py-3 px-6 bg-white/5 border border-purple-500/20 text-purple-100 text-xl font-bold rounded-lg hover: bg-white/10 transition-all flex items-center justify-center gap-2 ${!showSoiseol ? 'opacity-50 pointer-events-none' : ''} `}
                            >
                                <span>SKIP! 바로 카드뽑기</span>
                            </motion.button>


                        </div>
                    </div>
                </motion.div>
            </div>
        </motion.div>
    );
};

// Tarot Explain Stage
const TarotExplainStage = ({ onComplete }: { onComplete: () => void }) => {
    // Explanation lines
    const explainLines = ["타로는 78장의 상징적인 카드를 통해 당신의 무의식을 비추는 거울과 같아요.",
        "메이저 아르카나의 22장 카드는 당신의 중요한 인생의 여정을 보여주죠.",
        "당신이 뽑을 한 장의 카드가 오늘 어떤 이야기를 들려줄까요?",
        "자, 별들의 속삭임에 귀를 기울일 준비가 되셨나요?"];

    const [currentLineIndex, setCurrentLineIndex] = useState(0);
    const [typedText, setTypedText] = useState('');
    const [isTyping, setIsTyping] = useState(true);
    const typingIntervalRef = useRef<NodeJS.Timeout | null>(null);
    const { play } = useSound();

    useEffect(() => {
        setTypedText('');
        setIsTyping(true);
        let i = 0;
        const currentText = explainLines[currentLineIndex];

        if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);

        typingIntervalRef.current = setInterval(() => {
            if (i < currentText.length) {
                setTypedText(currentText.substring(0, i + 1));
                i++;
            } else {
                if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
                setIsTyping(false);
            }
        }, 50);

        return () => {
            if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
        };
    }, [currentLineIndex]);

    const handleNext = useCallback(() => {
        if (isTyping) {
            if (typingIntervalRef.current) clearInterval(typingIntervalRef.current);
            setTypedText(explainLines[currentLineIndex]);
            setIsTyping(false);
        } else {
            if (currentLineIndex < explainLines.length - 1) {
                setCurrentLineIndex(prev => prev + 1);
            } else {
                onComplete();
            }
        }
    }, [isTyping, currentLineIndex, onComplete]);

    // Keyboard support
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.code === 'Space' || e.code === 'Enter') {
                e.preventDefault();
                handleNext();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [handleNext]);

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-transparent cursor-pointer pointer-events-auto"
            onClick={handleNext}
        >
            <div className="relative w-full max-w-4xl h-full max-h-[90vh] flex items-end justify-center pb-10 z-10">
                {/* Stella Image */}
                <motion.div
                    animate={{ y: [0, -5, 0] }}
                    transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    className="absolute bottom-0 left-[-15%] md:left-[-25%] h-[80vh] w-[80vh] z-10 pointer-events-none"
                >
                    <img
                        src={stellaSmile}
                        alt="Stella"
                        className="w-full h-full object-contain object-bottom drop-shadow-[0_0_50px_rgba(255,255,255,0.1)] scale-110 origin-bottom"
                    />
                </motion.div>

                {/* Dialogue Box */}
                <motion.div
                    key={currentLineIndex}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                    className="absolute bottom-8 md:bottom-12 left-4 right-4 md:left-20 md:right-20 z-20 p-6 md:p-8 rounded-xl border-2 bg-slate-900/90 border-purple-500/50 text-white shadow-purple-900/50 backdrop-blur-xl flex flex-col items-start gap-4"
                >
                    {/* Character Name Tag */}
                    <div className="absolute -top-5 left-8 px-6 py-2 rounded-lg border-2 shadow-lg transform -skew-x-12 bg-indigo-600 border-purple-400 text-purple-50">
                        <span className="block transform skew-x-12 text-sm md:text-base font-bold tracking-widest uppercase font-gmarket">
                            스텔라
                        </span>
                    </div>

                    <div className="w-full pl-2">
                        <p className="text-lg md:text-2xl font-gmarket font-light leading-relaxed whitespace-pre-wrap break-keep">
                            {typedText}
                            {isTyping && <span className="animate-pulse inline-block ml-1">_</span>}
                        </p>
                    </div>
                </motion.div>
            </div>

            {/* Skip Button (Right Side for Tarot) */}
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    play('SFX', 'CLICK1');
                    onComplete();
                }}
                className="absolute bottom-12 right-8 z-50 text-white hover:text-white/80 text-sm tracking-[0.3em] font-bold uppercase transition-all duration-300 flex items-center gap-2 group hover:scale-105"
            >
                SKIP
            </button>
        </motion.div>
    );
};


const GameSelectionStage = ({ onSelect }: { onSelect: (game: GameType) => void }) => (
    <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 w-full h-full flex flex-col md:flex-row bg-black overflow-hidden pointer-events-auto rounded-3xl"
    >
        {/* Title Overlay-Stays on top with Blend Mode for contrast */}
        <div className="absolute top-10 left-0 w-full z-30 pointer-events-none flex flex-col items-center justify-center mix-blend-difference">
            <motion.h2
                initial={{ y: -50, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 0.5, duration: 0.8 }}
                className="text-6xl md:text-8xl font-black text-white/90 drop-shadow-[0_0_30px_rgba(255,255,255,0.3)] tracking-tight font-['GmarketSansBold'] text-center whitespace-nowrap"
            >
                운명의 갈림길
            </motion.h2>
            <motion.div
                initial={{ width: 0, opacity: 0 }}
                animate={{ width: 200, opacity: 1 }}
                transition={{ delay: 0.8, duration: 1 }}
                className="h-[1px] bg-white/50 mt-4"
            />
            <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1 }}
                className="mt-3 text-white/70 tracking-[0.2em] text-sm md:text-base uppercase font-light text-center break-keep"
            >
                서양의 예지력과 동양의 통찰력, 당신의 선택은?
            </motion.p>
        </div>

        {/* Tarot Section (Left)-Western Dark Theme */}
        <motion.div
            className="relative flex-1 basis-0 h-full cursor-pointer group overflow-hidden border-r border-white/10"
            onClick={() => onSelect('tarot')}
        >
            {/* Background Image */}
            <div className="absolute inset-0 flex items-end justify-center">
                <img
                    src={westStar}
                    alt="Tarot BG"
                    className="w-full h-full object-cover object-top opacity-60 group-hover:opacity-80 group-hover:scale-110 transition-all duration-1000 grayscale-50 group-hover:grayscale-0"
                />
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-indigo-950/90 via-indigo-900/40 to-black/60 group-hover:opacity-40 transition-opacity duration-500" />

            {/* Content */}
            < div className="absolute inset-0 flex flex-col items-center justify-center pt-20 z-10 transition-transform duration-500 group-hover:translate-y-[-20px]" >

                <h3 className="text-5xl md:text-6xl font-black text-white mb-2 font-serif tracking-wide group-hover:text-indigo-200 transition-colors drop-shadow-xl">TAROT</h3>
                <p className="text-indigo-200/80 text-lg tracking-[0.2em] font-light mb-8">서양의 신비 타로</p>

                <div className="px-8 py-3 border border-indigo-400/30 bg-indigo-900/30 rounded-full text-sm text-indigo-100/80 tracking-widest uppercase backdrop-blur-sm group-hover:bg-indigo-500 group-hover:text-white group-hover:border-indigo-400 transition-all shadow-lg">
                    운명 확인하기
                </div>
            </div >

            {/* Hover Glow Effect */}
            < div className="absolute inset-0 bg-indigo-500/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none mix-blend-overlay" />
        </motion.div >

        {/* Obang Section (Right)-Eastern Hanji Theme */}
        < motion.div
            className="relative flex-1 basis-0 h-full cursor-pointer group overflow-hidden border-l border-white/10 bg-[#f4efe4]"
            onClick={() => onSelect('obang')}
        >
            {/* Background Texture (Paper) */}
            < div className="absolute inset-0 opacity-40 bg-[url('https://www.transparenttextures.com/patterns/clean-gray-paper.png')] pointer-events-none" />

            {/* Background Image-Ink Style */}
            < div className="absolute inset-0 flex items-end justify-center" >
                <img
                    src={eastSaju}
                    alt="Obang BG"
                    className="w-full h-full object-cover object-top opacity-20 mix-blend-multiply group-hover:opacity-40 group-hover:scale-110 transition-all duration-1000 grayscale group-hover:grayscale-0"
                />
            </div >
            {/* Vignette for Hanji feel */}
            < div className="absolute inset-0 bg-gradient-to-t from-stone-400/20 via-transparent to-transparent opacity-50" />

            {/* Content */}
            < div className="absolute inset-0 flex flex-col items-center justify-center pt-20 z-10 transition-transform duration-500 group-hover:translate-y-[-20px]" >

                {/* Text-Dark Calligraphy Style */}
                < h3 className="text-5xl md:text-6xl font-black text-stone-800 mb-2 font-['JoseonPalace'] tracking-wide group-hover:text-black transition-colors drop-shadow-sm" > 오방신점</h3 >
                <p className="text-stone-600/80 text-lg tracking-[0.2em] font-light mb-8 font-['JoseonPalace']">동양의 신비 오방</p>

                {/* Button-Stamp Style */}
                <div className="px-8 py-3 border border-stone-800/40 bg-white/40 rounded-full text-sm text-stone-800 tracking-widest uppercase backdrop-blur-sm group-hover:bg-stone-800 group-hover:text-amber-50 group-hover:border-stone-900 transition-all shadow-md group-hover:shadow-xl font-['JoseonPalace']">
                    운명 확인하기
                </div>
            </div >

            {/* Hover Glow Effect-Warm Amber */}
            < div className="absolute inset-0 bg-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none" />
        </motion.div >

    </motion.div >
);





// Helper for dynamic background gradient based on element
const getElementGradient = (element: string) => {
    switch (element) {
        case 'wood': return 'from-green-900/40 via-emerald-950/60 to-black';
        case 'fire': return 'from-red-900/40 via-orange-950/60 to-black';
        case 'earth': return 'from-amber-900/40 via-yellow-950/60 to-black';
        case 'metal': return 'from-slate-800/40 via-gray-900/60 to-black';
        case 'water': return 'from-blue-900/40 via-indigo-950/60 to-black';
        default: return 'from-black via-black to-black';
    }
};

const CardRevealStage = ({ card, onNext }: { card: FortuneCard; onNext: () => void }) => {
    const [revealState, setRevealState] = useState<'hook' | 'shaking' | 'reveal' | 'reading'>('hook');

    useEffect(() => {
        // Sequence: Hook -> Shaking (Suspense) -> Reveal Card (Flash/Flip) -> Reading (Dialog)
        const timer0 = setTimeout(() => setRevealState('shaking'), 800);
        const timer1 = setTimeout(() => setRevealState('reveal'), 2800); // 2s shaking
        const timer2 = setTimeout(() => setRevealState('reading'), 4500);
        return () => { clearTimeout(timer0); clearTimeout(timer1); clearTimeout(timer2); };
    }, []);

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center justify-center w-full h-full relative z-20 pointer-events-none font-['Hahmlet']"
        >
            {/* Dynamic Background Gradient (Intensified) */}
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: revealState === 'reveal' || revealState === 'reading' ? 1 : 0 }}
                transition={{ duration: 2 }}
                className={`absolute inset-0 bg-gradient-radial ${getElementGradient(card.id)} pointer-events-none z-0 mix-blend-soft-light opacity-80`}
            />

            {/* Flash Effect on Reveal */}
            <AnimatePresence>
                {revealState === 'reveal' && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: [0, 1, 0] }}
                        transition={{ duration: 0.8 }}
                        className="absolute inset-0 bg-white z-40 pointer-events-none mix-blend-overlay"
                    />
                )}
            </AnimatePresence>

            {/* Main Content Container */}
            <div className="flex flex-col md:flex-row items-center justify-center relative z-10 w-full h-full max-w-7xl px-8">

                {/* [Left] Text Information */}
                <motion.div
                    initial={{ opacity: 0, x: -50 }}
                    animate={{
                        opacity: revealState === 'reading' ? 1 : 0,
                        x: revealState === 'reading' ? 0 : -50
                    }}
                    transition={{ duration: 1, delay: 0.5, type: "spring" }}
                    className="absolute left-4 md:left-12 top-1/2 -translate-y-1/2 z-20 max-w-sm w-full text-left hidden md:block"
                >
                    <div className="flex flex-col items-center md:items-start gap-4">
                        {/* Element Badge */}
                        <div className={`px-4 py-1.5 rounded-full border border-white/20 bg-black/40 backdrop-blur-md flex items-center gap-2 ${card.color === 'red' ? 'text-red-400' : card.color === 'blue' ? 'text-blue-400' : card.color === 'green' ? 'text-green-400' : card.color === 'yellow' ? 'text-amber-400' : 'text-slate-200'} `}>
                            <card.elementIcon size={16} />
                            <span className="text-sm font-bold tracking-[0.2em] font-['Hahmlet'] uppercase">{card.element}</span>
                        </div>

                        <h2 className="text-6xl md:text-7xl font-bold text-white drop-shadow-[0_0_40px_rgba(255,255,255,0.4)] font-['Hahmlet'] leading-tight mb-2">
                            {card.name.split(' (')[0]}
                        </h2>

                        <p className="text-xl md:text-2xl text-amber-200/90 font-['Hahmlet'] font-light tracking-wide leading-relaxed">
                            {card.title}
                        </p>

                        <div className="h-px w-20 bg-gradient-to-r from-transparent via-white/50 to-transparent my-2" />

                        <p className="text-white/60 font-['Hahmlet'] text-sm leading-7 break-keep">
                            {card.description}
                        </p>
                    </div>
                </motion.div>

                {/* [Right] 3D Card Reveal */}
                <motion.div
                    className="relative z-10 perspective-[1000px] order-1 md:order-2"
                    initial={{ scale: 0.8, y: 50, opacity: 0 }}
                    animate={{
                        scale: revealState === 'hook' ? 0.9 : revealState === 'shaking' ? 0.95 : 1.1,
                        y: revealState === 'hook' ? 20 : revealState === 'shaking' ? 0 : 0,
                        x: revealState === 'shaking' ? [-3, 3, -3, 3, -1, 1, 0] : 0,
                        opacity: 1
                    }}
                    transition={{
                        default: { duration: 1.5, type: "spring", bounce: 0.2 },
                        x: revealState === 'shaking' ? { repeat: Infinity, duration: 0.1, ease: "linear" } : { duration: 0.5 }
                    }}
                >
                    {/* Divine Burst (Behind) */}
                    <AnimatePresence>
                        {revealState === 'reveal' && (
                            <motion.div
                                initial={{ scale: 0, opacity: 0.8 }}
                                animate={{ scale: 2.5, opacity: 0 }}
                                transition={{ duration: 0.6, ease: "easeOut" }}
                                className="absolute inset-0 -z-20 bg-gradient-radial from-amber-100 to-transparent blur-2xl rounded-full mix-blend-screen"
                            />
                        )}
                    </AnimatePresence>

                    {/* Elemental Particles around card */}
                    <div className="absolute inset-0 -z-10 scale-150">
                        <ElementalParticles
                            element={card.id}
                            isActive={revealState === 'reveal' || revealState === 'reading'}
                            intensity={revealState === 'reading' ? 1.5 : 1}
                        />
                    </div>

                    {/* The Card Itself (Custom 3D Flip Implementation) */}
                    <div className="relative w-[300px] h-[500px] transform-style-3d">
                        <motion.div
                            className="w-full h-full relative transform-style-3d shadow-2xl rounded-[20px]"
                            initial={{ rotateY: 0 }}
                            animate={{
                                rotateY: (revealState === 'hook' || revealState === 'shaking') ? 0 :
                                    revealState === 'reveal' ? [0, 180] : 180,
                            }}
                            transition={{
                                duration: 1.5,
                                ease: [0.34, 1.56, 0.64, 1]
                            }}
                            style={{ transformStyle: 'preserve-3d' }}
                        >
                            {/* Back Face (Obang Pattern)-Now Front Facing (0deg) */}
                            <div
                                className="absolute inset-0 bg-[#1a1a1a] rounded-[20px] overflow-hidden backface-hidden"
                            >
                                <img src={obangBack} alt="Back" className="w-full h-full object-cover" />
                                <div className="absolute inset-0 bg-black/40" />
                            </div>

                            {/* Front Face (The Result)-Now Back Facing (180deg) */}
                            <div
                                className="absolute inset-0 bg-[#0a0a0a] rounded-[20px] overflow-hidden backface-hidden border border-amber-500/40"
                                style={{ transform: 'rotateY(180deg)' }}
                            >
                                <img src={card.imageUrl} alt={card.name} className="w-full h-full object-cover" />
                                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-white/10 mix-blend-overlay" />
                                {/* Shiny Border */}
                                <div className="absolute inset-0 rounded-[20px] border border-white/20" />
                                {/* Bottom Glow */}
                                <div className="absolute bottom-0 inset-x-0 h-32 bg-gradient-to-t from-amber-500/20 to-transparent pointer-events-none" />
                            </div>
                        </motion.div>

                        {/* Reflection (Static Floor) */}
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: revealState === 'reading' ? 0.4 : 0 }}
                            className="absolute top-full left-0 right-0 h-16 origin-top transform rotate-180 pointer-events-none"
                            style={{ maskImage: "linear-gradient(transparent, black)" }}
                        >
                            <div className={`w-full h-full bg-gradient-to-b ${getElementGradient(card.id)} blur-xl`} />
                        </motion.div>
                    </div>
                </motion.div>
            </div>

            {/* Soiseol Reaction (Glassmorphic) */}
            <AnimatePresence>
                {revealState === 'reading' && (
                    <>


                        {/* Speech Bubble */}
                        <motion.div
                            initial={{ opacity: 0, y: 20, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            transition={{ delay: 1 }}
                            className="absolute right-8 md:right-12 top-1/2 -translate-y-1/2 max-w-sm pointer-events-auto z-40"
                        >
                            <div className="relative bg-black/40 backdrop-blur-xl border border-white/20 p-6 rounded-2xl rounded-br-sm shadow-[0_10px_40px_rgba(0,0,0,0.4)]">
                                <div className="absolute -top-3 -left-3">
                                    <div className="w-10 h-10 rounded-full border-2 border-amber-400 bg-stone-900 overflow-hidden shadow-lg">
                                        <img src={eastSaju} alt="Face" className="w-full h-full object-cover object-top" />
                                    </div>
                                </div>

                                <h4 className="text-amber-400 font-bold mb-2 ml-6 text-sm tracking-widest uppercase">소이설</h4>
                                <p className="text-white/90 font-['Hahmlet'] leading-relaxed text-lg break-keep">
                                    와! <span className="text-amber-300 font-bold">{card.name.split(' (')[0]}</span>!<br />
                                    정말 영험한 기운이 느껴져요.
                                </p>

                                <motion.button
                                    whileHover={{ scale: 1.02 }}
                                    whileTap={{ scale: 0.98 }}
                                    onClick={onNext}
                                    className="mt-6 w-full py-3.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white font-bold rounded-xl shadow-lg hover:shadow-indigo-500/30 transition-all font-['Hahmlet'] text-base tracking-widest flex items-center justify-center gap-2 group"
                                >
                                    <span>결과 확인하기</span>
                                    <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
                                </motion.button>
                            </div>
                        </motion.div>
                    </>
                )}
            </AnimatePresence>
        </motion.div>
    );
};


// Level Reveal Stage-Premium Ethereal Bloom
const LevelRevealStage = ({ fortune, onNext }: { fortune: FortuneResult; onNext: () => void }) => {
    return (
        <motion.div
            className="flex flex-col items-center justify-center w-full h-full relative z-20 pointer-events-auto cursor-pointer p-4 overflow-hidden"
            onClick={onNext}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.5 } }}
        >
            {/* Background Atmosphere-Animated Gradient/Fog */}
            <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
                className="absolute inset-[-50%] bg-[radial-gradient(circle_at_center,_rgba(251,191,36,0.05)_0%,_transparent_60%)] z-0"
            />

            {/* Main Rank Text-Ethereal Bloom */}
            <div className="relative z-10">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0, filter: "blur(20px)" }}
                    animate={{ scale: 1, opacity: 1, filter: "blur(0px)" }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    className="relative"
                >
                    <h1 className={`text-[8rem] md: text-[12rem] font-black leading-none tracking-tighter font-['JoseonPalace'] text-amber-300 drop-shadow-[0_0_100px_rgba(251, 191, 36, 0.8),0_0_50px_rgba(251, 191, 36, 0.6),0_4px_20px_rgba(0, 0, 0, 0.5)]`}
                        style={{ textShadow: '0 0 40px rgba(251,191,36,0.9), 0 0 80px rgba(251,191,36,0.5), 0 4px 10px rgba(0,0,0,0.8)' }}
                    >
                        {fortune.levelName}
                    </h1>
                    {/* Floating Particles around Text */}
                    <div className="absolute inset-0 pointer-events-none">
                        {[...Array(8)].map((_, i) => (
                            <motion.div
                                key={i}
                                initial={{ opacity: 0, scale: 0, x: 0, y: 0 }}
                                animate={{ opacity: [0, 1, 0], scale: [0, 1, 0], x: (Math.random() - 0.5) * 150, y: (Math.random() - 0.5) * 100 }}
                                transition={{ duration: 2 + Math.random(), delay: 0.5 + Math.random(), repeat: Infinity }}
                                className="absolute left-1/2 top-1/2 w-1 h-1 bg-amber-200 rounded-full blur-[1px]"
                            />
                        ))}
                    </div>
                </motion.div>
            </div>

            {/* Subtext-Smooth Slide Up */}
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 1 }}
                className="mt-12 text-center space-y-6 max-w-lg z-10"
            >
                <div className="flex items-center justify-center gap-4">
                    <span className="h-[1px] w-8 bg-gradient-to-r from-transparent to-amber-500/50" />
                    <h2 className="text-2xl md:text-3xl text-amber-200 font-['JoseonPalace'] tracking-[0.2em] uppercase drop-shadow-[0_2px_10px_rgba(0,0,0,0.5)]">{fortune.level}</h2>
                    <span className="h-[1px] w-8 bg-gradient-to-l from-transparent to-amber-500/50" />
                </div>

                <p className="text-white/90 text-xl md:text-2xl font-light leading-relaxed break-keep whitespace-pre-line drop-shadow-[0_2px_8px_rgba(0,0,0,0.6)] font-['JoseonPalace']">
                    {fortune.card.blessing.split('.').filter(s => s.trim()).map(s => s.trim() + '.').join('\n')}
                </p>

                <div className="pt-8">
                    <span className="text-white text-sm tracking-[0.3em] font-light animate-pulse uppercase drop-shadow-lg">
                        화면을 터치하여 계속하기
                    </span>
                </div>
            </motion.div>
        </motion.div>
    );
};

// Fate Radar Stage-Game Style Analysis
const FateRadarStage = ({ fortune, onNext }: { fortune: FortuneResult; onNext: () => void }) => {
    // 5 Elements Data-Enhanced with Colors
    const stats = [{ label: '목(木)', value: fortune.categories.wood, key: 'wood', color: '#10b981' }, // Emerald
    { label: '화(火)', value: fortune.categories.fire, key: 'fire', color: '#ef4444' }, // Red
    { label: '토(土)', value: fortune.categories.earth, key: 'earth', color: '#f59e0b' }, // Amber
    { label: '금(金)', value: fortune.categories.metal, key: 'metal', color: '#e2e8f0' }, // Slate/Silver
    { label: '수(水)', value: fortune.categories.water, key: 'water', color: '#60a5fa' }, // Blue (Brighter)
    ];

    const maxStat = stats.reduce((prev, current) => (prev.value > current.value) ? prev : current);

    // Calculate Pentagon Points
    const size = 140; // Increased size
    const center = 200;
    const points = stats.map((stat, i) => {
        const angle = (Math.PI * 2 * i) / 5 - Math.PI / 2;
        const valueRatio = stat.value / 100;
        return {
            x: center + Math.cos(angle) * size * valueRatio,
            y: center + Math.sin(angle) * size * valueRatio,
            fullX: center + Math.cos(angle) * size,
            fullY: center + Math.sin(angle) * size,
            labelX: center + Math.cos(angle) * (size + 45), // Pushed out for larger labels
            labelY: center + Math.sin(angle) * (size + 45),
        };
    });

    const pathData = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x},${p.y} `).join(' ') + ' Z';

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center w-full h-full pointer-events-auto overflow-hidden relative"
        >
            {/* Background Runic Circle (Rotating) */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-[60%] w-[600px] h-[600px] opacity-20 pointer-events-none">
                <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
                    className="w-full h-full border-[1px] border-amber-500/30 rounded-full border-dashed"
                />
                <motion.div
                    animate={{ rotate: -360 }}
                    transition={{ duration: 40, repeat: Infinity, ease: "linear" }}
                    className="absolute inset-10 border-[1px] border-amber-500/20 rounded-full"
                />
            </div>

            <motion.div
                initial={{ x: -20, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                className="absolute top-8 left-8 z-20"
            >
                <h3 className="text-4xl md:text-5xl font-black text-amber-300 font-['JoseonPalace'] drop-shadow-[0_0_20px_rgba(251,191,36,0.6)]">
                    오행 분석
                </h3>
            </motion.div>

            {/* Elemental Particles based on strongest element */}
            <ElementalParticles
                element={maxStat.key}
                isActive={true}
                intensity={1.2}
            />



            {/* Radar Chart Area */}
            <div className="relative w-[400px] h-[400px] flex items-center justify-center shrink-0 z-10 md:scale-110 mt-16">
                <svg width="400" height="400" className="overflow-visible" viewBox="0 0 400 400">
                    <defs>
                        <radialGradient id="radarFill" cx="50%" cy="50%" r="50%" fx="50%" fy="50%">
                            <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.4" />
                            <stop offset="100%" stopColor="#d97706" stopOpacity="0.1" />
                        </radialGradient>
                        <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                            <feGaussianBlur stdDeviation="4" result="coloredBlur" />
                            <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                    </defs>

                    {/* Grid Levels */}
                    {[1, 0.75, 0.5, 0.25].map((scale, i) => {
                        const scaledPoints = stats.map((_, idx) => {
                            const angle = (Math.PI * 2 * idx) / 5 - Math.PI / 2;
                            const r = size * scale;
                            return `${center + Math.cos(angle) * r},${center + Math.sin(angle) * r} `;
                        }).join(' ');
                        return (
                            <polygon
                                key={i}
                                points={scaledPoints}
                                fill={i === 0 ? "rgba(0,0,0,0.3)" : "none"}
                                stroke="rgba(255,255,255,0.1)"
                                strokeWidth="1"
                            />
                        );
                    })}

                    {/* The Data Path */}
                    <motion.path
                        d={pathData}
                        fill="url(#radarFill)"
                        stroke="#fbbf24"
                        strokeWidth="3"
                        filter="url(#glow)"
                        initial={{ pathLength: 0, opacity: 0 }}
                        animate={{ pathLength: 1, opacity: 1 }}
                        transition={{ duration: 1.5, ease: "circOut" }}
                    />

                    {/* Points & Labels */}
                    {points.map((p, i) => {
                        const stat = stats[i];
                        const isMax = stat.value === maxStat.value;
                        return (
                            <g key={i}>
                                {/* Node */}
                                <motion.circle
                                    cx={p.x}
                                    cy={p.y}
                                    r={isMax ? 6 : 4}
                                    fill={isMax ? "#fff" : stat.color}
                                    stroke="#fff"
                                    strokeWidth="2"
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ delay: 1 + i * 0.1 }}
                                />

                                {/* Label Group */}
                                <foreignObject x={p.labelX - 50} y={p.labelY - 25} width="100" height="60">
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.5 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        transition={{ delay: 1.2 + i * 0.1 }}
                                        className={`flex flex-col items-center justify-center ${isMax ? 'scale-110' : ''} bg-black/50 backdrop-blur-sm rounded-xl px-3 py-1.5 border border-white/10 shadow-lg`}
                                    >
                                        <div className={`text-xl font-bold font-['JoseonPalace'] whitespace-nowrap drop-shadow-md flex items-center gap-1 ${isMax ? 'drop-shadow-[0_0_15px_rgba(251,191,36,0.8)]' : ''} `} style={{ color: stat.color }}>
                                            {stat.key === 'wood' && <TreeDeciduous size={16} />}
                                            {stat.key === 'fire' && <Flame size={16} />}
                                            {stat.key === 'earth' && <Mountain size={16} />}
                                            {stat.key === 'metal' && <Swords size={16} />}
                                            {stat.key === 'water' && <Droplet size={16} />}
                                            {stat.label}
                                        </div>
                                        <div className={`text-xl font-black mt-[-4px] font-['JoseonPalace'] ${isMax ? 'text-amber-300' : ''} `} style={{ color: stat.color }}>
                                            {stat.value}
                                        </div>
                                    </motion.div>
                                </foreignObject>
                            </g>
                        );
                    })}
                </svg>
            </div>


            {/* Dialogue integrated at bottom */}
            <motion.div
                initial={{ y: 50, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                transition={{ delay: 1.5 }}
                className="absolute bottom-4 left-0 right-0 px-6 flex justify-center z-20 pointer-events-none"
            >
                <div className="bg-black/80 border border-amber-500/30 backdrop-blur-md rounded-xl p-5 flex gap-5 max-w-lg w-full shadow-2xl pointer-events-auto cursor-pointer" onClick={onNext}>
                    <div className="flex flex-col items-center gap-2 shrink-0">
                        <div className="w-14 h-14 rounded-full border border-amber-500/50 overflow-hidden bg-stone-900 shadow-inner">
                            <img src={eastSaju} alt="So Yi-seol" className="w-full h-full object-cover object-top scale-[2.2] translate-y-7" />
                        </div>
                        <h4 className="text-amber-500 font-bold text-sm tracking-widest font-['JoseonPalace']">소이설</h4>
                    </div>
                    <div className="flex-1 flex items-center">
                        <p className="text-stone-200 text-lg md:text-xl font-['JoseonPalace'] break-keep leading-relaxed whitespace-pre-line">
                            <span className="text-amber-200 font-bold">"{maxStat.label}"</span>
                            의 기운이 가장 강하군요.{"\n"}{maxStat.key === 'fire' ? '열정이 넘치는 시기입니다.' : maxStat.key === 'water' ? '지혜와 유연함이 돋보입니다.' : maxStat.key === 'wood' ? '성장과 시작의 기운이 좋습니다.' : maxStat.key === 'metal' ? '결단력과 의지가 강합니다.' : '안정과 포용력이 뛰어납니다.'}
                        </p>
                    </div>
                </div>
            </motion.div>
        </motion.div >
    );
};

// Scroll Oracle Stage-Premium Dark/Gold Fantasy Theme with Hanji & Dynamic Seal
const ScrollOracleStage = ({ fortune, onNext }: { fortune: FortuneResult; onNext: () => void }) => (
    <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="flex flex-col items-center justify-center w-full h-full p-4 pointer-events-auto"
        onClick={onNext}
    >
        <motion.div
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.8 }}
            className="relative w-full max-w-lg bg-[#f8f4ed] border-4 border-[#3d2b1f] rounded-sm overflow-hidden flex flex-col items-center text-center shadow-[0_0_60px_rgba(0,0,0,0.9),inset_0_0_100px_rgba(61,43,31,0.1)]"
        >
            {/* Ornate Corner Accents-More Traditional */}
            <div className="absolute top-2 left-2 w-12 h-12 border-t-2 border-l-2 border-[#3d2b1f]/60 rounded-tl-sm pointer-events-none" />
            <div className="absolute top-2 right-2 w-12 h-12 border-t-2 border-r-2 border-[#3d2b1f]/60 rounded-tr-sm pointer-events-none" />
            <div className="absolute bottom-2 left-2 w-12 h-12 border-b-2 border-l-2 border-[#3d2b1f]/60 rounded-bl-sm pointer-events-none" />
            <div className="absolute bottom-2 right-2 w-12 h-12 border-b-2 border-r-2 border-[#3d2b1f]/60 rounded-br-sm pointer-events-none" />

            {/* Hanji Texture Layer */}
            <div className="absolute inset-0 opacity-40 bg-[url('https://www.transparenttextures.com/patterns/handmade-paper.png')] z-0 pointer-events-none mix-blend-multiply" />
            <div className="absolute inset-0 bg-gradient-to-br from-transparent via-[#e8dccb]/20 to-transparent z-0 pointer-events-none" />

            {/* Red Seal-Bottom Right Positioning */}
            <div className="absolute bottom-10 right-10 z-20 flex items-center justify-center pointer-events-none">
                <motion.div
                    initial={{ opacity: 0, rotate: 25, scale: 4, filter: "blur(20px)" }}
                    animate={{ opacity: 0.8, rotate: -12, scale: 1, filter: "blur(0px)" }}
                    transition={{
                        delay: 1.8,
                        duration: 0.4,
                        type: "spring",
                        stiffness: 200,
                        damping: 15
                    }}
                    className="relative w-28 h-28 border-[6px] border-[#8b0000] rounded-sm flex items-center justify-center bg-[#8b0000]/5 overflow-hidden mix-blend-multiply"
                    style={{
                        boxShadow: 'inset 0 0 15px rgba(139, 0, 0, 0.4)',
                    }}
                >
                    {/* Stamp Texture Effect */}
                    <div className="absolute inset-0 opacity-40 bg-[url('https://www.transparenttextures.com/patterns/concrete-wall.png')] mix-blend-multiply" />

                    <span className="text-[#8b0000] font-['JoseonPalace'] font-black text-4xl leading-none tracking-tighter -rotate-12">
                        {fortune.levelName}
                    </span>
                </motion.div>

                {/* Visual Impact Ripple */}
                <motion.div
                    initial={{ scale: 0.5, opacity: 0 }}
                    animate={{ scale: 2.5, opacity: 0 }}
                    transition={{ delay: 1.8, duration: 0.8 }}
                    className="absolute w-32 h-32 border-8 border-[#8b0000]/20 rounded-full"
                />
            </div>

            <div className="py-12 px-10 w-full relative z-30">
                <div className="w-full flex justify-center mb-8">
                    <span className="text-[#3d2b1f]/80 text-3xl font-bold border-b-2 border-[#3d2b1f]/30 pb-3 font-['Hahmlet'] px-4">
                        天命 (천명)
                    </span>
                </div>

                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5 }}
                >
                    <p className="text-2xl md:text-3xl text-[#1a120b] font-['JoseonPalace'] leading-[1.6] break-keep whitespace-pre-line mb-8 px-2 drop-shadow-sm">
                        "{formatDialogue(fortune.message)}"
                    </p>

                    <div className="w-full h-[2px] bg-gradient-to-r from-transparent via-[#3d2b1f]/30 to-transparent my-6" />

                    <p className="text-stone-800 text-sm md:text-lg leading-8 font-medium tracking-wide break-keep whitespace-pre-line px-4 font-['JoseonPalace']">
                        {fortune.advice
                            .replace(/연락해보주세요/g, '연락해보세요')
                            .split('.')
                            .filter(sentence => sentence.trim().length > 0)
                            .map((sentence) => sentence.trim() + '.')
                            .join('\n')}
                    </p>
                </motion.div>
            </div>
        </motion.div>

        <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 3.5 }}
            className="mt-8 text-white text-sm tracking-[0.4em] font-['JoseonPalace'] uppercase pointer-events-none animate-pulse"
        >
            운명 수락하기
        </motion.p>
    </motion.div>
);



// Destiny Seal Stage-Login/Signup Conversion
const DestinySealStage = ({ onClose, selectedGame, onSwitchGame }: { onRestart: () => void; onClose: () => void; selectedGame: GameType; onSwitchGame: (game: GameType) => void }) => {
    const isObang = selectedGame === 'obang';

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center w-full h-full p-4 pointer-events-auto relative overflow-hidden py-8"
        >
            {/* Decorative Background Elements */}
            <div className="absolute inset-0 pointer-events-none fixed">
                <div className={`absolute top-0 left-0 w-32 h-32 blur-3xl rounded-full mix-blend-screen ${isObang ? 'bg-amber-500/10' : 'bg-purple-500/10'} `} />
                <div className={`absolute bottom-0 right-0 w-32 h-32 blur-3xl rounded-full mix-blend-screen ${isObang ? 'bg-amber-500/10' : 'bg-purple-500/10'} `} />
            </div>

            <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.8 }}
                className="relative z-20 text-center space-y-3 flex flex-col items-center max-w-md w-full my-auto"
            >
                {/* Title Section */}
                <div>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.2 }}
                        className="relative"
                    >
                        <h2 className={`text-3xl md: text-4xl font-black text-transparent bg-clip-text drop-shadow-[0_0_20px_rgba(251, 191, 36, 0.5)] mb-3 ${isObang ? "bg-gradient-to-b from-amber-100 via-amber-200 to-amber-500 font-['JoseonPalace']" : "bg-gradient-to-b from-purple-100 via-purple-200 to-purple-500 font-gmarket tracking-tighter"} `}>
                            {isObang ? "운명의 문이 열렸습니다" : "운명의 문이 열립니다"}
                        </h2>
                    </motion.div>
                </div>

                {/* Character & Dialogue-Premium Presentation */}
                <div className="relative w-full flex flex-col items-center my-2">
                    {/* Character Avatar-Breathing Animation */}
                    <motion.div
                        animate={{ y: [0, -5, 0] }}
                        transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                        className={`w-28 h-28 rounded-full border-2 bg-gradient-to-br from-stone-800 to-black mb-6 shrink-0 relative z-10 group cursor-pointer overflow-visible ${isObang ? 'border-amber-400/60 shadow-[0_0_50px_rgba(251,191,36,0.4)]' : 'border-purple-400/60 shadow-[0_0_50px_rgba(168,85,247,0.4)]'} `}
                    >
                        <div className="w-full h-full rounded-full overflow-hidden relative">
                            <img src={isObang ? eastSaju : westStar} alt="Character" className={`w-full h-full object-cover object-top transition-transform duration-500 group-hover:scale-110 ${!isObang && 'scale-125'} `} />
                        </div>

                        {/* Name Tag */}
                        <div className={`absolute -bottom-3 left-1/2 -translate-x-1/2 px-5 py-1.5 rounded-full whitespace-nowrap shadow-lg z-20 ${isObang ? 'bg-gradient-to-r from-amber-950 to-amber-900 border border-amber-500/50' : 'bg-gradient-to-r from-purple-950 to-purple-900 border border-purple-500/50'} `}>
                            <span className={`text-sm font-bold tracking-widest flex items-center gap-1.5 ${isObang ? "text-amber-100 font-['JoseonPalace']" : "text-purple-100 font-gmarket"} `}>
                                <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${isObang ? 'bg-amber-400' : 'bg-purple-400'} `} />
                                {isObang ? '소이설' : '스텔라'}
                            </span>
                        </div>
                    </motion.div>

                    {/* Dialogue Bubble-Service Variety */}
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ delay: 0.5 }}
                        className={`relative bg-black/40 border rounded-2xl p-5 backdrop-blur-md max-w-sm text-center shadow-xl ring-1 ring-white/5 w-full ${isObang ? 'border-amber-500/30' : 'border-purple-500/30'} `}
                    >
                        {/* Triangle */}
                        <div className={`absolute-top-2 left-1/2-translate-x-1/2 w-4 h-4 bg-black/40 border-t border-l rotate-45 transform backdrop-blur-md ${isObang ? 'border-amber-500/30' : 'border-purple-500/30'} `} />

                        <p className={`text-white/95 text-sm md: text-base leading-6 break-keep ${isObang ? "font-['JoseonPalace']" : "font-serif"} `}>
                            {isObang ? (
                                <>
                                    <span className="text-amber-300 font-bold">서양의 점성술부터 동양의 사주팔자까지</span>...<br />
                                    당신의 운명을 위한 <span className="text-amber-300 font-bold border-b border-amber-300/50 pb-0.5">모든 이야기</span>가 기다려요.<br />
                                    <span className="text-amber-200 font-bold">지금 바로 시작해보세요.</span>
                                </>
                            ) : (
                                <>
                                    <span className="text-purple-300 font-bold">당신의 숨겨진 길</span>을 발견해보세요...<br />
                                    별들이 당신의 <span className="text-purple-300 font-bold border-b border-purple-300/50 pb-0.5">운명적 이야기</span>를 속삭이고 있어요.<br />
                                    <span className="text-purple-200 font-bold">지금 여정을 시작하세요.</span>
                                </>
                            )}
                        </p>
                    </motion.div>
                </div>

                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 1 }}
                    className="flex flex-col gap-4 w-full max-w-sm relative z-20 mt-4"
                >
                    {/* Self Login & Signup Buttons - Clean Layout */}
                    <div className="flex gap-4 w-full">
                        <button
                            onClick={() => window.location.href = '/login'}
                            className="flex-1 h-12 bg-white/10 hover:bg-white/20 text-white font-medium text-base rounded-xl border border-white/20 transition-all hover:scale-[1.02] backdrop-blur-sm shadow-lg"
                        >
                            로그인
                        </button>
                        <button
                            onClick={() => window.location.href = '/signup'}
                            className={`flex-1 h-12 text-white font-medium text-base rounded-xl border transition-all hover:scale-[1.02] backdrop-blur-sm shadow-lg ${isObang ? 'bg-amber-600/80 hover:bg-amber-600 border-amber-500/50' : 'bg-purple-600/80 hover:bg-purple-600 border-purple-500/50'} `}
                        >
                            회원가입
                        </button>
                    </div>

                    <button
                        onClick={onClose}
                        className="w-full py-3 text-white/40 hover:text-white/80 text-xs tracking-widest transition-colors font-light uppercase mt-2 hover:underline decoration-white/20 underline-offset-4"
                    >
                        다음에 하기
                    </button>
                </motion.div>
            </motion.div>

            {/* Background Effects */}
            <div className="absolute inset-0 z-0 pointer-events-none">
                <div className={`absolute top-1/2 left-1/2-translate-x-1/2-translate-y-1/2 w-[600px] h-[600px] rounded-full blur-[120px] animate-pulse ${isObang ? 'bg-amber-600/10' : 'bg-purple-600/10'} `} />
                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] opacity-20" />

                {/* Floating Magical Orbs */}
                {[...Array(12)].map((_, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, scale: 0 }}
                        animate={{
                            y: [0, -150 - Math.random() * 100],
                            x: [0, (Math.random() - 0.5) * 50],
                            opacity: [0, 0.4, 0],
                            scale: [0, 1 + Math.random(), 0]
                        }}
                        transition={{
                            duration: 4 + Math.random() * 4,
                            repeat: Infinity,
                            delay: Math.random() * 5,
                            ease: "easeInOut"
                        }}
                        className={`absolute bottom-[-20px] w-2 h-2 rounded-full blur-[2px] ${isObang ? 'bg-amber-300/40 shadow-[0_0_10px_rgba(251,191,36,0.5)]' : 'bg-purple-300/40 shadow-[0_0_10px_rgba(168,85,247,0.5)]'} `}
                        style={{ left: `${10 + Math.random() * 80}% ` }}
                    />
                ))}

                {/* Subtle Ambient Mist */}
                <motion.div
                    animate={{ opacity: [0.05, 0.15, 0.05], x: [-20, 20, -20] }}
                    transition={{ duration: 10, repeat: Infinity, ease: "easeInOut" }}
                    className={`absolute inset-x-0 bottom-0 h-1/2 blur-3xl pointer-events-none ${isObang ? 'bg-amber-900/10' : 'bg-purple-900/10'} `}
                />
            </div>

            {/* Cross-Promotion Characters (Bottom Section) */}
            <div className="fixed bottom-0 inset-x-0 h-0 z-30 pointer-events-none">
                {/* Stella-Appears after OBANG mode to suggest Tarot */}
                {isObang && (
                    <motion.div
                        initial={{ x: -100, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 1.5, duration: 0.8 }}
                        className="absolute bottom-8 left-8 flex items-end gap-3 pointer-events-auto"
                    >
                        {/* Stella Character */}
                        <motion.div
                            animate={{ y: [0, -8, 0] }}
                            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                            className="w-24 h-24 rounded-full border-2 border-purple-400/60 overflow-hidden shadow-[0_0_30px_rgba(168,85,247,0.4)] bg-gradient-to-br from-purple-900 to-black relative"
                        >
                            <img
                                src={westStar}
                                alt="Stella"
                                className="w-full h-full object-cover object-top scale-125"
                            />
                        </motion.div>

                        {/* Speech Bubble */}
                        <motion.div
                            animate={{ y: [0, -5, 0] }}
                            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                            className="relative bg-purple-950/90 border border-purple-400/50 rounded-2xl px-4 py-3 backdrop-blur-md shadow-xl max-w-[200px]"
                        >
                            <p className="text-purple-100 text-sm font-medium mb-2 font-['JoseonPalace']">
                                타로도 보러 오실거죠?
                            </p>
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.9, rotate: -2 }}
                                onClick={() => onSwitchGame('tarot')}
                                className="w-full bg-purple-500 hover:bg-purple-600 text-white text-xs font-bold py-2 px-3 rounded-lg transition-all shadow-lg"
                            >
                                간단 타로보기 →
                            </motion.button>
                            {/* Triangle pointer (Left side) */}
                            <div className="absolute -left-2 bottom-6 w-4 h-4 bg-purple-950/90 border-l border-b border-purple-400/50 rotate-45 transform"></div>
                        </motion.div>
                    </motion.div>
                )}

                {/* So Yi-seol-Appears after TAROT mode to suggest Obang */}
                {!isObang && (
                    <motion.div
                        initial={{ x: 100, opacity: 0 }}
                        animate={{ x: 0, opacity: 1 }}
                        transition={{ delay: 1.5, duration: 0.8 }}
                        className="absolute bottom-8 right-8 flex items-end flex-row-reverse gap-3 pointer-events-auto"
                    >
                        {/* Soiseol Character */}
                        <motion.div
                            animate={{ y: [0, -8, 0] }}
                            transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                            className="w-24 h-24 rounded-full border-2 border-amber-400/60 overflow-hidden shadow-[0_0_30px_rgba(251,191,36,0.4)] bg-gradient-to-br from-amber-950 to-black relative"
                        >
                            <img
                                src={eastSaju}
                                alt="Soiseol"
                                className="w-full h-full object-cover object-top"
                            />
                        </motion.div>

                        {/* Speech Bubble */}
                        <motion.div
                            animate={{ y: [0, -5, 0] }}
                            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                            className="relative bg-amber-950/90 border border-amber-400/50 rounded-2xl px-4 py-3 backdrop-blur-md shadow-xl max-w-[200px]"
                        >
                            <p className="text-amber-100 text-sm font-medium mb-2 font-['JoseonPalace']">
                                오방신점도 보러 오실거죠?
                            </p>
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.9, rotate: 2 }}
                                onClick={() => onSwitchGame('obang')}
                                className="w-full bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold py-2 px-3 rounded-lg transition-all shadow-lg"
                            >
                                오방신점 보러가기 →
                            </motion.button>
                            {/* Triangle pointer (Right side) */}
                            <div className="absolute -right-2 bottom-6 w-4 h-4 bg-amber-950/90 border-r border-b border-amber-400/50 rotate-45 transform"></div>
                        </motion.div>
                    </motion.div>
                )}
            </div>
        </motion.div>
    );
};

// Rune Circle Component
const RuneCircle = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-30 select-none">
        <svg viewBox="0 0 500 500" className="w-[800px] h-[800px] animate-[spin_60s_linear_infinite]">
            <defs>
                <path id="circlePath" d="M 250, 250 m -200, 0 a 200,200 0 1,1 400,0 a 200,200 0 1,1 -400,0" />
            </defs>
            <text fill="#a855f7" fontSize="12" letterSpacing="6px" fontWeight="bold">
                <textPath href="#circlePath" startOffset="0%">
                    THE WHEEL OF FORTUNE TURNS • DESTINY IS REVEALED • THE STARS ALIGN •
                    THE WHEEL OF FORTUNE TURNS • DESTINY IS REVEALED • THE STARS ALIGN •
                </textPath>
            </text>
            <circle cx="250" cy="250" r="210" stroke="#a855f7" strokeWidth="1" fill="none" strokeDasharray="5,5" />
            <circle cx="250" cy="250" r="190" stroke="#a855f7" strokeWidth="2" fill="none" />
        </svg>
    </div>
);

const TarotRevealStage = ({ result, onNext }: { result: TarotResult; onNext: () => void }) => {
    // Reveal Phases: 'summon' (face down center) -> 'flip' (face up center) -> 'insight' (move left, show text)
    const [revealPhase, setRevealPhase] = useState<'summon' | 'flip' | 'insight'>('summon');

    useEffect(() => {
        // Automatically proceed through phases
        const timer1 = setTimeout(() => setRevealPhase('flip'), 1500); // 1.5s waiting
        const timer2 = setTimeout(() => setRevealPhase('insight'), 3500); // reduced wait

        return () => {
            clearTimeout(timer1);
            clearTimeout(timer2);
        };
    }, []);

    const handleCapture = async () => {
        const element = document.getElementById('tarot-result-capture');
        if (!element) return;

        try {
            const dataUrl = await toPng(element, {
                backgroundColor: '#000000',
                pixelRatio: 2, // High resolution equivalent to scale: 2
                filter: (node) => {
                    // Exclude elements with the ignore data attribute
                    return !(node instanceof HTMLElement && node.hasAttribute('data-html2canvas-ignore'));
                }
            });

            const link = document.createElement('a');
            link.download = `tarot_destiny_${new Date().getTime()}.png`;
            link.href = dataUrl;
            link.click();
        } catch (error) {
            console.error('Screenshot failed:', error);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="w-full h-full pointer-events-auto overflow-hidden relative flex items-center justify-center bg-transparent"
        >
            {/* Background Atmosphere */}
            <div className="absolute inset-0 z-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-indigo-950/50 via-black to-black" />

            {/* Rune Circle */}
            <RuneCircle />

            {/* Content Container */}
            <div
                id="tarot-result-capture"
                className={`relative z-10 w-full max-w-7xl h-full flex flex-col md: flex-row items-center justify-center transition-all duration-1000 p-4 ${revealPhase === 'insight' ? 'gap-8 md:gap-16' : 'gap-0'} `}
            >

                {/* Left: Card Visual */}
                <motion.div
                    layout
                    initial={{ scale: 0.8, opacity: 0, y: 50 }}
                    animate={{
                        scale: revealPhase === 'summon' ? 1 : 1.1,
                        opacity: 1,
                        y: 0,
                    }}
                    transition={{
                        layout: { duration: 1.2, ease: [0.16, 1, 0.3, 1] },
                        scale: { duration: 0.8 }
                    }}
                    className="relative flex-shrink-0 z-20"
                    style={{ perspective: '1000px' }}
                >
                    <motion.div
                        className="relative w-[300px] h-[460px] md:w-[360px] md:h-[580px] cursor-pointer"
                        initial={{ rotateY: 180 }}
                        animate={{ rotateY: revealPhase === 'summon' ? 180 : 0 }}
                        transition={{ duration: 1.2, type: "spring", bounce: 0.15 }}
                        onClick={() => {
                            if (revealPhase === 'summon') setRevealPhase('flip');
                            if (revealPhase === 'flip') setRevealPhase('insight');
                        }}
                        style={{ transformStyle: 'preserve-3d' }}
                    >
                        {/* Front Face */}
                        <div
                            className="absolute inset-0 bg-black rounded-2xl overflow-hidden shadow-[0_0_80px_rgba(139,92,246,0.4)] border border-purple-500/50"
                            style={{ backfaceVisibility: 'hidden' }}
                        >
                            {/* Gold frame effect */}
                            <div className="absolute inset-0 border-[6px] border-double border-yellow-500/20 rounded-2xl z-20 pointer-events-none" />

                            {/* FULL HEIGHT IMAGE CONTAINER */}
                            <div className="absolute inset-0 w-full h-full">
                                <motion.img
                                    src={result.card.imageUrl}
                                    alt={result.card.name}
                                    initial={{ scale: 1.15 }} // Subtle start
                                    animate={{ scale: 1.2 }} // Subtle end
                                    transition={{ duration: 8, repeat: Infinity, repeatType: "mirror", ease: "easeInOut" }} // Slower, smoother
                                    className="w-full h-full object-cover opacity-100"
                                />
                                {/* Gradient Overlay for text readability */}
                                <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-black/30 to-transparent z-10" />
                            </div>

                            {/* TEXT OVERLAY (Bottom) */}
                            <div className="absolute bottom-0 inset-x-0 p-6 pb-10 z-20 text-center">
                                <h3 className="text-3xl font-gmarket font-bold text-white mb-2 drop-shadow-[0_2px_4px_rgba(0,0,0,0.8)]">{result.card.name}</h3>
                                <p className="text-purple-200/80 text-xs font-serif uppercase tracking-[0.3em] drop-shadow-md">{result.card.englishName}</p>
                            </div>

                            {/* Shimmer Overlay */}
                            <div className="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/10 to-white/0 translate-x-[-100%] animate-[shimmer_3s_infinite] pointer-events-none z-30" />
                        </div>

                        {/* Back Face */}
                        <div
                            className="absolute inset-0 rounded-2xl border border-white/10 shadow-2xl bg-[#1a1a2e]"
                            style={{
                                transform: 'rotateY(180deg)',
                                backgroundImage: `url(${tarotCardBack})`,
                                backgroundSize: 'cover',
                                backgroundPosition: 'center',
                                backfaceVisibility: 'hidden'
                            }}
                        >
                            {/* Pulse Glow while waiting */}
                            <div className="absolute inset-0 bg-purple-500/20 animate-pulse rounded-2xl" />
                        </div>
                    </motion.div>

                    {/* God Rays/Flash Effect on Flip */}
                    <AnimatePresence>
                        {revealPhase === 'flip' && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.5 }}
                                animate={{ opacity: [0, 1, 0], scale: 1.5, rotate: 45 }}
                                exit={{ opacity: 0 }}
                                transition={{ duration: 0.8 }}
                                className="absolute inset-0 -z-10 bg-white blur-3xl rounded-full mix-blend-overlay"
                            />
                        )}
                    </AnimatePresence>
                </motion.div>

                {/* Right: Meaning & Interpretation */}
                {revealPhase === 'insight' && (
                    <motion.div
                        initial={{ opacity: 0, x: 50, filter: 'blur(10px)' }}
                        animate={{ opacity: 1, x: 0, filter: 'blur(0px)' }}
                        transition={{ duration: 1.0, delay: 0.2 }}
                        className="flex flex-col items-center md:items-start text-center md:text-left max-w-lg z-10 w-full"
                    >
                        {/* Header Section */}
                        <div className="mb-4 relative w-full">
                            <div className="flex items-center gap-3 mb-2 md:justify-start justify-center">
                                <span className="px-2 py-0.5 bg-yellow-500/20 text-yellow-200 text-[10px] font-gmarket rounded tracking-widest border border-yellow-500/30">
                                    KEYWORD
                                </span>
                                <span className="text-purple-300/80 text-xs font-serif italic">
                                    {result.advice}
                                </span>
                            </div>

                            <h2 className="text-5xl md:text-6xl font-gmarket font-bold text-transparent bg-clip-text bg-gradient-to-br from-white via-purple-100 to-indigo-200 mb-2 drop-shadow-[0_0_30px_rgba(168,85,247,0.4)]">
                                {result.card.keyword}
                            </h2>
                        </div>

                        {/* Main Story Box */}
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5 }}
                            className="w-full bg-slate-900/60 p-6 rounded-lg backdrop-blur-md border border-white/5 mb-6 shadow-inner"
                        >
                            <p className="text-indigo-100/90 leading-7 font-serif text-sm md:text-base break-keep">
                                {result.story.split('\n').map((line, i) => (
                                    <span key={i} className="block mb-1">{line}</span>
                                ))}
                            </p>
                        </motion.div>

                        {/* 3 Columns: Love, Work, Money in compact cards */}
                        <div className="grid grid-cols-2 gap-3 w-full mb-8">
                            {/* Love Card */}
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.7 }}
                                className="col-span-2 bg-pink-900/20 border border-pink-500/20 rounded-lg p-3 flex items-start gap-3"
                            >
                                <div className="p-1.5 bg-pink-500/20 rounded-full mt-0.5">
                                    <Flame size={14} className="text-pink-300" />
                                </div>
                                <div>
                                    <h5 className="text-pink-200 text-xs font-bold font-gmarket mb-1">LOVE & HEART</h5>
                                    <p className="text-pink-100/80 text-xs font-serif leading-relaxed">{result.subAdvice.love}</p>
                                </div>
                            </motion.div>

                            {/* Work Card */}
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.8 }}
                                className="bg-blue-900/20 border border-blue-500/20 rounded-lg p-3"
                            >
                                <h5 className="text-blue-200 text-xs font-bold font-gmarket mb-1 flex items-center gap-1">
                                    <Mountain size={12} /> CAREER
                                </h5>
                                <p className="text-blue-100/80 text-[11px] font-serif leading-relaxed">{result.subAdvice.work}</p>
                            </motion.div>

                            {/* Money/Advice Card */}
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.9 }}
                                className="bg-yellow-900/20 border border-yellow-500/20 rounded-lg p-3"
                            >
                                <h5 className="text-yellow-200 text-xs font-bold font-gmarket mb-1 flex items-center gap-1">
                                    <Swords size={12} /> FORTUNE
                                </h5>
                                <p className="text-yellow-100/80 text-[11px] font-serif leading-relaxed">{result.subAdvice.money}</p>
                            </motion.div>
                        </div>

                        {/* Buttons Row */}
                        <div className="flex items-center gap-3 self-center md:self-end w-full md:w-auto" data-html2canvas-ignore>
                            {/* Share/Save Button */}
                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={handleCapture}
                                className="p-3 bg-white/10 hover:bg-white/20 text-purple-200 rounded-lg border border-purple-500/30 transition-all flex items-center justify-center"
                                title="이미지 저장"
                            >
                                <Download size={20} />
                            </motion.button>

                            <motion.button
                                whileHover={{ scale: 1.05 }}
                                whileTap={{ scale: 0.95 }}
                                onClick={onNext}
                                className="flex-1 md:flex-none px-10 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-gmarket font-bold text-sm tracking-widest uppercase rounded shadow-[0_0_20px_rgba(168,85,247,0.4)] transition-all"
                            >
                                확인 했어요!
                            </motion.button>
                        </div>
                    </motion.div>
                )}

            </div>
        </motion.div>
    );
};


const FortuneTeaserModal = ({ isOpen, onClose }: FortuneTeaserModalProps) => {
    const [stage, setStage] = useState<FortuneStage>('selection');
    const [fortune, setFortune] = useState<FortuneResult | null>(null);
    const [tarotFortune, setTarotFortune] = useState<TarotResult | null>(null);
    const [selectedGame, setSelectedGame] = useState<GameType>(null);
    const [isZooming, setIsZooming] = useState(false);
    const [showSinImage, setShowSinImage] = useState(false);
    const [isTransitioning, setIsTransitioning] = useState(false);
    const { play, stop } = useSound();

    // Obang & Tarot BGM management using global sound system
    useEffect(() => {
        // Play BGM when specific game is selected and modal isOpen
        if (isOpen) {
            if (selectedGame === 'obang') {
                // Stop the lobby BGM (WEST2) before playing Obang BGM to prevent overlap
                stop('BGM', 'WEST2');
                play('BGM', 'EAST1', { loop: true, volume: 0.3 });
            } else if (selectedGame === 'tarot') {
                // Stop the lobby BGM (WEST2) and play Tarot-specific BGM (WEST3)
                stop('BGM', 'WEST2');
                play('BGM', 'WEST3', { loop: true, volume: 0.3 });
            }
        }

        // Stop BGM and resume lobby BGM when modal closes or game changes
        return () => {
            if (selectedGame === 'obang') {
                stop('BGM', 'EAST1');
                // When leaving Obang mode, resume the lobby BGM (WEST2)
                const isAnalysisPage = window.location.pathname.startsWith('/card-reading') ||
                    window.location.pathname === '/compatibility';
                const isRootPath = window.location.pathname === '/';
                if (!isAnalysisPage && !isRootPath) {
                    play('BGM', 'WEST2', { loop: true, volume: 0.3 });
                }
            }
            if (selectedGame === 'tarot') {
                stop('BGM', 'WEST3');
                // When leaving Tarot mode, resume the lobby BGM (WEST2)
                const isAnalysisPage = window.location.pathname.startsWith('/card-reading') ||
                    window.location.pathname === '/compatibility';
                const isRootPath = window.location.pathname === '/';
                if (!isAnalysisPage && !isRootPath) {
                    play('BGM', 'WEST2', { loop: true, volume: 0.3 });
                }
            }
        };
    }, [isOpen, selectedGame, play, stop]);

    useEffect(() => {
        const handleClick = () => {
            if (selectedGame === 'tarot' || selectedGame === 'obang') {
                play('SFX', 'CLICK1');
            }
        };

        if (isOpen) {
            window.addEventListener('click', handleClick);
        }

        return () => {
            window.removeEventListener('click', handleClick);
        };
    }, [isOpen, selectedGame, play]);

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.code === 'Space') {
                // Prevent scrolling when space is pressed
                e.preventDefault();

                // Play SFX if in Tarot or Obang mode
                if (selectedGame === 'tarot' || selectedGame === 'obang') {
                    play('SFX', 'CLICK2');
                }

                // Trigger progression based on current stage
                switch (stage) {
                    case 'intro':
                        // CharacterIntroStage handles its own line index, but we might want to trigger it here
                        // However, simpler is to just let the individual stages handle their own space key
                        break;
                    case 'card':
                        // CardRevealStage: This one is tricky as it has revealState
                        break;
                    case 'level':
                        setStage('radar');
                        break;
                    case 'radar':
                        setStage('oracle');
                        break;
                    case 'oracle':
                        setStage('destiny');
                        break;
                    default:
                        break;
                }
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [stage, selectedGame, play]);

    const handleGameSelect = (game: GameType) => {
        setIsTransitioning(true);
        play('SFX', 'MAGIC_FLARE');

        // Play intro voice based on selection (Delayed 1.0s)
        setTimeout(() => {
            if (game === 'obang') {
                play('VOICE', 'SOISEOL', { subKey: 'SELECTION_INTRO' });
            } else if (game === 'tarot') {
                play('VOICE', 'STELLA', { subKey: 'INTRO' });
            }
        }, 1000);

        setTimeout(() => {
            setSelectedGame(game);
            setStage('intro');
            setTimeout(() => setIsTransitioning(false), 500);
        }, 300);
    };

    const handleIntroComplete = () => {
        if (selectedGame === 'obang') {
            setStage('obangGuide');
        } else if (selectedGame === 'tarot') {
            setStage('tarotGuide');
        } else {
            setStage('cardSelection');
        }
    };

    const handleCardReveal = () => {
        if (selectedGame === 'tarot') {
            setTarotFortune(generateTarotFortune());
            setStage('card');
        } else {
            setFortune(generateFortune());
            setStage('card');
        }
        setIsZooming(false); // Reset zooming when stage changes
        setShowSinImage(false); // Hide Sin image when reveal starts
    };



    const handleClose = () => {
        setStage('selection');
        setFortune(null);
        setTarotFortune(null);
        setSelectedGame(null);
        setIsZooming(false);
        setShowSinImage(false);
        onClose();
    };

    const handleRestart = () => {
        setStage('selection');
        setFortune(null);
        setTarotFortune(null);
        setSelectedGame(null);
        setIsZooming(false);
        setShowSinImage(false);
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm"
                        onClick={handleClose}
                    />

                    {/* Modal Container */}
                    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }} // Smooth "OutExpo" style ease
                            className={`relative w-full max-w-6xl h-[90vh] ${isZooming ? 'overflow-visible z-[100]' : 'overflow-hidden'} rounded-3xl border border-white/10 shadow-2xl bg-black/40 pointer-events-auto transition-all duration-300 scrollbar-hide`}
                        >
                            {/* Background Image Dynamic Selection */}
                            <div className="absolute inset-0 z-0 bg-black rounded-3xl overflow-hidden">
                                <AnimatePresence mode="wait">
                                    <motion.img
                                        key={stage === 'selection' ? 'intro' : selectedGame === 'obang' ? 'obang' : 'tarot'}
                                        src={
                                            stage === 'selection' ? introBackground :
                                                selectedGame === 'obang' ?
                                                    obangBackground // Unified Obang Background
                                                    : (stage === 'tarotExplain' || stage === 'cardSelection' ? tarotBg : back6)
                                        }
                                        alt="Background"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: showSinImage ? 0 : (selectedGame === 'obang' ? 1 : 0.6) }} // Hide background when Sin image is shown
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.8 }}
                                        className="w-full h-full object-cover"
                                    />
                                </AnimatePresence>
                                <div className={`absolute inset-0 transition-colors duration-700 ${showSinImage ? 'bg-black' : (selectedGame === 'obang' ? 'bg-black/80' : 'bg-gradient-to-b from-black/60 via-black/40 to-black/80')} `} />
                            </div>

                            {/* Close Button */}
                            <button
                                onClick={handleClose}
                                className="absolute top-6 right-6 z-50 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white/70 hover:text-white transition-colors"
                            >
                                <X size={24} />
                            </button>

                            {/* Sin Image Overlay-Persistent during explanation and selection */}
                            <AnimatePresence>
                                {showSinImage && (stage === 'obangExplain' || stage === 'cardSelection') && (
                                    <motion.div
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 0.7, scale: 1 }}
                                        exit={{ opacity: 0, scale: 1.1 }}
                                        transition={{ duration: 1.5 }}
                                        className="absolute inset-0 z-5 pointer-events-none flex items-center justify-center overflow-hidden"
                                    >
                                        <img
                                            src={sinImage}
                                            alt="Guardian Spirits"
                                            className="w-full h-full object-cover mix-blend-screen opacity-100 scale-125 md:scale-100"
                                        />
                                    </motion.div>
                                )}
                            </AnimatePresence>

                            {/* Content Area */}
                            <div className="relative z-10 w-full h-full flex flex-col pointer-events-none">
                                <AnimatePresence mode="wait">
                                    {stage === 'selection' && (
                                        <GameSelectionStage
                                            key="selection"
                                            onSelect={handleGameSelect}
                                        />
                                    )}
                                    {stage === 'intro' && (
                                        <CharacterIntroStage
                                            key="intro"
                                            onComplete={handleIntroComplete}
                                            selectedGame={selectedGame}
                                        />
                                    )}
                                    {stage === 'obangGuide' && (
                                        <ObangGuideStage
                                            key="obangGuide"
                                            onNext={(skipExplanation) => {
                                                if (skipExplanation) {
                                                    setStage('cardSelection');
                                                } else {
                                                    setStage('obangExplain');
                                                }
                                            }}
                                            onSwitchToTarot={() => {
                                                setSelectedGame('tarot');
                                                setStage('intro');
                                            }}
                                        />
                                    )}
                                    {stage === 'obangExplain' && (
                                        <ObangExplainStage
                                            onComplete={() => setStage('cardSelection')}
                                            onLineChange={(index) => {
                                                if (index === 1) setShowSinImage(true);
                                            }}
                                        />
                                    )}
                                    {stage === 'tarotGuide' && (
                                        <TarotGuideStage
                                            key="tarotGuide"
                                            onNext={(skipExplanation) => {
                                                if (skipExplanation) {
                                                    setStage('cardSelection');
                                                } else {
                                                    setStage('tarotExplain');
                                                }
                                            }}
                                            onSwitchToObang={() => {
                                                setSelectedGame('obang');
                                                setStage('intro');
                                            }}
                                        />
                                    )}
                                    {stage === 'tarotExplain' && (
                                        <TarotExplainStage
                                            onComplete={() => setStage('cardSelection')}
                                        />
                                    )}
                                    {stage === 'cardSelection' && (
                                        <CardSelectionStageNew
                                            key="cardSelection"
                                            onClick={handleCardReveal}
                                            selectedGame={selectedGame}
                                            onZoom={setIsZooming}
                                        />
                                    )}
                                    {stage === 'card' && (
                                        selectedGame === 'obang' && fortune ? (
                                            <CardRevealStage
                                                key="card"
                                                card={fortune.card}
                                                onNext={() => setStage('level')}
                                            />
                                        ) : selectedGame === 'tarot' && tarotFortune ? (
                                            <TarotRevealStage
                                                key="tarotCard"
                                                result={tarotFortune}
                                                onNext={() => setStage('destiny')}
                                            />
                                        ) : null
                                    )}
                                    {stage === 'level' && fortune && (
                                        <LevelRevealStage
                                            key="level"
                                            fortune={fortune}
                                            onNext={() => setStage('radar')}
                                        />
                                    )}
                                    {stage === 'radar' && fortune && (
                                        <FateRadarStage
                                            key="radar"
                                            fortune={fortune}
                                            onNext={() => setStage('oracle')}
                                        />
                                    )}
                                    {stage === 'oracle' && fortune && (
                                        <ScrollOracleStage
                                            key="oracle"
                                            fortune={fortune}
                                            onNext={() => setStage('destiny')}
                                        />
                                    )}

                                    {stage === 'destiny' && (
                                        <DestinySealStage
                                            key="destiny"
                                            onRestart={handleRestart}
                                            onClose={handleClose}
                                            selectedGame={selectedGame}
                                            onSwitchGame={handleGameSelect}
                                        />
                                    )}
                                </AnimatePresence>

                                {/* Dimension Shift Overlay */}
                                <AnimatePresence>
                                    {isTransitioning && (
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.8 }}
                                            animate={{ opacity: 1, scale: 1.5 }}
                                            exit={{ opacity: 0, scale: 2 }}
                                            transition={{ duration: 0.8 }}
                                            className="absolute inset-0 z-[100] pointer-events-none flex items-center justify-center overflow-hidden"
                                        >
                                            <div className="w-full h-full bg-white/20 backdrop-blur-sm" />
                                            <motion.div
                                                initial={{ scale: 0 }}
                                                animate={{ scale: 1 }}
                                                className="absolute w-full h-full bg-gradient-to-r from-purple-500/30 via-white/50 to-amber-500/30 blur-2xl rounded-full"
                                            />
                                        </motion.div>
                                    )}
                                </AnimatePresence>
                            </div>
                        </motion.div>
                    </div>
                </>
            )}
        </AnimatePresence>
    );
};

export default FortuneTeaserModal;

