package br.com.suporte.servico_tecnicos.service;

import br.com.suporte.servico_tecnicos.dto.TecnicoRequest;
import br.com.suporte.servico_tecnicos.dto.TecnicoResponse;
import br.com.suporte.servico_tecnicos.entity.Tecnico;
import br.com.suporte.servico_tecnicos.repository.TecnicoRepository;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.web.server.ResponseStatusException;

import java.util.List;

@Service
public class TecnicoService {

    private static final Logger log =
        LoggerFactory.getLogger(TecnicoService.class);

    private final TecnicoRepository repository;

    public TecnicoService(TecnicoRepository repository) {
        this.repository = repository;
    }

    public TecnicoResponse cadastrar(TecnicoRequest request) {

        if (repository.existsByEmail(request.email())) {
            throw new ResponseStatusException(
                HttpStatus.CONFLICT,
                "Já existe um técnico cadastrado com esse e-mail."
            );
        }

        Tecnico tecnico = new Tecnico();

        tecnico.setNome(request.nome());
        tecnico.setEmail(request.email());
        tecnico.setEspecialidade(request.especialidade());

        return TecnicoResponse.from(repository.save(tecnico));
    }

    public List<TecnicoResponse> listar() {

        return repository.findByAtivoTrue()
            .stream()
            .map(TecnicoResponse::from)
            .toList();
    }

    public TecnicoResponse buscarPorId(Long id) {

        Tecnico tecnico = buscarEntidade(id);

        return TecnicoResponse.from(tecnico);
    }

    public TecnicoResponse atualizar(Long id, TecnicoRequest request) {

        Tecnico tecnico = buscarEntidade(id);

        if (repository.existsByEmailAndIdNot(request.email(), id)) {
            throw new ResponseStatusException(
                HttpStatus.CONFLICT,
                "Esse e-mail já está sendo utilizado por outro técnico."
            );
        }

        tecnico.setNome(request.nome());
        tecnico.setEmail(request.email());
        tecnico.setEspecialidade(request.especialidade());

        return TecnicoResponse.from(repository.save(tecnico));
    }

    public void desativar(Long id) {

        Tecnico tecnico = buscarEntidade(id);

        tecnico.setAtivo(false);
        tecnico.setDisponivel(false);

        repository.save(tecnico);
    }

    public List<TecnicoResponse> listarDisponiveis() {

        return repository.findByDisponivelTrueAndAtivoTrue()
            .stream()
            .map(TecnicoResponse::from)
            .toList();
    }

    public void alterarDisponibilidade(Long id, boolean disponivel) {

        repository.findById(id)
            .filter(Tecnico::isAtivo)
            .ifPresentOrElse(
                tecnico -> {
                    tecnico.setDisponivel(disponivel);
                    repository.save(tecnico);
                    log.info("Técnico {} agora está {}.", id,
                        disponivel ? "disponível" : "indisponível");
                },
                () -> log.warn(
                    "Técnico {} não encontrado ou inativo; evento ignorado.", id)
            );
    }

    private Tecnico buscarEntidade(Long id) {

        Tecnico tecnico = repository.findById(id)
            .orElseThrow(() -> new ResponseStatusException(
                HttpStatus.NOT_FOUND,
                "Técnico não encontrado."
            ));

        if (!tecnico.isAtivo()) {
            throw new ResponseStatusException(
                HttpStatus.NOT_FOUND,
                "Técnico não encontrado."
            );
        }

        return tecnico;
    }
}