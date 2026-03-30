import { useState, useEffect, useMemo } from 'react';
import CardSelectionStageNew from './CardSelectionStage';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Flame, Droplet, Mountain, TreeDeciduous, Swords } from 'lucide-react';
// import westStar from '../../assets/character/west-star.png';
// import eastSaju from '../../assets/character/east-saju.png';
import { getCharacterImage, CHARACTER_SETTINGS } from '../../utils/character';
const eastSaju = getCharacterImage('east', CHARACTER_SETTINGS.east, 'normal');
const westStar = getCharacterImage('west', CHARACTER_SETTINGS.west, 'normal');
import obangBackground from '../../assets/obang_card/obang_background.png';
import obangBack from '../../assets/obang_card/obang_back.jpg';
import introBackground from '../../assets/login_page/back1.jpg';
import introBackground2 from '../../assets/login_page/back2.png';
import introBackground3 from '../../assets/login_page/back3.png';
import back6 from '../../assets/login_page/back6.jpg';
import tarotBack from '../../assets/타로카드/tarot_back2.png';
import { tarotDeck, type TarotCard } from '../../data/tarotData';

interface FortuneTeaserModalProps {
    isOpen: boolean;
    onClose: () => void;
}

// Fortune stages
type FortuneStage = 'selection' | 'intro' | 'cardSelection' | 'breaking' | 'card' | 'level' | 'radar' | 'oracle' | 'inventory' | 'destiny';
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

// Fortune Cards - 오방신 카드 (5장)
const fortuneCards: FortuneCard[] = [
    {
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
    },
];


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
    const shuffled = [...tarotDeck].sort(() => 0.5 - Math.random());
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

// Tone update helper - converting to polite/soft tone
const formatDialogue = (text: string) => {
    return text.replace(/합니다\./g, '해요.')
        .replace(/입니다\./g, '이에요.')
        .replace(/세요\./g, '주세요.')
        .replace(/이다\./g, '이에요.')
        .replace(/하옵니다\./g, '해요.')
        .replace(/이옵니다\./g, '이에요.')
        .replace(/시옵소서\./g, '주세요.')
        .replace(/이라네\./g, '이에요.');
};


// Generate random fortune
const generateFortune = (): FortuneResult => {
    const selectedCard = fortuneCards[Math.floor(Math.random() * fortuneCards.length)];

    const levels = [
        { level: '대길', levelName: '大吉', color: 'from-yellow-400 via-orange-400 to-red-500', desc: '최고의 대길! 모든 일이 순조롭게 풀릴 것입니다.' },
        { level: '중길', levelName: '中吉', color: 'from-green-400 via-emerald-400 to-teal-500', desc: '좋은 운세입니다. 노력하면 좋은 결과가 있을 것입니다.' },
        { level: '소길', levelName: '小吉', color: 'from-blue-400 via-cyan-400 to-sky-500', desc: '작은 행운이 함께합니다. 긍정적인 마음가짐을 유지하세요.' },
        { level: '길', levelName: '吉', color: 'from-purple-400 via-pink-400 to-rose-500', desc: '평온한 운세입니다. 현재에 만족하며 감사하세요.' },
    ];

    const messages = [
        {
            text: '오늘은 당신에게 특별한 기회가 찾아옵니다.',
            sub: '새로운 만남이 행운을 가져올 것입니다. 열린 마음으로 사람들을 대하세요.',
            detail: '특히 오후 시간대에 중요한 인연을 만날 수 있습니다. 첫인상을 소중히 여기고, 진심을 담아 대화하세요.'
        },
        {
            text: '새로운 시작을 위한 완벽한 날입니다.',
            sub: '용기를 내어 첫 걸음을 내딛으세요. 망설임은 기회를 놓치게 합니다.',
            detail: '오래 미뤄왔던 일이 있다면 지금이 바로 시작할 때입니다. 작은 것부터 하나씩 실천해보세요.'
        },
        {
            text: '주변 사람들과의 조화가 행운을 가져옵니다.',
            sub: '감사의 마음을 표현해보세요. 작은 배려가 큰 인연을 만듭니다.',
            detail: '가족, 친구, 동료들에게 고마움을 전하세요. 당신의 진심이 더 큰 행복으로 돌아올 것입니다.'
        },
        {
            text: '인내심을 가지면 좋은 결과가 있을 것입니다.',
            sub: '시간이 당신의 편입니다. 조급해하지 말고 차근차근 나아가세요.',
            detail: '지금은 준비하고 기다리는 시기입니다. 때가 되면 자연스럽게 좋은 결과가 찾아올 것입니다.'
        },
    ];

    const advices = [
        '아침 일찍 일어나 명상이나 가벼운 산책을 해보세요. 맑은 공기와 함께 마음의 평화를 찾을 수 있습니다. 하루를 긍정적으로 시작하는 것이 행운의 시작입니다.',
        '오늘 만나는 사람들에게 진심 어린 미소를 지어보세요. 긍정적인 에너지는 전염됩니다. 당신의 밝은 기운이 주변을 변화시킬 것입니다.',
        '중요한 결정은 오후 2시에서 5시 사이에 내리는 것이 좋습니다. 이 시간대에는 직관이 가장 예리해집니다. 마음의 소리에 귀 기울이세요.',
        '가족이나 오랜 친구에게 연락해보세요. 소중한 인연이 행운의 열쇠가 됩니다. 때로는 가까운 사람들의 조언이 가장 큰 도움이 됩니다.',
        '오늘 하루는 감사 일기를 써보세요. 작은 것에도 감사하는 마음이 더 큰 행운을 불러옵니다. 긍정적인 마음가짐이 운을 바꿉니다.',
    ];

    const colors = [
        { name: '붉은색', hex: '#EF4444', meaning: '열정과 활력을 상징합니다' },
        { name: '황금색', hex: '#F59E0B', meaning: '풍요와 번영을 의미합니다' },
        { name: '남색', hex: '#3B82F6', meaning: '지혜와 평온을 나타냅니다' },
        { name: '보라색', hex: '#A855F7', meaning: '고귀함과 영성을 뜻합니다' },
        { name: '초록색', hex: '#10B981', meaning: '성장과 조화를 상징합니다' },
    ];

    const items = [
        { name: '붉은 실', meaning: '인연을 이어주는 힘' },
        { name: '은빛 열쇠', meaning: '새로운 기회의 문' },
        { name: '작은 거울', meaning: '자기 성찰과 깨달음' },
        { name: '백옥 구슬', meaning: '순수함과 행운' },
        { name: '금색 동전', meaning: '재물과 풍요' },
        { name: '나침반', meaning: '올바른 방향 제시' },
    ];

    const directions = [
        { name: '동쪽', meaning: '새로운 시작과 희망' },
        { name: '서쪽', meaning: '결실과 완성' },
        { name: '남쪽', meaning: '열정과 성공' },
        { name: '북쪽', meaning: '지혜와 안정' },
    ];

    const times = [
        { name: '새벽 (5-7시)', meaning: '맑은 기운이 가득한 시간' },
        { name: '아침 (7-9시)', meaning: '활력이 넘치는 시간' },
        { name: '오전 (9-12시)', meaning: '집중력이 높은 시간' },
        { name: '오후 (12-15시)', meaning: '직관이 예리한 시간' },
        { name: '저녁 (18-21시)', meaning: '여유로운 성찰의 시간' },
    ];

    const guardians = [
        '해치 (Haechi)', '삼족오 (Samjoko)', '기린 (Kirin)', '백록 (White Deer)', '비익조 (Biikjo)'
    ];

    const actions = [
        '따뜻한 차 한 잔 마시기', '동쪽 하늘 바라보기', '오전 산책하기', '옛 친구에게 연락하기', '방 정리하기'
    ];

    const selectedLevel = levels[Math.floor(Math.random() * levels.length)];
    const selectedColor = colors[Math.floor(Math.random() * colors.length)];
    const selectedMessage = messages[Math.floor(Math.random() * messages.length)];
    const selectedItem = items[Math.floor(Math.random() * items.length)];
    const selectedDirection = directions[Math.floor(Math.random() * directions.length)];
    const selectedTime = times[Math.floor(Math.random() * times.length)];

    return {
        card: selectedCard,
        level: selectedLevel.level,
        levelName: selectedLevel.levelName,
        levelColor: selectedLevel.color,
        message: selectedMessage.text,
        advice: formatDialogue(advices[Math.floor(Math.random() * advices.length)]),
        categories: {
            wood: 50 + Math.floor(Math.random() * 50),
            fire: 50 + Math.floor(Math.random() * 50),
            earth: 50 + Math.floor(Math.random() * 50),
            metal: 50 + Math.floor(Math.random() * 50),
            water: 50 + Math.floor(Math.random() * 50),
        },
        lucky: {
            color: selectedColor.name,
            colorHex: selectedColor.hex,
            number: Math.floor(Math.random() * 99) + 1,
            direction: selectedDirection.name,
            item: selectedItem.name,
            time: selectedTime.name,
            guardian: guardians[Math.floor(Math.random() * guardians.length)],
            action: actions[Math.floor(Math.random() * actions.length)],
        },
    };
};

