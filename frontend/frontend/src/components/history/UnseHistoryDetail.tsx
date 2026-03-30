import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getUnseDetail, type UnseResultDetail } from '../../api/unse';
import TodayFortuneResult, { type DailyFortuneResult } from '../pages/TodayFortuneResult';
import { getRandomFortuneV2 } from '../../data/dummyFortuneV2';
import { type DualFortuneResultV2 } from '../../data/types';

const CATEGORY_MAP: Record<string, string> = {
    'TOTAL': '종합운',
    'GENERAL': '종합운',
    'LOVE': '연애운',
    'MONEY': '재물운',
    'WEALTH': '재물운',
    'CAREER': '직업운',
    'HEALTH': '건강운',
    'STUDY': '학업운'
};

const UnseHistoryDetail = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const [detailData, setDetailData] = useState<UnseResultDetail | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [mergedResult, setMergedResult] = useState<DualFortuneResultV2 | null>(null);

    useEffect(() => {
        const fetchDetail = async () => {
            if (!id) return;
            try {
                setIsLoading(true);
                const data = await getUnseDetail(Number(id));
                setDetailData(data);

                // Initialize with dummy data structure
                const dummy = getRandomFortuneV2();

                // Construct Merged Result
                // Strategy: Use the historical score/summary for the 'East' side primarily (since it's usually the main one)
                // If 'details' contains structure, we try to use it.
                // For now, we assume 'details' might be a simple object or string, so we map safe defaults.

                const resultData = data.analysis_result || {};
                const eastFortune = resultData.eastern?.fortune || resultData.eastern || {};
                const westFortune = resultData.western?.fortune || resultData.western || {};

                const merged: DualFortuneResultV2 = {
                    eastern: {
                        ...dummy.eastern,
                        ...eastFortune,
                        score: 0, // Score removed as per request
                        final_verdict: {
                            ...dummy.eastern.final_verdict,
                            ...(eastFortune.final_verdict || {}),
                            summary: eastFortune.one_line || eastFortune.summary || (eastFortune.final_verdict?.summary) || "분석 완료",
                            advice: eastFortune.detail || eastFortune.description || (eastFortune.final_verdict?.advice) || "상세 분석 결과입니다."
                        }
                    },
                    western: {
                        ...dummy.western,
                        ...westFortune,
                        score: 0, // Score removed as per request
                        fortune_content: {
                            ...dummy.western.fortune_content,
                            ...(westFortune.fortune_content || {}),
                            overview: westFortune.one_line || westFortune.summary || (westFortune.fortune_content?.overview) || "분석 완료",
                            detailed_analysis: Array.isArray(westFortune.detail)
                                ? westFortune.detail
                                : (westFortune.fortune_content?.detailed_analysis || [{ title: "상세 분석", content: String(westFortune.detail || westFortune.description || "상세 분석 결과입니다.") }]),
                            advice: westFortune.advice || westFortune.detail || (westFortune.fortune_content?.advice) || "오늘의 조언을 참고하세요."
                        }
                    }
                };

                setMergedResult(merged);

            } catch (err) {
                console.error("Failed to fetch unse detail:", err);
                setError("운세 기록을 불러오는 중 오류가 발생했습니다.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchDetail();
    }, [id]);

    const handleBack = () => {
        navigate('/history', { state: { tab: 'fortune' } });
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen bg-black text-white font-['Gowun_Batang']">
                <div className="text-center">
                    <div className="text-xl mb-4">운세 기록을 펼치는 중...</div>
                </div>
            </div>
        );
    }

    if (error || !detailData || !mergedResult) {
        return (
            <div className="flex items-center justify-center h-screen bg-black text-white font-['Gowun_Batang']">
                <div className="text-center space-y-4">
                    <div className="text-red-400">{error || "데이터를 찾을 수 없습니다."}</div>
                    <button
                        onClick={handleBack}
                        className="px-6 py-2 border border-white/20 rounded-full hover:bg-white/10"
                    >
                        돌아가기
                    </button>
                </div>
            </div>
        );
    }

    const resultData = detailData.analysis_result || detailData || {};

    // Deep extraction for Eastern
    const eastFortune = resultData.eastern?.fortune || resultData.eastern || {};
    // Map 'one_liner' from API to summary
    const eastSummary = eastFortune.one_liner || eastFortune.one_line || eastFortune.summary || "분석 결과가 없습니다.";
    const eastDetailsRaw = eastFortune.details || eastFortune.detail || [];
    // Keywords parsing (String `#Tag #Tag` -> Array)
    let eastKeywords: string[] = [];
    if (typeof eastFortune.keyword === 'string') {
        eastKeywords = eastFortune.keyword.split(' ').map((k: string) => k.replace('#', '').trim()).filter((k: string) => k.length > 0);
    } else if (Array.isArray(eastFortune.keywords)) {
        eastKeywords = eastFortune.keywords;
    }

    // Deep extraction for Western
    const westFortune = resultData.western?.fortune || resultData.western || {};
    const westSummary = westFortune.one_liner || westFortune.one_line || westFortune.summary || "분석 결과가 없습니다.";
    const westDetailsRaw = westFortune.details || westFortune.detail || [];
    // Keywords parsing
    let westKeywords: string[] = [];
    if (typeof westFortune.keyword === 'string') {
        westKeywords = westFortune.keyword.split(' ').map((k: string) => k.replace('#', '').trim()).filter((k: string) => k.length > 0);
    } else if (Array.isArray(westFortune.keywords)) {
        westKeywords = westFortune.keywords;
    }

    // Construct merged result for TodayFortuneResult
    const eastResult: DailyFortuneResult = {
        type: `${CATEGORY_MAP[detailData.category?.toUpperCase()] || detailData.category || '운세'} (동양)`,
        score: eastFortune.score || 0,
        summary: eastSummary,
        keywords: eastKeywords.length > 0 ? eastKeywords.slice(0, 3) : [],
        explanation: eastSummary, // Main explanation falls back to summary if no partials
        luckyItem: mergedResult.eastern.lucky.item, // Random if not in history
        details: Array.isArray(eastDetailsRaw) ? eastDetailsRaw : []
    };

    const westResult: DailyFortuneResult = {
        type: `${CATEGORY_MAP[detailData.category?.toUpperCase()] || detailData.category || 'Fortune'} (서양)`,
        score: westFortune.score || 0,
        summary: westSummary,
        keywords: westKeywords.length > 0 ? westKeywords.slice(0, 3) : [],
        explanation: westSummary,
        luckyItem: mergedResult.western.lucky.item,
        details: Array.isArray(westDetailsRaw) ? westDetailsRaw : []
    };

    return (
        <div className="h-screen w-full overflow-hidden relative">
            <TodayFortuneResult
                fortuneType={detailData.category || 'integrated'}
                eastResult={eastResult}
                westResult={westResult}
                staticResult={mergedResult}
                onBack={handleBack}
                onSaveAndExit={handleBack}
                mode="history"
            />
        </div>
    );
};

export default UnseHistoryDetail;
