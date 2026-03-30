import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Routes, Route, useLocation, useNavigate, Navigate } from 'react-router-dom';

import Navbar from './components/Navbar';
import Home from './components/pages/Home';
import About from './components/pages/About';
import History from './components/pages/History';
import SajuHistoryDetail from './components/history/SajuHistoryDetail';
import UnseHistoryDetail from './components/history/UnseHistoryDetail';
import CompatibilityHistoryDetail from './components/history/CompatibilityHistoryDetail';
import CardHistoryDetail from './components/history/CardHistoryDetail';
import Settings from './components/pages/Settings';
import FaceMyself from './components/features/FaceMyself';

import LoginPage from './components/pages/LoginPage';
import TodayFortunePage from './components/pages/TodayFortunePage';

import CollectionPage from './components/pages/CollectionPage';
import MyPage from './components/pages/MyPage';
import ShopPage from './components/pages/ShopPage';
import EventPage from './components/pages/EventPage';
import EventDetailPage from './components/pages/EventDetailPage';
import FriendsPage from './components/pages/FriendsPage';
import CompatibilityPage from './components/pages/CompatibilityPage';
import OAuthCallback from './components/auth/OAuthCallback';
import CardReadingPage from './components/pages/CardReadingPage';
import CustomCursor from './components/common/CustomCursor';
import GlobalSoundControl from './components/ui/GlobalSoundControl';
import { CollectionProvider } from './contexts/CollectionContext';
import { useSound } from './hooks/useSound';
import Modal from './components/common/Modal';
import { AUTH_EXPIRED_EVENT } from './utils/authEvents';

export interface AppSettings {
  volume: number;
  effectIntensity: 'low' | 'medium' | 'high';
  autoAdvance: boolean;
}

