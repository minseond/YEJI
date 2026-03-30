export const getHwatuImage = (cardCode: number): string => {
    if (cardCode < 0 || cardCode > 47) {
        console.warn(`Invalid hwatu cardCode: ${cardCode}. Using fallback.`);
        return '/assets/화투카드/hwatu_00.png'; // fallback to first card
    }

    // Handle shared images mapping as per user requirement (Pi cards sharing images)
    const sharedMapping: Record<number, number> = {
        7: 6,   // 2월 매조 피 -> 6번 이미지 공유
        15: 14, // 4월 흑싸리 피 -> 14번 이미지 공유
        19: 18, // 5월 난초 피 -> 18번 이미지 공유
        23: 22, // 6월 모란 피 -> 22번 이미지 공유
        27: 26, // 7월 홍싸리 피 -> 26번 이미지 공유
        31: 30, // 8월 공산 피 -> 30번 이미지 공유
        35: 34, // 9월 국진 피 -> 34번 이미지 공유
        39: 38, // 10월 단풍 피 -> 38번 이미지 공유
        43: 42  // 11월 오동 피 -> 42번 이미지 공유
    };

    const targetCode = sharedMapping[cardCode] !== undefined ? sharedMapping[cardCode] : cardCode;
    const paddedCode = String(targetCode).padStart(2, '0');

    return `/assets/hwatu/hwatu_${paddedCode}.png`;
};
