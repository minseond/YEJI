import { useState } from 'react';
import { motion } from 'framer-motion';
import { Calendar, ChevronRight, Sparkles, Scroll } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { SajuHistoryResponse } from '../../api/saju';
import ConstellationViewer from '../features/ConstellationViewer';
import FourElementsRadar from '../charts/FourElementsRadar';
import FiveElementsRadar from '../charts/FiveElementsRadar';
import { EAST_ELEMENTS } from '../../utils/domainMapping';

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

interface HistoryListSajuProps {
    data: SajuHistoryResponse | null;
    isLoading: boolean;
}

// Western Elements Colors
const WESTERN_ELEMENT_COLORS: Record<string, { bg: string, text: string, border: string }> = {
    fire: { bg: 'bg-orange-500/20', text: 'text-orange-400', border: 'border-orange-500/30' },
    earth: { bg: 'bg-amber-700/20', text: 'text-amber-600', border: 'border-amber-700/30' },
    air: { bg: 'bg-sky-400/20', text: 'text-sky-300', border: 'border-sky-400/30' },
    water: { bg: 'bg-indigo-500/20', text: 'text-indigo-400', border: 'border-indigo-500/30' }
};

const EASTERN_ELEMENT_COLORS: Record<string, { bg: string, text: string, border: string }> = {
    wood: { bg: 'bg-green-600/10', text: 'text-green-800', border: 'border-green-600/20' },
    fire: { bg: 'bg-red-600/10', text: 'text-red-800', border: 'border-red-600/20' },
    earth: { bg: 'bg-amber-600/10', text: 'text-amber-800', border: 'border-amber-600/20' },
    metal: { bg: 'bg-stone-500/10', text: 'text-stone-700', border: 'border-stone-500/20' },
    water: { bg: 'bg-blue-600/10', text: 'text-blue-800', border: 'border-blue-600/20' }
};