function App() {
  const location = useLocation();
  const { play, stop } = useSound();
  const navigate = useNavigate();

  const [cinematicMode, setCinematicMode] = useState(false);
  const [currentTheme, setCurrentTheme] = useState('western');
  const [menuVisible, setMenuVisible] = useState(true);

  // Global Settings State
  const [settings, setSettings] = useState<AppSettings>({
    volume: 50,
    effectIntensity: 'high',
    autoAdvance: false // Default: Manual progression
  });

  const [isSessionExpiredModalOpen, setIsSessionExpiredModalOpen] = useState(false);

  const updateSetting = (key: keyof AppSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  // BGM Management: Play WEST2 on all core/lobby pages
  React.useEffect(() => {
    const isAnalysisPage = location.pathname.startsWith('/card-reading') ||
      location.pathname === '/compatibility';
    const isRootPath = location.pathname === '/';
    const isAuthenticated = !!localStorage.getItem('accessToken');

    // Only stop BGM on root path if NOT authenticated (i.e., truly on the login page)
    const shouldStopOnRoot = isRootPath && !isAuthenticated;

    if (!isAnalysisPage && !shouldStopOnRoot) {
      play('BGM', 'WEST2', { loop: true, volume: 0.3 });
    } else {
      stop('BGM', 'WEST2');
    }
  }, [location.pathname, play, stop]);

  // Global Sound Effects: Click and Spacebar
  React.useEffect(() => {
    const handleGlobalClick = (e: MouseEvent) => {
      // Exclude clicks on input elements to avoid triple-firing or annoyance
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.closest('button') || // Buttons usually have their own click sounds
        target.closest('a')
      ) {
        return;
      }
      play('SFX', 'CLICK1');
    };

    const handleGlobalKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        const target = e.target as HTMLElement;
        if (
          target.tagName === 'INPUT' ||
          target.tagName === 'TEXTAREA' ||
          target.isContentEditable
        ) {
          return;
        }
        // Play sound for spacebar if not in input
        play('SFX', 'CLICK2');
      }
    };

    window.addEventListener('mousedown', handleGlobalClick);
    window.addEventListener('keydown', handleGlobalKeyDown);

    return () => {
      window.removeEventListener('mousedown', handleGlobalClick);
      window.removeEventListener('keydown', handleGlobalKeyDown);
    };
  }, [play]);

  // Auth Expiration Listener
  React.useEffect(() => {
    const handleAuthExpired = () => {
      setIsSessionExpiredModalOpen(true);
    };

    window.addEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleAuthExpired);
  }, []);

  const isAuthPage = location.pathname === '/' || location.pathname === '/login' || location.pathname === '/signup';

  // Helper component to redirect authenticated users
  const PublicRoute = ({ children }: { children: React.ReactNode }) => {
    const token = localStorage.getItem('accessToken');
    return token ? <Navigate to="/home" replace /> : children;
  };

  return (
    <CollectionProvider>
      <div className="relative min-h-screen w-full overflow-hidden bg-gradient-to-b from-slate-900 via-[#0b0d14] to-black text-white selection:bg-red-500/30 font-serif">
        <CustomCursor />
        <GlobalSoundControl />

        {/* Background Decor - textured paper overlay */}
        <div className="absolute top-0 left-0 w-full h-full pointer-events-none opacity-10 bg-[url('/textures/beige_paper.png')] bg-cover mix-blend-overlay z-0"></div>

        {/* Fixed Navbar (Visible on non-auth pages and not on today fortune page or history details) */}
        <AnimatePresence>
          {!isAuthPage &&
            !cinematicMode &&
            menuVisible &&
            location.pathname !== '/today' &&
            !location.pathname.startsWith('/unse/result/') &&
            !location.pathname.startsWith('/cards/result/') &&
            !location.pathname.startsWith('/compatibility/result/') &&
            !location.pathname.startsWith('/history/saju') && (
              <Navbar />
            )}
        </AnimatePresence>

        <motion.main
          className="relative z-10 flex-1 flex flex-col min-h-screen pt-0 w-full"
          animate={{
            filter: cinematicMode ? "blur(50px) brightness(0.2)" : "none",
            opacity: cinematicMode ? 0 : 1,
            scale: cinematicMode ? 1.2 : 1
          }}

          transition={{ duration: cinematicMode ? 2.5 : 1.5, ease: "easeInOut" }}
        >
          <Routes location={location}>
            <Route path="/" element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            } />
            <Route path="/home" element={<Home onStartCinematic={() => setCinematicMode(true)} onThemeChange={setCurrentTheme} onMenuVisibilityChange={setMenuVisible} />} />
            <Route path="/today" element={<TodayFortunePage />} />
            <Route path="/login" element={<Navigate to="/" replace />} />

            <Route path="/collection" element={<CollectionPage />} />
            <Route path="/mypage" element={<MyPage />} />
            <Route path="/shop" element={<ShopPage />} />
            <Route path="/friends" element={<FriendsPage />} />
            <Route path="/events" element={<EventPage />} />
            <Route path="/events/:id" element={<EventDetailPage />} />
            <Route path="/card-reading" element={<CardReadingPage onMenuVisibilityChange={setMenuVisible} />} />
            <Route path="/compatibility" element={<CompatibilityPage onMenuVisibilityChange={setMenuVisible} />} />
            <Route path="/about" element={<About />} />
            <Route path="/history" element={<History />} />
            <Route path="/history/saju" element={<SajuHistoryDetail />} />
            <Route path="/unse/result/:id" element={<UnseHistoryDetail />} />
            <Route path="/compatibility/result/:id" element={<CompatibilityHistoryDetail />} />
            <Route path="/cards/result/:id" element={<CardHistoryDetail />} />
            <Route path="/settings" element={<Settings settings={settings} onUpdate={updateSetting} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
            <Route path="/oauth/callback" element={<OAuthCallback />} />
          </Routes>
        </motion.main>

        <AnimatePresence>
          {cinematicMode && (
            <FaceMyself
              onClose={() => setCinematicMode(false)}
              autoAdvance={settings.autoAdvance}
              onToggleAutoAdvance={() => updateSetting('autoAdvance', !settings.autoAdvance)}
            />
          )}
        </AnimatePresence>

        {/* Global Session Expired Modal */}
        <Modal
          isOpen={isSessionExpiredModalOpen}
          onClose={() => {
            setIsSessionExpiredModalOpen(false);
            navigate('/');
          }}
          title="세션 만료"
          message="로그인 세션이 만료되었습니다. 다시 로그인하여 주십시오."
          type="info"
          confirmText="확인"
          onConfirm={() => {
            setIsSessionExpiredModalOpen(false);
            navigate('/');
          }}
        />
      </div>
    </CollectionProvider>
  );
}

export default App;
