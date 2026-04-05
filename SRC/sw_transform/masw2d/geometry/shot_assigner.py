"""Intelligent shot-subarray assignment engine.

Reclassifies shots relative to each subarray independently (not the
main array), builds a compatibility matrix of every (shot, subarray)
pair, and selects assignments via configurable strategies and
constraints.  This enables in-line shots to be used as valid
forward/reverse sources for subarrays they are exterior to.
"""

from __future__ import annotations

import math
import warnings
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from .subarray import SubArrayDef
from .shot_classifier import ShotInfo, ShotType, classify_all_shots


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class AssignmentStrategy(Enum):
    """Strategy for selecting shot-subarray assignments."""

    MAX_COVERAGE = "max_coverage"
    BALANCED = "balanced"
    OFFSET_OPTIMIZED = "offset_optimized"
    BOTH_SIDES_PRIORITY = "both_sides_priority"
    MANUAL = "manual"
    EXTERIOR_ONLY = "exterior_only"


class RelationType(Enum):
    """Spatial relationship of a shot to a subarray."""

    EXTERIOR_LEFT = "exterior_left"
    EXTERIOR_RIGHT = "exterior_right"
    EDGE_LEFT = "edge_left"
    EDGE_RIGHT = "edge_right"
    INTERIOR_LEFT = "interior_left"
    INTERIOR_RIGHT = "interior_right"


# ---------------------------------------------------------------------------
# Data-classes
# ---------------------------------------------------------------------------

@dataclass
class AssignmentConstraints:
    """User-configurable limits applied during assignment generation.

    Attributes
    ----------
    max_offset : float or None
        Absolute maximum source offset in metres.  ``None`` = no limit.
    min_offset : float
        Absolute minimum source offset in metres.
    max_offset_ratio : float
        Maximum offset / subarray_length ratio.
    min_offset_ratio : float
        Minimum offset / subarray_length ratio.
    max_shots_per_subarray : int or None
        Hard cap on assignments per subarray.  ``None`` = unlimited.
    require_both_sides : bool
        When True, subarrays that cannot get at least one forward *and*
        one reverse shot are excluded entirely.
    min_shots_per_side : int
        Minimum number of shots required from each direction (forward and
        reverse) per subarray.  Only enforced when > 0.
    allow_interior_shots : bool
        If True, shots whose position falls *inside* a subarray span are
        still considered (with direction inferred from nearest edge).
    """

    max_offset: Optional[float] = None
    min_offset: float = 0.0
    max_offset_ratio: float = 2.0
    min_offset_ratio: float = 0.0
    max_shots_per_subarray: Optional[int] = None
    require_both_sides: bool = False
    min_shots_per_side: int = 0
    allow_interior_shots: bool = False

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "AssignmentConstraints":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in d.items() if k in known})


@dataclass
class SubArrayShotRelation:
    """One cell of the compatibility matrix.

    Describes the geometric relationship between a single shot and a
    single subarray, *before* any strategy is applied.
    """

    shot_index: int
    subarray_index: int
    shot_file: str
    shot_position: float
    subarray: SubArrayDef
    relation_type: RelationType
    direction: str
    source_offset: float
    is_interior: bool
    quality_score: float
    is_valid: bool


@dataclass
class ShotAssignment:
    """A selected (shot, subarray) pair that will be processed."""

    subarray_def: SubArrayDef
    shot_file: str
    shot_position: float
    source_offset: float
    direction: str
    quality_score: float
    relation_type: RelationType
    shot_index: int
    subarray_index: int

    @property
    def midpoint(self) -> float:
        return self.subarray_def.midpoint

    @property
    def config_name(self) -> str:
        return self.subarray_def.config_name

    def __repr__(self) -> str:
        return (
            f"ShotAssignment(sa={self.subarray_index}, "
            f"mid={self.midpoint:.1f}m, shot={self.shot_index}, "
            f"off={self.source_offset:.1f}m, dir='{self.direction}')"
        )


