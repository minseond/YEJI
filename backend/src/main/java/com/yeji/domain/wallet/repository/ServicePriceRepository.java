package com.yeji.domain.wallet.repository;

import com.yeji.domain.wallet.entity.ServicePrice;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

//service_prices에 있는 service_code에 매칭되는 가격 차감
public interface ServicePriceRepository extends JpaRepository<ServicePrice, String> {
    Optional<ServicePrice> findByServiceCode(String serviceCode);
}
