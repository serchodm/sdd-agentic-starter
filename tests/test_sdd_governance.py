#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas unitarias de Gobernanza Git, CLI Universal, Instintos y Hooks SDD.
"""

import io
import json
import os
import pathlib
import sys
import tempfile
import unittest

ROOT_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from scripts.sdd_cli import DISPATCH_MAP
from scripts.sdd_git import load_git_governance, resolve_branch_name
from scripts.sdd_hooks import CONFLICT_PATTERNS, SECRET_PATTERNS, validate_pre_push
from scripts.sdd_instincts import (
    calculate_decayed_confidence,
    cosine_similarity,
    get_repo_root,
    load_instincts,
    save_instincts,
)


class TestSDDGovernance(unittest.TestCase):
    """Pruebas del arnés de gobernanza y CLI."""

    def test_sdd_cli_dispatch_map_integrity(self):
        """Verifica que todos los comandos mapeados apunten a ficheros válidos."""
        for cmd, path in DISPATCH_MAP.items():
            self.assertTrue(path.exists(), f"El script para el comando '{cmd}' debe existir en {path}")

    def test_sdd_git_branch_resolution(self):
        """Verifica la resolución determinista de prefijos y ramas SDD."""
        gov = load_git_governance()
        self.assertEqual(resolve_branch_name("FEAT-001", gov), "feat/FEAT-001")
        self.assertEqual(resolve_branch_name("CR-002", gov), "change/CR-002")
        self.assertEqual(resolve_branch_name("BUG-003", gov), "fix/BUG-003")
        self.assertEqual(resolve_branch_name("BUG-999", gov, is_hotfix=True), "hotfix/BUG-999")
        self.assertEqual(resolve_branch_name("1.0.0", gov, is_release=True), "release/v1.0.0")

    def test_sdd_hooks_conflict_and_secret_detection(self):
        """Verifica que los patrones de hooks detecten marcadores de conflicto y secretos."""
        conflict_sample = "line 1\n<<<<<<< HEAD\nline 2\n=======\nline 3\n>>>>>>> branch\n"
        self.assertTrue(any(p.search(conflict_sample) for p in CONFLICT_PATTERNS))

        clean_sample = "def hello():\n    return 'clean code'\n"
        self.assertFalse(any(p.search(clean_sample) for p in CONFLICT_PATTERNS))

        # Sample con token simulado generado dinámicamente para no disparar el escaneo estático
        prefix = "gh" + "p_"
        token_sample = f"export GITHUB_TOKEN={prefix}{'0123456789abcdefghijklmnopqrstuvwxyz'}\n"
        self.assertTrue(any(p.search(token_sample) for p, _ in SECRET_PATTERNS))

    def test_sdd_hooks_pre_push_main_guard(self):
        """Verifica que el hook pre-push bloquee intentos de push directo a main."""
        push_input = "refs/heads/main 1111 refs/heads/main 2222\n"
        old_stdin = sys.stdin
        try:
            sys.stdin = io.StringIO(push_input)
            ret = validate_pre_push([])
            self.assertEqual(ret, 1, "Debe rechazar el push hacia refs/heads/main")
        finally:
            sys.stdin = old_stdin

    def test_sdd_instincts_store(self):
        """Verifica que la persistencia y carga de instintos mantenga integridad."""
        instincts = load_instincts()
        self.assertIsInstance(instincts, list)
        self.assertGreaterEqual(len(instincts), 4, "Debe contener al menos los 4 instintos semilla")

        # Verificar que los instintos clave estén presentes
        ids = [i.get("id") for i in instincts]
        self.assertIn("inst-branch-sync-main-lock", ids)
        self.assertIn("inst-win-py-alias", ids)
        self.assertIn("inst-anti-rubber-stamp", ids)
        self.assertIn("inst-worktree-isolation", ids)

    def test_sdd_instincts_semantic_similarity(self):
        """Verifica la similitud coseno semántica para deduplicación (MemGPT pattern)."""
        t1 = "Al ejecutar scripts de Python en Windows con alias de Microsoft Store"
        t2 = "Al ejecutar comandos de Python en Windows con el alias de Microsoft Store"
        t3 = "Al configurar un bucket de Amazon S3 en produccion"

        sim_near = cosine_similarity(t1, t2)
        sim_diff = cosine_similarity(t1, t3)

        self.assertGreaterEqual(sim_near, 0.70, "Textos análogos deben tener alta similitud")
        self.assertLess(sim_diff, 0.25, "Textos dispares deben tener muy baja similitud")

    def test_sdd_instincts_temporal_decay(self):
        """Verifica el decaimiento temporal de confianza según vida media (half-life)."""
        fresh_instinct = {
            "confidence": 0.90,
            "last_reinforced": "2026-11-09T00:00:00+00:00",
        }
        # Un instinto reciente no debe decaer significativamente
        fresh_conf = calculate_decayed_confidence(fresh_instinct, half_life_days=90.0)
        self.assertAlmostEqual(fresh_conf, 0.90, delta=0.05)

        # Un instinto de hace 180 días con half-life 90 debe decaer a aprox 0.90 * 0.25 = 0.225 -> clamped a 0.30
        stale_instinct = {
            "confidence": 0.90,
            "last_reinforced": "2025-11-09T00:00:00+00:00",
        }
        stale_conf = calculate_decayed_confidence(stale_instinct, half_life_days=90.0)
        self.assertEqual(stale_conf, 0.30, "Instinto muy antiguo debe decaer al suelo mínimo de 0.30")

    def test_dynamic_repo_root_resolution(self):
        """Verifica que get_repo_root() resuelva el repositorio git dinámicamente."""
        root = get_repo_root()
        self.assertTrue(root.exists())
        self.assertTrue((root / ".git").exists() or (root / "specs").exists())


if __name__ == "__main__":
    unittest.main()
