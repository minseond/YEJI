import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Scroll } from 'lucide-react';



// Enso Style Brush Circle
const BrushCircle = () => (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none -z-10 opacity-90">
        <svg viewBox="0 0 140 140" className="w-[120%] h-[120%] rotate-[-10deg] overflow-visible mix-blend-multiply">
            <defs>
                <filter id="enso-brush" x="-20%" y="-20%" width="140%" height="140%">
                    <feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="3" seed="8" result="noise" />
                    <feDisplacementMap in="SourceGraphic" in2="noise" scale="6" xChannelSelector="R" yChannelSelector="G" />
                </filter>
            </defs>

            {/* Clean Enso Circle (Zen Ring) */}
            <motion.path
                d="M70,15 C35,15 10,45 10,75 C10,110 40,135 75,135 C115,135 135,100 135,60 C135,35 115,15 90,15 C88,15 88,20 90,20 C105,20 120,35 120,60 C120,90 100,120 75,120 C50,120 25,100 25,75 C25,50 45,30 70,30 C72,30 72,15 70,15 Z"
                fill="#2d1b16"
                filter="url(#enso-brush)"
                initial={{ pathLength: 0, opacity: 0, scale: 0.9, rotate: -20 }}
                animate={{ pathLength: 1, opacity: 0.85, scale: 1, rotate: 0 }}
                transition={{ duration: 0.5, ease: "easeInOut" }}
            />
        </svg>
    </div>
);

const MenuItem = ({ title, onClick }: { title: string, id: string, onClick: () => void }) => {
    const [isHovered, setIsHovered] = useState(false);

    return (
        <motion.button
            className="relative w-3/4 py-4 text-5xl text-[#3e2723] font-['Nanum_Brush_Script'] transition-colors z-10 font-bold tracking-widest"
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            onClick={onClick}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
        >
            {title}
            {isHovered && <BrushCircle />}
        </motion.button>
    );
};

// Traditional Eastern Tassel (Knotted Cord)
const ScrollTassel = () => (
    <motion.div
        className="absolute top-4 flex flex-col items-center z-50 pointer-events-auto cursor-pointer origin-top"
        // Independent physics for the tassel (pendulum effect)
        animate={{ rotate: [0, 5, -5, 2, -2, 0] }}
        transition={{ repeat: Infinity, duration: 4, ease: "easeInOut" }}
    >
        {/* The Cord */}
        <div className="w-[2px] h-12 bg-[#5d4037] relative shadow-sm"></div>

        {/* The Knot (Maedeup style visual) */}
        <div className="relative flex flex-col items-center -mt-1 drop-shadow-md">
            <div className="w-4 h-3 bg-[#8d6e63] rounded-full shadow-inner border border-[#5d4037]"></div>
            <div className="w-5 h-4 bg-[#5d4037] rounded-lg -mt-1 shadow-md flex items-center justify-center text-[8px] text-[#a1887f] border border-[#3e2723]">
                ※
            </div>
        </div>

        {/* The Fringe/Tassel Body */}
        <div className="relative -mt-1 flex flex-col items-center drop-shadow-sm">
            <div className="w-2 h-1 bg-[#3e2723]"></div>
            <div className="w-8 h-20 bg-[#5d4037] rounded-bl-lg rounded-br-lg shadow-inner flex justify-center overflow-hidden relative">
                {/* Texture lines for threads */}
                <div className="absolute inset-0 flex justify-center opacity-30">
                    {Array.from({ length: 8 }).map((_, i) => (
                        <div key={i} className="w-[1px] h-full bg-[#3e2723] mx-[1px]"></div>
                    ))}
                </div>
                {/* Gradient fade at bottom */}
                <div className="absolute bottom-0 w-full h-8 bg-gradient-to-b from-transparent to-[#3e2723]/30"></div>
            </div>
        </div>
    </motion.div>
);

