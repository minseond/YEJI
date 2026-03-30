import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';

interface Option {
    value: string;
    label: string;
}

interface CustomSelectProps {
    value: string;
    options: Option[];
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
    width?: string;
}

const CustomSelect = ({ value, options, onChange, placeholder, className = '', width = 'w-full' }: CustomSelectProps) => {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);
    const selectedOption = options.find(opt => opt.value === value);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div ref={containerRef} className={`relative ${width} ${className}`}>
            <button
                type="button"
                onClick={() => setIsOpen(!isOpen)}
                className="w-full bg-amber-500/5 border-b-2 border-amber-900/20 px-3 py-3 text-center flex items-center justify-center gap-2 hover:border-amber-700 transition-colors group"
            >
                <span className={selectedOption ? 'text-amber-950' : 'text-amber-900/40 text-sm'}>
                    {selectedOption ? selectedOption.label : placeholder}
                </span>
                <ChevronDown
                    size={14}
                    className={`text-amber-900/30 transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}
                />
            </button>

            <AnimatePresence>
                {isOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 5 }}
                        className="absolute z-[120] left-0 right-0 mt-1 bg-[#fdfaf3] border border-amber-900/20 rounded-md shadow-2xl overflow-hidden"
                        style={{ backgroundImage: "url('https://www.transparenttextures.com/patterns/handmade-paper.png')" }}
                    >
                        <div className="max-h-[200px] overflow-y-auto scrollbar-thin scrollbar-thumb-amber-900/20 scrollbar-track-transparent">
                            {options.map((opt) => (
                                <button
                                    key={opt.value}
                                    type="button"
                                    onClick={() => {
                                        onChange(opt.value);
                                        setIsOpen(false);
                                    }}
                                    className={`w-full text-center py-2 text-sm transition-colors hover:bg-amber-900/5 ${value === opt.value ? 'text-amber-900 font-bold bg-amber-900/10' : 'text-amber-900/70'
                                        }`}
                                >
                                    {opt.label}
                                </button>
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
};

export default CustomSelect;
