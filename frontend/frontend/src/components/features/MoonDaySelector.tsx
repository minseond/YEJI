import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

interface MoonDaySelectorProps {
    month: number;
    year?: number;
    onSelect: (day: number) => void;
    onBack: () => void;
    onClose?: () => void;
}

const MoonDaySelector = ({ month, year = 2000, onSelect, onBack, onClose }: MoonDaySelectorProps) => {
    // ... code ...
    // Note: I am replacing the import and interface area, but I need to reach the return statement to add the button.
    // Since I can't do two separate replacements easily in one go without replacing the whole file, I will split this into two steps if the tool doesn't support it well, OR replace the whole top part and then the bottom part.
    // I will replace the component start and then the button area.

    // ... (re-using existing valid code for variables)

    // Actually, let's just do two small edits. 
    // This Edit 1: Imports and Props.

    const getDaysInMonth = (m: number) => new Date(year, m, 0).getDate();
    const maxDays = getDaysInMonth(month);

    // Default to Day 15
    const [day, setDay] = useState(15);
    const [isHovered, setIsHovered] = useState(false);

    // Controls for Drag
    const [isDragging, setIsDragging] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    // Layout Constants
    const PIVOT_Y = 300;
    const ARC_RADIUS = 500;
    const MOON_SIZE = 280; // Adjusted size (Previous 350)

    // ... (rest of code)



    // Angle Mapping:
    // Left: -160 deg -> Day 1
    // Top: -90 deg -> Day 15 (Approx)
    // Right: -20 deg -> Day 31
    // Total Span: 140 degrees? 
    // User asked for "Semi-circle". That's 180 deg.
    // Let's go from -180 (Left) to 0 (Right).
    // Or better visual: -170 to -10 to avoid clipping at edges.
    const START_ANGLE = -140;
    const END_ANGLE = -40;

    // Calculate current angle based on day
    const progress = (day - 1) / (maxDays - 1); // 0 to 1
    const currentAngle = START_ANGLE + progress * (END_ANGLE - START_ANGLE);

    // Global Drag Handler
    useEffect(() => {
        const handleGlobalMove = (e: PointerEvent) => {
            if (!isDragging || !containerRef.current) return;
            e.preventDefault();

            // Calculate Angle from Pivot
            const rect = containerRef.current.getBoundingClientRect();
            const pivotX = rect.left + rect.width / 2;     // Center X
            const pivotY = rect.top + rect.height / 2 + PIVOT_Y; // Pivot Y (below center)

            const dx = e.clientX - pivotX;
            const dy = e.clientY - pivotY;

            // atan2(y, x) -> radians.
            // Screen Coords: Y is down.
            // Right: 0. Down: 90. Left: 180/-180. Up: -90.
            // We want angles between ~ -170 (Left-ish Up) and -10 (Right-ish Up).
            let angleDeg = Math.atan2(dy, dx) * (180 / Math.PI);

            // Clamp Angle
            // We expect negative angles (-180 to 0).
            // If user drags below pivot (positive angles), we should probably clamp to nearest valid.
            // But with pivot low, cursor is usually above.

            // Normalize clamp:
            // If angle is > 0 (Bottom half), map to closest edge?
            // Let's just Clamp between START/END.

            // Check boundary wrapping manually if needed, but atan2 handles -180/180 discontinuity well if we stay in upper half.

            let clampedAngle = Math.max(START_ANGLE, Math.min(END_ANGLE, angleDeg));

            // Map Angle -> Day
            // angle = START + p * (END - START)
            // p = (angle - START) / (END - START)
            const p = (clampedAngle - START_ANGLE) / (END_ANGLE - START_ANGLE);
            const newDay = Math.round(p * (maxDays - 1)) + 1;

            setDay(newDay);
        };

        const handleGlobalUp = () => {
            setIsDragging(false);
        };

        if (isDragging) {
            window.addEventListener('pointermove', handleGlobalMove);
            window.addEventListener('pointerup', handleGlobalUp);
        }

        return () => {
            window.removeEventListener('pointermove', handleGlobalMove);
            window.removeEventListener('pointerup', handleGlobalUp);
        };
    }, [isDragging, maxDays]);


    return (
        <div
            className="relative flex flex-col items-center justify-center w-full h-[700px] overflow-visible select-none"
            ref={containerRef}
        >
            {/* Visual Arc Guide (Optional, faint) */}
            <div
                className="absolute border border-white/10 rounded-full box-border pointer-events-none"
                style={{
                    width: ARC_RADIUS * 2,
                    height: ARC_RADIUS * 2,
                    top: `calc(50% + ${PIVOT_Y}px - ${ARC_RADIUS}px)`,
                    left: '50%',
                    transform: 'translate(-50%, -50%)'
                }}
            />

            {/* ArmContainer: Rotates around the Pivot */}
            <div
                className="absolute top-1/2 left-1/2 w-0 h-0 pointer-events-none"
                style={{
                    // Pivot Offset
                    transform: `translate(0, ${PIVOT_Y}px) rotate(${currentAngle}deg)`
                }}
            >
                {/* The Moon Wrapper - Offset by Radius to tip of arm */}
                <div
                    className="absolute flex items-center justify-center cursor-grab active:cursor-grabbing group"
                    style={{
                        width: MOON_SIZE * 2, // Double the hit area size
                        height: MOON_SIZE * 2,
                        // Move "Out" by radius. Since 0 deg is Right, X+ is Radius.
                        // We want standard polar? 
                        // If we rotate parent, we just translate X.
                        transform: `translateX(${ARC_RADIUS}px) rotate(${-currentAngle}deg)`, // Counter-rotate moon to keep it upright
                        // Center is offset by half of NEW size
                        top: -MOON_SIZE,
                        left: -MOON_SIZE,

                        pointerEvents: 'auto' // Re-enable pointer events for dragging
                    }}
                    onPointerDown={(e) => {
                        e.preventDefault();
                        setIsDragging(true);
                    }}
                >
                    {/* Visual Container (True Size) */}
                    <div style={{ width: MOON_SIZE, height: MOON_SIZE }} className="relative">
                        <MoonVisual progress={progress} />
                    </div>

                    {/* Day Text below moon */}
                    <div className="absolute -bottom-0 text-5xl text-white font-serif font-bold text-shadow-glow pointer-events-none">
                        {day}日
                    </div>
                </div>
            </div>

            {/* Bottom Controls */}
            <div className="absolute bottom-10 flex items-center gap-6 z-[100] pointer-events-auto">
                <button
                    onClick={onBack}
                    className="px-6 py-3 text-white/50 hover:text-white font-serif text-4xl tracking-widest transition-colors flex items-center justify-center"
                >
                    <span>←</span>
                </button>

                <button
                    onClick={() => onSelect(day)}
                    className="px-12 py-4 bg-white text-black font-serif font-bold text-lg tracking-widest rounded-full transition-all hover:scale-105 active:scale-95 shadow-[0_0_30px_rgba(255,255,255,0.3)] hover:shadow-[0_0_50px_rgba(255,255,255,0.5)] whitespace-nowrap"
                >
                    선택
                </button>

                {/* Close Button - Next to Select */}
                {onClose && (
                    <button
                        onClick={onClose}
                        className="w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 border border-white/30 text-white/80 hover:text-white backdrop-blur-md transition-all flex items-center justify-center group"
                    >
                        <X size={20} />
                    </button>
                )}

                {/* Helper Popup Button */}
                <button
                    onMouseEnter={() => setIsHovered(true)}
                    onMouseLeave={() => setIsHovered(false)}
                    className="w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 border border-white/30 text-white text-xl font-bold backdrop-blur-md transition-all flex items-center justify-center relative group"
                >
                    ?!
                    <AnimatePresence>
                        {isHovered && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.5, y: 10 }} // Popup UPwards
                                animate={{ opacity: 1, scale: 1, y: 0 }}
                                exit={{ opacity: 0, scale: 0.5, y: 5 }}
                                className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 w-40 pointer-events-none z-50 p-[2px] rounded-xl bg-gradient-to-br from-white/40 via-white/15 to-transparent"
                            >
                                <div className="bg-black/40 backdrop-blur-md rounded-xl p-3 border border-white/10">
                                    <p className="text-center text-xs text-white/90 font-['Gowun_Batang']">달을 드래그하세요!</p>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </button>
            </div>
        </div>
    );
};

