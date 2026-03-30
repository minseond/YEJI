import { useState, useEffect, useRef, Fragment } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronRight, Sparkles } from 'lucide-react';
import { RADAR_LABELS } from '../common/RadarChart';
import KoreanSeal from '../../assets/ui/korean_seal.png';
import WesternSeal from '../../assets/ui/western_wax_seal.png';
import { MOCK_WEST_DATA, MOCK_EAST_DATA, MOCK_PAST_LIFE_DATA, getPastLifeIndex } from '../../data/compatibilityData';
import type { CompatibilityResponse } from '../../api/compatibility';
import { useCharacterSettings, getCharacterName } from '../../utils/character';
import CharacterGuide from '../common/CharacterGuide';
import { COMPATIBILITY_INTERACTIVE_COMMENTS } from '../../data/compatibilityData';


interface CompatibilityResultViewProps {
    data?: CompatibilityResponse | null;
    userInfo?: { name: string };
    friendInfo?: { name: string };
    initialType?: 'east' | 'west';
    onBack?: () => void;
    onExit?: () => void;
    onTypeChange?: (type: 'east' | 'west') => void;
}

const CompatibilityResultView = ({ data, userInfo, friendInfo, initialType = 'east', onTypeChange }: CompatibilityResultViewProps) => {
    const [selectedType, setSelectedType] = useState<'east' | 'west'>(initialType);
    const [showScoreTooltip, setShowScoreTooltip] = useState(false);
    const [activeComment, setActiveComment] = useState<{ speaker: 'east' | 'west'; text: string } | null>(null);
    const commentTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const triggerComment = (speaker: 'east' | 'west', text: string) => {
        if (commentTimeoutRef.current) clearTimeout(commentTimeoutRef.current);
        setActiveComment({ speaker, text });
        commentTimeoutRef.current = setTimeout(() => {
            setActiveComment(null);
        }, 3000);
    };

    // Auto-clear timeout on unmount
    useEffect(() => {
        return () => {
            if (commentTimeoutRef.current) clearTimeout(commentTimeoutRef.current);
        };
    }, []);


    // Only inform parent when type actually changes via internal buttons
    const handleTypeChange = (type: 'east' | 'west') => {
        setSelectedType(type);
        onTypeChange?.(type);
        // Parent handles scrolling to top via selectedType effect
    };

    const [hoveredMetric, setHoveredMetric] = useState<string | null>(null);

    const settings = useCharacterSettings();
    const eastCharName = getCharacterName('east', settings.east);
    const westCharName = getCharacterName('west', settings.west);

    const currentUserName = userInfo?.name || "나";
    const targetName = friendInfo?.name || data?.targetName || "상대";

    // Extract real data from API response or use mock data as fallback
    const eastData = data?.resultData?.message?.east || MOCK_EAST_DATA;
    const westData = data?.resultData?.message?.west || MOCK_WEST_DATA;
    const totalScore = data?.resultData?.score?.total;
    const eastScore = data?.resultData?.score?.east;
    const westScore = data?.resultData?.score?.west;
    const gradeLabel = data?.resultData?.grade_label;


    return (
        <div className="w-full relative py-20 pb-12 isolation-isolate">
            <AnimatePresence mode="wait">
                {selectedType === 'east' ? (
                    <Fragment key="east_path">
                        <motion.div
                            key="east_report_wrapped"
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -30 }}
                            className="w-full max-w-5xl mx-auto relative group transform-gpu"
                        >
                            <div className="w-full bg-[#fdfaf3] text-amber-950 rounded-lg shadow-[0_30px_60px_-15px_rgba(0,0,0,0.5),0_10px_30px_-10px_rgba(0,0,0,0.3)] border-x-8 border-amber-900/10 p-1 md:p-2 relative overflow-hidden"
                                style={{ backgroundImage: "url('https://www.transparenttextures.com/patterns/rice-paper-2.png')" }}
                            >
                                <div className="absolute top-0 left-0 w-32 h-32 bg-amber-900/5 rotate-45 -translate-x-16 -translate-y-16 border-b border-amber-900/10" />
                                <div className="absolute bottom-0 right-0 w-32 h-32 bg-amber-900/5 rotate-45 translate-x-16 translate-y-16 border-t border-amber-900/10" />

                                <div className="relative z-10 w-full flex flex-col items-center py-16 px-6 md:px-12 border border-amber-900/20 rounded-sm">
                                    <div className="text-center mb-16 w-full">
                                        <h2 className="text-5xl md:text-6xl font-['Hahmlet'] font-black bg-gradient-to-b from-amber-700 via-amber-900 to-amber-950 bg-clip-text text-transparent mb-6 tracking-tight">궁합 보고서</h2>
                                        <div className="w-56 h-[2px] bg-gradient-to-r from-transparent via-amber-900/40 to-transparent mx-auto mb-6" />
                                        <p className="text-amber-900 font-bold text-base tracking-[0.2em] uppercase font-['GmarketSansMedium'] opacity-80">{eastCharName}의 사주 & 명리 분석 보고서</p>
                                        {/* Premium Score Display - East Theme */}
                                        {totalScore !== undefined && (
                                            <motion.div
                                                initial={{ scale: 0.8, opacity: 0 }}
                                                animate={{ scale: 1, opacity: 1 }}
                                                transition={{ delay: 0.5, type: "spring", stiffness: 200 }}
                                                className="mt-12 relative flex items-center justify-center cursor-pointer z-[60] transform-gpu will-change-transform"
                                                onMouseEnter={() => setShowScoreTooltip(true)}
                                                onMouseLeave={() => setShowScoreTooltip(false)}
                                                onClick={() => {
                                                    const comment = COMPATIBILITY_INTERACTIVE_COMMENTS.east.score(eastScore || 0);
                                                    triggerComment('east', comment);
                                                }}

                                            >

                                                <div className="absolute inset-0 bg-amber-500/10 blur-3xl rounded-full" />
                                                <div className="relative w-44 h-44 rounded-full border-2 border-amber-900/20 flex flex-col items-center justify-center bg-white/60 backdrop-blur-md shadow-[0_20px_50px_rgba(120,53,15,0.1),inset_0_0_30px_rgba(251,191,36,0.05)] ring-8 ring-amber-900/5 hover:ring-amber-900/10 transition-all">
                                                    <div className="text-amber-800/60 text-[11px] tracking-[0.3em] uppercase mb-1 font-black">궁합 점수</div>
                                                    <div className="text-6xl font-['Hahmlet'] font-black text-amber-950 drop-shadow-sm">{totalScore}</div>

                                                    {/* Sub Score */}
                                                    {eastScore !== undefined && (
                                                        <div className="mt-3 px-3 py-1 bg-amber-900/5 rounded-full text-[10px] text-amber-900 font-black border border-amber-900/10">
                                                            동양 : {eastScore}
                                                        </div>
                                                    )}

                                                    {/* Decorative Elements */}
                                                    <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-amber-900 rounded-full border-4 border-[#fdfaf3] shadow-lg" />
                                                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-6 h-6 bg-amber-900 rounded-full border-4 border-[#fdfaf3] shadow-lg" />
                                                </div>

                                                {/* Score Tooltip - East */}
                                                <AnimatePresence>
                                                    {showScoreTooltip && (
                                                        <motion.div
                                                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                                            animate={{ opacity: 1, y: 0, scale: 1 }}
                                                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                                            className="absolute top-full mt-4 w-72 p-4 bg-amber-900/95 backdrop-blur-xl border border-amber-500/30 rounded-2xl shadow-2xl z-[100] text-center pointer-events-none"
                                                        >
                                                            <div className="text-amber-200 text-[13px] font-['Hahmlet'] leading-relaxed break-keep">
                                                                총점은 <span className="text-white font-bold">동양(50점)</span>과 <span className="text-white font-bold">서양(50점)</span><br />
                                                                점수를 합산한 결과입니다. (100점 만점)
                                                            </div>
                                                            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1 w-3 h-3 bg-amber-900/95 rotate-45 border-l border-t border-amber-500/30" />
                                                        </motion.div>
                                                    )}
                                                </AnimatePresence>
                                            </motion.div>
                                        )}
                                    </div>

                                    {/* Enhanced Compatibility Summary - Moved to Top */}
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        whileInView={{ opacity: 1, y: 0 }}
                                        viewport={{ once: true }}
                                        className="w-full max-w-4xl mb-20 relative"
                                    >
                                        <div className="absolute inset-0 bg-amber-900/[0.03] backdrop-blur-[2px] rounded-[2rem] border-2 border-amber-900/5 shadow-inner cursor-pointer hover:bg-amber-900/5 transition-colors"
                                            onClick={() => triggerComment('east', COMPATIBILITY_INTERACTIVE_COMMENTS.east.summary)}
                                        />

                                        <div className="relative p-10 md:p-14 flex flex-col items-center">
                                            {/* Moved summary label to top and increased its size */}
                                            <div className="mb-10 flex items-center gap-4 text-amber-900/40">
                                                <div className="h-[1px] w-12 bg-amber-900/20" />
                                                <span className="text-sm md:text-base tracking-[0.4em] uppercase font-bold">운류(運流)의 총평</span>
                                                <div className="h-[1px] w-12 bg-amber-900/20" />
                                            </div>

                                            <div className="relative">
                                                <div className="absolute -top-6 -left-4 text-6xl text-amber-900/5 font-serif">"</div>
                                                <p className="text-xl md:text-2xl leading-[2.1] text-amber-950 font-['Hahmlet'] font-medium break-keep text-center relative z-10 flex flex-col gap-4">
                                                    {eastData.compatibility_summary.desc.split('.').map((sentence, idx, array) => (
                                                        sentence.trim() && (
                                                            <span key={idx}>
                                                                {sentence.trim()}{idx !== array.length - 1 ? '.' : ''}
                                                            </span>
                                                        )
                                                    ))}
                                                </p>
                                                <div className="absolute -bottom-10 -right-4 text-6xl text-amber-900/5 font-serif rotate-180">"</div>
                                            </div>

                                            <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-amber-900/10 to-transparent mt-12 mb-8" />

                                            {/* Moved keywords to bottom */}
                                            <div className="flex flex-wrap justify-center gap-2">
                                                {eastData.compatibility_summary.keywords.map((kw, i) => (
                                                    <motion.span
                                                        key={kw}
                                                        initial={{ opacity: 0, scale: 0.8 }}
                                                        whileInView={{ opacity: 1, scale: 1 }}
                                                        transition={{ delay: i * 0.1 }}
                                                        className="px-4 py-1.5 bg-amber-900/5 text-amber-900/60 rounded-full text-xs font-bold tracking-widest italic border border-amber-900/10"
                                                    >
                                                        #{kw}
                                                    </motion.span>
                                                ))}
                                            </div>
                                        </div>
                                    </motion.div>

                                    <div className="w-full max-w-3xl mb-20 bg-amber-900/5 p-8 rounded-3xl border border-amber-900/10 relative overflow-hidden cursor-pointer hover:bg-amber-900/10 transition-colors"
                                        onClick={() => triggerComment('east', COMPATIBILITY_INTERACTIVE_COMMENTS.east.pastLife)}
                                    >
                                        <div className="absolute top-0 right-0 w-24 h-24 bg-amber-900/5 -translate-y-12 translate-x-12 rotate-45 border-b border-amber-900/10" />
                                        <h4 className="text-xl font-['Hahmlet'] font-bold text-amber-900 mb-6 flex items-center gap-3">
                                            <span className="text-amber-700/50 text-xs tracking-tighter">전생 기록</span>
                                            두 분의 전생(前生) 인연
                                        </h4>
                                        <div className="flex flex-col md:flex-row items-center gap-8">
                                            <div className="w-32 h-32 flex-shrink-0 bg-white rounded-2xl shadow-inner border border-amber-900/10 flex items-center justify-center text-4xl">🏮</div>
                                            <div>
                                                <div className="text-2xl font-['Hahmlet'] font-bold text-amber-950 mb-3">{MOCK_PAST_LIFE_DATA[getPastLifeIndex(currentUserName, targetName)].title}</div>
                                                <p className="text-amber-900/80 leading-relaxed font-['GmarketSansMedium']">
                                                    {MOCK_PAST_LIFE_DATA[getPastLifeIndex(currentUserName, targetName)].desc}
                                                </p>
                                                <div className="mt-4 flex items-center gap-2">
                                                    <span className="text-xs text-amber-700/60 font-bold uppercase tracking-widest">업식의 끈:</span>
                                                    <span className="text-sm font-bold text-amber-900 bg-amber-100 px-3 py-1 rounded-full">{MOCK_PAST_LIFE_DATA[getPastLifeIndex(currentUserName, targetName)].keyword}</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Relationship Dynamics - Card Grid Layout */}
                                    <div className="w-full max-w-4xl mb-20 px-4">
                                        <div className="text-center mb-10">
                                            <h3 className="text-3xl font-bold text-amber-900 font-['Hahmlet'] tracking-widest mb-2">관계 분석</h3>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                                            {RADAR_LABELS.map((item, idx) => {
                                                const dynamicData = (eastData.relationship_dynamics as any)[item.key];
                                                if (!dynamicData) return null;

                                                const hanjaMap: Record<string, { char: string; meaning: string }> = {
                                                    communication: { char: '通', meaning: '통할 통' },
                                                    stability: { char: '安', meaning: '편안할 안' },
                                                    growth: { char: '成', meaning: '이룰 성' },
                                                    passion: { char: '熱', meaning: '더울 열' },
                                                    flexibility: { char: '柔', meaning: '부드러울 유' }
                                                };
                                                const hanja = hanjaMap[item.key];

                                                return (
                                                    <motion.div
                                                        key={item.key}
                                                        initial={{ opacity: 0, y: 20 }}
                                                        whileInView={{ opacity: 1, y: 0 }}
                                                        viewport={{ once: true }}
                                                        transition={{ delay: idx * 0.1 }}
                                                        onMouseEnter={() => setHoveredMetric(item.key)}
                                                        onMouseLeave={() => setHoveredMetric(null)}
                                                        onClick={() => {
                                                            const comment = (COMPATIBILITY_INTERACTIVE_COMMENTS.east.dynamics as any)[item.key];
                                                            if (comment) triggerComment('east', comment);
                                                        }}
                                                        className="group bg-white/40 backdrop-blur-sm p-6 rounded-2xl border border-amber-900/10 hover:border-amber-900/30 transition-all shadow-sm flex flex-col items-center text-center relative cursor-pointer active:scale-95"
                                                    >

                                                        <div
                                                            className="w-14 h-14 rounded-2xl flex items-center justify-center text-2xl font-['JoseonPalace'] font-black mb-4 border border-white shadow-inner transition-transform group-hover:scale-110 relative"
                                                            style={{ backgroundColor: item.color + '20', color: item.color }}
                                                        >
                                                            {hanja.char}

                                                            <AnimatePresence>
                                                                {hoveredMetric === item.key && (
                                                                    <motion.div
                                                                        initial={{ opacity: 0, y: 10, scale: 0.8 }}
                                                                        animate={{ opacity: 1, y: 0, scale: 1 }}
                                                                        exit={{ opacity: 0, y: 10, scale: 0.8 }}
                                                                        className="absolute -top-12 left-1/2 -translate-x-1/2 px-3 py-1 bg-amber-900 text-amber-50 text-[10px] rounded-lg whitespace-nowrap z-50 shadow-xl pointer-events-none"
                                                                    >
                                                                        {hanja.meaning}
                                                                        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-amber-900 rotate-45" />
                                                                    </motion.div>
                                                                )}
                                                            </AnimatePresence>
                                                        </div>
                                                        <h4 className="text-amber-900 font-bold text-lg mb-3 tracking-wider">{item.label.replace(' 지수', '')}</h4>
                                                        <p className="text-amber-950/70 text-sm leading-relaxed font-['GmarketSansMedium'] break-keep">
                                                            {dynamicData.desc}
                                                        </p>
                                                    </motion.div>
                                                );
                                            })}
                                        </div>
                                    </div>


                                    <div className="flex flex-col items-center mt-12 mb-4 w-full max-w-xs">
                                        <div className="w-[1px] h-12 bg-amber-900/10 mb-8" />
                                        <motion.div initial={{ opacity: 0, scale: 1.2, rotate: -15 }} whileInView={{ opacity: 0.7, scale: 1, rotate: -5 }} viewport={{ once: true }} transition={{ type: "spring", damping: 15 }}
                                            className="relative cursor-pointer hover:scale-110 transition-transform"
                                            onClick={() => triggerComment('east', COMPATIBILITY_INTERACTIVE_COMMENTS.east.seal)}
                                        >
                                            <img src={KoreanSeal} alt="공식 인장" className="w-24 h-24 object-contain mix-blend-multiply filter contrast-125 brightness-90" />
                                        </motion.div>

                                    </div>
                                </div>
                            </div>
                            <div className="flex flex-col items-center mt-24 mb-16">
                                <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => handleTypeChange('west')} className="px-12 py-5 bg-amber-900 text-amber-50 rounded-full font-bold text-lg shadow-2xl hover:bg-amber-800 transition-all flex items-center gap-3">
                                    {westCharName}의 별자리 & 수비학 보고서 보기
                                    <ChevronRight size={24} />
                                </motion.button>
                            </div>
                        </motion.div >

                        <CharacterGuide
                            region="east"
                            theme="amber"
                            characterId={settings.east}
                            characterName={eastCharName}
                            activeComment={activeComment?.speaker === 'east' ? activeComment.text : null}
                            onCommentClick={() => setActiveComment(null)}
                            position="right"
                        />
                    </Fragment >
                ) : (
                    <Fragment key="west_path">
                        <motion.div
                            key="west_report_wrapped"
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -30 }}
                            className="w-full max-w-5xl mx-auto relative px-4 transform-gpu"
                        >
                            <div
                                className="w-full bg-[#1a1b2e] text-indigo-100 rounded-2xl shadow-[0_40px_100px_rgba(0,0,0,0.8),inset_0_0_60px_rgba(79,70,229,0.1)] border border-indigo-500/30 p-1 md:p-3 relative overflow-hidden"
                                style={{ backgroundImage: "linear-gradient(to bottom right, rgba(26,27,46,0.95), rgba(30,32,56,0.95)), url('https://www.transparenttextures.com/patterns/dark-matter.png')" }}
                            >
                                <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-500/5 blur-[100px] rounded-full -translate-y-1/2 translate-x-1/2" />
                                <div className="absolute bottom-0 left-0 w-64 h-64 bg-purple-500/5 blur-[100px] rounded-full translate-y-1/2 -translate-x-1/2" />
                                <div className="absolute inset-0 border border-white/5 pointer-events-none rounded-2xl" />

                                <div className="relative z-10 w-full flex flex-col items-center py-20 px-6 md:px-12 border border-indigo-500/20 rounded-xl">
                                    <div className="text-center mb-20">
                                        <div className="flex items-center justify-center gap-4 mb-4">
                                            <div className="h-[1px] w-12 bg-gradient-to-r from-transparent to-indigo-500/50" />
                                            <Sparkles size={16} className="text-indigo-400 animate-pulse" />
                                            <div className="h-[1px] w-12 bg-gradient-to-l from-transparent to-indigo-500/50" />
                                        </div>
                                        <div className="text-center mb-16 relative z-20 w-full">
                                            <h2 className="text-5xl md:text-6xl font-['Hahmlet'] font-black bg-gradient-to-b from-white via-indigo-200 to-indigo-400 bg-clip-text text-transparent mb-6 tracking-tight">궁합 보고서</h2>
                                            <div className="w-56 h-[2px] bg-gradient-to-r from-transparent via-indigo-500/40 to-transparent mx-auto mb-6" />
                                            <p className="text-indigo-300 font-bold text-base tracking-[0.2em] uppercase font-['GmarketSansMedium'] opacity-80">{westCharName}의 별자리 & 수비학 분석 보고서</p>
                                        </div>

                                        {/* Premium Score Display - West Theme */}
                                        {totalScore !== undefined && (
                                            <motion.div
                                                initial={{ scale: 0.8, opacity: 0 }}
                                                animate={{ scale: 1, opacity: 1 }}
                                                transition={{ delay: 0.5, type: "spring", stiffness: 200 }}
                                                className="mt-12 relative flex items-center justify-center cursor-pointer z-[60] transform-gpu will-change-transform"
                                                onMouseEnter={() => setShowScoreTooltip(true)}
                                                onMouseLeave={() => setShowScoreTooltip(false)}
                                                onClick={() => {
                                                    const comment = COMPATIBILITY_INTERACTIVE_COMMENTS.west.score(westScore || 0);
                                                    triggerComment('west', comment);
                                                }}

                                            >

                                                <div className="absolute inset-0 bg-indigo-500/10 blur-3xl rounded-full" />
                                                <div className="relative w-44 h-44 rounded-full border-2 border-indigo-500/20 flex flex-col items-center justify-center bg-indigo-950/40 backdrop-blur-md shadow-[0_20px_50px_rgba(79,70,229,0.2),inset_0_0_30px_rgba(129,140,248,0.1)] ring-8 ring-indigo-500/5 hover:ring-indigo-500/10 transition-all">
                                                    <div className="text-indigo-400/60 text-[11px] tracking-[0.3em] uppercase mb-1 font-black">궁합 점수</div>
                                                    <div className="text-6xl font-['Hahmlet'] font-black text-white drop-shadow-sm">{totalScore}</div>

                                                    {/* Sub Score */}
                                                    {westScore !== undefined && (
                                                        <div className="mt-3 px-3 py-1 bg-indigo-500/10 rounded-full text-[10px] text-indigo-200 font-black border border-indigo-500/20">
                                                            서양 : {westScore}
                                                        </div>
                                                    )}

                                                    {/* Decorative Elements */}
                                                    <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-indigo-500 rounded-full border-4 border-[#1a1b2e] shadow-lg shadow-indigo-500/20" />
                                                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-6 h-6 bg-indigo-500 rounded-full border-4 border-[#1a1b2e] shadow-lg shadow-indigo-500/20" />
                                                </div>

                                                {/* Score Tooltip - West */}
                                                <AnimatePresence>
                                                    {showScoreTooltip && (
                                                        <motion.div
                                                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                                            animate={{ opacity: 1, y: 0, scale: 1 }}
                                                            exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                                            className="absolute top-full mt-4 w-72 p-4 bg-indigo-950/95 backdrop-blur-xl border border-indigo-500/30 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.5)] z-[100] text-center pointer-events-none"
                                                        >
                                                            <div className="text-indigo-200 text-[13px] font-['Hahmlet'] leading-relaxed break-keep">
                                                                총점은 <span className="text-white font-bold">동양(50점)</span>과 <span className="text-white font-bold">서양(50점)</span><br />
                                                                점수를 합산한 결과입니다. (100점 만점)
                                                            </div>
                                                            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1 w-3 h-3 bg-indigo-950/95 rotate-45 border-l border-t border-indigo-500/30" />
                                                        </motion.div>
                                                    )}
                                                </AnimatePresence>
                                            </motion.div>
                                        )}
                                        {/* West Report Stellar Summary */}
                                        <motion.div
                                            initial={{ opacity: 0, scale: 0.95 }}
                                            whileInView={{ opacity: 1, scale: 1 }}
                                            viewport={{ once: true }}
                                            className="mt-12 w-full max-w-3xl relative p-1 px-1 bg-gradient-to-br from-indigo-500/20 via-purple-500/10 to-transparent rounded-[2.5rem] cursor-pointer hover:scale-[1.01] transition-transform"
                                            onClick={() => triggerComment('west', COMPATIBILITY_INTERACTIVE_COMMENTS.west.summary)}
                                        >

                                            <div className="bg-[#1a1b2e]/80 backdrop-blur-xl p-10 rounded-[2.4rem] border border-white/5 flex flex-col items-center">
                                                <div className="text-center w-full max-w-2xl">
                                                    <div className="text-indigo-300 text-sm font-bold uppercase tracking-[0.3em] mb-4 italic">별들의 총평</div>
                                                    <h3 className="text-3xl font-['Hahmlet'] font-bold text-white mb-10 tracking-tight">
                                                        "{gradeLabel || '영혼의 동반자'}"
                                                    </h3>

                                                    <div className="text-lg md:text-xl text-indigo-100/80 leading-relaxed font-['GmarketSansMedium'] break-keep flex flex-col gap-4">
                                                        {(() => {
                                                            const fullText = `${westData.zodiac.aspects.moon_resonance.desc.split('.')[0]}. 점성술과 수비학이 가리키는 두 분의 관계는 우주적인 필연에 기초하고 있습니다.`;
                                                            return fullText.split('.').map((sentence, idx, array) => (
                                                                sentence.trim() && (
                                                                    <span key={idx}>
                                                                        {sentence.trim()}{idx !== array.length - 1 ? '.' : ''}
                                                                    </span>
                                                                )
                                                            ));
                                                        })()}
                                                    </div>
                                                </div>

                                                <div className="mt-8 flex gap-2">
                                                    {['운명', '조화', '영원'].map(tag => (
                                                        <span key={tag} className="px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-[10px] text-indigo-300 font-bold uppercase tracking-wider">
                                                            {tag}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        </motion.div>
                                        <div className="mt-12 text-indigo-300/10 font-serif text-3xl tracking-widest">✧ ✵ ✧</div>
                                    </div>


                                    <div className="w-full max-w-4xl mb-24">
                                        <h3 className="text-xl text-indigo-100 mb-12 font-bold flex items-center justify-center gap-6">
                                            <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent to-indigo-500/30" />
                                            <span className="tracking-[0.3em]">점성술 분석</span>
                                            <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent to-indigo-500/30" />
                                        </h3>
                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                                            {Object.entries(westData.zodiac.aspects).map(([key, item]) => (
                                                <motion.div key={key} whileHover={{ scale: 1.02, backgroundColor: 'rgba(255,255,255,0.03)' }}
                                                    onClick={() => {
                                                        const comment = COMPATIBILITY_INTERACTIVE_COMMENTS.west.aspects(key);
                                                        triggerComment('west', comment);
                                                    }}
                                                    className="bg-white/5 backdrop-blur-xl p-8 rounded-3xl border border-white/5 transition-all shadow-xl group/card cursor-pointer active:scale-95"
                                                >

                                                    <div className="flex items-center gap-3 mb-4">
                                                        <div className="w-2 h-2 rounded-full bg-indigo-400 shadow-[0_0_15px_rgba(129,140,248,1)] group-hover/card:scale-125 transition-transform" />
                                                        <h4 className="text-xl text-white font-bold tracking-wide">{item.title}</h4>
                                                    </div>
                                                    <p className="text-[15px] text-indigo-100/70 leading-relaxed font-['GmarketSansMedium'] flex flex-col gap-2">
                                                        {item.desc.split('.').map((sentence: string, sIdx: number, sArr: string[]) => (
                                                            sentence.trim() && (
                                                                <span key={sIdx}>
                                                                    {sentence.trim()}{sIdx !== sArr.length - 1 ? '.' : ''}
                                                                </span>
                                                            )
                                                        ))}
                                                    </p>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="w-full max-w-4xl mb-12">
                                        <h3 className="text-xl text-indigo-100 mb-12 font-bold flex items-center justify-center gap-6">
                                            <div className="h-[1px] flex-1 bg-gradient-to-r from-transparent to-indigo-500/30" />
                                            <span className="tracking-[0.3em]">수비학 분석</span>
                                            <div className="h-[1px] flex-1 bg-gradient-to-l from-transparent to-indigo-500/30" />
                                        </h3>
                                        <div className="flex flex-col gap-8">
                                            {Object.entries(MOCK_WEST_DATA.numerology).map(([key, item], idx) => (
                                                <motion.div key={key} initial={{ opacity: 0, x: idx % 2 === 0 ? -20 : 20 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }}
                                                    onClick={() => {
                                                        const comment = COMPATIBILITY_INTERACTIVE_COMMENTS.west.numerology(key);
                                                        triggerComment('west', comment);
                                                    }}
                                                    className="bg-indigo-900/20 backdrop-blur-md p-10 rounded-3xl border border-indigo-500/10 hover:border-indigo-500/30 transition-all relative group/insight cursor-pointer active:scale-95"
                                                >

                                                    <h4 className="text-2xl text-white font-bold mb-6 flex items-center gap-4">
                                                        <span className="text-indigo-400 text-sm italic font-serif">#</span>
                                                        {item.title}
                                                    </h4>
                                                    <p className="text-[17px] text-indigo-100/90 leading-[1.8] font-['GmarketSansMedium']">{item.desc}</p>
                                                </motion.div>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="flex flex-col items-center mt-16 w-full max-w-md">
                                        <div className="w-full h-[1px] bg-gradient-to-r from-transparent via-indigo-500/20 to-transparent mb-12" />
                                        <motion.div initial={{ opacity: 0, scale: 0.5, y: 20 }} whileInView={{ opacity: 1, scale: 1, y: 0 }} viewport={{ once: true }}
                                            className="relative group/seal cursor-pointer hover:scale-110 transition-transform"
                                            onClick={() => triggerComment('west', COMPATIBILITY_INTERACTIVE_COMMENTS.west.seal)}
                                        >
                                            <div className="absolute inset-0 bg-red-600/20 blur-2xl rounded-full group-hover/seal:bg-red-600/40 transition-colors" />
                                            <img src={WesternSeal} alt="왁스 실" className="w-32 h-32 object-contain relative z-10 drop-shadow-[0_15px_25px_rgba(0,0,0,0.6)]" />
                                        </motion.div>

                                    </div>
                                </div>
                            </div>

                            <div className="w-full flex flex-col items-center mt-24 mb-16">
                                <motion.button whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} onClick={() => handleTypeChange('east')} className="px-12 py-5 bg-white text-indigo-900 rounded-full font-black text-lg shadow-[0_0_50px_rgba(255,255,255,0.2)] hover:shadow-[0_0_60px_rgba(255,255,255,0.4)] transition-all flex items-center gap-3">
                                    {eastCharName}의 사주 & 명리 보고서 보기
                                    <ChevronRight size={24} />
                                </motion.button>
                            </div>
                        </motion.div>

                        <CharacterGuide
                            region="west"
                            theme="indigo"
                            characterId={settings.west}
                            characterName={westCharName}
                            activeComment={activeComment?.speaker === 'west' ? activeComment.text : null}
                            onCommentClick={() => setActiveComment(null)}
                            position="left"
                        />
                    </Fragment>
                )}
            </AnimatePresence >
        </div >
    );
};

export default CompatibilityResultView;
