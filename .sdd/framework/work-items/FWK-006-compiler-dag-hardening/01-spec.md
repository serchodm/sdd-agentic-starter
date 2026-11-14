# Spec Funcional: Compilador de Ownership, Generador Transaccional y Motor DAG (`FWK-006`)

- **ID:** `FWK-006-compiler-dag-hardening`
- **RFC:** [`RFC-003`](../../rfcs/RFC-003-audit-remediation-and-hardening.md) (`Aceptado`)
- **Gate 1 Sign-off:** `[x] Gate 1 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Requisitos (EARS)
- `RF-601` (`AUD-001`): `sdd:ownership-map` en `specs/STACK.md` / `00-stack.template.md` compilará zonas, agentes, reglas `forbid_imports` y validará solapamientos/zonas huérfanas con error fail-closed y enforcement AST en `verify_architecture_boundaries.py`.
- `RF-602` (`AUD-002`, `AUD-013`, `AUD-004`): `materialize_squad()` será transaccional (backup+rollback en fallo y `os.replace` atómico de `squad.lock.json`), incluirá `core_agents` en hash/verificación, detectará huérfanos (`--strict-agents`), gestionará drenaje/reasignación explícita de inboxes, ordenará colecciones determinísticamente y separará `timestamp` del hash de configuración.
- `RF-603` (`AUD-003`, `AUD-012`, `AUD-025`): `sdd_pack_registry.py` ignorará marcadores dentro de comentarios HTML y bloques vallados, validará compatibilidad `PackManifest.targets` vs `preset` tanto para `STACK.md` como para CLI `--packs`, y admitirá booleanos YAML sin sensibilidad a mayúsculas.
- `RF-604` (`AUD-005`, `AUD-014`): Los builders resolverán sus comandos DoD desde `STACK.md §2.5` (`verification_commands`) prohibiendo cadenas genéricas multi-stack, y `sdd_agent_generator.py --verify` comprobará en solo-lectura la coherencia disco <-> `squad.lock.json`.
- `RF-605` (`AUD-015`): Nuevo `scripts/sdd_dag.py` validará orden topológico y ausencia de ciclos en `03-tasks.md` integrado en `sdd_healthcheck.py`, además de gestionar transiciones de estado en `.agent-inbox/`.
