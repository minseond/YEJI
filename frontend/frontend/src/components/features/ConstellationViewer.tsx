import { motion, AnimatePresence } from 'framer-motion';

// Normalized Coordinates (0-100)
// Simplified but recognizable representation of 12 zodiac constellations.
type Star = { x: number; y: number };
type Connection = [number, number]; // Indices of connected stars

interface ConstellationData {
    stars: Star[];
    connections: Connection[];
}

const CONSTELLATIONS: Record<string, ConstellationData> = {
    Aquarius: {
        stars: [
            // 상단 긴 라인
            { x: 78, y: 12 }, // 0: 상단 오른쪽 끝
            { x: 62, y: 22 }, // 1
            { x: 48, y: 34 }, // 2 (중앙 분기점)

            // 중앙 오른쪽 짧은 팔
            { x: 60, y: 40 }, // 3
            { x: 72, y: 42 }, // 4

            // 왼쪽 위 짧은 가지
            { x: 42, y: 40 }, // 5
            { x: 38, y: 48 }, // 6

            // 아래쪽 물 흐름 (지그재그)
            { x: 44, y: 58 }, // 7
            { x: 50, y: 70 }, // 8
            { x: 42, y: 82 }, // 9
            { x: 30, y: 68 }, // 10
        ],
        connections: [
            // 상단 긴 선
            [0, 1],
            [1, 2],

            // 중앙 오른쪽 팔
            [2, 3],
            [3, 4],

            // 왼쪽 짧은 꺾임
            [2, 5],
            [5, 6],

            // 아래 물 흐름
            [6, 7],
            [7, 8],
            [8, 9],
            [9, 10],
        ]
    },
    Pisces: { // 물고기자리 (Accurate V-Shape with Western Circlet and Northern Fish)
        stars: [
            { x: 50, y: 85 }, // 0: Alrescha (The Knot/Vertex)
            { x: 80, y: 65 }, // 1: Southeastern Cord Mid
            { x: 85, y: 45 }, // 2: Circlet Start (Western Fish)
            { x: 90, y: 35 }, { x: 80, y: 30 }, { x: 70, y: 35 }, { x: 75, y: 50 }, // 3-6: Circlet Loop
            { x: 20, y: 55 }, // 7: Northwestern Cord Mid
            { x: 20, y: 25 }, // 8: Top Fish
            { x: 30, y: 15 }, // 9: Top Fish Head
            { x: 15, y: 15 }  // 10: Top Fish Tail
        ],
        connections: [
            [0, 1], [1, 2], // Cord to Circlet
            [2, 3], [3, 4], [4, 5], [5, 6], [6, 2], // The Circlet
            [0, 7], [7, 8], // Cord to Top Fish
            [8, 9], [8, 10] // Top Fish shape
        ]
    },
    Aries: { // 양자리 (The Ram - Simple Curved Horn)
        stars: [
            { x: 20, y: 65 }, // 0: Tail/Body end?
            { x: 50, y: 55 }, // 1: Bharani
            { x: 70, y: 50 }, // 2: Hamal (Alpha)
            { x: 85, y: 60 }, // 3: Sheratan (Beta)
            { x: 90, y: 70 }  // 4: Mesarthim (Gamma)
        ],
        connections: [
            [0, 1], [1, 2], [2, 3], [3, 4] // Simple arc/hook line
        ]
    },
    Taurus: { // 황소자리 (The Bull - V-Shape Hyades + Long Horns)
        stars: [
            { x: 60, y: 60 }, // 0: Aldebaran (Alpha - The Eye)
            { x: 50, y: 56 }, // 1: Epsilon
            { x: 45, y: 62 }, // 2: Gamma (Hyades vertex)
            { x: 30, y: 40 }, // 3: Zeta Tauri (Horn Tip)
            { x: 80, y: 35 }, // 4: Elnath (Horn Tip)
            { x: 50, y: 65 }, // 5: V-bottom
            { x: 20, y: 30 }  // 6: Pleiades cluster (approx)
        ],
        connections: [
            [0, 5], [5, 2], [2, 1], [1, 0], // V-Shape Face
            [0, 4], // Aldebaran to Elnath (Long Horn)
            [2, 3],  // Hyades to Zeta (Long Horn)
            [2, 6]   // Line pointing to Pleiades
        ]
    },
    Gemini: { // 쌍둥이자리 (The Twins - Two parallel stick figures)
        stars: [
            { x: 35, y: 15 }, // 0: Castor (Alpha)
            { x: 65, y: 15 }, // 1: Pollux (Beta)
            { x: 35, y: 30 }, // 2: Castor Neck
            { x: 65, y: 30 }, // 3: Pollux Neck
            { x: 30, y: 50 }, { x: 40, y: 50 }, // 4-5: Castor Arms/Torso
            { x: 60, y: 50 }, { x: 70, y: 50 }, // 6-7: Pollux Arms/Torso
            { x: 25, y: 75 }, // 8: Castor Foot
            { x: 35, y: 75 }, // 9: Castor Foot
            { x: 60, y: 75 }, // 10: Pollux Foot
            { x: 75, y: 75 }  // 11: Pollux Foot
        ],
        connections: [
            [0, 2], [2, 4], [2, 5], [4, 8], [5, 9], // Castor Figure
            [1, 3], [3, 6], [3, 7], [6, 10], [7, 11], // Pollux Figure
            [5, 6] // Holding Hands (optional but cute)
        ]
    },
    Cancer: { // 게자리 (The Crab - Detailed)
        stars: [
            { x: 50, y: 50 }, // 0: Asellus Australis (Body Center)
            { x: 50, y: 45 }, // 1: Asellus Borealis (Body Top)
            { x: 20, y: 75 }, // 2: Acubens (Left Claw)
            { x: 80, y: 75 }, // 3: Beta Cancri await (Right Leg)
            { x: 50, y: 20 },  // 4: Iota (Top Feeler/Leg)
            { x: 35, y: 35 }   // 5: Chi (Inner Leg) - optional detail
        ],
        connections: [
            [0, 1], // Body segment
            [0, 2], // Left Claw
            [0, 3], // Right Leg
            [1, 4], // Top Leg
            [1, 5]  // Extra detail
        ]
    },
    Leo: { // 사자자리 (The Lion - Sickle + Trapezoid)
        stars: [
            { x: 70, y: 50 }, // 0: Regulus (Alpha - Heart)
            { x: 70, y: 35 }, // 1: Eta (Neck)
            { x: 60, y: 20 }, // 2: Algieba (Mane)
            { x: 45, y: 25 }, // 3: Adhafera
            { x: 35, y: 35 }, // 4: Rasalas (Head top)
            { x: 40, y: 45 }, // 5: Sickle curve end (Muzzle)
            { x: 90, y: 55 }, // 6: Chertan (Hindquarters)
            { x: 80, y: 70 }, // 7: Denebola (Tail)
            { x: 60, y: 60 }  // 8: Zosma (Back)
        ],
        connections: [
            [0, 1], [1, 2], [2, 3], [3, 4], [4, 5], // The Sickle (Question Mark)
            [1, 8], [8, 6], [6, 0], // Body Triangle/Trapezoid? Actually Regulus connects to Chertan often.
            [6, 7] // Tail
        ]
    },
    Virgo: { // 처녀자리 (The Maiden - Large Box/Diamond Layout)
        stars: [
            { x: 45, y: 20 }, // 0: Vindemiatrix (Head area)
            { x: 30, y: 35 }, // 1: Porrima (Shoulder/Center)
            { x: 20, y: 50 }, // 2: Zaniah
            { x: 60, y: 40 }, // 3: Auva
            { x: 35, y: 65 }, // 4: Heze
            { x: 55, y: 80 }  // 5: Spica (Alpha - Wheat ear)
        ],
        connections: [
            [0, 1], [1, 2], // Upper body
            [1, 3], [3, 4], [4, 5], // Box/Skirt shape leading to Spica
            [2, 4] // Closing the box
        ]
    },
    Libra: { // 천칭자리 (The Scales - Detailed Balance)
        stars: [
            { x: 50, y: 20 }, // 0: Beta (Top Fulcrum)
            { x: 25, y: 60 }, // 1: Alpha (Left Pan)
            { x: 75, y: 55 }, // 2: Gamma (Right Pan)
            { x: 50, y: 40 }, // 3: Center Beam connect? No, just triangle.
            { x: 35, y: 75 }, // 4: Upsilon? (Left Pan bottom)
            { x: 80, y: 70 }  // 5: Tau? (Right Pan bottom)
        ],
        connections: [
            [0, 1], [0, 2], // Beam hangs
            [1, 2], // Beam crossbar
            [1, 4], // Left Pan drop
            [2, 5]  // Right Pan drop
        ]
    },
    Scorpio: { // 전갈자리 (The Scorpion - J-Hook Tail + Claws)
        stars: [
            { x: 85, y: 20 }, { x: 75, y: 25 }, { x: 70, y: 30 }, // 0-2: Claws (Graffias, Dschubba, Pi)
            { x: 55, y: 40 }, // 3: Antares (Alpha - Heart)
            { x: 45, y: 55 }, // 4: Epsilon
            { x: 40, y: 70 }, // 5: Mu
            { x: 50, y: 85 }, // 6: Theta (Tail Curve bottom)
            { x: 70, y: 80 }, // 7: Kappa
            { x: 80, y: 70 }, // 8: Shaula (Stinger)
            { x: 78, y: 65 }  // 9: Lesath (Stinger tip adjacent)
        ],
        connections: [
            [0, 1], [1, 2], [2, 3], // Head/Claws
            [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9] // Body to Tail Hook
        ]
    },
    Sagittarius: { // 궁수자리 (The Archer / Teapot)
        stars: [
            { x: 35, y: 45 }, // 0: Kaus Borealis (Lid Top)
            { x: 20, y: 60 }, // 1: Alnasl (Spout Tip)
            { x: 40, y: 65 }, // 2: Kaus Media (Spout Base)
            { x: 50, y: 80 }, // 3: Kaus Australis (Pot Bottom)
            { x: 65, y: 60 }, // 4: Ascella (Handle Base)
            { x: 80, y: 50 }, // 5: Tau (Handle Top)
            { x: 60, y: 45 }, // 6: Nunki (Lid/Handle Junction)
            { x: 55, y: 20 }  // 7: Polis (Head/Bow top?)
        ],
        connections: [
            [0, 2], [2, 3], [3, 4], [4, 6], [6, 0], // The Teapot Body (Lid + Pot)
            [2, 1], // Spout
            [4, 5], [5, 6], // Handle
            [0, 7] // Line up to head (optional)
        ]
    },
    Capricorn: { // 염소자리 (The Sea-Goat - Detailed V-Shape)
        stars: [
            { x: 15, y: 20 }, // 0: Algedi (Alpha) - Top Horn
            { x: 10, y: 30 }, // 1: Dabih (Beta) - Bottom Horn
            { x: 40, y: 50 }, // 2: Theta (Body Mid)
            { x: 60, y: 75 }, // 3: Omega (Belly Low)
            { x: 90, y: 40 }, // 4: Deneb Algedi (Tail)
            { x: 80, y: 30 }, // 5: Nashira (Tail Top)
            { x: 30, y: 40 }  // 6: Psi? (Neck join)
        ],
        connections: [
            [0, 1], // Horns tip
            [1, 6], [6, 2], [2, 3], // Belly curve
            [3, 4], // To Tail
            [4, 5], // Tail tip connection
            [5, 2], // Back line
            [6, 0]  // Closing the head loop
        ]
    },
};