@dataclass
class AssignmentPlan:
    """Complete assignment plan produced by the engine.

    Carries the selected assignments, the full compatibility matrix, the
    strategy and constraints used, plus convenience query methods.
    """

    assignments: List[ShotAssignment]
    strategy: AssignmentStrategy
    constraints: AssignmentConstraints
    compatibility_matrix: List[List[SubArrayShotRelation]]
    shots: List[Dict[str, Any]] = field(default_factory=list)
    subarrays: List[SubArrayDef] = field(default_factory=list)
    array_config: Dict[str, Any] = field(default_factory=dict)

    # -- query helpers ---------------------------------------------------

    def assignments_for_subarray(self, subarray_index: int) -> List[ShotAssignment]:
        return [a for a in self.assignments if a.subarray_index == subarray_index]

    def assignments_for_shot(self, shot_index: int) -> List[ShotAssignment]:
        return [a for a in self.assignments if a.shot_index == shot_index]

    def assignments_grouped_by_shot(self) -> Dict[int, List[ShotAssignment]]:
        groups: Dict[int, List[ShotAssignment]] = defaultdict(list)
        for a in self.assignments:
            groups[a.shot_index].append(a)
        return dict(groups)

    def assignments_grouped_by_subarray(self) -> Dict[int, List[ShotAssignment]]:
        groups: Dict[int, List[ShotAssignment]] = defaultdict(list)
        for a in self.assignments:
            groups[a.subarray_index].append(a)
        return dict(groups)

    def subarrays_without_assignments(self) -> List[int]:
        covered = {a.subarray_index for a in self.assignments}
        return [i for i in range(len(self.subarrays)) if i not in covered]

    def coverage_summary(self) -> Dict[int, Dict[str, Any]]:
        """Per-subarray summary: counts, offsets, directions."""
        summary: Dict[int, Dict[str, Any]] = {}
        for idx, sa in enumerate(self.subarrays):
            assigned = self.assignments_for_subarray(idx)
            fwd = [a for a in assigned if a.direction == "forward"]
            rev = [a for a in assigned if a.direction == "reverse"]
            summary[idx] = {
                "midpoint": sa.midpoint,
                "config_name": sa.config_name,
                "n_total": len(assigned),
                "n_forward": len(fwd),
                "n_reverse": len(rev),
                "offsets_forward": [a.source_offset for a in fwd],
                "offsets_reverse": [a.source_offset for a in rev],
                "has_both_sides": len(fwd) > 0 and len(rev) > 0,
            }
        return summary

    def midpoint_coverage(self) -> Dict[float, Dict[str, Any]]:
        mp_map: Dict[float, Dict[str, Any]] = defaultdict(
            lambda: {"subarrays": [], "n_assignments": 0, "configs": set()}
        )
        for a in self.assignments:
            entry = mp_map[a.midpoint]
            entry["subarrays"].append(a.subarray_index)
            entry["n_assignments"] += 1
            entry["configs"].add(a.config_name)
        for v in mp_map.values():
            v["configs"] = sorted(v["configs"])
        return dict(mp_map)

    def describe(self) -> str:
        """Human-readable summary."""
        lines = [
            f"AssignmentPlan  strategy={self.strategy.value}",
            f"  shots={len(self.shots)}  subarrays={len(self.subarrays)}  "
            f"assignments={len(self.assignments)}",
        ]
        uncovered = self.subarrays_without_assignments()
        if uncovered:
            lines.append(f"  WARNING: {len(uncovered)} subarrays have no assignments")
        cs = self.coverage_summary()
        both = sum(1 for v in cs.values() if v["has_both_sides"])
        lines.append(
            f"  subarrays with both-side coverage: {both}/{len(self.subarrays)}"
        )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Per-subarray classification & offset
# ---------------------------------------------------------------------------