const FortuneTeaserModal = ({ isOpen, onClose }: FortuneTeaserModalProps) => {
    const [stage, setStage] = useState<FortuneStage>('selection');
    const [fortune, setFortune] = useState<FortuneResult | null>(null);
    const [tarotFortune, setTarotFortune] = useState<TarotResult | null>(null);
    const [selectedGame, setSelectedGame] = useState<GameType>(null);
    const [isZooming, setIsZooming] = useState(false);

    const handleGameSelect = (game: GameType) => {
        setSelectedGame(game);
        setStage('intro');
    };

    const handleIntroComplete = () => {
        setStage('cardSelection');
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
    };



    const handleClose = () => {
        setStage('selection');
        setFortune(null);
        setTarotFortune(null);
        setSelectedGame(null);
        setIsZooming(false);
        onClose();
    };

    const handleRestart = () => {
        setStage('selection');
        setFortune(null);
        setTarotFortune(null);
        setSelectedGame(null);
        setIsZooming(false);
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
                            className={`relative w-full max-w-6xl h-[90vh] ${isZooming ? 'overflow-visible z-[100]' : 'overflow-hidden'} rounded-3xl border border-white/10 shadow-2xl bg-black/40 pointer-events-auto transition-all duration-300`}
                        >
                            {/* Background Image Dynamic Selection */}
                            <div className="absolute inset-0 z-0 bg-black rounded-3xl overflow-hidden">
                                <AnimatePresence mode="wait">
                                    <motion.img
                                        key={stage === 'selection' ? 'intro' : selectedGame === 'obang' ? 'obang' : 'tarot'}
                                        src={
                                            stage === 'selection' ? introBackground :
                                                selectedGame === 'obang' ?
                                                    (stage === 'intro' ? introBackground2 : obangBackground)
                                                    : back6 // Global Tarot Background (Intro + Stages)
                                        }
                                        alt="Background"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: selectedGame === 'obang' ? 1 : 0.6 }} // Adjusted opacity for Tarot readability
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.8 }}
                                        className="w-full h-full object-cover"
                                    />
                                </AnimatePresence>
                                <div className={`absolute inset-0 ${selectedGame === 'obang' ? 'bg-black/40' : 'bg-gradient-to-b from-black/60 via-black/40 to-black/80'}`} />
                            </div>

                            {/* Close Button */}
                            <button
                                onClick={handleClose}
                                className="absolute top-6 right-6 z-50 p-2 rounded-full bg-white/10 hover:bg-white/20 text-white/70 hover:text-white transition-colors"
                            >
                                <X size={24} />
                            </button>

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
                                            onNext={() => setStage('inventory')}
                                        />
                                    )}
                                    {stage === 'inventory' && fortune && (
                                        <TalismanInventoryStage
                                            key="inventory"
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
                                        />
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

// Character Intro Stage Component
const CharacterIntroStage = ({ onComplete, selectedGame }: { onComplete: () => void; selectedGame: GameType }) => {
    const [currentLineIndex, setCurrentLineIndex] = useState(0);
    const [typedText, setTypedText] = useState('');
    const [isTyping, setIsTyping] = useState(true);

    const isObang = selectedGame === 'obang';

    const dialogueLines = useMemo(() => isObang ? [
        "반가워요... 저는 오방신의 무녀, 소이설이라고 해요.",
        "당신이 이곳에 이끌린 건 단순한 우연이 아니랍니다.",
        "오방의 신비로운 기운이 당신을 감싸고 있군요...",
        "자, 이제 당신의 운명을 점쳐보도록 할까요?"
    ] : [
        "어서오세요, 별을 읽는 점성술사 스텔라입니다.",
        "카드는 당신의 과거와 현재, 그리고 미래를 비추는 거울이죠.",
        "당신의 직감을 믿고 마음을 열어보세요.",
        "별들이 속삭이는 당신의 운명을 들어볼까요?"
    ], [isObang]);

    useEffect(() => {
        setTypedText('');
        setIsTyping(true);
        let i = 0;
        const currentText = dialogueLines[currentLineIndex];

        const typingInterval = setInterval(() => {
            if (i < currentText.length) {
                setTypedText(currentText.substring(0, i + 1));
                i++;
            } else {
                clearInterval(typingInterval);
                setIsTyping(false);
            }
        }, 50);

        return () => clearInterval(typingInterval);
    }, [currentLineIndex, dialogueLines]);

    const handleNext = () => {
        if (isTyping) {
            setTypedText(dialogueLines[currentLineIndex]);
            setIsTyping(false);
        } else {
            if (currentLineIndex < dialogueLines.length - 1) {
                setCurrentLineIndex(prev => prev + 1);
            } else {
                onComplete();
            }
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-transparent cursor-pointer pointer-events-auto"
            onClick={handleNext}
        >
            {/* Background Image with Overlay */}
            <div className={`absolute inset-0 z-0 ${isObang ? 'bg-[#1a1510]' : 'bg-black'}`}>
                <img
                    src={isObang ? introBackground2 : back6}
                    alt="Intro Background"
                    className={`w-full h-full object-cover ${isObang ? 'opacity-100' : 'opacity-50'}`}
                />
                <div className={`absolute inset-0 ${isObang ? 'bg-black/50' : 'bg-purple-900/20 mix-blend-overlay'}`} />
            </div>

            <div className="relative w-full max-w-4xl h-full max-h-[90vh] flex items-end justify-center pb-10 z-10">
                {/* Character Image */}
                <motion.div
                    initial={{ x: 100, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: -100, opacity: 0 }}
                    transition={{ type: 'spring', damping: 20, stiffness: 100 }}
                    className="absolute bottom-0 right-0 md:right-20 w-[80vh] h-[80vh] z-10 pointer-events-none"
                >
                    <img
                        src={isObang ? eastSaju : westStar}
                        alt={isObang ? "East Saju" : "West Star"}
                        className={`w-full h-full object-contain object-bottom drop-shadow-[0_0_50px_rgba(255,255,255,0.1)] translate-x-10 md:translate-x-20 ${!isObang && 'scale-110 origin-bottom'}`}
                    />
                </motion.div>

                {/* Speech Bubble / Dialogue Box */}
                <motion.div
                    key={currentLineIndex}
                    initial={{ y: 20, opacity: 0, scale: 0.95 }}
                    animate={{ y: 0, opacity: 1, scale: 1 }}
                    transition={{ duration: 0.3 }}
                    className={`relative z-20 mb-20 md:mb-32 mr-auto md:ml-10 border p-8 rounded-tr-3xl rounded-bl-3xl rounded-tl-lg rounded-br-lg shadow-2xl max-w-xl min-w-[320px] ${isObang
                        ? 'bg-[#f4efe4]/95 border-stone-800/20 text-stone-900 shadow-stone-900/20'
                        : 'bg-slate-900/90 border-purple-500/30 text-white shadow-purple-900/30 backdrop-blur-md'
                        }`}
                >
                    <div className={`absolute -left-2 top-10 w-4 h-4 transform rotate-45 border-t border-l ${isObang ? 'bg-[#f4efe4] border-stone-800/20' : 'bg-slate-900 border-purple-500/30'
                        }`} />

                    <div className="mb-4 flex items-center gap-2">
                        <div className={`px-3 py-1 border rounded-full ${isObang ? 'bg-stone-800/10 border-stone-800/20' : 'bg-purple-500/20 border-purple-500/40'
                            }`}>
                            <h3 className={`text-sm font-bold tracking-widest uppercase ${isObang ? 'text-stone-800 font-["JoseonPalace"]' : 'text-purple-300 font-serif'
                                }`}>{isObang ? '소이설' : '스텔라'}</h3>
                        </div>
                        <div className={`h-[1px] flex-1 bg-gradient-to-r to-transparent ${isObang ? 'from-stone-800/20' : 'from-purple-500/40'
                            }`} />
                    </div>

                    <p className={`text-xl md:text-2xl leading-relaxed whitespace-pre-line break-keep min-h-[4rem] ${isObang ? 'font-["JoseonPalace"] text-stone-800' : 'font-serif text-slate-100'
                        }`}>
                        {typedText}
                        {isTyping && (
                            <span className={`inline-block w-2 H-5 ml-1 animate-pulse ${isObang ? 'bg-stone-800' : 'bg-purple-400'
                                }`}>|</span>
                        )}
                    </p>

                    <div className="absolute bottom-4 right-6 flex gap-1">
                        <span className="text-white/30 text-xs animate-pulse">
                            {currentLineIndex < dialogueLines.length - 1 ? "▼ 클릭하여 계속" : "▶ 시작하기"}
                        </span>
                    </div>
                </motion.div>
            </div>

            {/* Skip Button - Minimalist & Sophisticated */}
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    onComplete();
                }}
                className="absolute top-8 right-8 z-50 text-white/30 hover:text-white text-xs tracking-[0.3em] font-light uppercase transition-all duration-300 flex items-center gap-2 group hover:scale-105"
            >
                SKIP
                <span className="w-8 h-[1px] bg-white/30 group-hover:bg-white transition-colors" />
            </button>
        </motion.div >
    );
};


const GameSelectionStage = ({ onSelect }: { onSelect: (game: GameType) => void }) => (
    <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 w-full h-full flex flex-col md:flex-row bg-black overflow-hidden pointer-events-auto"
    >


        {/* Tarot Section (Left) - Western Dark Theme */}
        <motion.div
            className="relative flex-1 h-full cursor-pointer group overflow-hidden border-r border-white/10"
            onClick={() => onSelect('tarot')}
            whileHover={{ flex: 1.3 }}
            transition={{ type: "spring", stiffness: 150, damping: 25 }}
        >
            {/* Background Image */}
            <div className="absolute inset-0 flex items-end justify-center">
                <img
                    src={westStar}
                    alt="Tarot BG"
                    className="w-full h-full object-cover object-top opacity-60 group-hover:opacity-80 group-hover:scale-105 transition-all duration-700 grayscale group-hover:grayscale-0"
                />
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-indigo-950/90 via-indigo-900/40 to-black/60 group-hover:opacity-60 transition-opacity duration-500" />

            {/* Content */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pt-20 z-10 transition-transform duration-500 group-hover:translate-y-[-20px]">
                <div className="w-24 h-24 mb-6 rounded-full bg-white/5 border border-white/10 backdrop-blur-md flex items-center justify-center group-hover:scale-110 group-hover:border-indigo-400/50 transition-all duration-300 shadow-[0_0_30px_rgba(79,70,229,0.2)]">
                    <img src={westStar} alt="Tarot Icon" className="w-14 h-14 object-contain drop-shadow-lg" />
                </div>

                <h3 className="text-5xl md:text-6xl font-black text-white mb-2 font-serif tracking-wide group-hover:text-indigo-200 transition-colors drop-shadow-xl">TAROT</h3>
                <p className="text-indigo-200/80 text-lg tracking-[0.2em] font-light mb-8">서양의 신비 타로</p>

                <div className="px-8 py-3 border border-indigo-400/30 bg-indigo-900/30 rounded-full text-sm text-indigo-100/80 tracking-widest uppercase backdrop-blur-sm group-hover:bg-indigo-500 group-hover:text-white group-hover:border-indigo-400 transition-all shadow-lg font-serif">
                    운명 엿보기
                </div>
            </div>

            {/* Hover Effects - Purple Mist & Sparkles */}
            <div className="absolute inset-0 bg-indigo-600/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none mix-blend-screen">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(79,70,229,0.15)_0%,_transparent_70%)] animate-pulse" />
                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] opacity-30 animate-[shimmer_10s_linear_infinite]" />
            </div>
            <div className="absolute inset-0 shadow-[inset_0_0_100px_rgba(79,70,229,0.2)] opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
        </motion.div>

        {/* Divider Line (Center) */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-20 h-full w-[1px] bg-white/20 hidden md:block" />

        {/* VS Text */}
        <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-20 pointer-events-none mix-blend-difference opacity-50 hidden md:block">
            <span className="text-white/40 font-serif italic text-4xl">or</span>
        </div>

        {/* Obang Section (Right) - Eastern Hanji Theme */}
        <motion.div
            className="relative flex-1 h-full cursor-pointer group overflow-hidden border-l border-white/10 bg-[#f4efe4]"
            onClick={() => onSelect('obang')}
            whileHover={{ flex: 1.3 }}
            transition={{ type: "spring", stiffness: 150, damping: 25 }}
        >
            {/* Background Texture (Paper) */}
            <div className="absolute inset-0 opacity-40 bg-[url('https://www.transparenttextures.com/patterns/clean-gray-paper.png')] pointer-events-none" />

            {/* Background Image - Ink Style */}
            <div className="absolute inset-0 flex items-end justify-center">
                <img
                    src={eastSaju}
                    alt="Obang BG"
                    className="w-full h-full object-cover object-top opacity-20 mix-blend-multiply group-hover:opacity-40 group-hover:scale-105 transition-all duration-700 grayscale group-hover:grayscale-0"
                />
            </div>
            {/* Vignette for Hanji feel */}
            <div className="absolute inset-0 bg-gradient-to-t from-stone-400/20 via-transparent to-transparent opacity-50" />

            {/* Content */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pt-20 z-10 transition-transform duration-500 group-hover:translate-y-[-20px]">
                {/* Icon Container - Dark Ink Style */}
                <div className="w-24 h-24 mb-6 rounded-full bg-stone-900/5 border border-stone-900/10 backdrop-blur-sm flex items-center justify-center group-hover:scale-110 group-hover:border-stone-800/30 transition-all duration-300 shadow-xl">
                    <img src={eastSaju} alt="Obang Icon" className="w-14 h-14 object-contain drop-shadow-md opacity-80 mix-blend-multiply" />
                </div>

                {/* Text - Dark Calligraphy Style */}
                <h3 className="text-5xl md:text-6xl font-black text-stone-800 mb-2 font-['Hahmlet'] tracking-wide group-hover:text-black transition-colors drop-shadow-sm">五方神占</h3>
                <p className="text-stone-600/80 text-lg tracking-[0.2em] font-light mb-8 font-['Hahmlet']">동양의 신비 오방</p>

                {/* Button - Stamp Style */}
                <div className="px-8 py-3 border border-stone-800/40 bg-white/40 rounded-full text-sm text-stone-800 tracking-widest uppercase backdrop-blur-sm group-hover:bg-stone-800 group-hover:text-amber-50 group-hover:border-stone-900 transition-all shadow-md group-hover:shadow-xl font-['Hahmlet']">
                    천명(天命) 확인
                </div>
            </div>

            {/* Hover Effects - Golden Mist & Hanji Texture */}
            <div className="absolute inset-0 bg-amber-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700 pointer-events-none">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(212,175,55,0.1)_0%,_transparent_70%)]" />
                <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-transparent via-[#D4AF37]/5 to-transparent animate-pulse" />
            </div>
            <div className="absolute inset-0 shadow-[inset_0_0_100px_rgba(212,175,55,0.1)] opacity-0 group-hover:opacity-100 transition-opacity duration-1000" />
        </motion.div>

        {/* Title Overlay - Stays on top of everything */}
        <div className="absolute top-10 left-0 w-full z-50 pointer-events-none flex flex-col items-center justify-center mix-blend-difference">
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
    </motion.div>
);





