import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect, useMemo } from 'react';
import { getCharacterImage, getCharacterName, useCharacterSettings } from '../../utils/character';
import FortuneChatOverlay from '../effects/FortuneChatOverlay';
import AnimatedBubble from '../common/AnimatedBubble';

// Load all loading text files eagerly
const scriptFiles = import.meta.glob('../../assets/character/**/script/loading/text.txt', {
    eager: true,
    query: '?raw',
    import: 'default'
}) as Record<string, string>;

// Helper to parse script file content
const parseScripts = (content: string): string[] => {
    return content
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.length > 0)
        .map(line => line.replace(/^"|"$/g, '')); // Remove surrounding quotes if present
};

interface FortuneLoadingProps {
    loadingProgress: number; // Keeping prop for compatibility but not using it for bar
    mode: 'saju' | 'daily';
    userQuestion: string;
    onComplete: (finalAns: string) => void;
}

const FortuneLoading = ({ loadingProgress, mode, userQuestion, onComplete }: FortuneLoadingProps) => {

    // Use Reactive Settings Hook instead of static import
    const settings = useCharacterSettings();

    // Helper to get loading images directly
    const eastLoadingImg = getCharacterImage('east', settings.east, 'loading');
    const westLoadingImg = getCharacterImage('west', settings.west, 'loading');
    const EastName = getCharacterName('east', settings.east);
    const WestName = getCharacterName('west', settings.west);

    // Get Scripts for current characters
    const eastScripts = useMemo(() => {
        const path = `../../assets/character/east/${settings.east}/script/loading/text.txt`;
        const content = scriptFiles[path];
        if (!content) {
            console.warn(`[FortuneLoading] Script not found for ${path}`);
            return ["운명의 흐름을 읽고 있습니다..."];
        }
        return parseScripts(content);
    }, [settings.east]);

    const westScripts = useMemo(() => {
        const path = `../../assets/character/west/${settings.west}/script/loading/text.txt`;
        const content = scriptFiles[path];
        if (!content) {
            console.warn(`[FortuneLoading] Script not found for ${path}`);
            return ["별들의 목소리를 듣고 있습니다..."];
        }
        return parseScripts(content);
    }, [settings.west]);

    // Script Rotation State
    const [scriptIndex, setScriptIndex] = useState(0);

    // Rotate scripts every 5 seconds (slower rotation for readability)
    useEffect(() => {
        const interval = setInterval(() => {
            setScriptIndex((prev) => prev + 1);
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    // Pick current lines (ensure index is valid)
    const currentEastScript = eastScripts[scriptIndex % eastScripts.length];
    const currentWestScript = westScripts[scriptIndex % westScripts.length];


    return (
        <motion.div
            key="loading"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-black"
        >
            <div className="relative w-full h-full max-w-4xl max-h-[800px] flex items-center justify-center">

                {/* Star Field Background */}
                <div className="absolute inset-0 overflow-hidden">
                    {[...Array(30)].map((_, i) => (
                        <motion.div
                            key={i}
                            initial={{
                                opacity: 0,
                                x: Math.random() * window.innerWidth - window.innerWidth / 2,
                                y: Math.random() * window.innerHeight - window.innerHeight / 2
                            }}
                            animate={{
                                opacity: [0, 1, 0],
                                scale: [0, 2, 0],
                                rotate: [0, 360]
                            }}
                            transition={{ duration: Math.random() * 2 + 1.5, repeat: Infinity, delay: Math.random() * 2 }}
                            className="absolute top-1/2 left-1/2 w-1 h-1 bg-white rounded-full blur-[1px]"
                        />
                    ))}
                </div>

                {/* Mystic Portal Effect (Enhanced) */}
                <div className="relative w-[500px] h-[500px] flex items-center justify-center opacity-90">
                    {/* Core Glow */}
                    <motion.div
                        animate={{ scale: [1, 1.2, 1], opacity: [0.5, 0.8, 0.5] }}
                        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
                        className="absolute w-40 h-40 bg-indigo-500/20 rounded-full blur-3xl"
                    />

                    {/* Ring 1 - Solid & Shadow */}
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-0 rounded-full border border-white/10 shadow-[0_0_60px_rgba(255,255,255,0.15)]"
                    />

                    {/* Ring 2 - Dashed Reverse */}
                    <motion.div
                        animate={{ rotate: -360 }}
                        transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-12 rounded-full border-2 border-dashed border-white/20"
                    />

                    {/* Ring 3 - Dotted Inner */}
                    <motion.div
                        animate={{ rotate: 180 }}
                        transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-28 rounded-full border-4 border-dotted border-white/10"
                    />

                    {/* Ring 4 - Accent Particles */}
                    <motion.div
                        animate={{ rotate: -180 }}
                        transition={{ duration: 30, repeat: Infinity, ease: "linear" }}
                        className="absolute inset-4 rounded-full"
                    >
                        <div className="absolute top-0 left-1/2 w-3 h-3 bg-indigo-400 rounded-full blur-[2px] shadow-[0_0_15px_#818cf8]" />
                        <div className="absolute bottom-0 left-1/2 w-3 h-3 bg-amber-400 rounded-full blur-[2px] shadow-[0_0_15px_#fbbf24]" />
                    </motion.div>
                </div>

                {/* Content Layer */}
                <div className="absolute inset-0 z-30 flex flex-col items-center justify-center">
                    {mode === 'saju' ? (
                        <div className="flex flex-col items-center gap-6 h-full justify-center pb-20">
                            {/* Loading Title - Korean */}
                            <div className="relative mt-0 animate-pulse flex flex-col items-center gap-4">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: "100px" }}
                                    transition={{ duration: 1, repeat: Infinity, repeatType: "mirror" }}
                                    className="h-[1px] bg-gradient-to-r from-transparent via-white/50 to-transparent"
                                />
                                <h2 className="text-3xl text-white font-['Gowun_Batang'] tracking-[0.2em] text-center drop-shadow-[0_0_20px_rgba(255,255,255,0.6)]">
                                    나를 마주하는 중...
                                </h2>
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: "100px" }}
                                    transition={{ duration: 1, repeat: Infinity, repeatType: "mirror" }}
                                    className="h-[1px] bg-gradient-to-r from-transparent via-white/50 to-transparent"
                                />
                            </div>
                        </div>
                    ) : (
                        <div className="absolute inset-0 pt-20">
                            <FortuneChatOverlay
                                userQuestion={userQuestion}
                                onComplete={onComplete}
                            />
                        </div>
                    )}
                </div>
            </div>

            {/* Characters & Scripts Layer - Moved outside max-w-4xl for full width */}
            {mode === 'saju' && (
                <div className="absolute inset-0 flex justify-center items-end pointer-events-none pb-0 w-full overflow-hidden">
                    {/* West Character - Back on LEFT */}
                    <div className="absolute left-4 md:left-16 bottom-40 md:bottom-48 flex flex-col items-center pointer-events-auto">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={`west-${scriptIndex}`}
                                initial={{ opacity: 0, y: 20, scale: 0.9 }}
                                animate={{ opacity: 1, y: 10, scale: 1 }}
                                exit={{ opacity: 0, y: 0, scale: 0.95 }}
                                transition={{ duration: 0.5 }}
                                className="mb-2 translate-y-60 w-[280px] md:w-[350px] relative z-50"
                            >
                                <AnimatedBubble
                                    theme="indigo"
                                    size="normal"
                                    title={WestName}
                                    text={currentWestScript}
                                    className="shadow-2xl"
                                />
                            </motion.div>
                        </AnimatePresence>
                        <motion.div
                            animate={{ y: [0, -10, 0] }}
                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                            className="relative z-0"
                        >
                            <img src={westLoadingImg} className="h-[40vh] md:h-[50vh] object-contain drop-shadow-[0_0_10px_rgba(129,140,248,0.6)] contrast-125 brightness-110" />
                        </motion.div>
                    </div>

                    {/* East Character - Back on RIGHT */}
                    <div className="absolute right-4 md:right-16 bottom-40 md:bottom-48 flex flex-col items-center pointer-events-auto">
                        <AnimatePresence mode="wait">
                            <motion.div
                                key={`east-${scriptIndex}`}
                                initial={{ opacity: 0, y: 20, scale: 0.9 }}
                                animate={{ opacity: 1, y: 10, scale: 1 }}
                                exit={{ opacity: 0, y: 0, scale: 0.95 }}
                                transition={{ duration: 0.5 }}
                                className="mb-2 translate-y-60 w-[280px] md:w-[350px] relative z-50"
                            >
                                <AnimatedBubble
                                    theme="amber"
                                    size="normal"
                                    title={EastName}
                                    text={currentEastScript}
                                    className="shadow-2xl"
                                />
                            </motion.div>
                        </AnimatePresence>
                        <motion.div
                            animate={{ y: [0, -10, 0] }}
                            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut", delay: 2 }}
                            className="relative z-0"
                        >
                            <img src={eastLoadingImg} className="h-[40vh] md:h-[50vh] object-contain drop-shadow-[0_0_10px_rgba(251,191,36,0.6)] contrast-125 brightness-110" />
                        </motion.div>
                    </div>
                </div>
            )}

            {/* Overlay Vignette */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_transparent_0%,_black_90%)] pointer-events-none" />
        </motion.div>
    );
};

export default FortuneLoading;