const ScrollRoller = ({ position, hasHandle = false }: { position: 'top' | 'bottom', hasHandle?: boolean }) => (
    <div className={`absolute ${position === 'top' ? 'top-0' : 'bottom-0'} w-full flex items-center justify-center z-30 pointer-events-none`}>
        {/* Main Roller Bar - Dark Wood */}
        <div className="relative w-[112%] h-10 rounded-full shadow-[0_5px_15px_rgba(0,0,0,0.5)] border border-[#3e2723] overflow-hidden bg-[#3e2723] flex items-center justify-center z-20">
            <div className="absolute inset-0 w-full h-full bg-[url('/textures/dark_wood.png')] bg-cover opacity-90"></div>
            {/* 3D Cylindrical Shading - Stronger contrast for roundness */}
            <div className="absolute inset-0 w-full h-full bg-gradient-to-b from-white/20 via-transparent to-black/70"></div>
        </div>

        {/* Tassel Handle (Only for Bottom Roller) */}
        {hasHandle && <ScrollTassel />}

        {/* Left Knob - Tiered Wood Style */}
        <div className="absolute -left-[calc(6%+24px)] flex flex-col items-center justify-center z-40 drop-shadow-2xl feature-knob">
            {/* Inner Connector */}
            <div className="w-8 h-8 rounded-full bg-[#3e2723] relative -mr-2 shadow-[inset_-2px_-2px_4px_rgba(0,0,0,0.5)] border border-[#2d1b16]">
                <div className="absolute inset-0 bg-[url('/textures/dark_wood.png')] bg-cover opacity-100 rounded-full"></div>
            </div>
            {/* Middle Tier */}
            <div className="w-10 h-3 bg-[#4e342e] rounded-sm -mt-6 relative z-10 border border-[#2d1b16] shadow-sm">
                <div className="absolute inset-0 bg-[url('/textures/dark_wood.png')] bg-cover opacity-100"></div>
            </div>
            {/* Outer Cap */}
            <div className="w-6 h-6 rounded-t-lg bg-[#3e2723] -mt-1 relative z-20 border border-[#2d1b16] shadow-md">
                <div className="absolute inset-0 bg-[url('/textures/dark_wood.png')] bg-cover opacity-100 rounded-t-lg"></div>
            </div>
            {/* Finial */}
            <div className="w-3 h-4 bg-[#2d1b16] -mt-1 rounded-t-full relative z-30 shadow-sm"></div>
        </div>

        {/* Right Knob - Tiered Wood Style (Mirrored roughly) */}
        <div className="absolute -right-[calc(6%+24px)] flex flex-col items-center justify-center z-40 drop-shadow-2xl feature-knob">
            {/* Inner Connector */}
            <div className="w-8 h-8 rounded-full bg-[#3e2723] relative -ml-2 shadow-[inset_2px_-2px_4px_rgba(0,0,0,0.5)] border border-[#2d1b16]">
                <div className="absolute inset-0 bg-[url('/textures/dark_wood.png')] bg-cover opacity-100 rounded-full"></div>
            </div>
            {/* Middle Tier */}
            <div className="w-10 h-3 bg-[#4e342e] rounded-sm -mt-6 relative z-10 border border-[#2d1b16] shadow-sm">
                <div className="absolute inset-0 bg-[url('/textures/dark_wood.png')] bg-cover opacity-100"></div>
            </div>
            {/* Outer Cap */}
            <div className="w-6 h-6 rounded-t-lg bg-[#3e2723] -mt-1 relative z-20 border border-[#2d1b16] shadow-md">
                <div className="absolute inset-0 bg-[url('/textures/dark_wood.png')] bg-cover opacity-100 rounded-t-lg"></div>
            </div>
            {/* Finial */}
            <div className="w-3 h-4 bg-[#2d1b16] -mt-1 rounded-t-full relative z-30 shadow-sm"></div>
        </div>
    </div>
);

