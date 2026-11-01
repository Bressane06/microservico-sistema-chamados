package br.com.suporte.servico_tecnicos.messaging;

import br.com.suporte.servico_tecnicos.service.TecnicoService;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.stereotype.Component;

/**
 * Consome os eventos publicados pelo serviço de chamados e mantém a
 * disponibilidade dos técnicos (consistência eventual entre os serviços).
 *
 * Os identificadores são lidos dos cabeçalhos AMQP; o corpo JSON da mensagem
 * traz o mesmo conteúdo, mais metadados, para outros consumidores.
 */
@Component
public class ChamadoEventosListener {

    private static final Logger log =
        LoggerFactory.getLogger(ChamadoEventosListener.class);

    private final TecnicoService service;

    public ChamadoEventosListener(TecnicoService service) {
        this.service = service;
    }

    @RabbitListener(queues = RabbitConfig.FILA_CHAMADO_ATRIBUIDO)
    public void aoAtribuirChamado(
        @Header("tecnico_id") Number tecnicoId,
        @Header(name = "tecnico_anterior_id", required = false) Number tecnicoAnteriorId
    ) {
        log.info("Evento chamado.atribuido: técnico {} (anterior: {}).",
            tecnicoId, tecnicoAnteriorId);

        // Novo técnico fica ocupado; o anterior (se houver) é liberado.
        service.alterarDisponibilidade(tecnicoId.longValue(), false);

        if (tecnicoAnteriorId != null) {
            service.alterarDisponibilidade(tecnicoAnteriorId.longValue(), true);
        }
    }

    @RabbitListener(queues = RabbitConfig.FILA_CHAMADO_ENCERRADO)
    public void aoEncerrarChamado(@Header("tecnico_id") Number tecnicoId) {
        log.info("Evento chamado.encerrado: liberando técnico {}.", tecnicoId);

        service.alterarDisponibilidade(tecnicoId.longValue(), true);
    }
}
