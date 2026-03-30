import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface FortuneChatOverlayProps {
    userQuestion: string;
    onComplete: (finalAnswer: string) => void;
}

interface DialogueLine {
    speaker: 'east' | 'west';
    text: string;
}

const INITIAL_DIALOGUE: DialogueLine[] = [
    { speaker: 'east', text: "이 사주... '비견(比肩)'이 너무 강해! 재물이 들어오는 족족 불타 없어질 형국이야." },
    { speaker: 'west', text: "잠깐만요! 차트를 보세요. 목성(Jupiter)이 제10하우스, 즉 직업의 방에서 강력하게 빛나고 있어요." },
    { speaker: 'east', text: "직업운이 좋다는 건 인정하네. 하지만 '군겁쟁재(群劫爭財)', 주변에 돈을 노리는 자가 너무 많아." },
    { speaker: 'west', text: "그건 토성(Saturn)의 위치로 보완됩니다. 시련은 있겠지만 결국엔 막대한 부를 축적할 구조예요." },
    { speaker: 'east', text: "흠... 그렇다면 불필요한 지출만 막는다면, 거부가 될 상이긴 하군." },
    { speaker: 'west', text: "맞아요. 우리의 결론은 하나로 모이는군요. '강한 소비 욕구만 통제하라'." },
];

const FOLLOW_UP_RESPONSES: DialogueLine[] = [
    { speaker: 'east', text: "그 질문... 역시 자네도 그 부분이 걱정되는가 보군." },
    { speaker: 'west', text: "걱정 마세요. 수성(Mercury)이 역행하고 있어 잠시 혼란스러울 뿐입니다." },
    { speaker: 'east', text: "내년 초, '정재(正財)'의 운이 들어오니 그때 승부를 봐야 해." },
    { speaker: 'west', text: "별들의 주기도 일치해요. 3월, 큰 기회가 올 겁니다." },
    { speaker: 'east', text: "자, 이제 나아갈 길이 명확해졌네." },
];

