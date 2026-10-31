package br.com.suporte.servico_tecnicos.repository;

import br.com.suporte.servico_tecnicos.entity.Tecnico;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface TecnicoRepository extends JpaRepository<Tecnico, Long> {

    List<Tecnico> findByAtivoTrue();

    List<Tecnico> findByDisponivelTrueAndAtivoTrue();

    boolean existsByEmail(String email);

    boolean existsByEmailAndIdNot(String email, Long id);
}