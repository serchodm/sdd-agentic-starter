#!/usr/bin/env python3
"""Validador Determinista de Tokens de Diseño y Anti-Deriva Estilística SDD.

Verifica la coherencia bidireccional entre docs/design-system/design-tokens.json
y docs/design-system/MASTER.md, y audita los ficheros fuente frontend en busca de
literales hardcodeados donde existan tokens normativos.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

EXCLUDED_DIR_NAMES = frozenset({"node_modules", ".git", "dist", "build", "vendor", "__pycache__"})
FRONTEND_EXTENSIONS = frozenset({".css", ".scss", ".sass", ".less", ".tsx", ".jsx", ".vue", ".html", ".svelte"})
EXCLUDED_EXTENSIONS = frozenset({
    ".json", ".md", ".ts", ".tsx", ".js", ".jsx", ".css", ".scss", ".sass",
    ".less", ".html", ".svg", ".png", ".jpg", ".jpeg", ".py", ".lock", ".yml",
    ".yaml", ".map", ".txt", ".csv",
})
METADATA_KEYS = frozenset({
    "$schema", "$version", "version", "$description", "description",
    "$type", "type", "$extensions", "extensions", "meta",
})

HEX_COLOR_REGEX = re.compile(
    r"(?<![a-zA-Z0-9_-])#([0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{4}|[0-9a-fA-F]{3})(?![0-9a-fA-F])"
)
HEX_VALUE_REGEX = re.compile(r"^#([0-9a-fA-F]{3,4}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")
TOKEN_IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z][a-zA-Z0-9_-]*(?:\.[a-zA-Z0-9_-]+)+$")


class ValidationSeverity(str, Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class TokenViolation:
    severity: ValidationSeverity
    category: str
    message: str
    file_path: str = ""
    line_number: int = 0
    token_name: str = ""
    literal_value: str = ""


@dataclass
class TokenValidationResult:
    is_valid: bool
    total_tokens_checked: int = 0
    total_sources_scanned: int = 0
    missing_in_master: list[str] = field(default_factory=list)
    missing_in_json: list[str] = field(default_factory=list)
    violations: list[TokenViolation] = field(default_factory=list)
    skipped_reason: str | None = None


def normalize_hex(val: str) -> str | None:
    """Normaliza un color hexadecimal a minúsculas y expande variantes cortas."""
    if not isinstance(val, str):
        return None
    val = val.strip()
    m = HEX_VALUE_REGEX.match(val)
    if not m:
        return None
    hex_digits = m.group(1).lower()
    if len(hex_digits) in (3, 4):
        hex_digits = "".join(c * 2 for c in hex_digits)
    return f"#{hex_digits}"


def is_valid_token_name(tok: str) -> bool:
    """Verifica si un identificador tiene formato canónico de token de diseño."""
    if not TOKEN_IDENTIFIER_REGEX.match(tok):
        return False
    low = tok.lower()
    if any(low.endswith(ext) for ext in EXCLUDED_EXTENSIONS):
        return False
    parts = tok.split(".")
    if all(p.isdigit() for p in parts):
        return False
    if parts[0].lower().startswith("v") and all(p.isdigit() for p in [parts[0][1:]] + parts[1:] if p):
        return False
    return True


def flatten_tokens(data: Any, prefix: str = "") -> dict[str, Any]:
    """Aplana un árbol JSON DTCG en un diccionario con claves dot-notation."""
    tokens: dict[str, Any] = {}
    if not isinstance(data, dict):
        return tokens

    for key, value in data.items():
        if not prefix and (key.startswith("$") or key in ("version", "meta")):
            continue
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            if "value" in value or "$value" in value:
                raw_val = value.get("value") if "value" in value else value.get("$value")
                if isinstance(raw_val, str):
                    norm = normalize_hex(raw_val)
                    tokens[path] = norm if norm is not None else raw_val.strip()
                else:
                    tokens[path] = raw_val
            else:
                tokens.update(flatten_tokens(value, prefix=path))
        elif isinstance(value, (str, int, float, bool)) and key not in METADATA_KEYS:
            if isinstance(value, str):
                norm = normalize_hex(value)
                tokens[path] = norm if norm is not None else value.strip()
            else:
                tokens[path] = value
    return tokens


def extract_master_tokens(master_text: str) -> set[str]:
    """Extrae todos los identificadores de tokens citados en MASTER.md."""
    found: set[str] = set()
    text = master_text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            text = parts[2]

    # 1. Bloques de código inline (`...`)
    for match in re.finditer(r"`([a-zA-Z][a-zA-Z0-9_.-]+)`", text):
        tok = match.group(1).strip()
        if is_valid_token_name(tok):
            found.add(tok)

    # 2. Celdas de tablas Markdown y listas con viñetas
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("|") and line.endswith("|"):
            if re.match(r"^\|[\s\-:|]+\|$", line):
                continue
            for cell in line.split("|")[1:-1]:
                cell_clean = cell.strip("`").strip()
                if is_valid_token_name(cell_clean):
                    found.add(cell_clean)
        list_match = re.match(r"^[-*]\s+`?([a-zA-Z][a-zA-Z0-9_.-]+)`?[:\s-]", line)
        if list_match:
            tok = list_match.group(1).strip()
            if is_valid_token_name(tok):
                found.add(tok)
    return found


def build_color_token_map(flattened_tokens: dict[str, Any]) -> dict[str, list[str]]:
    """Construye un índice inverso de valores hexadecimales normalizados a tokens."""
    color_map: dict[str, list[str]] = {}
    for tok_name, val in flattened_tokens.items():
        if isinstance(val, str):
            norm = normalize_hex(val)
            if norm:
                color_map.setdefault(norm, []).append(tok_name)
    return color_map


def is_excluded_path(path: Path) -> bool:
    """Determina si un fichero o directorio debe ignorarse durante el escaneo."""
    if set(path.parts) & EXCLUDED_DIR_NAMES:
        return True
    path_parts = list(path.parts)
    for i in range(len(path_parts) - 1):
        if path_parts[i] == "tests" and path_parts[i + 1] == "fixtures":
            return True
    return False


def scan_file_for_literals(
    file_path: Path, color_map: dict[str, list[str]], strict: bool = False
) -> list[TokenViolation]:
    """Escanea un fichero individual detectando literales de color hardcodeados."""
    violations: list[TokenViolation] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except OSError as exc:
        violations.append(TokenViolation(
            severity=ValidationSeverity.ERROR, category="sources:read-error",
            message=f"No se pudo leer el fichero {file_path}: {exc}",
            file_path=str(file_path).replace("\\", "/"),
        ))
        return violations

    try:
        display_path = str(file_path.relative_to(Path.cwd())).replace("\\", "/")
    except ValueError:
        display_path = str(file_path).replace("\\", "/")

    for line_no, raw_line in enumerate(lines, start=1):
        line = raw_line.rstrip("\r\n")
        if "/* sdd-token-ignore */" in line or "// sdd-token-ignore" in line:
            continue

        seen_in_line: set[str] = set()
        for match in HEX_COLOR_REGEX.finditer(line):
            raw_hex = match.group(0)
            if raw_hex in seen_in_line:
                continue
            seen_in_line.add(raw_hex)

            norm_hex = normalize_hex(raw_hex)
            if norm_hex and norm_hex in color_map:
                tokens = color_map[norm_hex]
                token_name = tokens[0]
                violations.append(TokenViolation(
                    severity=ValidationSeverity.ERROR, category="literal:forbidden",
                    message=f"Literal '{raw_hex}' detectado en {display_path}:{line_no}; utilice el token '{token_name}'",
                    file_path=display_path, line_number=line_no, token_name=token_name, literal_value=raw_hex,
                ))
            elif strict:
                style_keywords = ("color", "background", "border", "fill", "stroke", "style", "shadow")
                if any(k in line.lower() for k in style_keywords):
                    violations.append(TokenViolation(
                        severity=ValidationSeverity.WARNING, category="literal:unmapped-color",
                        message=f"Literal '{raw_hex}' detectado en {display_path}:{line_no}; no coincide con ningún token de diseño registrado",
                        file_path=display_path, line_number=line_no, token_name="", literal_value=raw_hex,
                    ))
    return violations


def scan_sources_for_literals(
    sources_dir: Path | str, color_map: dict[str, list[str]], strict: bool = False
) -> tuple[int, list[TokenViolation]]:
    """Escanea recursivamente el directorio de código fuente frontend."""
    base_dir = Path(sources_dir)
    if not base_dir.is_dir():
        return 0, []

    total_scanned = 0
    violations: list[TokenViolation] = []
    for file_path in sorted(base_dir.rglob("*")):
        if not file_path.is_file() or file_path.suffix.lower() not in FRONTEND_EXTENSIONS or is_excluded_path(file_path):
            continue
        total_scanned += 1
        violations.extend(scan_file_for_literals(file_path, color_map, strict=strict))
    return total_scanned, violations


def validate_design_tokens(
    tokens_path: Path | str = "docs/design-system/design-tokens.json",
    master_path: Path | str = "docs/design-system/MASTER.md",
    check_sources: Path | str | None = None,
    allow_missing: bool = False,
    strict: bool = False,
) -> TokenValidationResult:
    """Ejecuta la suite completa de validación estática de tokens de diseño."""
    tokens_p = Path(tokens_path)
    master_p = Path(master_path)
    violations: list[TokenViolation] = []
    missing_in_master: list[str] = []
    missing_in_json: list[str] = []

    if not tokens_p.is_file():
        if allow_missing:
            return TokenValidationResult(
                is_valid=True,
                skipped_reason=f"Design tokens file not found at '{tokens_p}' (--allow-missing enabled)",
            )
        violations.append(TokenViolation(
            severity=ValidationSeverity.ERROR, category="file:not-found",
            message=f"Design tokens file not found: {tokens_p}",
            file_path=str(tokens_p).replace("\\", "/"),
        ))
        return TokenValidationResult(is_valid=False, violations=violations)

    try:
        with open(tokens_p, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        violations.append(TokenViolation(
            severity=ValidationSeverity.ERROR, category="json:syntax-error",
            message=f"JSON inválido en {tokens_p}: {exc}", file_path=str(tokens_p).replace("\\", "/"),
        ))
        return TokenValidationResult(is_valid=False, violations=violations)
    except OSError as exc:
        violations.append(TokenViolation(
            severity=ValidationSeverity.ERROR, category="file:read-error",
            message=f"No se pudo leer {tokens_p}: {exc}", file_path=str(tokens_p).replace("\\", "/"),
        ))
        return TokenValidationResult(is_valid=False, violations=violations)

    if not isinstance(data, dict):
        violations.append(TokenViolation(
            severity=ValidationSeverity.ERROR, category="json:schema-error",
            message=f"La raíz de {tokens_p} debe ser un objeto JSON", file_path=str(tokens_p).replace("\\", "/"),
        ))
        return TokenValidationResult(is_valid=False, violations=violations)

    flattened = flatten_tokens(data)
    total_tokens = len(flattened)

    if not master_p.is_file():
        violations.append(TokenViolation(
            severity=ValidationSeverity.ERROR, category="master:not-found",
            message=f"Design system MASTER.md not found: {master_p}", file_path=str(master_p).replace("\\", "/"),
        ))
        missing_in_master = sorted(flattened.keys())
        for tok in missing_in_master:
            violations.append(TokenViolation(
                severity=ValidationSeverity.ERROR, category="drift:missing-in-master",
                message=f"Token '{tok}' definido en JSON ausente en MASTER.md", token_name=tok,
            ))
    else:
        try:
            with open(master_p, "r", encoding="utf-8") as f:
                master_text = f.read()
            master_tokens = extract_master_tokens(master_text)
        except OSError as exc:
            violations.append(TokenViolation(
                severity=ValidationSeverity.ERROR, category="master:read-error",
                message=f"No se pudo leer {master_p}: {exc}", file_path=str(master_p).replace("\\", "/"),
            ))
            master_tokens = set()

        json_token_keys = set(flattened.keys())
        missing_in_master = sorted(json_token_keys - master_tokens)
        missing_in_json = sorted(master_tokens - json_token_keys)

        for tok in missing_in_master:
            violations.append(TokenViolation(
                severity=ValidationSeverity.ERROR, category="drift:missing-in-master",
                message=f"Token '{tok}' definido en JSON ausente en MASTER.md", token_name=tok,
            ))
        for tok in missing_in_json:
            violations.append(TokenViolation(
                severity=ValidationSeverity.ERROR, category="drift:missing-in-json",
                message=f"Token '{tok}' referenciado en MASTER.md ausente en JSON", token_name=tok,
            ))

    total_sources = 0
    if check_sources is not None:
        sources_p = Path(check_sources)
        if not sources_p.is_dir():
            violations.append(TokenViolation(
                severity=ValidationSeverity.ERROR, category="sources:not-found",
                message=f"Directorio de fuentes frontend no encontrado: {sources_p}",
                file_path=str(sources_p).replace("\\", "/"),
            ))
        else:
            color_map = build_color_token_map(flattened)
            scanned_count, source_violations = scan_sources_for_literals(sources_p, color_map, strict=strict)
            total_sources = scanned_count
            violations.extend(source_violations)

    has_errors = any(v.severity == ValidationSeverity.ERROR for v in violations)
    has_warnings = any(v.severity == ValidationSeverity.WARNING for v in violations)
    is_valid = not has_errors and not (strict and has_warnings)

    return TokenValidationResult(
        is_valid=is_valid,
        total_tokens_checked=total_tokens,
        total_sources_scanned=total_sources,
        missing_in_master=missing_in_master,
        missing_in_json=missing_in_json,
        violations=violations,
        skipped_reason=None,
    )


def result_to_dict(result: TokenValidationResult) -> dict[str, Any]:
    """Convierte el resultado a un diccionario serializable en JSON."""
    return {
        "is_valid": result.is_valid,
        "total_tokens_checked": result.total_tokens_checked,
        "total_sources_scanned": result.total_sources_scanned,
        "missing_in_master": result.missing_in_master,
        "missing_in_json": result.missing_in_json,
        "violations": [
            {
                "severity": v.severity.value,
                "category": v.category,
                "message": v.message,
                "file_path": v.file_path,
                "line_number": v.line_number,
                "token_name": v.token_name,
                "literal_value": v.literal_value,
            }
            for v in result.violations
        ],
        "skipped_reason": result.skipped_reason,
    }


def format_text_report(result: TokenValidationResult) -> str:
    """Genera un informe en texto plano legible para terminal o CI."""
    if result.skipped_reason:
        return f"[SKIPPED] {result.skipped_reason}"

    status_tag = "[PASS]" if result.is_valid else "[FAIL]"
    lines = [
        f"{status_tag} Validación de Design Tokens",
        f"  • Total tokens verificados: {result.total_tokens_checked}",
        f"  • Ficheros frontend escaneados: {result.total_sources_scanned}",
    ]
    if result.missing_in_master:
        lines.append(f"  • Faltantes en MASTER.md ({len(result.missing_in_master)}):")
        lines.extend(f"    - {tok}" for tok in result.missing_in_master)
    if result.missing_in_json:
        lines.append(f"  • Faltantes en JSON ({len(result.missing_in_json)}):")
        lines.extend(f"    - {tok}" for tok in result.missing_in_json)
    if result.violations:
        lines.append(f"  • Violaciones detectadas ({len(result.violations)}):")
        for v in result.violations:
            loc = f" ({v.file_path}:{v.line_number})" if v.file_path else ""
            lines.append(f"    [{v.severity.value}] [{v.category}]{loc} {v.message}")
    elif result.is_valid:
        lines.append("  • Cero discrepancias estilísticas detectadas.")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(
        description="Validador Determinista de Tokens de Diseño y Anti-Deriva Estilística SDD.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--tokens", dest="tokens_path", default="docs/design-system/design-tokens.json",
        help="Ruta al archivo design-tokens.json (por defecto: docs/design-system/design-tokens.json).",
    )
    parser.add_argument(
        "--master", dest="master_path", default="docs/design-system/MASTER.md",
        help="Ruta al archivo MASTER.md (por defecto: docs/design-system/MASTER.md).",
    )
    parser.add_argument(
        "--check-sources", dest="sources_dir", metavar="DIR", default=None,
        help="Directorio de código frontend a escanear en busca de literales prohibidos.",
    )
    parser.add_argument(
        "--allow-missing", action="store_true",
        help="Si design-tokens.json no existe, finaliza con éxito (código 0) e informa skip.",
    )
    parser.add_argument(
        "--format", dest="output_format", choices=["text", "json"], default="text",
        help="Formato de salida de los resultados (por defecto: text).",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Trata advertencias como errores bloqueantes.",
    )

    args = parser.parse_args(argv)
    result = validate_design_tokens(
        tokens_path=args.tokens_path,
        master_path=args.master_path,
        check_sources=args.sources_dir,
        allow_missing=args.allow_missing,
        strict=args.strict,
    )

    if args.output_format == "json":
        print(json.dumps(result_to_dict(result), indent=2, ensure_ascii=False))
    else:
        print(format_text_report(result))

    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
