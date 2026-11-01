package br.com.suporte.servico_tecnicos.messaging;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.QueueBuilder;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Topologia do RabbitMQ consumida pelo serviço de técnicos.
 * O exchange é publicado pelo serviço de chamados (Python); declará-lo aqui
 * também garante que a fila possa ser criada em qualquer ordem de inicialização.
 */
@Configuration
public class RabbitConfig {

    public static final String EXCHANGE = "chamados.eventos";

    public static final String FILA_CHAMADO_ATRIBUIDO = "tecnicos.chamado-atribuido";
    public static final String FILA_CHAMADO_ENCERRADO = "tecnicos.chamado-encerrado";

    public static final String ROTA_ATRIBUIDO = "chamado.atribuido";
    public static final String ROTA_ENCERRADO = "chamado.encerrado";

    @Bean
    public TopicExchange chamadosExchange() {
        return new TopicExchange(EXCHANGE, true, false);
    }

    @Bean
    public Queue filaChamadoAtribuido() {
        return QueueBuilder.durable(FILA_CHAMADO_ATRIBUIDO).build();
    }

    @Bean
    public Queue filaChamadoEncerrado() {
        return QueueBuilder.durable(FILA_CHAMADO_ENCERRADO).build();
    }

    @Bean
    public Binding bindingChamadoAtribuido() {
        return BindingBuilder
            .bind(filaChamadoAtribuido())
            .to(chamadosExchange())
            .with(ROTA_ATRIBUIDO);
    }

    @Bean
    public Binding bindingChamadoEncerrado() {
        return BindingBuilder
            .bind(filaChamadoEncerrado())
            .to(chamadosExchange())
            .with(ROTA_ENCERRADO);
    }
}