def classify_shot_for_subarray(
    source_position: float,
    subarray: SubArrayDef,
    tolerance: float = 0.01,
) -> Tuple[RelationType, str, float, bool]:
    """Classify a shot relative to a specific subarray.

    Returns
    -------
    relation_type : RelationType
    direction : str   ("forward" or "reverse")
    source_offset : float  (always >= 0)
    is_interior : bool
    """
    sa_start = subarray.start_position
    sa_end = subarray.end_position

    if abs(source_position - sa_start) < tolerance:
        return RelationType.EDGE_LEFT, "forward", 0.0, False
    if abs(source_position - sa_end) < tolerance:
        return RelationType.EDGE_RIGHT, "reverse", 0.0, False

    if source_position < sa_start:
        offset = sa_start - source_position
        return RelationType.EXTERIOR_LEFT, "forward", offset, False

    if source_position > sa_end:
        offset = source_position - sa_end
        return RelationType.EXTERIOR_RIGHT, "reverse", offset, False

    # Interior: decide direction by proximity to edges
    dist_start = source_position - sa_start
    dist_end = sa_end - source_position
    if dist_start <= dist_end:
        return RelationType.INTERIOR_LEFT, "forward", dist_start, True
    return RelationType.INTERIOR_RIGHT, "reverse", dist_end, True


def _offset_quality_score(
    offset: float,
    subarray_length: float,
    optimal_ratio: float = 0.5,
) -> float:
    if subarray_length <= 0:
        return 0.0
    ratio = offset / subarray_length
    deviation = abs(ratio - optimal_ratio)
    k = 2.77
    return max(0.0, min(1.0, math.exp(-k * deviation * deviation)))


# ---------------------------------------------------------------------------
# Compatibility matrix
# ---------------------------------------------------------------------------

def build_compatibility_matrix(
    shots: List[Dict[str, Any]],
    subarrays: List[SubArrayDef],
    constraints: AssignmentConstraints,
    tolerance: float = 0.01,
) -> List[List[SubArrayShotRelation]]:
    """Build N_shots x M_subarrays compatibility matrix.

    Each cell describes whether the (shot, subarray) pair is
    geometrically valid and how good the offset is.
    """
    matrix: List[List[SubArrayShotRelation]] = []

    for si, shot in enumerate(shots):
        row: List[SubArrayShotRelation] = []
        src_pos = shot["source_position"]
        shot_file = shot.get("file", "")

        for sai, sa in enumerate(subarrays):
            rel_type, direction, offset, is_interior = classify_shot_for_subarray(
                src_pos, sa, tolerance
            )
            quality = _offset_quality_score(offset, sa.length)

            valid = True
            if is_interior and not constraints.allow_interior_shots:
                valid = False
            if valid and constraints.max_offset is not None and offset > constraints.max_offset:
                valid = False
            if valid and offset < constraints.min_offset:
                valid = False
            if valid and sa.length > 0:
                ratio = offset / sa.length
                if ratio < constraints.min_offset_ratio:
                    valid = False
                if ratio > constraints.max_offset_ratio:
                    valid = False

            row.append(SubArrayShotRelation(
                shot_index=si,
                subarray_index=sai,
                shot_file=shot_file,
                shot_position=src_pos,
                subarray=sa,
                relation_type=rel_type,
                direction=direction,
                source_offset=offset,
                is_interior=is_interior,
                quality_score=quality,
                is_valid=valid,
            ))
        matrix.append(row)

    return matrix


# ---------------------------------------------------------------------------
# Strategy implementations
# ---------------------------------------------------------------------------

def _valid_relations_for_subarray(
    matrix: List[List[SubArrayShotRelation]],
    subarray_index: int,
) -> List[SubArrayShotRelation]:
    return [
        row[subarray_index]
        for row in matrix
        if row[subarray_index].is_valid
    ]


def _relation_to_assignment(r: SubArrayShotRelation) -> ShotAssignment:
    return ShotAssignment(
        subarray_def=r.subarray,
        shot_file=r.shot_file,
        shot_position=r.shot_position,
        source_offset=r.source_offset,
        direction=r.direction,
        quality_score=r.quality_score,
        relation_type=r.relation_type,
        shot_index=r.shot_index,
        subarray_index=r.subarray_index,
    )


