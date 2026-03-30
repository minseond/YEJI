import instance from './axios';

// Interfaces for Shop & Payment
export interface Product {
    productId: number;
    name: string;
    priceKrw: number;
    fpAmount: number;
    isActive: boolean;
}

export interface PaymentCreateResponse {
    orderId: string;
    amount: number;
    orderName: string;
}

export interface PaymentVerifyRequest {
    paymentKey: string; // imp_uid
}

export interface PaymentHistory {
    orderId: string;
    status: string; // PENDING, PAID, CANCELLED, FAILED
    amount: number;
    productName: string;
    createdAt: string;
}

// 1. Fetch Product List
export const fetchProducts = async (): Promise<Product[]> => {
    const response = await instance.get<Product[]>('/shop/products');
    return response.data;
};

// 2. Create Payment (Order)
export const createPayment = async (productId: number): Promise<PaymentCreateResponse> => {
    const response = await instance.post<PaymentCreateResponse>('/shop/payments', { productId });
    return response.data;
};

// 3. Verify Payment
export const verifyPayment = async (orderId: string, paymentKey: string): Promise<void> => {
    await instance.post(`/shop/payments/${orderId}/verify`, { paymentKey });
};

// 4. Fetch Payment History
export const fetchPaymentHistory = async (): Promise<PaymentHistory[]> => {
    const response = await instance.get<PaymentHistory[]>('/shop/payments');
    return response.data;
};
