import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Coins, Hammer, PlayCircle, CheckCircle, Sparkles, Receipt, Trophy } from 'lucide-react';
import { createPayment, verifyPayment, type Product } from '../../api/shop';
import Modal from '../common/Modal';
import PaymentHistoryModal from '../common/PaymentHistoryModal';
import TickerLoading2 from '../../assets/character/west/Ticker/Ticker_loading2.png';

const ShopPage = () => {
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [verifying, setVerifying] = useState(false);
    const [showHistoryModal, setShowHistoryModal] = useState(false);
    const [alertModal, setAlertModal] = useState<{
        isOpen: boolean;
        title: string;
        message: string;
        type: 'error' | 'success' | 'info';
        onConfirm?: () => void;
    }>({
        isOpen: false,
        title: '',
        message: '',
        type: 'info'
    });

    const showAlert = (title: string, message: string, type: 'error' | 'success' | 'info' = 'info', onConfirm?: () => void) => {
        setAlertModal({ isOpen: true, title, message, type, onConfirm });
    };

    const handleCloseModal = () => {
        if (alertModal.onConfirm) {
            alertModal.onConfirm();
        }
        setAlertModal(prev => ({ ...prev, isOpen: false, onConfirm: undefined }));
    };

    // Fetch Products (Mock Data for UI Update)
    useEffect(() => {
        // [Frontend] Sync with current DB state (Backend needs update)
        const newProducts: Product[] = [
            { productId: 1, name: 'FP 입문 팩', priceKrw: 1000, fpAmount: 10, isActive: true },
            { productId: 2, name: 'FP 실속 팩', priceKrw: 5000, fpAmount: 55, isActive: true },
            { productId: 3, name: 'FP 인기 팩', priceKrw: 10000, fpAmount: 120, isActive: true },
        ];
        setProducts(newProducts);
        setLoading(false);
    }, []);

    // Mock Data for Ad Missions - UPDATED REWARDS (1FP, 3FP)
    const adMissions = [
        { id: 1, title: '짧은 광고 시청', reward: 1, icon: PlayCircle, time: '30초', desc: '광고를 끝까지 시청하고 포인트 받기' },
        { id: 3, title: '설문조사 참여', reward: 3, icon: CheckCircle, time: '3분', desc: '간단한 설문에 응답하고 포인트 획득' },
    ];

    const handlePurchase = async (product: Product) => {
        try {
            setLoading(true);
            let orderData;

            // [Test Mode] Skip Backend Order Creation for 100 KRW Test Product
            if (product.productId === 99999) {
                orderData = {
                    orderId: `test_order_${Date.now()} `,
                    orderName: '테스트 상품 100원',
                    amount: 100
                };
            } else {
                // 1. 주문 생성 (Backend)
                orderData = await createPayment(product.productId);
            }

            // 2. PortOne 결제 요청
            if (!window.IMP) {
                showAlert("오류", "결제 모듈 로드 실패", "error");
                setLoading(false);
                return;
            }
            const { IMP } = window;
            IMP.init('imp30812426'); // User Merchant ID

            const paymentData = {
                pg: 'kakaopay',
                pay_method: 'card',
                merchant_uid: orderData.orderId,
                name: orderData.orderName,
                amount: product.priceKrw, // Frontend Data Usage (Safer)
                buyer_email: 'test@yeji.com',
                buyer_name: '예지 유저',
                buyer_tel: '010-1234-5678',
            };

            IMP.request_pay(paymentData, async (rsp: any) => {
                if (rsp.success) {
                    // [Test Mode] Skip Verification for Test Product
                    if (product.productId === 99999) {
                        // Save to LocalStorage for History Display
                        const testHistoryItem = {
                            orderId: orderData.orderId,
                            productName: product.name,
                            amount: product.priceKrw,
                            status: 'PAID',
                            createdAt: new Date().toISOString()
                        };
                        const prevHistory = JSON.parse(localStorage.getItem('local_test_payments') || '[]');
                        localStorage.setItem('local_test_payments', JSON.stringify([testHistoryItem, ...prevHistory]));

                        showAlert(
                            "테스트 성공",
                            `✨ 결제 테스트가 완료되었습니다!\n(테스트 상품이므로 실제 포인트 지급 및 서버 검증은 스킵됩니다.)`,
                            "success",
                            () => window.location.reload()
                        );
                        setVerifying(false);
                        setLoading(false);
                        return;
                    }

                    // 3. 결제 검증 (Backend)
                    try {
                        setVerifying(true);
                        // [BugFix] Send correct FP amount (including bonus) to backend
                        await verifyPayment(orderData.orderId, rsp.imp_uid);
                        // Success -> Reload after generic modal close
                        showAlert(
                            "구매 성공",
                            `✨ ${product.name} 구매가 완료되었습니다!`,
                            "success",
                            () => window.location.reload()
                        );
                    } catch (verifyError) {
                        console.error("Verification Failed:", verifyError);
                        showAlert(
                            "검증 실패",
                            "결제는 성공했으나, 서버 검증에 실패했습니다.\n관리자에게 문의하세요.",
                            "error"
                        );
                    } finally {
                        setVerifying(false);
                        setLoading(false);
                    }
                } else {
                    showAlert("결제 실패", `사유: ${rsp.error_msg} `, "error");
                    setLoading(false);
                }
            });
        } catch (error) {
            console.error("Payment Error:", error);
            showAlert("오류", "결제 진행 중 오류가 발생했습니다.", "error");
            setLoading(false);
        }
    };

    // [New] Check Daily Mission Completion Status
    const [completedMissions, setCompletedMissions] = useState<Record<number, boolean>>({});

    useEffect(() => {
        const checkMissions = () => {
            const today = new Date().toISOString().split('T')[0];
            const missionStatus = JSON.parse(localStorage.getItem('daily_missions_status') || '{}');
            const completed: Record<number, boolean> = {};

            [1, 3].forEach(id => {
                if (missionStatus[id] === today) {
                    completed[id] = true;
                }
            });
            setCompletedMissions(completed);
        };

        checkMissions();
    }, []);

    const handleAdWatch = (mission: any) => {
        if (completedMissions[mission.id]) {
            showAlert("참여 완료", "이미 오늘 참여하신 미션입니다. 내일 다시 참여해주세요!", "info");
            return;
        }

        const today = new Date().toISOString().split('T')[0];
        const updateStatus = () => {
            const missionStatus = JSON.parse(localStorage.getItem('daily_missions_status') || '{}');
            missionStatus[mission.id] = today;
            localStorage.setItem('daily_missions_status', JSON.stringify(missionStatus));
            setCompletedMissions(prev => ({ ...prev, [mission.id]: true }));
        };

        // [New] 짧은 광고 시청 (ID: 1) -> YouTube Link
        if (mission.id === 1) {
            window.open('https://www.youtube.com/watch?v=XIoPeobfuhE', '_blank');
            updateStatus();
            showAlert("완료", `${mission.title} 완료! 무료 FP ${mission.reward}개를 획득했습니다.`, "success");
        }
        // 설문조사 미션인 경우 Google Form 새창 열기
        else if (mission.id === 3) {
            window.open('https://forms.gle/261pSmuGHFEkzmNu7', '_blank');
            updateStatus();
            showAlert("완료", `${mission.title} 완료! 무료 FP ${mission.reward}개를 획득했습니다.`, "success");
        } else {
            updateStatus();
            showAlert("완료", `${mission.title} 완료! 무료 FP ${mission.reward}개를 획득했습니다.`, "success");
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="w-full h-screen relative px-6 pb-20 pt-28 bg-[#0b0d14] text-white overflow-y-auto font-['GmarketSansMedium'] custom-scrollbar"
        >
            {/* Background Effects */}
            <div className="fixed inset-0 bg-[radial-gradient(circle_at_50%_10%,_#1e1b4b_0%,_#0b0d14_100%)] pointer-events-none" />
            <div className="fixed top-[-20%] left-[-10%] w-[600px] h-[600px] bg-purple-600/10 blur-[150px] rounded-full pointer-events-none" />
            <div className="fixed bottom-[-20%] right-[-10%] w-[600px] h-[600px] bg-amber-600/10 blur-[150px] rounded-full pointer-events-none" />

            {/* Header */}
            <div className="relative z-10 max-w-6xl mx-auto w-full mb-12">


                <div className="flex flex-col md:flex-row items-start md:items-end justify-between gap-6 pb-8 border-b border-white/5">
                    <div>
                        <h1 className="text-4xl md:text-5xl font-gmarket font-bold text-transparent bg-clip-text bg-gradient-to-r from-amber-200 via-yellow-100 to-amber-200 mb-3 drop-shadow-[0_0_15px_rgba(251,191,36,0.3)]">
                            신비한 FP 상점
                        </h1>
                        <p className="text-white/40 text-lg font-light">
                            운명을 엿보기 위한 정성, 이곳에서 준비하세요.
                        </p>
                    </div>
                    <button
                        onClick={() => setShowHistoryModal(true)}
                        className="flex items-center gap-2 px-5 py-2.5 bg-white/5 hover:bg-white/10 rounded-full text-sm font-medium transition-all border border-white/10 hover:border-white/20"
                    >
                        <Receipt size={16} className="text-gray-300" />
                        <span>결제 내역</span>
                    </button>
                </div>
            </div>

            {/* Main Content: Products */}
            <div className="relative z-10 max-w-6xl mx-auto w-full mb-20">
                <h2 className="text-xl text-white/90 mb-8 flex items-center gap-3 font-bold">
                    <span className="w-1 h-6 bg-gradient-to-b from-amber-300 to-amber-600 rounded-full block" />
                    <span>FP 구매하기</span>
                </h2>

                {loading || verifying ? (
                    <div className="flex flex-col items-center justify-center py-32 text-center gap-4">
                        <div className="w-12 h-12 border-4 border-amber-500/30 border-t-amber-500 rounded-full animate-spin" />
                        <span className="text-white/40 font-light animate-pulse">
                            {verifying ? "결제 확인 중입니다..." : "상품을 진열하고 있습니다..."}
                        </span>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                        {products.map((product, idx) => (
                            <motion.div
                                key={product.productId}
                                initial={{ opacity: 0, y: 30 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: idx * 0.1, type: "spring", stiffness: 100 }}
                                whileHover={{ y: -8, boxShadow: "0 20px 40px -10px rgba(0,0,0,0.5)" }}
                                className="relative group"
                            >
                                {/* Card Glow Effect */}
                                <div className="absolute -inset-[1px] bg-gradient-to-b from-white/20 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 blur-sm" />

                                <div className="relative h-full bg-[#16161a]/80 backdrop-blur-xl border border-white/5 rounded-2xl p-6 flex flex-col items-center justify-between gap-6 overflow-hidden transition-colors group-hover:border-white/20">

                                    {/* Best Badge (Left Top) */}
                                    {product.productId === 3 && (
                                        <div className="absolute top-0 left-0">
                                            <div className="bg-gradient-to-br from-amber-400 to-orange-500 text-black text-[10px] font-bold px-3 py-1.5 rounded-br-xl shadow-lg flex items-center gap-1 z-10">
                                                <Sparkles size={10} fill="black" /> BEST
                                            </div>
                                        </div>
                                    )}

                                    {/* Bonus Badge (Right Top) */}
                                    {(product.priceKrw >= 5000) && (
                                        <div className="absolute top-0 right-0">
                                            <div className={`text-[10px] font-bold px-3 py-1.5 rounded-bl-xl shadow-lg flex items-center gap-1 z-10 
                                                ${product.productId === 4 ? 'bg-indigo-500 text-white' : 'bg-neutral-800 text-amber-200 border-l border-b border-amber-500/30'}`}>
                                                <span>+{product.priceKrw === 5000 ? '10%' : product.priceKrw === 10000 ? '20%' : '30%'}</span> Bonus
                                            </div>
                                        </div>
                                    )}

                                    {/* Image Container */}
                                    <div className="relative w-24 h-24 mt-4">
                                        <div className="absolute inset-0 bg-amber-500/20 blur-[30px] rounded-full group-hover:bg-amber-500/30 transition-colors duration-500" />
                                        <div className="relative w-full h-full flex items-center justify-center drop-shadow-[0_10px_20px_rgba(0,0,0,0.5)] transform group-hover:scale-110 transition-transform duration-500">
                                            {/* Dynamic Icon Size based on Amount */}
                                            <span style={{ fontSize: product.fpAmount >= 5000 ? '3.5rem' : product.fpAmount >= 1000 ? '3rem' : product.fpAmount >= 100 ? '2.5rem' : '1.5rem' }}>
                                                💰
                                            </span>
                                        </div>
                                    </div>

                                    {/* Content */}
                                    <div className="text-center space-y-2 w-full">
                                        <h3 className="text-xl font-bold text-white group-hover:text-amber-200 transition-colors">
                                            {product.name}
                                        </h3>
                                        <div className="flex items-center justify-center gap-1.5 text-amber-100/60 bg-white/5 rounded-lg py-1.5 mx-auto w-fit px-4">
                                            <span className="text-sm font-light">FP</span>
                                            <span className="text-lg font-bold text-white">{product.fpAmount}</span>
                                            <span className="text-sm font-light">개</span>
                                        </div>
                                    </div>

                                    {/* Action */}
                                    <button
                                        onClick={() => handlePurchase(product)}
                                        className="w-full py-3.5 rounded-xl bg-gradient-to-r from-white/10 to-white/5 hover:from-amber-500 hover:to-orange-600 text-white font-bold flex items-center justify-center gap-2 transition-all shadow-lg border border-white/5 group-hover:border-transparent group-hover:shadow-amber-500/25 relative overflow-hidden"
                                    >
                                        <div className="absolute inset-0 bg-white/20 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                                        <span className="relative z-10">{product.priceKrw.toLocaleString()}원</span>
                                    </button>
                                </div>
                            </motion.div>
                        ))}

                        {/* 4th Slot : Ticker Decoration */}
                        <motion.div
                            initial={{ opacity: 0, scale: 0.9 }}
                            animate={{ opacity: 1, scale: 1 }}
                            transition={{ delay: 0.4, type: "spring", stiffness: 100 }}
                            className="relative h-full flex items-end justify-center pointer-events-none"
                        >
                            {/* Speech Bubble */}
                            <motion.div
                                initial={{ opacity: 0, y: 10, scale: 0.8 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                transition={{ delay: 0.8, type: "spring", stiffness: 200, damping: 10 }}
                                className="absolute top-[15%] right-[5%] bg-[#1a1a20]/90 backdrop-blur-sm text-amber-100 px-5 py-2.5 rounded-2xl rounded-bl-none shadow-[0_4px_20px_rgba(0,0,0,0.3)] border border-amber-500/30 z-50 whitespace-nowrap"
                            >
                                <div className="flex items-center gap-2">
                                    <Sparkles size={14} className="text-amber-400 fill-amber-400 animate-pulse" />
                                    <span className="text-sm font-bold font-['GmarketSansMedium'] tracking-wide">헉, 이건 사야해!</span>
                                </div>
                                {/* Bubble Tail */}
                                <div className="absolute -bottom-1.5 left-5 w-3 h-3 bg-[#1a1a20] border-b border-r border-amber-500/30 transform rotate-45" />
                            </motion.div>

                            <img
                                src={TickerLoading2}
                                alt="Ticker Decoration"
                                className="w-full max-w-[200px] lg:max-w-full object-contain mb-[-10%] drop-shadow-[0_10px_20px_rgba(0,0,0,0.5)] opacity-90"
                            />
                        </motion.div>
                    </div>
                )}
            </div>

            {/* Ad Reward Section - Premium UI */}
            <div className="relative z-10 max-w-6xl mx-auto w-full">
                <div className="bg-gradient-to-b from-white/5 to-transparent border border-white/5 rounded-3xl p-8 md:p-10 backdrop-blur-md relative overflow-hidden">
                    {/* Decorative Background */}
                    <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-gradient-to-bl from-indigo-500/10 to-transparent blur-[80px] rounded-full pointer-events-none -translate-y-1/2 translate-x-1/2" />

                    <div className="relative z-10 flex flex-col md:flex-row md:items-end justify-between gap-6 mb-8 border-b border-white/5 pb-6">
                        <div>
                            <div className="flex items-center gap-2 text-indigo-300 mb-2">
                                <Trophy size={18} />
                                <span className="text-sm font-bold tracking-wider uppercase">Free Rewards</span>
                                {/* Beta Badge moved here */}
                                <div className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 backdrop-blur-md ml-2">
                                    <Hammer size={10} className="text-indigo-400" />
                                    <span className="text-indigo-300 text-[9px] font-bold tracking-wider">BETA</span>
                                </div>
                            </div>
                            <h2 className="text-2xl font-bold text-white mb-2">무료 FP 충전소</h2>
                            <p className="text-white/50 text-sm font-light">간단한 미션에 참여하고 FP를 무료로 받아가세요.</p>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {adMissions.map((mission) => {
                            const isCompleted = completedMissions[mission.id];
                            return (
                                <motion.button
                                    key={mission.id}
                                    whileHover={isCompleted ? {} : { scale: 1.01, paddingLeft: "1.5rem" }}
                                    whileTap={isCompleted ? {} : { scale: 0.99 }}
                                    onClick={() => handleAdWatch(mission)}
                                    disabled={isCompleted}
                                    className={`group relative w-full bg-[#1a1a20]/80 border rounded-2xl p-5 flex items-center justify-between transition-all duration-300 overflow-hidden
                                        ${isCompleted ? 'border-white/5 opacity-50 grayscale cursor-not-allowed' : 'border-white/10 hover:border-indigo-500/50'}`}
                                >
                                    {/* Hover Gradient Background */}
                                    {!isCompleted && (
                                        <div className="absolute inset-0 bg-gradient-to-r from-indigo-600/0 via-indigo-600/5 to-indigo-600/10 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                                    )}

                                    <div className="flex items-center gap-5 relative z-10">
                                        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-300 shadow-inner
                                            ${isCompleted ? 'bg-white/5 text-white/20' : 'bg-indigo-500/10 text-indigo-400 group-hover:bg-indigo-500 group-hover:text-white group-hover:shadow-indigo-500/50'}`}>
                                            {isCompleted ? <CheckCircle size={26} strokeWidth={1.5} /> : <mission.icon size={26} strokeWidth={1.5} />}
                                        </div>
                                        <div className="text-left">
                                            <h3 className={`text-lg font-bold transition-colors ${isCompleted ? 'text-white/40' : 'text-white group-hover:text-indigo-100'}`}>
                                                {mission.title}
                                                {isCompleted && <span className="ml-2 text-xs font-normal text-indigo-400/60">(내일 다시 참여 가능)</span>}
                                            </h3>
                                            <div className="flex items-center gap-2 mt-1">
                                                <span className={`text-xs px-2 py-0.5 rounded text-center min-w-[3rem] ${isCompleted ? 'bg-white/5 text-white/20' : 'text-indigo-200/60 bg-indigo-500/10'}`}>
                                                    {isCompleted ? '참여 완료' : mission.time}
                                                </span>
                                                <span className={`text-xs truncate max-w-[150px] md:max-w-none ${isCompleted ? 'text-white/20' : 'text-white/30'}`}>
                                                    {isCompleted ? '오늘의 보상을 이미 획득했습니다.' : mission.desc}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="relative z-10 pl-4 border-l border-white/5 ml-4">
                                        <div className="flex flex-col items-center justify-center min-w-[60px]">
                                            <span className={`text-[10px] uppercase tracking-widest mb-0.5 ${isCompleted ? 'text-white/10' : 'text-white/40'}`}>Reward</span>
                                            <div className={`flex items-center gap-1 font-bold text-xl transition-colors ${isCompleted ? 'text-white/20' : 'text-indigo-300 group-hover:text-white'}`}>
                                                <span>+{mission.reward}FP</span>
                                                <Coins size={16} fill="currentColor" className="opacity-80" />
                                            </div>
                                        </div>
                                    </div>
                                </motion.button>
                            );
                        })}
                    </div>
                </div>
            </div>

            {/* Alert Modal */}
            <Modal
                isOpen={alertModal.isOpen}
                onClose={handleCloseModal}
                title={alertModal.title}
                message={alertModal.message}
                type={alertModal.type}
            />

            {/* Payment History Modal */}
            <PaymentHistoryModal
                isOpen={showHistoryModal}
                onClose={() => setShowHistoryModal(false)}
            />
        </motion.div>
    );
};

export default ShopPage;

