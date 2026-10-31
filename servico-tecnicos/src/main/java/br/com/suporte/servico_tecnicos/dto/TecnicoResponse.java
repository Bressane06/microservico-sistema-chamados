package br.com.suporte.servico_tecnicos.dto;

import br.com.suporte.servico_tecnicos.entity.Tecnico;
import java.time.LocalDateTime;

public record TecnicoResponse(
    Long id,
    String nome,
    String email,
    String especialidade,
    boolean disponivel,
    boolean ativo,
    LocalDateTime criadoEm
) {

    public static TecnicoResponse from(Tecnico tecnico) {
        return new TecnicoResponse(
            tecnico.getId(),
            tecnico.getNome(),
            tecnico.getEmail(),
            tecnico.getEspecialidade(),
            tecnico.isDisponivel(),
            tecnico.isAtivo(),
            tecnico.getCriadoEm()
        );
    }
}