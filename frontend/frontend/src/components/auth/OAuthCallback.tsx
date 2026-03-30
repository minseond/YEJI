import { useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';

const OAuthCallback = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();

    useEffect(() => {
        const accessToken = searchParams.get('accessToken');
        const refreshToken = searchParams.get('refreshToken');

        if (accessToken) {

            // 1. Store Tokens
            localStorage.setItem('accessToken', accessToken);
            if (refreshToken) localStorage.setItem('refreshToken', refreshToken);

            // 2. Redirect to Home (replace to prevent back tracking to callback url)
            navigate('/home', { replace: true });
        } else {
            // Handle Failure
            console.error("OAuth Failed: No tokens found");
            alert('로그인에 실패했습니다. 다시 시도해주세요.');
            navigate('/login', { replace: true });
        }
    }, [navigate, searchParams]);

    return (
        <div className="flex min-h-screen w-full items-center justify-center bg-black text-white">
            <div className="flex flex-col items-center gap-4">
                <div className="w-12 h-12 border-4 border-indigo-500/30 border-t-indigo-500 rounded-full animate-spin" />
                <p className="text-white/60 text-sm font-['Pretendard']">로그인 처리 중입니다...</p>
            </div>
        </div>
    );
};

export default OAuthCallback;
