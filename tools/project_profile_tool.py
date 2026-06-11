"""MCP tools: project profile — per-model structuurconventies.

Het profiel maakt de query-tools convention-vrij: projects/<model>.json beschrijft
welke parameters de grouping, het ruimtetype en de programmalink dragen voor één
Revit-model. Geen profiel = fallback naar de KSS-conventie.

Zie FutureUpdates/project-profile-architecture.md en projects/README.md.
"""

import json
import re
from pathlib import Path

from mcp.server.fastmcp import Context

PROJECTS_DIR = Path(__file__).resolve().parent.parent / "projects"
RULESETS_DIR = Path(__file__).resolve().parent.parent / "rulesets"

DEFAULT_GROUPING_PARAMETER = "BEEL_C_TX_AppartementNummer"
DEFAULT_GROUPING_LABEL = "appartement"

_ALLOWED_PROGRAM_MODES = {"key_schedule", "external_json", "none"}


def known_rulesets():
    """Namen van beschikbare rulesets (bestanden in rulesets/, zonder README)."""
    if not RULESETS_DIR.exists():
        return set()
    return {p.stem for p in RULESETS_DIR.glob("*.md") if p.stem.lower() != "readme"}


# ---------------------------------------------------------------------------
# Helpers — ook gebruikt door andere tool-modules (profile-injectie)
# ---------------------------------------------------------------------------

def _safe_filename(model_name):
    name = re.sub(r'[<>:"/\\|?*]', "_", model_name or "").strip()
    return name or "unnamed_model"


def profile_path(model_name):
    return PROJECTS_DIR / (_safe_filename(model_name) + ".json")


def load_profile_for_model(model_name):
    """Profiel-dict voor een modelnaam, of None."""
    if not model_name:
        return None
    path = profile_path(model_name)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
    if PROJECTS_DIR.exists():
        for p in PROJECTS_DIR.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                continue
            if data.get("model_name") == model_name:
                return data
    return None


async def get_current_model_name(revit_get, ctx=None):
    """Bestandsnaam (doc.Title) van het open model — via de lichte /status/ route."""
    resp = await revit_get("/status/", ctx)
    if isinstance(resp, dict) and resp.get("document_title"):
        return resp["document_title"]
    # Fallback: zwaardere model_info route
    resp = await revit_get("/model_info/", ctx)
    if isinstance(resp, dict):
        info = resp.get("project_info") or {}
        return info.get("file_name") or info.get("name") or ""
    return ""


async def load_current_profile(revit_get, ctx=None):
    """(profile_dict_of_None, model_name) voor het open model."""
    model_name = await get_current_model_name(revit_get, ctx)
    return load_profile_for_model(model_name), model_name


def grouping_levels(profile):
    if not profile:
        return []
    return [lvl for lvl in (profile.get("grouping") or []) if isinstance(lvl, dict)]


def finest_grouping(profile):
    """(parameter, label) van het fijnste grouping-niveau met een directe parameter.

    derive-niveaus (prefix van een andere parameter) worden overgeslagen;
    geen profiel of geen direct niveau = KSS-fallback.
    """
    for lvl in reversed(grouping_levels(profile)):
        param = lvl.get("parameter")
        if param:
            return param, (lvl.get("label") or param)
    return DEFAULT_GROUPING_PARAMETER, DEFAULT_GROUPING_LABEL


async def get_grouping(revit_get, ctx=None):
    """Profile-aware grouping voor het open model: (parameter, label, profile)."""
    profile, _ = await load_current_profile(revit_get, ctx)
    param, label = finest_grouping(profile)
    return param, label, profile


def _validate_profile(profile):
    """Lijst van foutmeldingen (leeg = geldig)."""
    errors = []
    if not isinstance(profile, dict):
        return ["Profiel moet een JSON-object zijn."]

    grouping = profile.get("grouping")
    if grouping is not None:
        if not isinstance(grouping, list):
            errors.append("'grouping' moet een lijst van niveaus zijn (grof → fijn).")
        else:
            for i, lvl in enumerate(grouping):
                if not isinstance(lvl, dict):
                    errors.append("grouping[{}] moet een object zijn.".format(i))
                    continue
                if not lvl.get("parameter") and not lvl.get("derive"):
                    errors.append(
                        "grouping[{}] heeft 'parameter' of 'derive' nodig.".format(i))
                derive = lvl.get("derive")
                if derive is not None and not (
                        isinstance(derive, dict) and derive.get("from")):
                    errors.append("grouping[{}].derive heeft een 'from' nodig.".format(i))

    link = profile.get("program_link")
    if link is not None:
        mode = (link or {}).get("mode") if isinstance(link, dict) else None
        if mode not in _ALLOWED_PROGRAM_MODES:
            errors.append("program_link.mode moet één van {} zijn.".format(
                sorted(_ALLOWED_PROGRAM_MODES)))

    for key in ("room_classification", "family_keywords"):
        val = profile.get(key)
        if val is not None and not isinstance(val, dict):
            errors.append("'{}' moet een object zijn (categorie → keywords).".format(key))

    rulesets = profile.get("rulesets")
    if rulesets is not None:
        if not isinstance(rulesets, list) or not all(isinstance(r, str) for r in rulesets):
            errors.append("'rulesets' moet een lijst van namen zijn (bv. [\"codex-wonen\"]).")
        else:
            unknown = [r for r in rulesets if r not in known_rulesets()]
            if unknown:
                errors.append("Onbekende ruleset(s): {} — beschikbaar in rulesets/: {}".format(
                    ", ".join(unknown), ", ".join(sorted(known_rulesets())) or "geen"))

    return errors