const CardRevealStage = ({ card, onNext }: { card: FortuneCard; onNext: () => void }) => {
    const [revealState, setRevealState] = useState<'hook' | 'reveal' | 'reading'>('hook');

    useEffect(() => {
        // Sequence: Hook -> Reveal Card -> Show Reading/Actions
        const timer1 = setTimeout(() => setRevealState('reveal'), 2500);
        const timer2 = setTimeout(() => setRevealState('reading'), 5000); // Allow time for card animation
        return () => { clearTimeout(timer1); clearTimeout(timer2); };
    }, []);

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center w-full h-full relative z-20 pointer-events-none"
        >
            <AnimatePresence mode="wait">
                {revealState === 'hook' && (
                    <motion.div
                        key="hook"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="absolute inset-0 flex items-center justify-center z-50 pointer-events-none"
                    >
                        {/* Dynamic Flash Effect */}
                        <motion.div
                            initial={{ scale: 0, opacity: 0, rotate: 0 }}
                            animate={{
                                scale: [0, 20, 30],
                                opacity: [0, 1, 0],
                                rotate: 180
                            }}
                            transition={{ duration: 1.5, ease: "easeOut" }}
                            className="w-40 h-40 bg-gradient-radial from-white via-amber-200 to-transparent rounded-full blur-xl"
                        />
                        <motion.div
                            initial={{ scale: 0, opacity: 0 }}
                            animate={{ scale: [1, 1.5, 2], opacity: [0, 0.8, 0] }}
                            transition={{ duration: 0.5, delay: 0.2 }}
                            className="absolute inset-0 bg-white mix-blend-overlay"
                        />
                    </motion.div>
                )}
            </AnimatePresence>

            <motion.div
                animate={{
                    y: revealState === 'hook' ? 100 : 0,
                    opacity: revealState === 'hook' ? 0 : 1,
                    scale: revealState === 'reading' ? 0.9 : 1
                }}
                transition={{ duration: 1, type: "spring" }}
                className="relative flex flex-col items-center"
            >
                {/* Card Name */}
                <motion.div
                    initial={{ opacity: 0, y: -20 }}
                    animate={{ opacity: revealState !== 'hook' ? 1 : 0, y: revealState !== 'hook' ? 0 : -20 }}
                    transition={{ delay: 0.5 }}
                    className="mb-8 text-center"
                >
                    <div className="flex items-center justify-center gap-4 mb-2">
                        <span className="h-[1px] w-12 bg-amber-400/50" />
                        <span className="text-amber-400 tracking-[0.2em] text-sm font-bold uppercase font-['JoseonPalace']">{card.element}</span>
                        <span className="h-[1px] w-12 bg-amber-400/50" />
                    </div>
                    <h2 className="text-4xl md:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-b from-white via-white to-gray-400 drop-shadow-[0_0_20px_rgba(255,255,255,0.4)] font-['JoseonPalace']">
                        {card.name}
                    </h2>
                </motion.div>

                {/* Card Object - 3D Flip */}
                <div className="relative group perspective-1000">
                    <motion.div
                        initial={{ rotateY: 180, scale: 0.5 }}
                        animate={{
                            rotateY: revealState !== 'hook' ? 0 : 180,
                            scale: revealState === 'reading' ? 0.9 : 1
                        }}
                        transition={{ duration: 1.5, type: "spring", stiffness: 60, damping: 12 }}
                        className="relative w-[300px] h-[450px] bg-[#0a0a0a] rounded-[2rem] p-2 shadow-[0_0_50px_rgba(0,0,0,0.5)] border border-white/10 ring-1 ring-white/5"
                    >
                        {/* Inner Gold Border */}
                        <div className="absolute inset-4 rounded-[1.5rem] border border-amber-500/30 z-20" />
                        <div className="absolute inset-4 rounded-[1.5rem] border border-white/5 z-20 scale-[0.98]" />

                        {/* Card Content */}
                        <div className="w-full h-full rounded-[1.8rem] overflow-hidden relative bg-[#0a0a0a]">
                            <img
                                src={card.imageUrl}
                                alt={card.name}
                                className="w-full h-full object-cover opacity-80 group-hover:scale-110 transition-transform duration-700"
                            />
                            <div className={`absolute inset-0 bg-gradient-to-t ${card.bgGradient} opacity-40 mix-blend-overlay`} />
                            <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-black/90" />
                        </div>

                        {/* Floating Element Icon */}
                        <motion.div
                            initial={{ y: 0 }}
                            animate={{ y: [-10, 10, -10] }}
                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute -top-6 -right-6 w-20 h-20 bg-gradient-to-br from-stone-800 to-black rounded-full border border-white/10 shadow-2xl flex items-center justify-center z-30"
                        >
                            <card.elementIcon className="w-10 h-10 text-white drop-shadow-[0_0_10px_rgba(255,255,255,0.5)]" />
                        </motion.div>
                    </motion.div>
                </div>
            </motion.div>

            {/* Character Reading Dialogue */}
            <AnimatePresence>
                {revealState === 'reading' && (
                    <motion.div
                        initial={{ opacity: 0, y: 50 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        className="fixed bottom-0 md:bottom-12 left-0 right-0 z-50 p-4 flex justify-center pointer-events-auto"
                    >
                        <div className="w-full max-w-4xl bg-[#f8f4ed] border-2 border-stone-800/20 rounded-xl p-2 shadow-2xl relative overflow-hidden">
                            {/* Decorative Corner */}
                            <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-stone-800/40 rounded-tl-lg" />
                            <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-stone-800/40 rounded-tr-lg" />
                            <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-stone-800/40 rounded-bl-lg" />
                            <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-stone-800/40 rounded-br-lg" />

                            {/* Inner Content with Texture */}
                            <div className="bg-[#f8f4ed] border border-stone-800/10 rounded-lg p-6 md:p-8 flex flex-col md:flex-row items-center gap-8 relative">
                                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/clean-gray-paper.png')] opacity-50 mix-blend-multiply pointer-events-none" />

                                {/* Avatar: So Yi-seol Traditional Frame */}
                                <div className="relative shrink-0">
                                    <div className="w-24 h-24 rounded-full border-4 border-double border-stone-800/20 overflow-hidden shadow-lg bg-[#e8e4d9]">
                                        <img src={eastSaju} alt="So Yi-seol" className="w-full h-full object-cover object-top scale-110 translate-y-2 opacity-80 mix-blend-multiply" />
                                    </div>
                                    <div className="absolute -bottom-3 left-1/2 -translate-x-1/2 bg-stone-800 text-amber-50 text-xs font-bold px-3 py-1 rounded-full font-['JoseonPalace'] shadow-md whitespace-nowrap border border-amber-900/50">
                                        소이설
                                    </div>
                                </div>

                                <div className="flex-1 space-y-3 text-center md:text-left relative z-10">
                                    <p className="text-stone-800 leading-loose text-xl font-medium break-keep font-['JoseonPalace'] drop-shadow-sm">
                                        "{card.reading}"
                                    </p>
                                </div>

                                <motion.button
                                    whileHover={{ scale: 1.05 }}
                                    whileTap={{ scale: 0.95 }}
                                    onClick={onNext}
                                    className="px-10 py-3 bg-stone-800 text-amber-50 font-bold text-lg rounded-lg hover:bg-stone-900 transition-colors shadow-lg shrink-0 font-['JoseonPalace'] relative group overflow-hidden border border-amber-500/20"
                                >
                                    <div className="absolute inset-0 bg-white/10 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                                    <span className="relative z-10">결과 확인하기</span>
                                </motion.button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
};

// Level Reveal Stage - Premium Ethereal Bloom
const LevelRevealStage = ({ fortune, onNext }: { fortune: FortuneResult; onNext: () => void }) => {
    return (
        <motion.div
            className="flex flex-col items-center justify-center w-full h-full relative z-20 pointer-events-auto cursor-pointer p-4 overflow-hidden"
            onClick={onNext}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, transition: { duration: 0.5 } }}
        >
            {/* Background Atmosphere - Animated Gradient/Fog */}
            <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 60, repeat: Infinity, ease: "linear" }}
                className="absolute inset-[-50%] bg-[radial-gradient(circle_at_center,_rgba(251,191,36,0.05)_0%,_transparent_60%)] z-0"
            />

            {/* Main Rank Text - Ethereal Bloom */}
            <div className="relative z-10">
                <motion.div
                    initial={{ scale: 0.8, opacity: 0, filter: "blur(20px)" }}
                    animate={{ scale: 1, opacity: 1, filter: "blur(0px)" }}
                    transition={{ duration: 1.5, ease: "easeOut" }}
                    className="relative"
                >
                    <h1 className={`text-[6rem] md:text-[10rem] font-black leading-none tracking-tighter font-['JoseonPalace'] text-transparent bg-clip-text bg-gradient-to-b ${fortune.levelColor} drop-shadow-[0_0_80px_rgba(251,191,36,0.4)]`}
                        style={{ WebkitTextStroke: '1px rgba(255,255,255,0.1)' }}
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

            {/* Subtext - Smooth Slide Up */}
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 1 }}
                className="mt-12 text-center space-y-6 max-w-lg z-10"
            >
                <div className="flex items-center justify-center gap-4">
                    <span className="h-[1px] w-8 bg-gradient-to-r from-transparent to-amber-500/50" />
                    <h2 className="text-xl md:text-2xl text-amber-100 font-['JoseonPalace'] tracking-[0.2em] uppercase">{fortune.level}</h2>
                    <span className="h-[1px] w-8 bg-gradient-to-l from-transparent to-amber-500/50" />
                </div>

                <p className="text-white/80 text-lg font-light leading-relaxed break-keep drop-shadow-md font-['JoseonPalace']">
                    {fortune.card.blessing}
                </p>

                <div className="pt-8">
                    <span className="text-white/30 text-xs tracking-[0.3em] font-light animate-pulse uppercase">
                        화면을 터치하여 계속하기
                    </span>
                </div>
            </motion.div>
        </motion.div>
    );
};

