# Tech Spec: Concurrencia Multi-Worktree en `sdd_git` (`FWK-008`)

- **ID:** `FWK-008-git-concurrency`
- **Gate 2 Sign-off:** `[x] Gate 2 Approved (Pre-authorized by PO on 2026-11-14T16:05:46+01:00)`

## Arquitectura Modular (`<= 500` líneas)
1. **`scripts/sdd_git_state.py`** (`<=450L`): gobernanza Git (`copy.deepcopy(DEFAULT_GOVERNANCE)`), resolución de rama, estado activo aislado por worktree (`.agents/worktree_states/<wt_id>.json` / worktree-local `.agents/active_work_item.json` con lectura retrocompatible) y sincronización determinista de `.agents/ACTIVE_STATE.md`.
2. **`scripts/sdd_git_worktree.py`** (`<=450L`): `WorktreeManager` con reserva atómica de puertos (escaneo de puertos asignados + bind-check loopback real), detección dinámica de `default_base_branch` / `origin` remote y preservación del bloqueo `is_relative_to(worktrees_root)` de `FWK-005`.
3. **`scripts/sdd_git.py`** (`<=450L`): punto de entrada CLI y re-export de API pública compatible (`load_git_governance`, `resolve_branch_name`, `WorktreeManager`, etc.).
4. **Tests:** actualizar `tests/test_sdd_governance.py` y crear `tests/test_sdd_git_concurrency.py` (`<=500L`).
