
const HopaeNameplate = ({ name, subName }: { name: string, subName?: string }) => (
    <div className="w-32 h-80 relative flex flex-col items-center bg-gradient-to-br from-[#4a3728] via-[#3d2e1f] to-[#2d1f14] rounded-xl border-4 border-[#6b4e3d]/80 shadow-2xl overflow-hidden">
        <div className="absolute inset-0 opacity-30 mix-blend-overlay pointer-events-none" style={{ backgroundImage: "url('https://www.transparenttextures.com/patterns/wood-pattern.png')" }} />
        <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/70 pointer-events-none" />
        <div className="absolute top-6 left-1/2 -translate-x-1/2 z-20">
            <div className="w-4 h-4 bg-[#0d0805] rounded-full shadow-inner border border-black/50" />
            <div className="absolute -top-16 left-1/2 -translate-x-1/2 w-[2px] h-20 bg-red-900/60" />
        </div>
        <div className="flex-1 flex flex-col items-center justify-center writing-vertical-rl relative z-10 w-full p-4">
            <span className="font-['Hahmlet'] font-extrabold text-amber-50/95 tracking-[0.25em] text-2xl" style={{ writingMode: 'vertical-rl', textOrientation: 'upright' }}>
                {name}
            </span>
            {subName && (
                <span className="font-['Hahmlet'] font-medium text-amber-50/40 tracking-widest text-[10px] mt-2" style={{ writingMode: 'vertical-rl', textOrientation: 'upright' }}>
                    ({subName})
                </span>
            )}
        </div>
    </div>
);

export default HopaeNameplate;
