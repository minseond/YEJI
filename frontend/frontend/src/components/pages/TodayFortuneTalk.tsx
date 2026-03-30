import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { type TodayFortuneDataEntry } from '../../data/todayFortuneApi';
import type { DualFortuneResultV2 } from '../../data/types';
import { sendChatTurnStream, type UnseMessage, getRegionByCode } from '../../api/unse';
import { getCharacterImage, getCharacterName, useCharacterSettings } from '../../utils/character';
import { Send, Sparkles, Scroll, ArrowLeft } from 'lucide-react';

// Background mapping - Moved to Parent Components
// import { getCharacterImage, CHARACTER_SETTINGS } from '../../utils/character';


interface DebateOverlayProps {
    fortuneResult: TodayFortuneDataEntry | DualFortuneResultV2 | null;
    conversationTopic?: string;
    onComplete: () => void;
    sessionId: string;
    initialMessages: UnseMessage[];
}

type Emotion = 'neutral' | 'angry' | 'happy' | 'surprise' | 'serious' | 'confident';
type Speaker = 'east' | 'west' | 'user';

interface DialogueLine {
    id: string;
    speaker: Speaker;
    text: string;
    emotion: Emotion;
    isTyping?: boolean; // New flag for typing animation
}

type TalkPhase = 'intro' | 'dialogue_1' | 'choice' | 'input' | 'processing' | 'dialogue_2' | 'end';

