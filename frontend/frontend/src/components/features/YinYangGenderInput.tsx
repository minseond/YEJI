
import { motion } from 'framer-motion';
import { useState } from 'react';
import { X } from 'lucide-react';

// Image Paths
const MALE_IMG = "/assets/images/gender/male.png";
const FEMALE_IMG = "/assets/images/gender/female.png";
// Backgrounds
const MALE_BG = "/assets/images/gender/men_sun.png";
const FEMALE_BG = "/assets/images/gender/women_moon.png";

interface YinYangGenderInputProps {
    onSelect: (gender: string) => void;
    onClose?: () => void;
}

const YinYangGenderInput = ({ onSelect, onClose }: YinYangGenderInputProps) => {
    const [hovered, setHovered] = useState<'male' | 'female' | null>(null);
    const [selected, setSelected] = useState<'male' | 'female' | null>(null);

    const handleSelect = (gender: 'male' | 'female') => {
        setSelected(gender);
        // Faster animation: 0.7s
        setTimeout(() => {
            onSelect(gender === 'male' ? '남성' : '여성');
        }, 700);
    };

    return (
        // Compact Size: max-w-4xl, h-[600px] 
        // Darker Base: from-black to-slate-950
        <motion.div
            className="relative w-full max-w-4xl h-[600px] flex flex-col items-center justify-center overflow-hidden select-none bg-gradient-to-br from-black/70 to-slate-950/70 backdrop-blur-md rounded-3xl border border-white/10 shadow-2xl"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.4 }}
        >
            {/* Title */}
            <motion.h2
                animate={{ opacity: selected ? 0 : 1 }}
                transition={{ duration: 0.3 }}
                className="absolute top-10 text-2xl font-serif text-white/80 drop-shadow-lg tracking-widest font-bold z-30"
            >
                성별 선택
            </motion.h2>

            {/* BACKGROUND LAYER */}
            <div className="absolute inset-0 z-0 flex items-center justify-center pointer-events-none overflow-hidden rounded-3xl">
                {/* Male BG Layer - Blurred & Dimmed */}
                <motion.div
                    className="absolute inset-0 bg-cover bg-center"
                    initial={{ opacity: 0, filter: 'blur(8px) brightness(0.6)', scale: 1 }}
                    animate={{
                        // Reduced opacity for dark emphasis
                        opacity: selected === 'male' ? 0.8 : (hovered === 'male' && !selected ? 0.4 : 0),
                        filter: selected === 'male' ? 'blur(0px) brightness(1.2)' : 'blur(8px) brightness(0.6)',
                        scale: selected === 'male' ? 1.1 : 1,
                    }}
                    transition={{ duration: selected === 'male' ? 0.7 : 0.5, ease: "easeOut" }}
                    style={{ backgroundImage: `url(${MALE_BG})` }}
                />
                {/* Female BG Layer - Blurred & Dimmed */}
                <motion.div
                    className="absolute inset-0 bg-cover bg-center"
                    initial={{ opacity: 0, filter: 'blur(8px) brightness(0.6)', scale: 1 }}
                    animate={{
                        // Reduced opacity for dark emphasis
                        opacity: selected === 'female' ? 0.8 : (hovered === 'female' && !selected ? 0.4 : 0),
                        filter: selected === 'female' ? 'blur(0px) brightness(1.2)' : 'blur(8px) brightness(0.6)',
                        scale: selected === 'female' ? 1.1 : 1,
                    }}
                    transition={{ duration: selected === 'female' ? 0.7 : 0.5, ease: "easeOut" }}
                    style={{ backgroundImage: `url(${FEMALE_BG})` }}
                />
            </div>

            {/* CONTENT LAYER */}
            <div className="flex items-center justify-center gap-16 md:gap-24 relative z-10 w-full h-full mt-6">

                {/* Male (Yang) Selection - Left */}
                <motion.div
                    className="relative cursor-pointer group flex items-center justify-center"
                    onHoverStart={() => !selected && setHovered('male')}
                    onHoverEnd={() => !selected && setHovered(null)}
                    onClick={() => !selected && handleSelect('male')}
                    animate={{
                        opacity: selected ? 0 : 1, // Fate out on selection for cinematic view
                    }}
                    whileHover={!selected ? { scale: 1.1, zIndex: 30 } : {}}
                    whileTap={!selected ? { scale: 0.95 } : {}}
                    transition={{ duration: 0.5 }}
                >
                    {/* Silhouette Image - Smaller */}
                    <img
                        src={MALE_IMG}
                        alt="남성"
                        className={`
                             w-[220px] h-[380px] md:w-[280px] md:h-[480px] 
                            object-contain transition-all duration-500
                            ${(hovered === 'male' && !selected)
                                ? 'drop-shadow-[0_0_60px_rgba(100,200,255,0.8)] brightness-125 saturate-150'
                                : 'drop-shadow-none opacity-60 grayscale brightness-75' // Darker default
                            }
                        `}
                    />
                </motion.div>


                {/* Female (Yin) Selection - Right */}
                <motion.div
                    className="relative cursor-pointer group flex items-center justify-center"
                    onHoverStart={() => !selected && setHovered('female')}
                    onHoverEnd={() => !selected && setHovered(null)}
                    onClick={() => !selected && handleSelect('female')}
                    animate={{
                        opacity: selected ? 0 : 1,
                    }}
                    whileHover={!selected ? { scale: 1.1, zIndex: 30 } : {}}
                    whileTap={!selected ? { scale: 0.95 } : {}}
                    transition={{ duration: 0.5 }}
                >
                    {/* Silhouette Image - Smaller */}
                    <img
                        src={FEMALE_IMG}
                        alt="여성"
                        className={`
                            w-[220px] h-[380px] md:w-[280px] md:h-[480px] 
                            object-contain transition-all duration-500
                            ${(hovered === 'female' && !selected)
                                ? 'drop-shadow-[0_0_60px_rgba(255,100,100,0.8)] brightness-125 saturate-150'
                                : 'drop-shadow-none opacity-60 grayscale brightness-75'
                            }
                        `}
                    />
                </motion.div>
            </div>

            {/* Close Button - Bottom Center */}
            {onClose && (
                <motion.div
                    className="absolute bottom-8 z-[60]"
                    animate={{ opacity: selected ? 0 : 1 }}
                >
                    <button
                        onClick={onClose}
                        className="w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 border border-white/30 text-white/80 hover:text-white backdrop-blur-md transition-all flex items-center justify-center group shadow-lg"
                    >
                        <X size={20} />
                    </button>
                </motion.div>
            )}

        </motion.div>
    );
};

export default YinYangGenderInput;