// Fate Radar Stage - Constellation Style (Refined Layout & Aura)
const FateRadarStage = ({ fortune, onNext }: { fortune: FortuneResult; onNext: () => void }) => {
    // 5 Elements Data
    const stats = [
        { label: '목(木)', value: fortune.categories.wood, key: 'wood' },
        { label: '화(火)', value: fortune.categories.fire, key: 'fire' },
        { label: '토(土)', value: fortune.categories.earth, key: 'earth' },
        { label: '금(金)', value: fortune.categories.metal, key: 'metal' },
        { label: '수(水)', value: fortune.categories.water, key: 'water' },
    ];

    const maxStat = stats.reduce((prev, current) => (prev.value > current.value) ? prev : current);

    // Calculate Pentagon Points
    const size = 120; // Reduced slightly to ensure no overlap
    const center = 200;
    const points = stats.map((stat, i) => {
        const angle = (Math.PI * 2 * i) / 5 - Math.PI / 2;
        const valueRatio = stat.value / 100;
        return {
            x: center + Math.cos(angle) * size * valueRatio,
            y: center + Math.sin(angle) * size * valueRatio,
            fullX: center + Math.cos(angle) * size,
            fullY: center + Math.sin(angle) * size,
            labelX: center + Math.cos(angle) * (size + 40),
            labelY: center + Math.sin(angle) * (size + 40),
            angle: angle // Store angle for calculating aura rotation or effects
        };
    });

    const pathData = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x},${p.y}`).join(' ') + ' Z';

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center w-full h-full pointer-events-auto overflow-hidden pt-10" // Added pt-10 and removed justify-center to bias content upwards
        >
            <motion.h3
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-200 to-amber-500 mb-1 font-['JoseonPalace'] text-center"
            >
                오행 분석 (五行分析)
            </motion.h3>
            <p className="text-white/40 text-[10px] font-light tracking-[0.5em] uppercase font-['JoseonPalace']">당신의 기운</p>

            <div className="relative w-[400px] h-[400px] flex items-center justify-center mt-2 mb-4 shrink-0">
                <svg width="400" height="400" className="overflow-visible" viewBox="0 0 400 400">
                    <defs>
                        <filter id="glow-line" x="-50%" y="-50%" width="200%" height="200%">
                            <feGaussianBlur stdDeviation="2" result="coloredBlur" />
                            <feMerge>
                                <feMergeNode in="coloredBlur" />
                                <feMergeNode in="SourceGraphic" />
                            </feMerge>
                        </filter>
                        {/* Aura Filter */}
                        <radialGradient id="auraGradient">
                            <stop offset="0%" stopColor="#fbbf24" stopOpacity="0.6" />
                            <stop offset="50%" stopColor="#fbbf24" stopOpacity="0.2" />
                            <stop offset="100%" stopColor="transparent" stopOpacity="0" />
                        </radialGradient>
                    </defs>

                    {/* Background Grid - Very faint */}
                    {[1, 0.6].map((scale, i) => {
                        const scaledPoints = stats.map((_, idx) => {
                            const angle = (Math.PI * 2 * idx) / 5 - Math.PI / 2;
                            const r = size * scale;
                            return `${center + Math.cos(angle) * r},${center + Math.sin(angle) * r}`;
                        }).join(' ');
                        return (
                            <g key={i}>
                                <polygon
                                    points={scaledPoints}
                                    fill="none"
                                    stroke="rgba(255,255,255,0.05)"
                                    strokeWidth="1"
                                />
                            </g>
                        );
                    })}

                    {/* Guide Lines */}
                    <g>
                        {points.map((p, i) => (
                            <line
                                key={i}
                                x1={center}
                                y1={center}
                                x2={p.fullX}
                                y2={p.fullY}
                                stroke="rgba(255,255,255,0.05)"
                                strokeWidth="1"
                            />
                        ))}

                        {/* Data Path - Glowing Constellation */}
                        <motion.path
                            d={pathData}
                            fill="rgba(251, 191, 36, 0.1)"
                            stroke="#fbbf24"
                            strokeWidth="2"
                            filter="url(#glow-line)"
                            initial={{ pathLength: 0, fillOpacity: 0 }}
                            animate={{ pathLength: 1, fillOpacity: 0.1 }}
                            transition={{ duration: 2, ease: "easeInOut" }}
                        />

                        {/* Star Nodes */}
                        {points.map((p, i) => {
                            const isMax = stats[i].value === maxStat.value;
                            return (
                                <motion.g
                                    key={i}
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ delay: 1.5 + i * 0.1 }}
                                >
                                    {/* Aura for Max Stat - Pulsing Glow */}
                                    {isMax && (
                                        <>
                                            {/* Inner Glow */}
                                            <motion.circle
                                                cx={p.x}
                                                cy={p.y}
                                                r="8"
                                                fill="#fbbf24"
                                                initial={{ opacity: 0 }}
                                                animate={{ opacity: [0.2, 0.6, 0.2] }}
                                                transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
                                                filter="url(#glow-line)"
                                            />
                                            {/* Expanding Ring Ripple */}
                                            <motion.circle
                                                cx={p.x}
                                                cy={p.y}
                                                r="8"
                                                fill="transparent"
                                                stroke="#fbbf24"
                                                strokeWidth="1"
                                                initial={{ opacity: 0.8, scale: 1 }}
                                                animate={{ opacity: 0, scale: 3 }}
                                                transition={{ duration: 2, repeat: Infinity, ease: "easeOut" }}
                                            />
                                        </>
                                    )}

                                    <circle cx={p.x} cy={p.y} r={isMax ? "4" : "3"} fill="#fff" />
                                    <circle cx={p.x} cy={p.y} r={isMax ? "8" : "6"} stroke={isMax ? "#fbbf24" : "#fbbf24"} strokeWidth="1" strokeOpacity="0.5" />
                                </motion.g>
                            );
                        })}

                        {/* Labels - Better positioning */}
                        {stats.map((stat, i) => {
                            const p = points[i];
                            const isMax = stat.value === maxStat.value;
                            return (
                                <foreignObject key={i} x={p.labelX - 40} y={p.labelY - 20} width="80" height="45">
                                    <motion.div
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        transition={{ delay: 1 + i * 0.1 }}
                                        className={`flex flex-col items-center justify-center h-full ${isMax ? 'scale-110' : 'opacity-60'}`}
                                    >
                                        <div className={`text-xs font-['JoseonPalace'] font-bold ${isMax ? 'text-amber-300 drop-shadow-[0_0_8px_rgba(251,191,36,0.8)]' : 'text-stone-400'}`}>
                                            {stat.label}
                                        </div>
                                        <div className="text-[10px] text-white/50 font-mono tracking-tighter mt-0.5">
                                            {stat.value}
                                        </div>
                                    </motion.div>
                                </foreignObject>
                            );
                        })}
                    </g>
                </svg>
            </div>

            {/* So Yi-seol Dialogue - Bottom Fixed with Margin */}
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 2 }}
                className="mt-auto mb-6 w-full max-w-lg px-6 relative z-10 pointer-events-none" // Changed absolute bottom scaling to flex alignment
            >
                <div className="bg-[#1a1919]/90 border border-amber-500/20 rounded-xl p-5 flex gap-5 shadow-lg backdrop-blur-md pointer-events-auto">
                    <div className="flex flex-col items-center gap-2 shrink-0">
                        <div className="w-12 h-12 rounded-full bg-stone-800 border border-white/10 overflow-hidden shadow-inner">
                            <img src={eastSaju} alt="So Yi-seol" className="w-full h-full object-cover object-top scale-125 translate-y-1" />
                        </div>
                        <h4 className="text-amber-500/80 text-sm font-bold tracking-widest uppercase font-['JoseonPalace']">소이설</h4>
                    </div>
                    <div className="flex-1 flex items-center">
                        <p className="text-stone-300 text-lg font-['JoseonPalace'] leading-relaxed break-keep">
                            "<span className="text-amber-200 font-bold">{maxStat.label}</span>의 별빛이 가장 밝게 빛나고 있어요. {maxStat.label === '화(火)' ? '열정을 태우기 좋은 시기예요.' : maxStat.label === '수(水)' ? '지혜롭게 흐름을 타세요.' : '균형 잡힌 시기군요.'}"
                        </p>
                    </div>
                </div>
            </motion.div>

            <motion.p
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 3 }}
                className="absolute bottom-8 text-white/20 text-[10px] tracking-[0.3em] cursor-pointer"
                onClick={onNext}
            >
                신탁 듣기 (터치)
            </motion.p>
        </motion.div>
    );
};

// Scroll Oracle Stage - Premium Dark/Gold Fantasy Theme
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
            className="relative w-full max-w-lg bg-[#0c0c0c] border border-amber-900/50 rounded-lg overflow-hidden flex flex-col items-center text-center shadow-[0_0_50px_rgba(0,0,0,0.8)]"
        >
            {/* Ornate Corner Accents */}
            <div className="absolute top-0 left-0 w-8 h-8 border-t-2 border-l-2 border-amber-600/60 rounded-tl-lg" />
            <div className="absolute top-0 right-0 w-8 h-8 border-t-2 border-r-2 border-amber-600/60 rounded-tr-lg" />
            <div className="absolute bottom-0 left-0 w-8 h-8 border-b-2 border-l-2 border-amber-600/60 rounded-bl-lg" />
            <div className="absolute bottom-0 right-0 w-8 h-8 border-b-2 border-r-2 border-amber-600/60 rounded-br-lg" />

            <div className="py-12 px-8 w-full relative z-10">
                <div className="w-full flex justify-center mb-8">
                    <span className="text-amber-500/40 text-xs tracking-[0.5em] uppercase border-b border-amber-500/20 pb-2">천명 (天命)</span>
                </div>

                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 0.5 }}
                >
                    <p className="text-2xl md:text-3xl text-white font-['JoseonPalace'] leading-10 break-keep drop-shadow-lg mb-8">
                        "{formatDialogue(fortune.message)}"
                    </p>

                    <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-amber-900/50 to-transparent my-6" />

                    <p className="text-stone-400 text-sm md:text-md leading-7 font-light tracking-wide break-keep px-4 font-['JoseonPalace']">
                        {formatDialogue(fortune.advice)}
                    </p>
                </motion.div>

                {/* Red Seal - Modernized */}
                <motion.div
                    initial={{ opacity: 0, rotate: 10, scale: 1.5 }}
                    animate={{ opacity: 1, rotate: -5, scale: 1 }}
                    transition={{ delay: 1.5, type: "spring" }}
                    className="mt-10 mx-auto w-24 h-24 border-2 border-red-900 rounded-lg flex items-center justify-center bg-red-950/30 backdrop-blur-sm"
                >
                    <span className="text-red-700 font-['JoseonPalace'] font-black text-4xl drop-shadow-[0_0_10px_rgba(185,28,28,0.5)]">吉</span>
                </motion.div>
            </div>

            {/* Background Texture */}
            <div className="absolute inset-0 opacity-10 bg-[url('https://www.transparenttextures.com/patterns/dark-matter.png')] z-0 pointer-events-none" />
        </motion.div>

        <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 2.5 }}
            className="mt-8 text-white/20 text-xs tracking-widest pointer-events-none"
        >
            운명 수락하기
        </motion.p>
    </motion.div>
);

// Talisman Inventory Stage - Modern RPG Item Cards
import { Award, Compass, Sparkles, Gem, Clock } from 'lucide-react';

const TalismanInventoryStage = ({ fortune, onNext }: { fortune: FortuneResult; onNext: () => void }) => {

    // Inventory Items
    const items = [
        { label: '행운색 (色)', value: fortune.lucky.color, icon: Sparkles, desc: '행운을 부르는 색', rarity: 'RARE' },
        { label: '행운수 (數)', value: fortune.lucky.number, icon: Award, desc: '오늘의 행운 숫자', rarity: 'COMMON' },
        { label: '방위 (方)', value: fortune.lucky.direction, icon: Compass, desc: '길한 방향', rarity: 'EPIC' },
        { label: '수호신 (神)', value: fortune.lucky.guardian, icon: Gem, desc: '당신을 지키는 수호신', rarity: 'LEGENDARY' },
        { label: '행동 (行)', value: fortune.lucky.action, icon: Clock, desc: '오늘의 추천 행동', rarity: 'RARE' },
    ];

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center justify-center w-full h-full max-w-6xl mx-auto p-4 pointer-events-auto overflow-hidden relative"
        >
            {/* Silk Background Texture */}
            <div className="absolute inset-0 bg-[#1a1510] opacity-90 z-0">
                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/black-scales.png')] opacity-30 mix-blend-overlay" />
                <div className="absolute top-0 inset-x-0 h-32 bg-gradient-to-b from-black/80 to-transparent" />
                <div className="absolute bottom-0 inset-x-0 h-32 bg-gradient-to-t from-black/80 to-transparent" />
            </div>

            <motion.div
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="mb-10 text-center relative z-10"
            >
                <div className="inline-block relative">
                    <div className="absolute -inset-4 bg-amber-500/10 blur-xl rounded-full" />
                    <h3 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-yellow-100 to-amber-300 font-['JoseonPalace'] mb-2 drop-shadow-sm relative">운명 보따리</h3>
                </div>
                <p className="text-amber-500/50 text-xs tracking-[0.5em] font-light border-t border-amber-500/20 pt-2 mt-1 font-['JoseonPalace']">오방의 선물</p>
            </motion.div>

            {/* Grid of Item Cards - Ultra Premium Wooden Tablet Style */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 md:gap-6 w-full max-w-4xl overflow-y-auto max-h-[60vh] custom-scrollbar p-4 relative z-10 perspective-1000">
                {items.map((item, i) => (
                    <motion.div
                        key={i}
                        initial={{ opacity: 0, y: 50, rotateX: -10 }}
                        animate={{ opacity: 1, y: 0, rotateX: 0 }}
                        transition={{ delay: i * 0.1, type: "spring", stiffness: 100 }}
                        whileHover={{
                            scale: 1.05,
                            y: -10,
                            rotateX: 5,
                            rotateY: 5,
                            zIndex: 50,
                            transition: { duration: 0.3 }
                        }}
                        className="group relative h-48 md:h-56 cursor-pointer preserve-3d"
                    >
                        {/* Shadows & Glows */}
                        <div className={`absolute -inset-2 rounded-xl blur-xl transition-all duration-500 opacity-0 group-hover:opacity-100 ${item.rarity === 'LEGENDARY' ? 'bg-purple-600/40' :
                            item.rarity === 'EPIC' ? 'bg-amber-600/40' : 'bg-stone-500/20'
                            }`} />

                        {/* Physical Card Body */}
                        <div className="absolute inset-0 bg-[#2c241b] rounded-xl border border-[#5d4037] shadow-xl overflow-hidden transform-style-3d">
                            {/* Textures */}
                            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/wood-pattern.png')] opacity-40 mix-blend-soft-light" />
                            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-black/80" />

                            {/* Gold Inlay Pattern (Simulated) */}
                            {(item.rarity === 'LEGENDARY' || item.rarity === 'EPIC') && (
                                <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_50%_0%,rgba(255,215,0,0.5),transparent_70%)]" />
                            )}

                            {/* Corner Ornaments */}
                            <div className="absolute top-2 left-2 w-4 h-4 border-t-2 border-l-2 border-[#8d6e63]/50" />
                            <div className="absolute top-2 right-2 w-4 h-4 border-t-2 border-r-2 border-[#8d6e63]/50" />
                            <div className="absolute bottom-2 left-2 w-4 h-4 border-b-2 border-l-2 border-[#8d6e63]/50" />
                            <div className="absolute bottom-2 right-2 w-4 h-4 border-b-2 border-r-2 border-[#8d6e63]/50" />

                            {/* Content */}
                            <div className="absolute inset-0 flex flex-col p-5 z-20">
                                {/* Top Row */}
                                <div className="flex justify-between items-start">
                                    <div className={`p-2.5 rounded-full border border-white/10 backdrop-blur-sm shadow-inner ${item.rarity === 'LEGENDARY' ? 'bg-purple-900/60 text-purple-200' :
                                        item.rarity === 'EPIC' ? 'bg-amber-900/60 text-amber-200' : 'bg-stone-800/60 text-stone-300'
                                        }`}>
                                        <item.icon size={20} strokeWidth={1.5} />
                                    </div>

                                    {/* Vertical Wooden Tag */}
                                    <div className="w-8 h-16 bg-[#1a1510] border border-[#3e2723] shadow-md flex items-center justify-center relative -mr-1 -mt-1 rounded-sm">
                                        <div className="absolute top-1 left-1/2 -translate-x-1/2 w-1.5 h-1.5 bg-[#3e2723] rounded-full" /> {/* Nail */}
                                        <span className="text-[10px] text-[#d7ccc8] font-['JoseonPalace'] writing-vertical-rl tracking-[0.2em] font-light opacity-80 pt-2">
                                            {item.rarity === 'LEGENDARY' ? '전설' : item.rarity === 'EPIC' ? '영웅' : item.rarity === 'RARE' ? '희귀' : '일반'}
                                        </span>
                                    </div>
                                </div>

                                {/* Main Text */}
                                <div className="mt-auto mb-2 relative">
                                    <p className="text-amber-500/60 text-[10px] font-['JoseonPalace'] mb-1 tracking-wider">{item.label}</p>
                                    <h4 className={`font-bold text-xl leading-tight font-['JoseonPalace'] break-keep drop-shadow-lg ${item.rarity === 'LEGENDARY' ? 'text-transparent bg-clip-text bg-gradient-to-r from-purple-200 to-purple-400' :
                                        'text-amber-100'
                                        }`}>
                                        {item.value}
                                    </h4>
                                </div>

                                {/* Description */}
                                <div className="pt-3 border-t border-white/5">
                                    <p className="text-[#a1887f] text-xs font-['JoseonPalace'] line-clamp-2 leading-relaxed opacity-80">{item.desc}</p>
                                </div>
                            </div>

                            {/* Shimmer Effect for Legendaries */}
                            {item.rarity === 'LEGENDARY' && (
                                <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/10 to-transparent -translate-x-full group-hover:animate-shimmer pointer-events-none" />
                            )}
                        </div>
                    </motion.div>
                ))}
            </div>

            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: 1.5 }}
                className="mt-10 relative z-20"
            >
                <button
                    onClick={onNext}
                    className="px-12 py-4 bg-[#3e2723] hover:bg-[#2d1b18] border border-amber-500/20 text-amber-100/80 font-bold rounded-lg shadow-[0_10px_30px_rgba(0,0,0,0.5)] transition-all hover:-translate-y-1 hover:text-amber-100 text-sm tracking-[0.3em] flex items-center gap-3 font-['JoseonPalace'] group relative overflow-hidden"
                >
                    <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent -translate-x-full group-hover:animate-shimmer" />
                    <span className="w-1 h-1 bg-amber-500/50 rounded-full" />
                    <span>운명 각인하기</span>
                    <span className="w-1 h-1 bg-amber-500/50 rounded-full" />
                </button>
            </motion.div>
        </motion.div>
    );
};

// Destiny Seal Stage - Login/Signup Conversion
const DestinySealStage = ({ onRestart, onClose, selectedGame }: { onRestart: () => void; onClose: () => void; selectedGame: GameType }) => {
    const isObang = selectedGame === 'obang';

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col items-center w-full h-full p-4 pointer-events-auto relative overflow-y-auto custom-scrollbar py-8"
        >
            {/* Decorative Background Elements */}
            <div className="absolute inset-0 pointer-events-none fixed">
                <div className={`absolute top-0 left-0 w-32 h-32 blur-3xl rounded-full mix-blend-screen ${isObang ? 'bg-amber-500/10' : 'bg-purple-500/10'}`} />
                <div className={`absolute bottom-0 right-0 w-32 h-32 blur-3xl rounded-full mix-blend-screen ${isObang ? 'bg-amber-500/10' : 'bg-purple-500/10'}`} />
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
                        <h2 className={`text-3xl md:text-4xl font-black text-transparent bg-clip-text drop-shadow-[0_0_20px_rgba(251,191,36,0.5)] mb-3 ${isObang ? "bg-gradient-to-b from-amber-100 via-amber-200 to-amber-500 font-['JoseonPalace']" : "bg-gradient-to-b from-purple-100 via-purple-200 to-purple-500 font-gmarket tracking-tighter"}`}>
                            {isObang ? "운명의 문이 열렸습니다" : "운명의 문이 열립니다"}
                        </h2>
                        <div className={`flex items-center justify-center gap-4 text-xs md:text-sm font-light tracking-[0.2em] uppercase ${isObang ? 'text-amber-100/60' : 'text-purple-100/60'}`}>
                            <span className={`h-[1px] w-8 ${isObang ? 'bg-amber-500/30' : 'bg-purple-500/30'}`}></span>
                            <span className={isObang ? "font-['JoseonPalace']" : "font-gmarket"}>Destiny Awaits</span>
                            <span className={`h-[1px] w-8 ${isObang ? 'bg-amber-500/30' : 'bg-purple-500/30'}`}></span>
                        </div>
                    </motion.div>
                </div>

                {/* Character & Dialogue - Premium Presentation */}
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

                    {/* Dialogue Bubble - Service Variety */}
                    <motion.div
                        initial={{ opacity: 0, y: 10, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        transition={{ delay: 0.5 }}
                        className={`relative bg-black/40 border rounded-2xl p-5 backdrop-blur-md max-w-sm text-center shadow-xl ring-1 ring-white/5 w-full ${isObang ? 'border-amber-500/30' : 'border-purple-500/30'}`}
                    >
                        {/* Triangle */}
                        <div className={`absolute -top-2 left-1/2 -translate-x-1/2 w-4 h-4 bg-black/40 border-t border-l rotate-45 transform backdrop-blur-md ${isObang ? 'border-amber-500/30' : 'border-purple-500/30'}`} />

                        <p className={`text-white/95 text-sm md:text-base leading-6 break-keep ${isObang ? "font-['JoseonPalace']" : "font-serif"}`}>
                            {isObang ? (
                                <>
                                    "<span className="text-amber-300 font-bold">궁합, 타로, 정통사주</span>까지...<br />
                                    당신의 운명을 위한 <span className="text-amber-300 font-bold border-b border-amber-300/50 pb-0.5">모든 이야기</span>가 기다려요.<br />
                                    <span className="text-amber-200 font-bold">지금 바로 시작해보세요.</span>"
                                </>
                            ) : (
                                <>
                                    "<span className="text-purple-300 font-bold">당신의 숨겨진 길</span>을 발견해보세요...<br />
                                    별들이 당신의 <span className="text-purple-300 font-bold border-b border-purple-300/50 pb-0.5">운명적 이야기</span>를 속삭이고 있어요.<br />
                                    <span className="text-purple-200 font-bold">지금 여정을 시작하세요.</span>"
                                </>
                            )}
                        </p>
                    </motion.div>
                </div>

                {/* Social Login Buttons - Card Style */}
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
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-amber-600/5 rounded-full blur-[120px] animate-pulse" />
                <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/stardust.png')] opacity-30" />
                {/* Floating Particles */}
                {[...Array(5)].map((_, i) => (
                    <motion.div
                        key={i}
                        animate={{ y: [0, -100], opacity: [0, 0.5, 0] }}
                        transition={{ duration: 3 + Math.random() * 2, repeat: Infinity, delay: Math.random() * 2 }}
                        className="absolute bottom-0 w-1 h-1 bg-amber-300 rounded-full blur-[1px]"
                        style={{ left: `${20 + Math.random() * 60}%` }}
                    />
                ))}
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
        const timer2 = setTimeout(() => setRevealPhase('insight'), 4000); // 1.5s + 2.5s reading card

        return () => {
            clearTimeout(timer1);
            clearTimeout(timer2);
        };
    }, []);

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
            <div className={`relative z-10 w-full max-w-7xl h-full flex flex-col md:flex-row items-center justify-center transition-all duration-1000 ${revealPhase === 'insight' ? 'gap-12 md:gap-24' : 'gap-0'}`}>

                {/* Left: Card Visual */}
                <motion.div
                    layout
                    initial={{ scale: 0.8, opacity: 0, y: 50 }}
                    animate={{
                        scale: revealPhase === 'summon' ? 1 : 1.1,
                        opacity: 1,
                        y: 0,
                        x: revealPhase === 'insight' ? 0 : 0 // Controlled by Flexbox layout, but Motion layout prop handles smooth transition
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

                            <div className="relative h-full flex flex-col bg-[#050505]">
                                <div className="relative flex-1 overflow-hidden">
                                    {/* Image with Parallax-like Zoom */}
                                    <motion.img
                                        src={result.card.imageUrl}
                                        alt={result.card.name}
                                        initial={{ scale: 1.2 }}
                                        animate={{ scale: 1 }}
                                        transition={{ duration: 10, repeat: Infinity, repeatType: "mirror" }}
                                        className="w-full h-full object-cover opacity-90"
                                    />
                                    <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-90" />
                                </div>
                                <div className="relative p-6 pt-2 pb-8 bg-black border-t border-purple-900/30">
                                    <h3 className="text-3xl font-gmarket font-bold text-white text-center mb-1 drop-shadow-md">{result.card.name}</h3>
                                    <p className="text-purple-300/60 text-xs text-center font-serif uppercase tracking-[0.3em]">{result.card.englishName}</p>
                                </div>
                            </div>
                            {/* Shimmer Overlay */}
                            <div className="absolute inset-0 bg-gradient-to-tr from-white/0 via-white/10 to-white/0 translate-x-[-100%] animate-[shimmer_3s_infinite] pointer-events-none z-30" />
                        </div>

                        {/* Back Face */}
                        <div
                            className="absolute inset-0 rounded-2xl border border-white/10 shadow-2xl bg-[#1a1a2e]"
                            style={{
                                transform: 'rotateY(180deg)',
                                backgroundImage: `url(${tarotBack})`,
                                backgroundSize: 'cover',
                                backgroundPosition: 'center',
                                backfaceVisibility: 'hidden'
                            }}
                        >
                            {/* Pulse Glow while waiting */}
                            <div className="absolute inset-0 bg-purple-500/20 animate-pulse rounded-2xl" />
                        </div>
                    </motion.div>

                    {/* God Rays / Flash Effect on Flip */}
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

                {/* Right: Meaning & Interpretation (Only visibly in Insight phase) */}
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

                        <motion.button
                            whileHover={{ scale: 1.05 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={onNext}
                            className="self-center md:self-end px-10 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-gmarket font-bold text-sm tracking-widest uppercase rounded shadow-[0_0_20px_rgba(168,85,247,0.4)] transition-all w-full md:w-auto"
                        >
                            Accept Destiny
                        </motion.button>
                    </motion.div>
                )}

            </div>
        </motion.div>
    );
};

export default FortuneTeaserModal;
