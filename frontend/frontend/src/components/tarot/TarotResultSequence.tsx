import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowLeft, X } from 'lucide-react';
import TarotCardReveal from './TarotCardReveal';
import TarotFinalSummary from './TarotFinalSummary';

interface CardData {
    stepTitle: string;
    cardName: string;
    cardDescription: string;
    cardImageUrl?: string;
    isReversed: boolean;
}

interface TarotResultSequenceProps {
    cards: CardData[];
    overallSummary: string;
    onRestart?: () => void;
    onShuffle?: () => void;
    onExit: () => void;
    onBack?: () => void;
}

const TarotResultSequence = ({ cards, overallSummary, onRestart, onShuffle, onExit, onBack }: TarotResultSequenceProps) => {
    const [currentPage, setCurrentPage] = useState<number>(0);

    const handleBackLocal = () => {
        if (currentPage > 0) {
            setCurrentPage((prev: number) => prev - 1);
        } else if (onBack) {
            onBack();
        }
    };

    const handleNext = () => {
        if (currentPage < cards.length) {
            setCurrentPage((prev: number) => prev + 1);
        }
    };

    return (
        <div className="relative w-full h-full">
            {/* Top Navigation - Western Style */}
            <div className="absolute top-8 left-8 right-8 z-[70] flex justify-between items-center pointer-events-none">
                <motion.button
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    onClick={handleBackLocal}
                    className="pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full bg-purple-950/60 border border-purple-400/40 text-purple-100 shadow-xl hover:bg-purple-900/80 backdrop-blur-xl transition-all font-['Hahmlet'] text-sm"
                >
                    <ArrowLeft size={20} />
                    BACK
                </motion.button>

                <motion.button
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    onClick={onExit}
                    className="pointer-events-auto flex items-center gap-2 px-5 py-2 rounded-full bg-purple-950/60 border border-purple-400/40 text-purple-100 shadow-xl hover:bg-purple-900/80 backdrop-blur-xl transition-all font-['Hahmlet'] text-sm"
                >
                    EXIT
                    <X size={20} />
                </motion.button>
            </div>

            <AnimatePresence mode="wait">
                {currentPage < cards.length ? (
                    <TarotCardReveal
                        key={`card-${currentPage}`}
                        stepTitle={cards[currentPage].stepTitle}
                        cardName={cards[currentPage].cardName}
                        cardDescription={cards[currentPage].cardDescription}
                        cardImageUrl={cards[currentPage].cardImageUrl}
                        isReversed={cards[currentPage].isReversed}
                        onNext={handleNext}
                    />
                ) : (
                    <TarotFinalSummary
                        key="final-summary"
                        cards={cards.map(c => ({
                            stepTitle: c.stepTitle,
                            cardName: c.cardName,
                            isReversed: c.isReversed,
                            cardImageUrl: c.cardImageUrl
                        }))}
                        overallSummary={overallSummary}
                        onRestart={onRestart}
                        onShuffle={onShuffle}
                    />
                )}
            </AnimatePresence>
        </div>
    );
};

export default TarotResultSequence;