const DebateOverlay = ({ fortuneResult, conversationTopic, onComplete, sessionId, initialMessages }: DebateOverlayProps) => {

    const [fullScript, setFullScript] = useState<DialogueLine[]>([]);
    const [step, setStep] = useState(0);
    const [phase, setPhase] = useState<TalkPhase>('choice');
    const [userQuestion, setUserQuestion] = useState('');
    const [isAutoScrolling, setIsAutoScrolling] = useState(true);
    const [isStreaming, setIsStreaming] = useState(false);

    // Initial Character Load (Reactive)
    const settings = useCharacterSettings();
    const EastSajuImg = getCharacterImage('east', settings.east, 'normal');
    const WestStarImg = getCharacterImage('west', settings.west, 'normal');
    const EastName = getCharacterName('east', settings.east);
    const WestName = getCharacterName('west', settings.west);

    const inputRef = useRef<HTMLInputElement>(null);
    const chatContainerRef = useRef<HTMLDivElement>(null);
    const scrollEndRef = useRef<HTMLDivElement>(null);
    const isProcessingRef = useRef(false); // Lock for submission

    const handleScroll = () => {
        if (chatContainerRef.current) {
            const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
            const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
            setIsAutoScrolling(isAtBottom);
        }
    };

    useEffect(() => {
        if (isAutoScrolling && scrollEndRef.current) {
            scrollEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [fullScript, step, isAutoScrolling]);

    // Initialize with greetings
    useEffect(() => {
        if (initialMessages && initialMessages.length > 0 && fullScript.length === 0) {
            const mapped: DialogueLine[] = initialMessages.map((msg, idx) => ({
                id: `init-${idx}`,
                speaker: getRegionByCode(msg.character),
                text: msg.content,
                emotion: 'neutral'
            }));
            setFullScript(mapped);
            setStep(0);
            setPhase('dialogue_1');
        }
    }, [initialMessages]);

    // Advance Conversation
    const handleNext = () => {
        if (phase === 'intro' || phase === 'choice' || phase === 'input' || phase === 'processing') return;

        // Check if we can advance within the current script
        if (step < fullScript.length - 1) {
            setStep(prev => prev + 1);
        } else {
            // End of current flow
            if (isStreaming) {
                // If streaming, wait for more chunks.
                return;
            }
            if (phase === 'dialogue_1') {
                setPhase('choice');
            } else {
                setPhase('choice');
            }
        }
    };

    // Handle Send
    const handleSendQuestion = async () => {
        if (isProcessingRef.current || !userQuestion.trim()) {
            return;
        }
        isProcessingRef.current = true;

        // 1. Add User Message
        const userMsg: DialogueLine = {
            id: `user-${Date.now()}`,
            speaker: 'user',
            text: userQuestion,
            emotion: 'neutral'
        };

        // 2. Add Helper Placeholder (Typing...)
        const loadingMsg: DialogueLine = {
            id: `loading-${Date.now()}`,
            speaker: 'east',
            text: "...",
            emotion: 'neutral',
            isTyping: true
        };

        setFullScript(prev => [...prev, userMsg, loadingMsg]);
        setStep(prev => prev + 2);

        const currentQuestion = userQuestion;
        setUserQuestion("");
        setPhase('processing');
        setIsAutoScrolling(true);
        setIsStreaming(true); // Re-enable streaming flag

        try {
            const stream = sendChatTurnStream({ session_id: sessionId, message: currentQuestion });

            let hasReplacedLoading = false;

            for await (const chunk of stream) {
                // Handle new array-based payload
                if (chunk.messages && Array.isArray(chunk.messages)) {
                    const newLines: DialogueLine[] = chunk.messages.map((msg: any) => ({
                        id: `ans-${Date.now()}-${Math.random()}`,
                        speaker: getRegionByCode(msg.character),
                        text: msg.content,
                        emotion: 'neutral'
                    }));

                    if (newLines.length === 0) continue;

                    setFullScript(prev => {
                        const loadingIdx = prev.findIndex(m => m.isTyping);
                        if (loadingIdx !== -1 && !hasReplacedLoading) {
                            hasReplacedLoading = true;
                            // Replace loading msg with first new msg
                            const updated = [...prev];
                            updated[loadingIdx] = newLines[0];
                            // Append rest
                            return [...updated, ...newLines.slice(1)];
                        } else {
                            // If loading is gone or we already replaced it, just append new ones (if any valid case for this)
                            // Usually we expect one main block.
                            // Validate we aren't adding duplicates if IDs were stable, but here IDs are random.
                            // Assuming backend sends all valid new messages in one go or subsequent events are new messages.
                            if (!hasReplacedLoading) {
                                // Fallback: if no loading msg found, just append
                                return [...prev, ...newLines];
                            }
                            return prev; // Ignore subsequent chunks if we assume one-shot for now, or append if needed
                        }
                    });

                    // Allow clicking again
                    setPhase('dialogue_2');
                }
            }

        } catch (err) {
            console.error("Error in handleSendQuestion:", err);
            setFullScript(prev => {
                // Remove loading message if error occurs
                const last = prev[prev.length - 1];
                if (last.text === '...' && last.isTyping) return prev.slice(0, -1);
                return prev;
            });
            setPhase('choice'); // Return to choice phase on error
        } finally {
            setIsStreaming(false);
            isProcessingRef.current = false;
        }
    };

    // Keyboard
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.code === 'Space' || e.key === ' ' || e.key === 'Enter') && phase !== 'input') {
                e.preventDefault();
                handleNext();
            }
        };
        // Removed Enter key nav here, purely handled in Input onKeyDown for question
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [step, fullScript.length, phase]);

    // Focus Input
    useEffect(() => {
        if (phase === 'input' && inputRef.current) {
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [phase]);

    const visibleMessages = fullScript.slice(0, step + 1);

    // Active speaker logic
    const currentMsg = fullScript[step];
    const activeData = phase === 'processing' ? { speaker: 'east' } : (currentMsg ? { speaker: currentMsg.speaker } : null);

    return (
        <div className="absolute inset-0 z-40 overflow-hidden flex flex-col pointer-events-none">

            {/* Background handled by parent for persistence */}
            <div className="absolute inset-0 bg-transparent z-0" />

            {/* Characters */}
            <div className="absolute inset-0 flex items-end justify-center pointer-events-none z-10">
                <motion.div
                    initial={{ x: -100, opacity: 0 }}
                    animate={{
                        x: 0,
                        opacity: activeData?.speaker === 'west' ? 1 : 0.6,
                        scale: activeData?.speaker === 'west' ? 1.05 : 0.95,
                        filter: activeData?.speaker === 'west' ? 'brightness(1.1) blur(0px)' : 'brightness(0.6) blur(2px)'
                    }}
                    transition={{ duration: 0.4 }}
                    className="absolute left-[-2%] md:left-[5%] bottom-[5vh] h-[40vh] md:h-[55vh] w-auto origin-bottom"
                >
                    <img src={WestStarImg} className="h-full w-auto object-contain" />
                </motion.div>
                <motion.div
                    initial={{ x: 100, opacity: 0 }}
                    animate={{
                        x: 0,
                        opacity: activeData?.speaker === 'east' ? 1 : 0.6,
                        scale: activeData?.speaker === 'east' ? 1.05 : 0.95,
                        filter: activeData?.speaker === 'east' ? 'brightness(1.1) blur(0px)' : 'brightness(0.6) blur(2px)'
                    }}
                    transition={{ duration: 0.4 }}
                    className="absolute right-[-2%] md:right-[5%] bottom-[5vh] h-[40vh] md:h-[55vh] w-auto origin-bottom"
                >
                    <img src={EastSajuImg} className="h-full w-auto object-contain" />
                </motion.div>
            </div>

            {/* Chat UI Container */}
            <div className="absolute inset-x-0 bottom-[10vh] top-[15vh] z-30 flex flex-col items-center pointer-events-none">
                <div className="w-full max-w-2xl h-full flex flex-col px-4">

                    {/* Message List */}
                    <div
                        ref={chatContainerRef}
                        onScroll={handleScroll}
                        className="flex-1 overflow-y-auto space-y-8 pr-2 scrollbar-hide pointer-events-auto pb-4"
                        onClick={handleNext}
                    >
                        {visibleMessages.map((msg) => (
                            <motion.div
                                key={msg.id}
                                initial={{ opacity: 0, y: 30, scale: 0.9 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                className={`flex items-start gap-4 ${msg.speaker === 'east' || msg.speaker === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
                            >
                                {/* Avatar */}
                                {msg.speaker !== 'user' && (
                                    <div className="w-16 h-16 md:w-20 md:h-20 rounded-full border-2 border-white/20 bg-black/40 overflow-hidden flex-shrink-0 shadow-lg mt-1">
                                        <img
                                            src={msg.speaker === 'east' ? EastSajuImg : WestStarImg}
                                            className="w-full h-full object-cover object-[center_15%]"
                                        />
                                    </div>
                                )}

                                {/* Bubble */}
                                <div className={`flex flex-col ${msg.speaker === 'east' || msg.speaker === 'user' ? 'items-end' : 'items-start'} max-w-[85%]`}>
                                    <span className={`text-sm text-white/60 mb-2 px-2 font-bold drop-shadow-md 
                                        ${msg.speaker === 'west' ? "font-western tracking-wider text-indigo-200" : "font-eastern"}`}>
                                        {msg.speaker === 'east' ? EastName : msg.speaker === 'west' ? WestName : '나'}
                                    </span>
                                    {/* Themed Bubble Styles */}
                                    <div className={`px-8 py-6 rounded-[2rem] text-xl md:text-2xl leading-relaxed shadow-xl backdrop-blur-md border relative transition-all duration-300 ${msg.speaker === 'west' ? 'font-western' : 'font-eastern'}
                                        ${msg.speaker === 'east'
                                            ? 'bg-[#f4efe4]/95 text-stone-900 border-stone-800/20 rounded-tr-none'
                                            : msg.speaker === 'west'
                                                ? 'bg-slate-900/90 text-indigo-100 border-indigo-500/30 rounded-tl-none'
                                                : 'bg-white/20 text-white border-white/30 rounded-tr-none'
                                        }`}
                                    >
                                        {/* Decorative Corner for East */}
                                        {msg.speaker === 'east' && (
                                            <div className="absolute right-0 top-0 w-4 h-4 border-l border-b border-stone-800/10 pointer-events-none" />
                                        )}
                                        {/* Typing Indicator or Text */}
                                        {msg.isTyping ? (
                                            <div className="flex gap-2 items-center h-8 px-2">
                                                <span className="w-2 h-2 bg-stone-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
                                                <span className="w-2 h-2 bg-stone-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
                                                <span className="w-2 h-2 bg-stone-500 rounded-full animate-bounce" />
                                            </div>
                                        ) : (
                                            msg.text
                                        )}
                                    </div>
                                </div>
                            </motion.div>
                        ))}
                        <div ref={scrollEndRef} className="h-4" />
                    </div>

                    {/* Bottom Controls */}
                    <div className="mt-6 pointer-events-auto min-h-[80px]">
                        <AnimatePresence mode="wait">

                            {/* Input Field */}
                            {phase === 'input' ? (
                                <motion.div
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 20 }}
                                    className="flex items-center gap-2 w-full"
                                >
                                    <button
                                        onClick={() => setPhase('choice')}
                                        className="p-3 bg-white/10 hover:bg-white/20 rounded-full text-white transition-all"
                                    >
                                        <ArrowLeft size={24} />
                                    </button>
                                    <div className="relative flex-1">
                                        <input
                                            ref={inputRef}
                                            type="text"
                                            value={userQuestion}
                                            onChange={(e) => setUserQuestion(e.target.value)}
                                            onKeyDown={(e) => {
                                                e.stopPropagation();
                                                if (e.key === 'Enter') handleSendQuestion();
                                            }}
                                            placeholder="질문을 입력해주세요..."
                                            className="w-full bg-black/70 border border-white/40 focus:border-amber-400 rounded-full text-white text-xl py-4 px-8 pr-14 outline-none font-eastern placeholder:text-white/30 shadow-2xl backdrop-blur-xl transition-all"
                                        />
                                        <button
                                            onClick={handleSendQuestion}
                                            disabled={!userQuestion.trim()}
                                            className="absolute right-3 top-1/2 -translate-y-1/2 p-3 bg-amber-500 hover:bg-amber-400 rounded-full text-black disabled:opacity-30 disabled:bg-gray-500 transition-all shadow-lg"
                                        >
                                            <Send size={24} fill="currentColor" />
                                        </button>
                                    </div>
                                </motion.div>
                            ) : phase === 'choice' ? (
                                <motion.div
                                    initial={{ opacity: 0, y: 30 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: 20 }}
                                    className="flex gap-4 justify-center w-full"
                                >
                                    <button
                                        onClick={() => setPhase('input')}
                                        className="flex-1 py-4 bg-white/10 hover:bg-white/20 border-2 border-white/30 hover:border-white/60 rounded-2xl text-white font-bold text-xl flex items-center justify-center gap-3 backdrop-blur-md transition-all shadow-lg hover:scale-105"
                                    >
                                        <Sparkles size={24} className="text-amber-400" />
                                        질문하기
                                    </button>
                                    <button
                                        onClick={onComplete}
                                        className="flex-1 py-4 bg-indigo-600/80 hover:bg-indigo-500/80 border-2 border-indigo-400/50 rounded-2xl text-white font-bold text-xl flex items-center justify-center gap-3 backdrop-blur-md transition-all shadow-lg hover:scale-105"
                                    >
                                        <Scroll size={24} />
                                        결과 보기
                                    </button>
                                </motion.div>
                            ) : (
                                // Continue Hint
                                <div className="h-full flex items-center justify-center text-white/40 text-base animate-pulse cursor-pointer" onClick={handleNext}>
                                    대화를 계속하려면 화면을 터치하세요 ▼
                                </div>
                            )}

                        </AnimatePresence>
                    </div>
                </div>
            </div>

        </div>
    );
};

export default DebateOverlay;
