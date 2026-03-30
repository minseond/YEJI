import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Sparkles, ScrollText, BookOpen, UserCircle, LogOut, LogIn, Menu, X, Users } from 'lucide-react';
import Modal from './common/Modal';
import { useSound } from '../hooks/useSound';
import logoImage from '../assets/logo.png';

const Navbar = () => {
    const location = useLocation();
    const navigate = useNavigate();
    const { play } = useSound();
    const [scrolled, setScrolled] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('accessToken'));
    const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
    // Update auth state on location change (navigation)
    useEffect(() => {
        const checkAuth = () => {
            const token = localStorage.getItem('accessToken');
            setIsLoggedIn(!!token);
        };
        checkAuth();
    }, [location]);

    // Scroll effect for glassmorphism intensity
    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const handleLogoutConfirm = () => {
        play('SFX', 'CLICK1');
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        setIsLoggedIn(false);
        navigate('/');
        setIsLogoutModalOpen(false);
    };

    const navLinks = [
        { title: '운세', path: '/home', icon: Sparkles },
        { title: '히스토리', path: '/history', icon: ScrollText },
        { title: '도감', path: '/collection', icon: BookOpen },
        { title: '친구', path: '/friends', icon: Users },
        { title: '마이페이지', path: '/mypage', icon: UserCircle },
    ];

    const isActive = (path: string) => location.pathname === path;
    const shouldHideNav = location.pathname === '/history/saju';

    return (
        <>
            <motion.nav
                initial={{ y: -100 }}
                animate={{ y: shouldHideNav ? -100 : 0 }}
                className={`fixed top-0 left-0 right-0 z-[100] transition-all duration-300 border-b
                    bg-black/20 backdrop-blur-md pb-4 pt-6
                    ${scrolled
                        ? 'bg-black/80 border-white/10 py-4 shadow-lg'
                        : 'border-transparent'
                    }`}
            >
                <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
                    {/* Brand / Logo Area (Minimalist) */}
                    <Link
                        to="/home"
                        onClick={() => play('SFX', 'CLICK1')}
                        className="flex items-center gap-2 group"
                    >
                        <img src={logoImage} alt="YEJI Logo" className="w-10 h-10 rounded-full object-cover opacity-80 group-hover:opacity-100 transition-opacity" />
                        <span className="text-2xl font-bold tracking-widest text-white font-['Pretendard'] group-hover:text-indigo-200 transition-colors">
                            YEJI
                        </span>
                    </Link>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex items-center gap-8">
                        {navLinks.map((link) => (
                            <Link
                                key={link.path}
                                to={link.path}
                                onClick={() => play('SFX', 'CLICK1')}
                                className={`relative flex items-center gap-2 text-base font-['Pretendard'] font-bold transition-all duration-300 group
                                    ${isActive(link.path) ? 'text-white' : 'text-white/50 hover:text-white'}
                                `}
                            >
                                <span className={`uppercase tracking-wider ${isActive(link.path) ? 'text-indigo-400' : ''}`}>
                                    {link.title}
                                </span>
                                {isActive(link.path) && (
                                    <motion.div
                                        layoutId="navIndicator"
                                        className="absolute -bottom-2 left-0 right-0 h-0.5 bg-indigo-400 shadow-[0_0_10px_rgba(129,140,248,0.7)]"
                                    />
                                )}
                            </Link>
                        ))}
                    </div>

                    {/* Right Side Actions */}
                    <div className="hidden md:flex items-center gap-4">
                        {isLoggedIn ? (
                            <button
                                onClick={() => {
                                    play('SFX', 'CLICK1');
                                    setIsLogoutModalOpen(true);
                                }}
                                className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 hover:bg-red-500/20 text-white/50 hover:text-red-300 transition-colors"
                                title="Logout"
                            >
                                <LogOut size={16} />
                                <span className="text-xs font-bold font-['Pretendard']">로그아웃</span>
                            </button>
                        ) : (
                            <button
                                onClick={() => {
                                    play('SFX', 'CLICK1');
                                    navigate('/');
                                }}
                                className="flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/10 hover:bg-indigo-500/20 text-white/50 hover:text-indigo-300 transition-colors"
                                title="Login"
                            >
                                <LogIn size={16} />
                                <span className="text-xs font-bold font-['Pretendard']">로그인</span>
                            </button>
                        )}
                    </div>

                    {/* Mobile Menu Toggle */}
                    <div className="md:hidden">
                        <button
                            onClick={() => {
                                play('SFX', 'CLICK1');
                                setMobileMenuOpen(!mobileMenuOpen);
                            }}
                            className="text-white"
                        >
                            {mobileMenuOpen ? <X /> : <Menu />}
                        </button>
                    </div>
                </div>
            </motion.nav>

            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {mobileMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0, y: -20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="fixed inset-0 z-90 bg-black/95 backdrop-blur-xl md:hidden flex flex-col items-center justify-center gap-8 pt-20"
                    >
                        {navLinks.map((link) => (
                            <Link
                                key={link.path}
                                to={link.path}
                                onClick={() => {
                                    play('SFX', 'CLICK1');
                                    setMobileMenuOpen(false);
                                }}
                                className={`text-2xl font-['Pretendard'] font-bold tracking-widest flex items-center gap-3
                                    ${isActive(link.path) ? 'text-indigo-400' : 'text-white/60'}
                                `}
                            >
                                <link.icon size={24} />
                                {link.title}
                            </Link>
                        ))}
                        {isLoggedIn ? (
                            <button
                                onClick={() => {
                                    setMobileMenuOpen(false);
                                    setIsLogoutModalOpen(true);
                                }}
                                className="mt-8 flex items-center gap-2 text-white/40 hover:text-red-400 font-['Pretendard'] font-bold transition-colors"
                            >
                                <LogOut size={20} /> 로그아웃
                            </button>
                        ) : (
                            <button
                                onClick={() => {
                                    setMobileMenuOpen(false);
                                    navigate('/');
                                }}
                                className="mt-8 flex items-center gap-2 text-white/40 hover:text-indigo-400 font-['Pretendard'] font-bold transition-colors"
                            >
                                <LogIn size={20} /> 로그인
                            </button>
                        )}
                    </motion.div>
                )}
            </AnimatePresence>

            <Modal
                isOpen={isLogoutModalOpen}
                onClose={() => setIsLogoutModalOpen(false)}
                title="로그아웃"
                message="정말 로그아웃 하시겠습니까?"
                showCancel={true}
                onConfirm={handleLogoutConfirm}
            />
        </>
    );
};

export default Navbar;