const HistoryListSaju = ({ data, isLoading }: HistoryListSajuProps) => {
    const navigate = useNavigate();
    const [viewMode, setViewMode] = useState<'eastern' | 'western'>('eastern');

    const handleModeChange = (mode: 'eastern' | 'western') => {
        if (viewMode === mode) return;
        setViewMode(mode);
    };

    if (isLoading) {
        return <div className="text-white/50 text-center py-20 font-['Gowun_Batang']">사주 기록을 불러오는 중입니다...</div>;
    }

    if (!data || !data.analysis_result) {
        return (
            <div className="text-center py-20 space-y-4">
                <div className="text-white/30 font-light font-['Gowun_Batang']">아직 분석된 사주 정보가 없습니다.</div>
                <button
                    onClick={() => navigate('/home', { state: { showSaju: true } })}
                    className="px-6 py-2 bg-amber-900/40 hover:bg-amber-800/60 border border-amber-700/30 rounded-full text-amber-200 text-sm transition-all"
                >
                    내 사주 분석하러 가기
                </button>
            </div>
        );
    }

    const { user_info, analysis_result } = data;
    const eastern = analysis_result.eastern;
    const western = analysis_result.western;
    const chart = eastern.chart;
    const fiveElements = eastern.stats.five_elements;
    const yinYangRatio = eastern.stats.yin_yang_ratio;

    // Calculate element distribution for visualization from elements_list
    const elementsList = fiveElements?.elements_list || [];
    const elementDist: Record<string, number> = {};
    elementsList.forEach(elem => {
        const codeMap: Record<string, string> = {
            'wood': 'wood', '목': 'wood',
            'fire': 'fire', '화': 'fire',
            'earth': 'earth', '토': 'earth',
            'metal': 'metal', '금': 'metal',
            'water': 'water', '수': 'water'
        };
        const key = codeMap[elem.code.toLowerCase()] || elem.code.toLowerCase();
        elementDist[key] = elem.percent;
    });

    // Western Data
    const westernElements = western.stats.element_4_distribution || [];
    const mainSign = western.stats.main_sign?.name || 'Unknown Sign';

    const cardContainerStyles = viewMode === 'eastern'
        ? "border-[#d7ccc8] hover:border-[#bcaaa4]"
        : "border-indigo-900/30 hover:border-indigo-600/50";

    const cardBgColor = viewMode === 'eastern'
        ? "bg-[#f4efe4]"
        : "bg-black/80";

    const glowColor = viewMode === 'eastern' ? 'bg-stone-200/50' : 'bg-indigo-500/10';

    return (
        <div className="space-y-6">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className={`relative ${cardContainerStyles} ${cardBgColor} border rounded-3xl p-8 backdrop-blur-md transition-all duration-500 group shadow-[0_8px_32px_rgba(0,0,0,0.1)] overflow-hidden`}
            >
                {/* Background Layer - Eastern */}
                <div
                    className={`absolute inset-0 z-0 bg-cover bg-center transition-opacity duration-500 pointer-events-none ${viewMode === 'eastern' ? 'opacity-20' : 'opacity-0'}`}
                    style={{ backgroundImage: "url('/assets/bg/saju_east.png')" }}
                />

                {/* Background Layer - Western */}
                <div
                    className={`absolute inset-0 z-0 bg-cover bg-center transition-opacity duration-500 pointer-events-none ${viewMode === 'western' ? 'opacity-20' : 'opacity-0'}`}
                    style={{ backgroundImage: "url('/assets/bg/saju_west.png')" }}
                />

                {/* Edge Gradient / Vignette Overlay */}
                <div className={`absolute inset-0 z-0 pointer-events-none rounded-3xl transition-all duration-500 ${viewMode === 'eastern' ? 'shadow-[inset_0_0_40px_rgba(121,85,72,0.1)]' : 'shadow-[inset_0_0_60px_rgba(0,0,0,0.8)]'}`} />
                {/* Decorative Corner Elements */}
                <div className={`absolute top-0 right-0 w-32 h-32 ${glowColor} blur-3xl rounded-full -translate-y-16 translate-x-16`} />
                <div className={`absolute bottom-0 left-0 w-32 h-32 ${glowColor} blur-3xl rounded-full translate-y-16 -translate-x-16`} />

                {/* Header */}
                <div className={`relative z-10 mb-8 pb-6 border-b ${viewMode === 'eastern' ? 'border-stone-300' : 'border-white/10'} flex justify-between items-start`}>
                    <div className={viewMode === 'eastern' ? "font-['Hahmlet']" : "font-['GmarketSans']"}>
                        <h3 className={`text-2xl font-bold ${viewMode === 'eastern' ? 'text-stone-900' : 'text-indigo-100 group-hover:text-indigo-300'} transition-colors mb-2`}>
                            {viewMode === 'eastern' ? '나의 사주 팔자' : '나의 점성술 분석'}
                        </h3>
                        <p className={`text-sm ${viewMode === 'eastern' ? 'text-stone-500' : 'text-indigo-200/60'}`}>
                            {user_info?.name || '사용자'}님 ({user_info?.gender === 'M' ? '남성' : '여성'})
                            {user_info?.birth_year && user_info?.birth_month && user_info?.birth_day && (
                                <> · {user_info.birth_year}년 {user_info.birth_month}월 {user_info.birth_day}일</>
                            )}
                        </p>
                    </div>

                    {/* View Switcher Toggle */}
                    <div className={`${viewMode === 'eastern' ? 'bg-stone-200' : 'bg-white/5'} p-1 rounded-full flex gap-1 border ${viewMode === 'eastern' ? 'border-stone-300' : 'border-white/10'}`} onClick={(e) => e.stopPropagation()}>
                        <button
                            onClick={() => handleModeChange('eastern')}
                            className={`px-4 py-2 rounded-full transition-all flex items-center gap-2 ${viewMode === 'eastern' ? 'bg-amber-700 text-white shadow-md' : 'text-amber-500/80 hover:text-amber-400'}`}
                        >
                            <Scroll size={16} />
                            <span className="text-sm font-bold font-['JoseonPalace']">사주팔자</span>
                        </button>
                        <button
                            onClick={() => handleModeChange('western')}
                            className={`px-4 py-2 rounded-full transition-all flex items-center gap-2 ${viewMode === 'western' ? 'bg-indigo-600/80 text-white shadow-lg' : 'text-purple-600 hover:text-purple-500'}`}
                        >
                            <Sparkles size={16} />
                            <span className="text-sm font-bold font-['GmarketSans']">점성술</span>
                        </button>
                    </div>
                </div>

                {/* Main Content Grid */}
                <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-6 mb-8 min-h-[400px]">
                    {/* Loader Overlay */}


                    {/* Content */}

                    {viewMode === 'eastern' ? (
                        <div
                            className="col-span-1 md:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-6 font-['Hahmlet'] animate-in fade-in duration-0"
                        >
                            {/* 1. 사주팔자 (Four Pillars) */}
                            <div className="col-span-1 md:col-span-3 bg-white/50 backdrop-blur-sm rounded-2xl p-8 border border-stone-300 hover:border-stone-400 transition-all shadow-sm">
                                <h4 className="text-stone-500 text-xs uppercase tracking-widest font-bold mb-6 flex items-center gap-2">
                                    사주팔자 (四柱八字)
                                </h4>
                                <div className="grid grid-cols-4 gap-4 h-[160px]">
                                    {[
                                        { label: '년(年)', gan: chart.year.gan, ji: chart.year.ji },
                                        { label: '월(月)', gan: chart.month.gan, ji: chart.month.ji },
                                        { label: '일(日)', gan: chart.day.gan, ji: chart.day.ji },
                                        { label: '시(時)', gan: chart.hour.gan, ji: chart.hour.ji }
                                    ].map((pillar, idx) => {
                                        const GAN_MAP: Record<string, string> = { '甲': '갑', '乙': '을', '丙': '병', '丁': '정', '戊': '무', '己': '기', '庚': '경', '辛': '신', '壬': '임', '癸': '계' };
                                        const JI_MAP: Record<string, string> = { '子': '자', '丑': '축', '寅': '인', '卯': '묘', '辰': '진', '巳': '사', '午': '오', '未': '미', '申': '신', '酉': '유', '戌': '술', '亥': '해' };

                                        // Get element color from domain mapping logic would be better but let's use a simple one
                                        return (
                                            <div
                                                key={idx}
                                                className="flex flex-col items-center justify-center p-4 rounded-2xl h-full transition-all bg-stone-50/50 border border-stone-200"
                                            >
                                                <span className="text-xs text-stone-400 mb-2">{pillar.label}</span>
                                                <div className="flex flex-col items-center leading-tight gap-2">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs text-stone-400 w-4 text-center">{GAN_MAP[pillar.gan] || ''}</span>
                                                        <span className="text-3xl md:text-4xl font-serif font-bold text-stone-900">{pillar.gan}</span>
                                                    </div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs text-stone-400 w-4 text-center">{JI_MAP[pillar.ji] || ''}</span>
                                                        <span className="text-3xl md:text-4xl font-serif font-bold text-stone-800">{pillar.ji}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* 2. 오행 (Five Elements) */}
                            <div className="col-span-1 md:col-span-2 bg-white/50 backdrop-blur-sm rounded-2xl p-8 border border-stone-300 hover:border-stone-400 transition-all flex flex-col items-center shadow-sm">
                                <h4 className="text-stone-500 text-xs uppercase tracking-widest font-bold mb-4 w-full text-left">
                                    오행 분포 (五行)
                                </h4>
                                <div className="relative w-full aspect-square flex items-center justify-center min-h-[200px] max-h-[250px] mb-4">
                                    <div className="w-full h-full max-w-[280px]">
                                        <FiveElementsRadar data={elementsList} isActive={viewMode === 'eastern'} textColor="text-stone-800" />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-x-4 gap-y-3 w-full">
                                    {elementsList.map((el) => {
                                        const code = el.code.toUpperCase(); // Ensure uppercase for mapping
                                        const lowerCode = code.toLowerCase(); // For color mapping keys
                                        const colors = EASTERN_ELEMENT_COLORS[lowerCode] || EASTERN_ELEMENT_COLORS.earth;
                                        return (
                                            <div key={el.code} className={`flex justify-between items-center text-sm p-2 rounded-lg border ${colors.bg} ${colors.border}`}>
                                                <span className="text-stone-600 font-bold flex items-center gap-1">
                                                    <span>{EAST_ELEMENTS[code]?.hanja}</span>
                                                    <span className="text-xs opacity-70">({EAST_ELEMENTS[code]?.label})</span>
                                                </span>
                                                <span className={`${colors.text} font-black text-base`}>{Math.round(el.percent)}%</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* 3. 음양 (Yin-Yang) */}
                            <div className="col-span-1 md:col-span-1 bg-white/50 backdrop-blur-sm rounded-2xl p-8 border border-stone-300 hover:border-stone-400 transition-all flex flex-col justify-center shadow-sm">
                                <h4 className="text-stone-500 text-xs uppercase tracking-widest font-bold mb-6">
                                    음양 조화 (陰陽)
                                </h4>
                                <div className="flex flex-col items-center gap-6">
                                    <div className="relative w-28 h-28">
                                        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-lg">
                                            <path
                                                d="M 50 0 A 50 50 0 0 1 50 100 A 25 25 0 0 1 50 50 A 25 25 0 0 0 50 0"
                                                fill="#1c1917"
                                            />
                                            <path
                                                d="M 50 0 A 50 50 0 0 0 50 100 A 25 25 0 0 0 50 50 A 25 25 0 0 1 50 0"
                                                fill="#ffffff"
                                            />
                                            <circle cx="50" cy="25" r="8" fill="#ffffff" />
                                            <circle cx="50" cy="75" r="8" fill="#1c1917" />
                                            <circle cx="50" cy="50" r="50" fill="none" stroke="#d7ccc8" strokeWidth="1" />
                                        </svg>
                                    </div>
                                    <div className="text-center">
                                        <div className="flex justify-center gap-4 text-sm font-bold text-stone-800 mb-2">
                                            <span>陰(음) {Math.round(yinYangRatio?.yin || 50)}%</span>
                                            <span>•</span>
                                            <span>陽(양) {Math.round(yinYangRatio?.yang || 50)}%</span>
                                        </div>
                                        <p className="text-xs text-stone-500 italic">
                                            {yinYangRatio?.summary || '음양의 조화'}
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        <div
                            className="col-span-1 md:col-span-3 grid grid-cols-1 md:grid-cols-3 gap-6 font-['GmarketSans'] animate-in fade-in duration-0"
                        >
                            {/* 1. Star Sign & Keywords */}
                            <div className="col-span-1 md:col-span-3 bg-black/40 backdrop-blur-md rounded-2xl p-8 border border-indigo-500/20 hover:border-indigo-500/40 transition-all flex flex-col justify-center items-center text-center">
                                <h4 className="text-indigo-300 text-xs uppercase tracking-widest font-bold mb-6 w-full text-left">
                                    탄생 별자리 (Zodiac)
                                </h4>
                                <div className="mb-6 relative w-32 h-32 flex items-center justify-center">
                                    <div className="absolute inset-0 bg-indigo-500/30 rounded-full blur-3xl animate-pulse" />
                                    <div className="scale-[1.2] origin-center z-10 drop-shadow-[0_0_20px_rgba(99,102,241,0.5)]">
                                        <ConstellationViewer zodiacName={ZODIAC_ENGLISH_MAP[mainSign] || 'Aries'} />
                                    </div>
                                </div>
                                <div className="text-4xl font-bold text-white mb-4 drop-shadow-[0_2px_10px_rgba(0,0,0,0.5)]">{mainSign}</div>
                                <div className="flex flex-wrap gap-3 justify-center">
                                    {western.stats.keywords?.slice(0, 4).map((k, i) => (
                                        <span key={i} className="text-xs px-3 py-1.5 bg-indigo-500/20 text-indigo-100 border border-indigo-500/40 rounded-full">
                                            #{k.label}
                                        </span>
                                    ))}
                                </div>
                            </div>

                            {/* 2. Four Elements */}
                            <div className="col-span-1 md:col-span-2 bg-black/40 backdrop-blur-md rounded-2xl p-8 border border-indigo-500/20 hover:border-indigo-500/40 transition-all">
                                <h4 className="text-indigo-300 text-xs uppercase tracking-widest font-bold mb-6">
                                    4원소 분포 (Elements)
                                </h4>
                                <div className="relative h-64 flex items-center justify-center overflow-hidden">
                                    <div className="w-full h-full flex items-center justify-center max-w-[280px]">
                                        <FourElementsRadar data={westernElements} isActive={viewMode === 'western'} />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-x-6 gap-y-3 mt-8">
                                    {westernElements.slice(0, 4).map((el) => {
                                        const colors = WESTERN_ELEMENT_COLORS[el.code?.toLowerCase()] || WESTERN_ELEMENT_COLORS.fire;
                                        return (
                                            <div key={el.code} className="flex justify-between items-center text-sm p-2 bg-white/5 rounded-lg border border-white/5">
                                                <span className="text-indigo-200/60 font-medium">{el.label}</span>
                                                <span className={`${colors.text} font-bold text-base`}>{Math.round(el.percent)}%</span>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* 3. Western Modalities / Info */}
                            <div className="col-span-1 md:col-span-1 bg-black/40 backdrop-blur-md rounded-2xl p-8 border border-indigo-500/20 hover:border-indigo-500/40 transition-all flex flex-col justify-center">
                                <h4 className="text-indigo-300 text-xs uppercase tracking-widest font-bold mb-8">
                                    점성술 특성 (Traits)
                                </h4>
                                <div className="space-y-8">
                                    <div>
                                        <div className="text-xs text-indigo-400/60 mb-3 uppercase tracking-wider font-bold">Main Modality</div>
                                        <div className="flex flex-col gap-3">
                                            <div className="text-2xl font-bold text-indigo-50">
                                                {western.stats.modality_3_distribution?.[0]?.label || 'Cardinal'}
                                            </div>
                                            <span className="w-fit px-4 py-1.5 rounded-full bg-indigo-500/30 border border-indigo-500/50 text-xs text-indigo-100 font-bold uppercase tracking-widest">
                                                {western.stats.modality_3_distribution?.[0]?.code || 'CARDINAL'}
                                            </span>
                                        </div>
                                    </div>
                                    <div className="p-5 bg-white/5 border border-white/10 rounded-2xl shadow-inner">
                                        <p className="text-sm text-indigo-100/70 leading-relaxed italic text-center">
                                            "{western.stats.modality_summary || '별들이 당신의 에너지를 안내합니다.'}"
                                        </p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                </div>

                {/* Summary Section */}
                <div className={`relative z-10 ${viewMode === 'eastern' ? 'bg-[#e7e0d3] border-stone-300' : 'bg-indigo-950/30 border-indigo-900/20'} rounded-xl p-6 border transition-colors shadow-inner ${viewMode === 'eastern' ? "font-['Hahmlet']" : "font-['GmarketSans']"}`}>
                    <p className={`text-base ${viewMode === 'eastern' ? 'text-stone-800 font-bold' : 'text-indigo-100/90'} leading-relaxed`}>
                        {viewMode === 'eastern'
                            ? (eastern.final_verdict?.summary || "상세한 사주 분석 결과가 준비되어 있습니다.")
                            : (western.fortune_content?.overview || "별들이 전하는 오늘의 운명 분석입니다.")
                        }
                    </p>
                </div>

                {/* Footer */}
                <div className={`relative z-10 mt-6 pt-4 border-t ${viewMode === 'eastern' ? 'border-stone-200' : 'border-white/5'} flex justify-between items-center ${viewMode === 'eastern' ? "font-['Hahmlet']" : "font-['GmarketSans']"}`}>
                    <span className={`flex items-center gap-2 text-xs ${viewMode === 'eastern' ? 'text-stone-400' : 'text-indigo-300/40'}`}>
                        <Calendar size={12} />
                        최근 분석 기록
                    </span>
                    <button
                        onClick={() => navigate('/history/saju', { state: { viewMode } })}
                        className={`flex items-center gap-2 text-xl px-4 py-1.5 rounded-xl ${viewMode === 'eastern' ? 'text-stone-950 hover:bg-amber-600/10' : 'text-indigo-200 hover:bg-indigo-600/20'} transition-all font-black group pointer-events-auto`}
                    >
                        상세보기
                        <ChevronRight size={24} className="group-hover:translate-x-1 transition-transform" />
                    </button>
                </div>
            </motion.div >


            <div className="text-center text-xs text-white/20 pt-4 font-['Gowun_Batang']">
                * 사주 분석 결과는 가장 최근의 데이터 1건만 유지됩니다.
            </div>
        </div >
    );
};

export default HistoryListSaju;
