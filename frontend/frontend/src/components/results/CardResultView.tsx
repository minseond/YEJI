import { useMemo } from 'react';
import type { CardResultDetailResponse } from '../../api/card';
import { HWATU_CARDS } from '../../data/hwatuCards';
import { getHwatuImage } from '../../utils/getHwatuImage';
import HwatuSummaryResult from '../results/HwatuSummaryResult';
import TarotResultView from '../results/TarotResultView';

interface CardResultViewProps {
    data: CardResultDetailResponse;
    onBack: () => void;
    mode?: 'default' | 'history';
}

const CardResultView = ({ data, onBack, mode = 'default' }: CardResultViewProps) => {
    // Determine type: HWATU or TAROT
    const isHwatu = data.category === 'HWATU';

    const resultData = useMemo(() => {
        const aiData = data.aiReading?.data;
        const rawCards = data.cards || [];

        if (isHwatu) {
            // Map Hwatu Cards
            const mappedCards = rawCards.map((card, idx) => {
                const cardId = typeof card.cardCode === 'number' ? card.cardCode : parseInt(card.cardCode as unknown as string);
                const cardInfo = HWATU_CARDS[cardId];

                // Finds nested interpretation if available
                const aiCard = aiData?.cards?.find((c: any) => Number(c.card_code) === cardId);

                const imgPath = getHwatuImage(cardId);

                return {
                    name: cardInfo?.name || `카드 ${cardId}`,
                    img: imgPath,
                    type: aiCard?.position_label || `${idx + 1}번째 패`,
                    desc: aiCard?.keywords ? aiCard.keywords.join(', ') : (cardInfo?.desc || ''),
                    detailedDesc: aiCard?.interpretation || (cardInfo?.detailedDesc || '')
                };
            });

            return {
                cards: mappedCards,
                keyword: aiData?.summary?.overall_theme?.split(' ')[0] || '운명',
                summary: aiData?.summary?.overall_theme || '분석 결과가 없습니다.',
                report: aiData?.summary ? `${aiData.summary.flow_analysis}\n\n[조언]\n${aiData.summary.advice}` : 'AI 분석 내용을 불러올 수 없습니다.',
                lucky: aiData?.lucky
            };
        } else {
            return null;
        }
    }, [data, isHwatu]);

    if (isHwatu) {
        return (
            <div className="w-full h-full bg-black">
                {resultData && (
                    <HwatuSummaryResult
                        data={{
                            cards: resultData.cards as any,
                            keyword: resultData.keyword || '운명',
                            summary: resultData.summary || '결과 없음',
                            report: resultData.report || '상세 내용 없음',
                            lucky: resultData.lucky ? {
                                color: resultData.lucky.color || '',
                                number: resultData.lucky.number || '',
                                direction: resultData.lucky.direction || '',
                                timing: resultData.lucky.timing || '',
                                element: resultData.lucky.element
                            } : undefined,
                            vibe: '운명의 결'
                        }}
                        onRestart={() => { }} // Provide dummy function or null if allowed, but strict typing might require func
                        onExit={onBack}
                        onBack={onBack}
                        mode={mode}
                    />
                )}
            </div>
        );
    } else {
        return (
            <div className="w-full h-full bg-black relative">
                <TarotResultView
                    data={data}
                    onRestart={() => { }} // dummy
                    onExit={onBack}
                    onBack={onBack}
                    mode={mode}
                />
            </div>
        );
    }
};

export default CardResultView;
