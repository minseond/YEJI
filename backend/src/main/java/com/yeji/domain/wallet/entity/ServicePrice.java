package com.yeji.domain.wallet.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Entity
@Getter
@Table(name = "service_prices")
@NoArgsConstructor
public class ServicePrice {

    @Id
    @Column(name = "service_code", length = 50)
    private String serviceCode;

    @Column(name = "service_name", nullable = false, length = 50)
    private String serviceName;

    @Column(name = "cost_fp", nullable = false)
    private Integer costFp;

    @Column(name = "description")
    private String description;

    public ServicePrice(String serviceCode, String serviceName, Integer costFp, String description) {
        this.serviceCode = serviceCode;
        this.serviceName = serviceName;
        this.costFp = costFp;
        this.description = description;
    }
}