
import { motion, AnimatePresence } from 'framer-motion';
import { getCharacterVisualConfig, getSDCharacterImage } from '../../utils/character';
import AnimatedBubble from './AnimatedBubble';

interface CharacterGuideProps {
    region: 'east' | 'west';
    characterId: string;
    characterName: string;
    pose?: string;
    activeComment?: string | null;
    onCommentClick?: () => void;
    position?: 'left' | 'right';
    theme: 'amber' | 'indigo';
}

const CharacterGuide = ({
    region,
    characterId,
    characterName,
    pose = 'loading',
    activeComment,
    onCommentClick,
    position = 'right',
    theme
}: CharacterGuideProps) => {
    const config = getCharacterVisualConfig(characterId);

    // Dynamically determining the pose: if there is an activeComment, use 'explain', otherwise use the passed pose
    const currentPose = activeComment ? 'explain' : pose;
    const imageUrl = getSDCharacterImage(region, characterId, currentPose);

    // Bubble alignment
    const bubbleClass = position === 'right'
        ? "absolute bottom-[135%] right-36 min-w-[260px] max-w-[300px] z-50 pointer-events-auto cursor-pointer"
        : "absolute bottom-[135%] left-4 min-w-[260px] max-w-[300px] z-50 pointer-events-auto cursor-pointer";

    return (
        <div className={`fixed top-[65%] ${position === 'right' ? 'right-12' : 'left-12'} -translate-y-1/2 hidden xl:flex flex-col items-center z-50 pointer-events-none transform-gpu will-change-transform`}>
            <motion.div
                initial={{ opacity: 0, x: position === 'right' ? 50 : -50 }}
                animate={{ opacity: 1, x: 0 }}
                className="relative"
            >
                {/* Character Image Container */}
                <div className="h-80 w-64 flex items-end justify-center">
                    <img
                        src={imageUrl}
                        alt={characterName}
                        className={`h-full w-full object-contain object-bottom ${theme === 'amber' ? 'filter contrast-125' : ''} ${region === 'west' ? 'drop-shadow-[0_0_40px_rgba(129,140,248,0.4)]' : 'drop-shadow-[0_0_30px_rgba(251,191,36,0.3)]'}`}
                        style={{
                            transform: `scale(${config.scale}) translateY(${config.yOffset})`
                        }}
                    />
                </div>

                {/* Name Plaque */}
                <div className={`absolute -bottom-4 left-1/2 -translate-x-1/2 px-4 py-1.5 rounded-full text-[10px] font-bold tracking-widest whitespace-nowrap backdrop-blur-sm border ${theme === 'amber'
                    ? 'bg-amber-900/90 text-amber-50 border-amber-500/30'
                    : 'bg-indigo-600/90 text-white border-indigo-400/30'
                    }`}>
                    {characterName}의 가이드
                </div>

                {/* Speech Bubble */}
                <AnimatePresence>
                    {activeComment && (
                        <div
                            className={bubbleClass}
                            onClick={onCommentClick}
                        >
                            <AnimatedBubble
                                theme={theme}
                                size="large"
                                title={characterName}
                                text={activeComment}
                            />
                        </div>
                    )}
                </AnimatePresence>
            </motion.div>
        </div>
    );
};

export default CharacterGuide;
