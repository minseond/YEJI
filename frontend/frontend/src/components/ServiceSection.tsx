import { motion } from 'framer-motion';
import type { ReactNode } from 'react';

interface ServiceSectionProps {
    title: string;
    description: string;
    icon: ReactNode;
    colorTheme?: string;
    children?: ReactNode;
}

const ServiceSection = ({ title, description, icon, colorTheme = "text-white", children }: ServiceSectionProps) => {
    return (
        <section className="h-screen w-full snap-start flex flex-col items-center justify-center relative p-8">
            <motion.div
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: false, amount: 0.5 }}
                transition={{ duration: 0.8, ease: "easeOut" }}
                className="flex flex-col items-center text-center gap-6 z-10"
            >
                {/* Icon Container */}
                <div className={`text-6xl md:text-8xl ${colorTheme} drop-shadow-[0_0_15px_rgba(255,255,255,0.3)] mb-4`}>
                    {icon}
                </div>

                <h2 className={`text-5xl md:text-7xl font-['Nanum_Brush_Script'] ${colorTheme} drop-shadow-lg`}>
                    {title}
                </h2>

                <p className="text-xl md:text-2xl text-white/80 font-['Gowun_Batang'] max-w-lg leading-relaxed drop-shadow-md">
                    {description}
                </p>

                {children}

                {/* Decorative Button */}
                <button className="mt-8 px-8 py-3 border border-white/30 rounded-full text-white/70 font-['Gowun_Batang'] hover:bg-white/10 hover:text-white transition-all backdrop-blur-sm">
                    입장하기
                </button>
            </motion.div>
        </section>
    );
};

export default ServiceSection;
