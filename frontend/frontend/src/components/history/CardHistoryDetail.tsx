import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getCardHistoryDetail, type CardResultDetailResponse } from '../../api/card';
import CardResultView from '../results/CardResultView';

const CardHistoryDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState<CardResultDetailResponse | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDetail = async () => {
            if (!id) return;
            try {
                const response = await getCardHistoryDetail(Number(id));
                if (response) {
                    setData(response);
                }
            } catch (error) {
                console.error("Failed to fetch detail:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchDetail();
    }, [id]);

    if (loading) {
        return <div className="min-h-screen bg-stone-950 flex items-center justify-center text-white">로딩 중...</div>;
    }

    if (!data) {
        return <div className="min-h-screen bg-stone-950 flex items-center justify-center text-white">데이터를 불러올 수 없습니다.</div>;
    }

    return (
        <div className="fixed inset-0 z-50 bg-black text-white overflow-hidden">
            <CardResultView
                data={data}
                onBack={() => navigate('/history', { state: { tab: 'card' } })}
                mode="history"
            />
        </div>
    );
};

export default CardHistoryDetail;
