package br.com.suporte.servico_tecnicos.controller;

import br.com.suporte.servico_tecnicos.dto.TecnicoRequest;
import br.com.suporte.servico_tecnicos.dto.TecnicoResponse;
import br.com.suporte.servico_tecnicos.service.TecnicoService;

import jakarta.validation.Valid;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/tecnicos")
public class TecnicoController {

    private final TecnicoService service;

    public TecnicoController(TecnicoService service) {
        this.service = service;
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public TecnicoResponse cadastrar(
        @Valid @RequestBody TecnicoRequest request
    ) {
        return service.cadastrar(request);
    }

    @GetMapping
    public List<TecnicoResponse> listar() {
        return service.listar();
    }

    @GetMapping("/{id}")
    public TecnicoResponse buscarPorId(@PathVariable Long id) {
        return service.buscarPorId(id);
    }

    @PutMapping("/{id}")
    public TecnicoResponse atualizar(
        @PathVariable Long id,
        @Valid @RequestBody TecnicoRequest request
    ) {
        return service.atualizar(id, request);
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void desativar(@PathVariable Long id) {
        service.desativar(id);
    }

    @GetMapping("/disponiveis")
    public List<TecnicoResponse> listarDisponiveis() {
        return service.listarDisponiveis();
    }
}