// ... existing MoonVisual ...
// Let's inline a cleaner MoonVisual that relies on simpler composition.

const MoonVisual = ({ progress }: { progress: number }) => {
    // Phase Simulation
    // 0.0 (New) -> 0.5 (Full) -> 1.0 (New)
    const isWaxing = progress <= 0.5;

    // Shadow Logic:
    // We start with Full Moon Image.
    // We overlay a "Shadow Mask".

    // Visual Hack for Phases:
    // Waxing (0 -> 0.5):
    //   Starts Black.
    //   Light enters from Right? (Korean northern hemisphere view) -> Waxing Crescent is Right side.
    //   So Shadow moves Left?
    //   Let's just use a simplified "Curved Shadow" approach.

    // Using 2 semi-circles is the standard CSS way but complex to animate with single var.
    // Let's stick to the Sliding Blur Shadow we had, but tuned.

    return (
        <div className="w-full h-full rounded-full relative overflow-hidden group">
            <img
                src="/assets/moon/moon.png"
                alt="Moon"
                className="w-full h-full object-contain drop-shadow-[0_0_50px_rgba(255,255,255,0.4)]"
            />

            {/* Phase Shadow Wrapper */}
            <div className="absolute inset-0 rounded-full mix-blend-multiply pointer-events-none">
                {/* 
                    We move a large black box with a blur edge.
                    Waxing: Box moves Left (-100%).
                    Waning: Box moves Right (+100%)?
                    
                    Refined Logic:
                    Waxing (0 -> 0.5): Shadow is initially covering (0%). Moves Left to -150%. 
                    Waning (0.5 -> 1.0): Shadow starts at Right (+150%). Moves Left to 0%? No.
                    Waning means Light is leaving from Right? 
                    Waning Gibbous -> Left side lit. Right side dark.
                    So Shadow comes from Right.
                    
                    So:
                    0.0: Center.
                    0.5: Left (Hidden).
                    0.5: Right (Hidden).
                    1.0: Center.
                 */}
                <div
                    className="absolute inset-0 bg-black blur-xl transition-transform duration-75"
                    style={{
                        transform: isWaxing
                            ? `translateX(${(progress / 0.5) * 115}%) scale(1.15)` // 0 -> 115% (Move Right, Larger Shadow)
                            : `translateX(${(1 - (progress - 0.5) / 0.5) * -115}%) scale(1.15)` // -115% -> 0% (Move In from Left)
                    }}
                />
            </div>
        </div>
    );
};

export default MoonDaySelector;