def _summarize_profile(profile, model_name):
    lines = ["# Project profile — {}".format(profile.get("project_name") or model_name)]
    lines.append("Model: {}".format(profile.get("model_name") or model_name))

    levels = grouping_levels(profile)
    if levels:
        lines.append("")
        lines.append("## Grouping (grof → fijn)")
        for lvl in levels:
            if lvl.get("parameter"):
                lines.append("  - {}: parameter '{}'".format(
                    lvl.get("label") or "?", lvl["parameter"]))
            else:
                derive = lvl.get("derive") or {}
                lines.append("  - {}: afgeleid ({} van '{}')".format(
                    lvl.get("label") or "?", derive.get("rule") or "prefix",
                    derive.get("from") or "?"))
        param, label = finest_grouping(profile)
        lines.append("  → filter-as voor query-tools: '{}' ({})".format(param, label))
    else:
        lines.append("Geen grouping — fallback: '{}'".format(DEFAULT_GROUPING_PARAMETER))

    if profile.get("room_type_parameter"):
        lines.append("Ruimtetype-parameter: '{}'".format(profile["room_type_parameter"]))
    occupancy = profile.get("occupancy") or {}
    if occupancy.get("source") and occupancy["source"] != "none":
        lines.append("Occupancy: {} ({})".format(
            occupancy.get("source"), occupancy.get("scheme") or occupancy.get("parameter") or ""))
    link = profile.get("program_link") or {}
    mode = link.get("mode") or "none"
    if mode == "external_json":
        lines.append("Programma-link: external_json → programs/{}.json (join: {})".format(
            link.get("program") or "?", link.get("join_parameter") or "roomnaam"))
    else:
        lines.append("Programma-link: {}".format(mode))
    rulesets = profile.get("rulesets") or []
    if rulesets:
        lines.append("Rulesets: {} (zie rulesets/)".format(", ".join(rulesets)))
    if profile.get("room_classification"):
        lines.append("Classificatie: {} categorieën".format(len(profile["room_classification"])))
    if profile.get("notes"):
        lines.append("Notities: {}".format(profile["notes"]))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# MCP tools
# ---------------------------------------------------------------------------

def register_project_profile_tools(mcp, revit_get):

    @mcp.tool()
    async def get_project_profile(ctx: Context) -> str:
        """
        Haal het project profile op voor het momenteel geopende Revit-model.

        Het profiel beschrijft de structuurconventies van dit project: welke parameter
        de unit-grouping draagt (appartement / ruimtegroep / UnitID), het ruimtetype,
        occupancy en de programmalink. Alle profile-aware query-tools gebruiken dit
        intern — roep deze tool aan bij sessiestart om de conventies te kennen.

        Geen profiel gevonden = de tools vallen terug op de KSS-conventie
        (BEEL_C_TX_AppartementNummer). Start dan het project-setup interview
        (zie de revit-query skill) en sla het resultaat op met save_project_profile.
        """
        profile, model_name = await load_current_profile(revit_get, ctx)
        if not model_name:
            return "Kon de modelnaam niet ophalen — is Revit verbonden?"
        if profile is None:
            return (
                "Geen project profile gevonden voor model '{}'.\n"
                "Query-tools vallen terug op de KSS-conventie ('{}').\n"
                "Run het project-setup interview en sla op met save_project_profile."
            ).format(model_name, DEFAULT_GROUPING_PARAMETER)

        summary = _summarize_profile(profile, model_name)
        raw = json.dumps(profile, indent=2, ensure_ascii=False)
        return "{}\n\n```json\n{}\n```".format(summary, raw)

    @mcp.tool()
    async def save_project_profile(profile_json: str, ctx: Context = None) -> str:
        """
        Valideer en bewaar een project profile voor het momenteel geopende Revit-model.

        Schrijft projects/<modelnaam>.json; model_name wordt automatisch gezet op de
        naam van het open model. Bestaand profiel wordt overschreven.

        Het profiel komt uit het project-setup interview (zie de revit-query skill):
        eerst discovery (get_model_structure + discover_room_parameters), dan per
        bevinding één bevestigingsvraag aan de gebruiker, dan deze tool.

        Parameters:
          profile_json: het volledige profiel als JSON-string. Schema:
            {
              "project_name": "...",
              "grouping": [  // hiërarchisch, grof → fijn; laatste 'parameter' = filter-as
                {"derive": {"from": "<param>", "rule": "prefix"}, "label": "gebouw"},
                {"parameter": "<param>", "label": "unit"}
              ],
              "room_type_parameter": null,     // of parameternaam met genormaliseerd type
              "occupancy": {"source": "area_scheme|room_parameter|none", ...},
              "program_link": {"mode": "key_schedule|external_json|none"},
              "room_classification": {"badkamer": ["bad", "douche"], ...},
              "family_keywords": {"toilet": ["toilet"], ...}
            }
          Parameternamen letterlijk overnemen zoals gedumpt — nooit reconstrueren.
        """
        try:
            profile = json.loads(profile_json)
        except Exception as e:
            return "Ongeldige JSON: {}".format(e)

        errors = _validate_profile(profile)
        if errors:
            return "Profiel niet opgeslagen — validatiefouten:\n  - " + "\n  - ".join(errors)

        model_name = await get_current_model_name(revit_get, ctx)
        if not model_name:
            return "Kon de modelnaam niet ophalen — is Revit verbonden?"

        profile["model_name"] = model_name
        PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
        path = profile_path(model_name)
        path.write_text(
            json.dumps(profile, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        param, label = finest_grouping(profile)
        return (
            "Profiel opgeslagen: {}\n"
            "Filter-as voor query-tools: '{}' ({}).\n\n{}"
        ).format(path.name, param, label, _summarize_profile(profile, model_name))
