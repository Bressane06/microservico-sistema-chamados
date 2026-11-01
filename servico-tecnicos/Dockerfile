
FROM eclipse-temurin:21-jdk AS build

WORKDIR /app

COPY .mvn .mvn
COPY mvnw pom.xml ./
COPY src ./src

RUN chmod +x mvnw && ./mvnw -DskipTests package

FROM eclipse-temurin:21-jre

WORKDIR /app

# Baixa o agente Java do OpenTelemetry.
ADD https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v2.24.0/opentelemetry-javaagent.jar /app/opentelemetry-javaagent.jar

COPY --from=build /app/target/*.jar app.jar

EXPOSE 8081

ENTRYPOINT ["java", "-javaagent:/app/opentelemetry-javaagent.jar", "-jar", "app.jar"]