const FortuneChatOverlay = ({ userQuestion, onComplete }: FortuneChatOverlayProps) => {
    const [step, setStep] = useState(0);
    const [dialogue, setDialogue] = useState<DialogueLine[]>(INITIAL_DIALOGUE);
    const [isFinished, setIsFinished] = useState(false);

    // Prompt State
    const [showPrompt, setShowPrompt] = useState(false);
    const [promptValue, setPromptValue] = useState("");

    // If user asks a follow-up, we append more dialogue
    const [hasAskedFollowUp, setHasAskedFollowUp] = useState(false);

    // Initial Setup: If user asked a question at start, maybe modify intro? 
    // For now, we stick to generic intro, but could inject userQuestion context.

    // Handle user input to advance dialogue
    const advanceDialogue = () => {
        if (step < dialogue.length - 1) {
            setStep(prev => prev + 1);
        } else {
            setIsFinished(true); // Reached end of current script
        }
    };

    const handleFollowUpSubmit = () => {
        if (!promptValue.trim()) return;

        setShowPrompt(false);
        setHasAskedFollowUp(true);
        setIsFinished(false); // Resume chat

        // Append follow-up dialogue
        const newLines = [
            ...FOLLOW_UP_RESPONSES
        ];

        // Update dialogue array and continue
        setDialogue(prev => [...prev, ...newLines]);
        setStep(prev => prev + 1);
    };

    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (showPrompt) return; // Don't advance if typing in prompt
            if (e.code === 'Space' || e.code === 'Enter') {
                e.preventDefault();
                advanceDialogue();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [step, isFinished, showPrompt, dialogue.length]);

    const currentLine = dialogue[step];

    return (
        <div
            onClick={!showPrompt ? advanceDialogue : undefined}
            className="absolute inset-0 z-50 flex items-center justify-center bg-black/40 overflow-hidden cursor-pointer"
        >
            {/* Ambient Effects - Dynamic based on speaker */}
            <div className={`absolute inset-0 transition-colors duration-1000 ${currentLine?.speaker === 'east'
                ? 'bg-gradient-to-r from-amber-900/40 to-black'
                : 'bg-gradient-to-l from-indigo-900/40 to-black'
                }`} />

            {/* Context Info (User's initial topic) */}
            <div className="absolute top-8 left-0 right-0 text-center pointer-events-none z-40">
                <div className="inline-block px-4 py-1 bg-white/5 backdrop-blur-sm rounded-full border border-white/10 text-white/40 text-sm">
                    주제: <span className="text-amber-200">{userQuestion || "운세 전반"}</span>
                </div>
            </div>

            {/* Characters Container - Centered Vertically */}
            <div className="relative w-full max-w-6xl h-full flex justify-between items-center pointer-events-none px-4 md:px-10">

                {/* EASTERN CHARACTER */}
                <motion.div
                    initial={{ x: -300, opacity: 0 }}
                    animate={{
                        x: 0,
                        opacity: 1,
                        scale: currentLine?.speaker === 'east' ? 1.1 : 1.0,
                        filter: currentLine?.speaker === 'east' ? 'brightness(1.2)' : 'brightness(0.6) grayscale(0.5)'
                    }}
                    transition={{ type: "spring", stiffness: 100, damping: 20 }}
                    className="relative w-1/2 md:w-1/3 h-[60vh] flex items-center justify-center z-10"
                >
                    <img src="/assets/images/east.png" alt="Eastern Sage" className="w-full h-full object-contain drop-shadow-[0_0_50px_rgba(251,191,36,0.3)]" />
                </motion.div>

                {/* WESTERN CHARACTER */}
                <motion.div
                    initial={{ x: 300, opacity: 0 }}
                    animate={{
                        x: 0,
                        opacity: 1,
                        scale: currentLine?.speaker === 'west' ? 1.1 : 1.0,
                        filter: currentLine?.speaker === 'west' ? 'brightness(1.2)' : 'brightness(0.6) grayscale(0.5)'
                    }}
                    transition={{ type: "spring", stiffness: 100, damping: 20 }}
                    className="relative w-1/2 md:w-1/3 h-[60vh] flex items-center justify-center z-10"
                >
                    <img src="/assets/images/west.png" alt="Western Astrologer" className="w-full h-full object-contain drop-shadow-[0_0_50px_rgba(129,140,248,0.3)]" />
                </motion.div>
            </div>

            {/* Dialogue Area */}
            {!isFinished && (
                <div className="absolute bottom-1/4 left-0 right-0 flex justify-center z-50 px-4">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={step}
                            initial={{ opacity: 0, y: 20, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            exit={{ opacity: 0, y: -20, scale: 0.95 }}
                            transition={{ duration: 0.2 }}
                            className={`
                                relative max-w-2xl w-full p-8 md:p-10 rounded-2xl border-2 shadow-2xl backdrop-blur-xl
                                ${currentLine.speaker === 'east'
                                    ? 'bg-black/70 border-amber-500/50 text-amber-50 rounded-tl-none ml-10 md:ml-0 md:-translate-x-20 shadow-amber-900/20'
                                    : 'bg-black/70 border-indigo-500/50 text-indigo-50 rounded-tr-none mr-10 md:mr-0 md:translate-x-20 shadow-indigo-900/20'
                                }
                            `}
                        >
                            {/* Speaker Label */}
                            <div className={`
                                absolute -top-5 px-6 py-1.5 rounded-full text-sm font-bold uppercase tracking-widest shadow-lg border border-white/10
                                ${currentLine.speaker === 'east' ? 'left-0 bg-amber-700 text-white' : 'right-0 bg-indigo-700 text-white'}
                            `}>
                                {currentLine.speaker === 'east' ? '동양 도사' : '서양 점성술사'}
                            </div>

                            <p className="text-xl md:text-3xl font-['Gowun_Batang'] leading-relaxed text-center drop-shadow-md whitespace-pre-line">
                                "{currentLine.text}"
                            </p>

                            {/* Interaction Hint */}
                            <div className="absolute bottom-3 right-4 text-xs text-white/30 animate-pulse uppercase tracking-widest">
                                Click or Space to Continue ▶
                            </div>
                        </motion.div>
                    </AnimatePresence>
                </div>
            )}

            {/* Final Options Overlay */}
            <AnimatePresence>
                {isFinished && !showPrompt && (
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="absolute inset-0 z-[60] flex flex-col items-center justify-center bg-black/60 backdrop-blur-sm"
                    >
                        <h2 className="text-4xl md:text-5xl font-['Nanum_Brush_Script'] text-white mb-12 drop-shadow-[0_0_15px_rgba(255,255,255,0.5)]">
                            {hasAskedFollowUp ? "천기누설이 완료되었습니다." : "운명의 해석이 완료되었습니다."}
                        </h2>

                        <div className="flex flex-col md:flex-row gap-6">
                            {!hasAskedFollowUp && (
                                <button
                                    onClick={(e) => { e.stopPropagation(); setShowPrompt(true); }}
                                    className="px-10 py-4 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-white text-lg transition-all hover:scale-105 active:scale-95 flex items-center gap-3 group"
                                >
                                    <span className="group-hover:rotate-12 transition-transform text-2xl">💬</span>
                                    <span>추가 질문하기</span>
                                </button>
                            )}

                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    onComplete(hasAskedFollowUp
                                        ? "내년 3월, 정재운과 목성의 조화로 인생 일대의 재물 기회가 찾아옵니다."
                                        : "직업적 성공으로 큰 돈을 벌지만, 소비 통제가 관건인 '대기만성형 부자' 운세입니다.");
                                }}
                                className="px-10 py-4 rounded-xl bg-gradient-to-r from-amber-600 to-indigo-600 hover:from-amber-500 hover:to-indigo-500 text-white text-lg font-bold shadow-lg shadow-indigo-900/50 transition-all hover:scale-105 active:scale-95 flex items-center gap-3"
                            >
                                <span>결과 확인하기</span>
                                <span className="text-xl">✨</span>
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Prompt Modal (Chat Follow-up) */}
            <AnimatePresence>
                {showPrompt && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="absolute inset-0 z-[70] flex items-center justify-center bg-black/80 backdrop-blur-md p-4"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="w-full max-w-2xl bg-[#1a1a1a] border border-white/10 rounded-2xl p-6 md:p-8 shadow-2xl relative">
                            <button
                                onClick={() => setShowPrompt(false)}
                                className="absolute top-4 right-4 text-white/50 hover:text-white"
                            >
                                ✕
                            </button>

                            <h3 className="text-2xl font-['Gowun_Batang'] text-amber-100 mb-2">무엇이 궁금하신가요?</h3>
                            <p className="text-white/40 text-sm mb-6">구체적인 질문을 입력하면 도사님들이 답변해드립니다.</p>

                            <textarea
                                value={promptValue}
                                onChange={(e) => setPromptValue(e.target.value)}
                                placeholder="예: 재물운이 언제쯤 좋아질까요? / 저의 연애 스타일은 어떤가요?"
                                className="w-full h-32 bg-black/30 text-white p-4 rounded-xl border border-white/10 focus:border-amber-500/50 focus:outline-none resize-none mb-6 placeholder:text-white/20"
                            />

                            <div className="flex justify-end gap-3">
                                <button
                                    onClick={() => setShowPrompt(false)}
                                    className="px-6 py-2 rounded-lg text-white/60 hover:bg-white/5 transition-colors"
                                >
                                    취소
                                </button>
                                <button
                                    onClick={handleFollowUpSubmit}
                                    className="px-8 py-2 rounded-lg bg-amber-600 hover:bg-amber-500 text-white font-medium transition-colors"
                                >
                                    질문하기
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Background Particles overlay */}
            <div className="absolute inset-0 pointer-events-none mix-blend-screen opacity-50">
                {/* We can reuse ParticleBackground here if passed as prop or imported, 
                    but simple CSS pulse or pre-rendered effects work for cutscenes */}
            </div>
        </div>
    );
};

export default FortuneChatOverlay;
