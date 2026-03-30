import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { getSajuHistory, type SajuHistoryResponse } from '../../api/saju';
import FortuneResult from '../pages/FortuneResult'; // Correct Component
import { getRandomFortuneV2 } from '../../data/dummyFortuneV2';
import { type DualFortuneResultV2 } from '../../data/types';

const SajuHistoryDetail = () => {
    const navigate = useNavigate();
    const { state } = useLocation();
    const initialViewMode = state?.viewMode || 'eastern';
    const [historyData, setHistoryData] = useState<SajuHistoryResponse | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [mergedResult, setMergedResult] = useState<DualFortuneResultV2 | null>(null);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                setIsLoading(true);
                const data = await getSajuHistory();

                if (!data || !data.analysis_result) {
                    setError("저장된 사주 분석 결과가 없습니다.");
                    setHistoryData(null);
                } else {
                    setHistoryData(data);

                    // MERGE Logic: Deep merge for missing stats (same as TodayFortunePage)
                    const res = data.analysis_result;
                    const dummy = getRandomFortuneV2();

                    const mergeStats = (realStats: any, dummyStats: any) => {
                        if (!realStats) return dummyStats;
                        return {
                            ...dummyStats,
                            ...realStats,
                            five_elements: realStats.five_elements || dummyStats.five_elements,
                            ten_gods: realStats.ten_gods || dummyStats.ten_gods,
                            yin_yang_ratio: realStats.yin_yang_ratio || dummyStats.yin_yang_ratio,
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
                            lucky: res.eastern?.lucky || dummy.eastern.lucky,
                            chart: res.eastern?.chart || dummy.eastern.chart // Ensure chart exists
                        },
                        western: {
                            ...res.western,
                            stats: mergeStats(res.western?.stats, dummy.western.stats),
                            fortune_content: res.western?.fortune_content || dummy.western.fortune_content,
                            lucky: res.western?.lucky || dummy.western.lucky
                        }
                    };
                    setMergedResult(merged);
                }
            } catch (err) {
                console.error("Failed to fetch saju history:", err);
                setError("사주 기록을 불러오는 중 오류가 발생했습니다.");
            } finally {
                setIsLoading(false);
            }
        };

        fetchHistory();
    }, []);

    const handleBack = () => {
        navigate('/history');
    };

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-screen bg-black text-white font-['Gowun_Batang']">
                <div className="text-center">
                    <div className="text-xl mb-4">운명의 기록을 펼치는 중...</div>
                </div>
            </div>
        );
    }

    if (error || !historyData || !mergedResult) {
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

    // Convert User Info Safely
    const safeUserInfo = historyData.user_info || {};
    const userInfo = {
        name: safeUserInfo.name || "사용자",
        gender: (safeUserInfo.gender === 'M' ? 'male' : 'female') as 'male' | 'female',
        year: safeUserInfo.birth_year || 2000,
        month: safeUserInfo.birth_month || 1,
        day: safeUserInfo.birth_day || 1,
        time: safeUserInfo.birth_time || "00:00",
        solarConstellation: mergedResult.western.stats.main_sign?.name || "별자리"
    };

    return (
        <div className="h-screen w-full overflow-hidden relative">
            <FortuneResult
                fortuneResult={mergedResult}
                userInfo={userInfo}
                userQuestion="과거의 기록"
                initialViewMode={initialViewMode}
                onBack={handleBack}
                onRestart={handleBack}
                onSaveAndExit={handleBack}
                mode="history"
            />
        </div>
    );
};

export default SajuHistoryDetail;
