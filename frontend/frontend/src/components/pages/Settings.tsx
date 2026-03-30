import PageContainer from '../PageContainer';
import type { AppSettings } from '../../App';

interface SettingsProps {
    settings: AppSettings;
    onUpdate: (key: keyof AppSettings, value: any) => void;
}

const Settings = ({ settings, onUpdate }: SettingsProps) => {
    return (
        <PageContainer>
            <h2 className="text-5xl font-['Nanum_Brush_Script'] mb-12 text-[#2d1b16]">환경설정</h2>
            <div className="w-full max-w-md space-y-10 px-4">

                {/* Volume Control */}
                <div className="space-y-4">
                    <label className="flex justify-between text-lg font-['Gowun_Batang'] text-[#4e342e]">
                        <span>소리 크기</span>
                        <span className="font-bold">{settings.volume}%</span>
                    </label>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={settings.volume}
                        onChange={(e) => onUpdate('volume', parseInt(e.target.value))}
                        className="w-full h-1 bg-[#8d6e63]/30 rounded-lg appearance-none cursor-pointer accent-[#5d4037]"
                    />
                </div>

                {/* Effect Intensity */}
                <div className="space-y-4">
                    <label className="flex justify-between text-lg font-['Gowun_Batang'] text-[#4e342e]">
                        <span>효과 강도</span>
                        <span className="font-bold">
                            {settings.effectIntensity === 'low' ? '낮음' : settings.effectIntensity === 'medium' ? '중간' : '높음'}
                        </span>
                    </label>
                    <div className="flex gap-4">
                        {['low', 'medium', 'high'].map((level) => (
                            <button
                                key={level}
                                onClick={() => onUpdate('effectIntensity', level)}
                                className={`flex-1 py-2 rounded border border-[#8d6e63]/30 font-['Gowun_Batang'] transition-colors ${settings.effectIntensity === level ? 'bg-[#5d4037] text-[#e8e0c5]' : 'bg-transparent text-[#5d4037] hover:bg-[#8d6e63]/10'}`}
                            >
                                {level === 'low' ? '낮음' : level === 'medium' ? '중간' : '높음'}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Auto Advance Toggle (New) */}
                <div className="flex items-center justify-between pt-4 border-t border-[#8d6e63]/20">
                    <div className="flex flex-col">
                        <span className="text-lg font-['Gowun_Batang'] text-[#4e342e]">대화 자동 넘김</span>
                        <span className="text-sm text-[#4e342e]/60">활성화 시 일정 시간 후 다음 대화로 넘어갑니다.</span>
                    </div>
                    <div
                        className={`w-12 h-6 rounded-full relative cursor-pointer transition-colors ${settings.autoAdvance ? 'bg-[#5d4037]' : 'bg-[#8d6e63]/30'}`}
                        onClick={() => onUpdate('autoAdvance', !settings.autoAdvance)}
                    >
                        <div className={`absolute top-1 w-4 h-4 bg-[#e8e0c5] rounded-full shadow-sm transition-all ${settings.autoAdvance ? 'right-1' : 'left-1'}`}></div>
                    </div>
                </div>

                {/* Theme Toggle (Placeholder for now, maybe use for something else or keep simple) */}
                {/* <div className="flex items-center justify-between pt-4 border-t border-[#8d6e63]/20">
                    <span className="text-lg font-['Gowun_Batang'] text-[#4e342e]">야간 모드</span>
                    <div className="w-12 h-6 bg-[#3e2723] rounded-full relative cursor-pointer opacity-80">
                        <div className="absolute right-1 top-1 w-4 h-4 bg-[#e8e0c5] rounded-full shadow-sm"></div>
                    </div>
                </div> */}

            </div>
        </PageContainer>
    );
};

export default Settings;