const ScrollNavbar = ({ onNavigate }: { onNavigate: (page: string) => void }) => {
    const [isOpen, setIsOpen] = useState(false);

    const menuItems = [
        { title: '운세', id: 'home' },
        { title: '소개', id: 'about' },
        { title: '기록패', id: 'history' },
        { title: '환경설정', id: 'settings' },
    ];

    return (
        <div className="fixed top-0 left-0 right-0 z-50 flex justify-center p-4 font-sans perspective-1000">
            {/* The Main Hanging Assembly */}
            <div className="relative w-full max-w-lg flex flex-col items-center">

                {/* Triangle Hanger String (Realistic Suspension) */}
                <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-64 h-32 flex justify-center z-0 pointer-events-none">
                    <svg width="100%" height="100%" viewBox="0 0 200 100" overflow="visible">
                        {/* The string forming a triangle */}
                        <path d="M100,0 L20,100 M100,0 L180,100" stroke="#3e2723" strokeWidth="2" fill="none" filter="drop-shadow(2px 2px 2px rgba(0,0,0,0.5))" />
                        {/* The imaginary nail */}
                        <circle cx="100" cy="0" r="4" fill="#1a0f00" />
                    </svg>
                </div>

                {/* Wall Shadow - Blurred copy behind the scroll for depth */}
                <motion.div
                    className="absolute top-0 w-[95%] bg-black/40 blur-xl rounded-b-3xl z-[-1]"
                    initial={{ height: 80 }}
                    animate={{
                        height: isOpen ? 520 : 80,
                        // Shadow moves slightly opposite to light source or lags behind
                        rotateZ: isOpen ? [0, 0.2, -0.2, 0] : 0,
                    }}
                    transition={{ type: "spring", stiffness: 80, damping: 14 }}
                />

                {/* The Scroll Container - Animated Height on Hover */}
                <motion.div
                    layout
                    initial={{ height: 80, rotateX: 0 }}
                    animate={{
                        height: isOpen ? 500 : 80,
                        rotateX: isOpen ? [0, 2, -1, 0] : 0,
                        rotateZ: [0, 0.5, -0.5, 0] // Gentle pendulum sway
                    }}
                    transition={{
                        height: { type: "spring", stiffness: 80, damping: 14, mass: 1.2 },
                        rotateX: { duration: 1, ease: "easeOut" },
                        rotateZ: { repeat: Infinity, duration: 8, ease: "easeInOut" } // Slow, heavy sway
                    }}
                    className="relative w-full flex flex-col items-center shadow-[0_25px_50px_-12px_rgba(0,0,0,0.6)] cursor-pointer group origin-top"
                    onMouseEnter={() => setIsOpen(true)}
                    onMouseLeave={() => setIsOpen(false)}
                    style={{ transformStyle: 'preserve-3d' }}
                >
                    {/* The Paper Body - Beige Parchment */}
                    <motion.div
                        className="absolute inset-x-0 top-5 bottom-5 w-full bg-[#e8e0c5] z-10 overflow-hidden border-x-[1px] border-[#8d6e63]/30"
                        style={{
                            backgroundImage: `url('/textures/beige_paper.png')`,
                            backgroundSize: 'cover',
                            backgroundPosition: 'center',
                        }}
                        // Gentle Paper Sway Physics when open (Wind effect)
                        animate={isOpen ? {
                            rotateZ: [0, 0.5, -0.5, 0],
                            skewX: [0, 0.2, -0.2, 0],
                        } : {}}
                        transition={{
                            repeat: Infinity,
                            duration: 5,
                            ease: "easeInOut",
                            repeatType: "mirror"
                        }}
                    >
                        {/* Deep 3D Shadowing for Curvature */}
                        <div className="absolute inset-0 bg-gradient-to-r from-black/25 via-transparent to-black/25 pointer-events-none mix-blend-multiply"></div>
                        {/* Top/Bottom shadows to show paper entering rollers */}
                        <div className="absolute top-0 w-full h-8 bg-gradient-to-b from-black/40 to-transparent pointer-events-none"></div>
                        <div className="absolute bottom-0 w-full h-8 bg-gradient-to-t from-black/40 to-transparent pointer-events-none"></div>

                        {/* Paper Grain Overlay */}
                        <div className="absolute inset-0 opacity-10 bg-[url('https://www.transparenttextures.com/patterns/cream-paper.png')] pointer-events-none mix-blend-overlay"></div>
                    </motion.div>

                    {/* Top Roller Visual */}
                    <ScrollRoller position="top" hasHandle={false} />

                    {/* Closed State Header / Toggle Trigger */}
                    <div className="w-full h-16 flex items-center justify-center z-20 absolute top-0 pointer-events-none">
                        <motion.div
                            className="px-6 py-1"
                            animate={{ opacity: isOpen ? 0 : 1 }}
                        >
                            <span className="text-[#4e342e] font-['Nanum_Brush_Script'] text-3xl tracking-widest flex items-center gap-2 opacity-90 drop-shadow-sm font-bold">
                                <Scroll size={24} className="text-[#5d4037]" strokeWidth={2} />
                                메뉴
                            </span>
                        </motion.div>
                    </div>

                    {/* Menu Content (Unfurled part) */}
                    <AnimatePresence>
                        {isOpen && (
                            <motion.div
                                initial={{ opacity: 0, y: -20 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -20 }}
                                transition={{ duration: 0.3, delay: 0.1 }}
                                className="w-full flex-1 flex flex-col items-center justify-center gap-6 mt-16 pb-16 relative z-20 pointer-events-auto"
                            >
                                {/* Simple horizontal divider */}
                                <div className="w-2/3 h-px bg-[#8d6e63]/30 shadow-[0_1px_0_rgba(255,255,255,0.2)]"></div>

                                {menuItems.map((item) => (
                                    <MenuItem
                                        key={item.id}
                                        title={item.title}
                                        id={item.id}
                                        onClick={() => {
                                            setIsOpen(false);
                                            onNavigate(item.id);
                                        }}
                                    />
                                ))}

                                <div className="w-2/3 h-px bg-[#8d6e63]/30 shadow-[0_1px_0_rgba(255,255,255,0.2)]"></div>
                            </motion.div>
                        )}
                    </AnimatePresence>

                    {/* Bottom Roller Visual */}
                    <div className="absolute bottom-0 w-full z-30 pointer-events-none">
                        <ScrollRoller position="bottom" hasHandle={!isOpen} />
                    </div>
                </motion.div>
            </div>
        </div>
    );
};

export default ScrollNavbar;