def _split_by_direction(
    rels: List[SubArrayShotRelation],
) -> Tuple[List[SubArrayShotRelation], List[SubArrayShotRelation]]:
    fwd = [r for r in rels if r.direction == "forward"]
    rev = [r for r in rels if r.direction == "reverse"]
    return fwd, rev


def _apply_max_shots(
    assignments: List[ShotAssignment],
    constraints: AssignmentConstraints,
    n_subarrays: int,
) -> List[ShotAssignment]:
    """Trim assignments per subarray to max_shots_per_subarray."""
    if constraints.max_shots_per_subarray is None:
        return assignments

    cap = constraints.max_shots_per_subarray
    groups: Dict[int, List[ShotAssignment]] = defaultdict(list)
    for a in assignments:
        groups[a.subarray_index].append(a)

    result: List[ShotAssignment] = []
    for sai in range(n_subarrays):
        bucket = groups.get(sai, [])
        bucket.sort(key=lambda a: a.quality_score, reverse=True)
        result.extend(bucket[:cap])
    return result


def _apply_both_sides_filter(
    assignments: List[ShotAssignment],
    require: bool,
) -> List[ShotAssignment]:
    if not require:
        return assignments
    groups: Dict[int, List[ShotAssignment]] = defaultdict(list)
    for a in assignments:
        groups[a.subarray_index].append(a)

    result: List[ShotAssignment] = []
    for bucket in groups.values():
        dirs = {a.direction for a in bucket}
        if "forward" in dirs and "reverse" in dirs:
            result.extend(bucket)
    return result


def _apply_min_per_side(
    assignments: List[ShotAssignment],
    min_per_side: int,
) -> List[ShotAssignment]:
    if min_per_side <= 0:
        return assignments
    groups: Dict[int, List[ShotAssignment]] = defaultdict(list)
    for a in assignments:
        groups[a.subarray_index].append(a)

    result: List[ShotAssignment] = []
    for bucket in groups.values():
        fwd = [a for a in bucket if a.direction == "forward"]
        rev = [a for a in bucket if a.direction == "reverse"]
        if len(fwd) >= min_per_side and len(rev) >= min_per_side:
            result.extend(bucket)
    return result


# -- individual strategies --------------------------------------------------

def _strategy_max_coverage(
    matrix: List[List[SubArrayShotRelation]],
    constraints: AssignmentConstraints,
    n_subarrays: int,
    **_kw: Any,
) -> List[ShotAssignment]:
    assignments = []
    for sai in range(n_subarrays):
        for r in _valid_relations_for_subarray(matrix, sai):
            assignments.append(_relation_to_assignment(r))
    assignments = _apply_max_shots(assignments, constraints, n_subarrays)
    assignments = _apply_both_sides_filter(assignments, constraints.require_both_sides)
    assignments = _apply_min_per_side(assignments, constraints.min_shots_per_side)
    return assignments


def _strategy_balanced(
    matrix: List[List[SubArrayShotRelation]],
    constraints: AssignmentConstraints,
    n_subarrays: int,
    **_kw: Any,
) -> List[ShotAssignment]:
    assignments: List[ShotAssignment] = []
    for sai in range(n_subarrays):
        rels = _valid_relations_for_subarray(matrix, sai)
        fwd, rev = _split_by_direction(rels)
        fwd.sort(key=lambda r: r.quality_score, reverse=True)
        rev.sort(key=lambda r: r.quality_score, reverse=True)

        n_pick = min(len(fwd), len(rev))
        if n_pick == 0 and not constraints.require_both_sides:
            n_pick = max(len(fwd), len(rev))
            chosen = (fwd or rev)[:n_pick]
        else:
            if constraints.max_shots_per_subarray is not None:
                per_side = constraints.max_shots_per_subarray // 2
                n_pick = min(n_pick, per_side)
            chosen = fwd[:n_pick] + rev[:n_pick]

        for r in chosen:
            assignments.append(_relation_to_assignment(r))

    assignments = _apply_both_sides_filter(assignments, constraints.require_both_sides)
    assignments = _apply_min_per_side(assignments, constraints.min_shots_per_side)
    return assignments


