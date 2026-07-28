package com.kidneystone.patient.service;

import org.springframework.stereotype.Component;

import java.time.Year;
import java.util.concurrent.atomic.AtomicInteger;

@Component
public class PatientCodeGenerator {

    private final AtomicInteger sequence = new AtomicInteger(1000);

    public String generate() {
        int year = Year.now().getValue() % 100; // last two digits
        int seq  = sequence.getAndIncrement();
        return String.format("PAT-%02d-%05d", year, seq);
    }
}
