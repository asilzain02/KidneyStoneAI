# ──────────────────────────────────────────────────────────────
# Dockerfile — KidneyStoneAI: report-service
# Multi-stage build: compile with Maven, run with JRE only.
# ──────────────────────────────────────────────────────────────

# ── Stage 1: Build ─────────────────────────────────────────────
FROM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /build

# Copy parent POM first for layer caching
COPY ../../pom.xml /parent-pom.xml
COPY pom.xml .
RUN --mount=type=cache,target=/root/.m2 \
    mvn dependency:go-offline -q || true

COPY src ./src
RUN mvn clean package -DskipTests -q

# ── Stage 2: Runtime ───────────────────────────────────────────
FROM eclipse-temurin:21-jre-alpine AS runtime
WORKDIR /app

# Security: run as non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

COPY --from=builder /build/target/*.jar app.jar

EXPOSE 8087

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD wget -qO- http://localhost:8087/actuator/health || exit 1

ENTRYPOINT ["java", "-jar", "app.jar", "--spring.profiles.active=docker"]