interface ConstellationViewerProps {
    zodiacName: string;
}

const ConstellationViewer = ({ zodiacName }: ConstellationViewerProps) => {
    const data = CONSTELLATIONS[zodiacName] || CONSTELLATIONS['Aries'];
    const totalLines = data.connections.length;

    return (
        <div className="relative w-[300px] h-[300px] mx-auto opacity-80">
            <svg
                viewBox="0 0 100 100"
                className="w-full h-full drop-shadow-[0_0_10px_rgba(255,255,255,0.8)]"
            >
                {/* Lines */}
                <AnimatePresence>
                    {data.connections.map(([startIdx, endIdx], i) => {
                        const start = data.stars[startIdx];
                        const end = data.stars[endIdx];

                        return (
                            <motion.line
                                key={`line-${zodiacName}-${i}`}
                                x1={start.x}
                                y1={start.y}
                                x2={end.x}
                                y2={end.y}
                                stroke="white"
                                strokeWidth="0.5"
                                strokeOpacity="0.6"
                                variants={{
                                    initial: { pathLength: 0, opacity: 0 },
                                    animate: {
                                        pathLength: 1,
                                        opacity: 1,
                                        transition: { duration: 0.5, delay: 0.1 + i * 0.05, ease: "easeInOut" }
                                    },
                                    exit: {
                                        pathLength: 0,
                                        opacity: 0,
                                        transition: { duration: 0.8, delay: (totalLines - i) * 0.05, ease: "easeInOut" } // Reverse undraw
                                    }
                                }}
                                initial="initial"
                                animate="animate"
                                exit="exit"
                            />
                        );
                    })}
                </AnimatePresence>

                {/* Stars */}
                <AnimatePresence>
                    {data.stars.map((star, i) => (
                        <motion.circle
                            key={`star-${zodiacName}-${i}`}
                            cx={star.x}
                            cy={star.y}
                            r="1.5"
                            fill="white"
                            variants={{
                                initial: { scale: 0, opacity: 0, filter: 'blur(0px)' },
                                animate: {
                                    scale: [1, 1.5, 1],
                                    opacity: [0.6, 1, 0.6],
                                    filter: ['blur(0px)', 'blur(2px)', 'blur(0px)'],
                                    transition: {
                                        duration: 2,
                                        repeat: Infinity,
                                        repeatType: "reverse",
                                        delay: i * 0.2, // Staggered twinkling
                                        ease: "easeInOut"
                                    }
                                },
                                exit: {
                                    scale: 0,
                                    opacity: 0,
                                    transition: { duration: 0.5, delay: 1.0 } // Fade out while lines undraw
                                }
                            }}
                            initial="initial"
                            animate="animate"
                            exit="exit"
                        />
                    ))}
                </AnimatePresence>
            </svg>

            {/* Glowing Backdrop */}
            <motion.div
                className="absolute inset-0 bg-blue-500/10 rounded-full blur-3xl -z-10"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 2 }}
            />
        </div>
    );
};

export default ConstellationViewer;
