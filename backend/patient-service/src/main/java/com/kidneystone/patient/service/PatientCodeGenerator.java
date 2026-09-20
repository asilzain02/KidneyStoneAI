package com.kidneystone.patient.service;

import org.springframework.stereotype.Component;

import java.time.Year;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.UUID;

@Component
public class PatientCodeGenerator {

    private final AtomicInteger sequence = new AtomicInteger(1000);

    public String generate() {
        int year = Year.now().getValue() % 100; // last two digits
        int seq  = sequence.getAndIncrement();
        String randomSuffix = UUID.randomUUID().toString().substring(0, 4).toUpperCase();
        return String.format("PAT-%02d-%05d-%s", year, seq, randomSuffix);
    }
}
