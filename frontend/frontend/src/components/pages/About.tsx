import PageContainer from '../PageContainer';

const About = () => {
    return (
        <PageContainer>
            <h2 className="text-5xl font-['Nanum_Brush_Script'] mb-8 text-[#2d1b16]">이야기</h2>
            <div className="max-w-prose text-lg space-y-6 font-['Gowun_Batang'] leading-loose text-justify text-[#4e342e]">
                <p>
                    오래된 전설에 따르면, 동양의 신비로운 힘이 깃든 구슬이 세상을 비추고 있었다고 합니다.
                    우리는 그 전설을 현대의 기술로 재해석하여, 당신의 손끝에서 펼쳐지는 새로운 경험을 만들었습니다.
                </p>
                <p>
                    이곳은 과거와 현재, 그리고 미래가 공존하는 공간입니다.
                    스크롤을 내려 기록을 확인하고, 수정 구슬을 통해 당신의 운명을 점쳐보세요.
                </p>
                <div className="w-full flex justify-center py-8 opacity-50">
                    <div className="w-32 h-[1px] bg-[#8d6e63]"></div>
                </div>
                <p className="text-center italic opacity-80">
                    "모든 것은 조화 속에서 이루어진다."
                </p>
            </div>
        </PageContainer>
    );
};

export default About;