def _strategy_offset_optimized(
    matrix: List[List[SubArrayShotRelation]],
    constraints: AssignmentConstraints,
    n_subarrays: int,
    **_kw: Any,
) -> List[ShotAssignment]:
    assignments: List[ShotAssignment] = []
    cap = constraints.max_shots_per_subarray or 4

    for sai in range(n_subarrays):
        rels = _valid_relations_for_subarray(matrix, sai)
        rels.sort(key=lambda r: r.quality_score, reverse=True)
        for r in rels[:cap]:
            assignments.append(_relation_to_assignment(r))

    assignments = _apply_both_sides_filter(assignments, constraints.require_both_sides)
    assignments = _apply_min_per_side(assignments, constraints.min_shots_per_side)
    return assignments


def _strategy_both_sides_priority(
    matrix: List[List[SubArrayShotRelation]],
    constraints: AssignmentConstraints,
    n_subarrays: int,
    **_kw: Any,
) -> List[ShotAssignment]:
    assignments: List[ShotAssignment] = []
    cap = constraints.max_shots_per_subarray

    for sai in range(n_subarrays):
        rels = _valid_relations_for_subarray(matrix, sai)
        fwd, rev = _split_by_direction(rels)
        if not fwd or not rev:
            continue
        fwd.sort(key=lambda r: r.quality_score, reverse=True)
        rev.sort(key=lambda r: r.quality_score, reverse=True)

        if cap is not None:
            per_side = max(1, cap // 2)
            chosen = fwd[:per_side] + rev[:per_side]
        else:
            chosen = fwd + rev

        for r in chosen:
            assignments.append(_relation_to_assignment(r))

    assignments = _apply_min_per_side(assignments, constraints.min_shots_per_side)
    return assignments


def _strategy_manual(
    matrix: List[List[SubArrayShotRelation]],
    constraints: AssignmentConstraints,
    n_subarrays: int,
    manual_assignments: Optional[List[Dict[str, Any]]] = None,
    **_kw: Any,
) -> List[ShotAssignment]:
    if not manual_assignments:
        warnings.warn("Manual strategy selected but no manual_assignments provided")
        return []

    assignments: List[ShotAssignment] = []
    n_shots = len(matrix)

    for entry in manual_assignments:
        sai = entry.get("subarray_index")
        shot_indices = entry.get("shot_indices", [])
        if sai is None or sai < 0 or sai >= n_subarrays:
            warnings.warn(f"Skipping invalid subarray_index: {sai}")
            continue

        for si in shot_indices:
            if si < 0 or si >= n_shots:
                warnings.warn(f"Skipping invalid shot_index: {si}")
                continue
            r = matrix[si][sai]
            assignments.append(_relation_to_assignment(r))

    return assignments


def _strategy_exterior_only(
    matrix: List[List[SubArrayShotRelation]],
    constraints: AssignmentConstraints,
    n_subarrays: int,
    array_config: Optional[Dict[str, Any]] = None,
    shots: Optional[List[Dict[str, Any]]] = None,
    **_kw: Any,
) -> List[ShotAssignment]:
    """Legacy behaviour: only shots exterior to the *main* array."""
    if array_config is None or shots is None:
        warnings.warn(
            "exterior_only strategy requires array_config and shots; "
            "falling back to max_coverage"
        )
        return _strategy_max_coverage(matrix, constraints, n_subarrays)

    classified = classify_all_shots(shots, array_config)
    exterior_indices = {
        i for i, s in enumerate(classified) if s.is_exterior
    }

    assignments: List[ShotAssignment] = []
    for sai in range(n_subarrays):
        for r in _valid_relations_for_subarray(matrix, sai):
            if r.shot_index in exterior_indices:
                assignments.append(_relation_to_assignment(r))

    assignments = _apply_max_shots(assignments, constraints, n_subarrays)
    assignments = _apply_both_sides_filter(assignments, constraints.require_both_sides)
    return assignments


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_STRATEGY_DISPATCH = {
    AssignmentStrategy.MAX_COVERAGE: _strategy_max_coverage,
    AssignmentStrategy.BALANCED: _strategy_balanced,
    AssignmentStrategy.OFFSET_OPTIMIZED: _strategy_offset_optimized,
    AssignmentStrategy.BOTH_SIDES_PRIORITY: _strategy_both_sides_priority,
    AssignmentStrategy.MANUAL: _strategy_manual,
    AssignmentStrategy.EXTERIOR_ONLY: _strategy_exterior_only,
}


def generate_assignment_plan(
    shots: List[Dict[str, Any]],
    subarrays: List[SubArrayDef],
    constraints: Optional[AssignmentConstraints] = None,
    strategy: AssignmentStrategy = AssignmentStrategy.BALANCED,
    manual_assignments: Optional[List[Dict[str, Any]]] = None,
    array_config: Optional[Dict[str, Any]] = None,
    tolerance: float = 0.01,
) -> AssignmentPlan:
    """Master entry-point: build compatibility matrix and apply strategy.

    Parameters
    ----------
    shots : list of dict
        Each dict must have ``"file"`` and ``"source_position"`` keys.
    subarrays : list of SubArrayDef
        All enumerated subarrays (from sliding window or manual list).
    constraints : AssignmentConstraints, optional
        Filtering constraints.  Defaults to permissive defaults.
    strategy : AssignmentStrategy
        Selection strategy.
    manual_assignments : list of dict, optional
        Required when ``strategy`` is ``MANUAL``.  Each dict has
        ``"subarray_index"`` (int) and ``"shot_indices"`` (list[int]).
    array_config : dict, optional
        Main array config (needed only by ``EXTERIOR_ONLY`` strategy).
    tolerance : float
        Edge-detection tolerance in metres.

    Returns
    -------
    AssignmentPlan
    """
    if constraints is None:
        constraints = AssignmentConstraints()

    matrix = build_compatibility_matrix(shots, subarrays, constraints, tolerance)
    n_subarrays = len(subarrays)

    strategy_fn = _STRATEGY_DISPATCH[strategy]
    assignments = strategy_fn(
        matrix,
        constraints,
        n_subarrays,
        manual_assignments=manual_assignments,
        array_config=array_config,
        shots=shots,
    )

    return AssignmentPlan(
        assignments=assignments,
        strategy=strategy,
        constraints=constraints,
        compatibility_matrix=matrix,
        shots=shots,
        subarrays=subarrays,
        array_config=array_config or {},
    )


def generate_plan_from_config(
    config: Dict[str, Any],
    tolerance: float = 0.01,
) -> AssignmentPlan:
    """Convenience wrapper that reads everything from a survey config dict.

    If the config has no ``"assignment"`` section the ``EXTERIOR_ONLY``
    strategy is used (backward-compatible behaviour).
    """
    from .subarray import get_all_subarrays_from_config, flatten_subarrays

    shots = config["shots"]
    array_cfg = config["array"]
    sa_dict = get_all_subarrays_from_config(config)
    subarrays = flatten_subarrays(sa_dict)

    assign_cfg = config.get("assignment", {})
    strategy_name = assign_cfg.get("strategy", "exterior_only")
    strategy = AssignmentStrategy(strategy_name)

    constraints_dict = assign_cfg.get("constraints", {})
    constraints = AssignmentConstraints.from_dict(constraints_dict)

    manual = assign_cfg.get("manual_assignments", None)

    return generate_assignment_plan(
        shots=shots,
        subarrays=subarrays,
        constraints=constraints,
        strategy=strategy,
        manual_assignments=manual,
        array_config=array_cfg,
        tolerance=tolerance,
    )
