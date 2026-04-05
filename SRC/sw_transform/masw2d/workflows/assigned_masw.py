"""Assignment-based MASW workflow.

Uses the intelligent shot-subarray assignment engine to decide which
(shot, subarray) pairs to process, enabling in-line shots and multiple
configurable strategies.  Backward-compatible with the exterior-only
approach when no ``assignment`` section is present in the config.
"""

from __future__ import annotations

import warnings
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from .base import BaseWorkflow
from ..config.loader import load_config
from ..geometry.subarray import get_all_subarrays_from_config, flatten_subarrays
from ..geometry.shot_assigner import (
    AssignmentConstraints,
    AssignmentPlan,
    AssignmentStrategy,
    generate_assignment_plan,
    generate_plan_from_config,
)
from ..extraction.subarray_extractor import extract_from_assignment
from ..processing.batch_processor import process_batch, DispersionResult
from ..output.organizer import (
    export_single_result,
    write_summary_from_metadata,
    write_combined_csv_per_midpoint,
    write_combined_npz_per_midpoint,
)


def _load_npz_metadata(data) -> dict:
    meta = {}
    for k in data.files:
        if k.startswith("meta_"):
            key = k.replace("meta_", "", 1)
            val = data[k]
            if val.ndim == 0:
                try:
                    meta[key] = float(val)
                except (ValueError, TypeError):
                    meta[key] = str(val)
            else:
                meta[key] = val
    return meta


class AssignedMASWWorkflow(BaseWorkflow):
    """Workflow driven by the shot-subarray assignment engine.

    1. Loads configuration (file or dict).
    2. Enumerates all subarrays via sliding-window configs.
    3. Runs the assignment engine (strategy + constraints) to produce
       an :class:`AssignmentPlan`.
    4. Groups assignments by shot file so each file is loaded once.
    5. Extracts and processes only the assigned pairs.
    6. Writes results using the standard output pipeline.

    Parameters
    ----------
    config : dict or str or Path
        Survey configuration dictionary or path to JSON config file.
    """

    def __init__(self, config):
        if isinstance(config, (str, Path)):
            config = load_config(config)
        super().__init__(config)
        self._plan: Optional[AssignmentPlan] = None

    @property
    def plan(self) -> AssignmentPlan:
        """Lazily-generated assignment plan."""
        if self._plan is None:
            self._plan = generate_plan_from_config(self.config)
        return self._plan

    def get_info(self) -> Dict[str, Any]:
        plan = self.plan
        cs = plan.coverage_summary()
        both_count = sum(1 for v in cs.values() if v["has_both_sides"])
        uncovered = plan.subarrays_without_assignments()
        midpoints = sorted({a.midpoint for a in plan.assignments})

        return {
            "survey_name": self.survey_name,
            "workflow": self.name,
            "array": self.config.get("array", {}),
            "strategy": plan.strategy.value,
            "n_total_shots": len(plan.shots),
            "n_subarrays": len(plan.subarrays),
            "n_assignments": len(plan.assignments),
            "n_unique_midpoints": len(midpoints),
            "midpoints": midpoints,
            "subarrays_with_both_sides": both_count,
            "subarrays_without_assignments": len(uncovered),
            "processing_method": self.config.get("processing", {}).get("method", "ps"),
        }

    # ------------------------------------------------------------------
    # run
    # ------------------------------------------------------------------

    def run(
        self,
        output_dir: Optional[str] = None,
        parallel: bool = False,
        max_workers: Optional[int] = None,
    ) -> Dict[str, Any]:
        from sw_transform.processing.seg2 import load_seg2_ar

        output_dir = output_dir or self.config.get("output", {}).get(
            "directory", "./output_2d/"
        )
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        plan = self.plan

        if not plan.assignments:
            return {
                "status": "error",
                "error": "Assignment plan produced zero assignments",
                "n_results": 0,
            }

        proc_params = self.config.get("processing", {})
        method = proc_params.get("method", "ps")

        output_config = self.config.get("output", {})
        export_formats = output_config.get("export_formats", ["csv"])
        organize_by = output_config.get("organize_by", "midpoint")
        include_images = output_config.get("include_images", False) or any(
            fmt in export_formats for fmt in ("image", "png", "jpg", "jpeg")
        )
        image_params = {
            "max_frequency": output_config.get("max_frequency", None),
            "cmap": output_config.get("cmap", "jet"),
            "dpi": output_config.get("image_dpi", 150),
            "auto_velocity_limit": output_config.get("auto_velocity_limit", True),
            "auto_frequency_limit": output_config.get("auto_frequency_limit", True),
            "fig_width": output_config.get("fig_width", 8),
            "fig_height": output_config.get("fig_height", 6),
            "contour_levels": output_config.get("contour_levels", 30),
            "plot_style": output_config.get("plot_style", "contourf"),
        }
        if "max_velocity" in output_config and not output_config.get(
            "auto_velocity_limit", True
        ):
            image_params["max_velocity"] = output_config["max_velocity"]

        export_fmts_for_processing = list(export_formats)
        needs_npz = (
            include_images
            or output_config.get("export_combined_npz_per_midpoint", True)
            or output_config.get("export_individual_npz", True)
        )
        if needs_npz and "npz" not in export_fmts_for_processing:
            export_fmts_for_processing.append("npz")

        all_results_meta: List[Dict[str, Any]] = []
        all_exported_files: List[str] = []

        # Group assignments by shot file so each file is loaded once.
        by_shot = plan.assignments_grouped_by_shot()
        shot_files = sorted(by_shot.keys())
        total_files = len(shot_files)

        self._report_progress(0, total_files, "Starting assignment-based processing...")

        dx_cfg = self.config["array"]["dx"]

        for file_idx, shot_idx in enumerate(shot_files):
            shot_assignments = by_shot[shot_idx]
            shot_file = shot_assignments[0].shot_file
            self._report_progress(
                file_idx,
                total_files,
                f"Processing shot {file_idx + 1}/{total_files}: {Path(shot_file).name}",
            )

            try:
                time, data, _, file_dx, dt, _ = load_seg2_ar(shot_file)
                dx = file_dx if file_dx > 0 else dx_cfg

                extracted_list = []
                for asgn in shot_assignments:
                    try:
                        ext = extract_from_assignment(
                            data, time, dt, dx, asgn, reverse_if_needed=True
                        )
                        extracted_list.append(ext)
                    except IndexError as exc:
                        warnings.warn(f"Extraction failed: {exc}")
                        continue

                if not extracted_list:
                    continue

                results = process_batch(
                    extracted_list, method=method, processing_params=proc_params
                )

                for result in results:
                    meta = export_single_result(
                        result,
                        output_dir,
                        organize_by=organize_by,
                        export_formats=export_fmts_for_processing,
                        include_images=False,
                        image_params=image_params,
                    )
                    all_results_meta.append(meta)
                    all_exported_files.extend(meta["files"])
                del results

            except Exception as exc:
                warnings.warn(f"Failed to process {shot_file}: {exc}")
                continue

        self._report_progress(total_files, total_files, "Writing summary...")

        if not all_results_meta:
            return {
                "status": "error",
                "error": "No dispersion curves were extracted",
                "n_results": 0,
            }

        if output_config.get("export_combined_csv_per_midpoint", True):
            combined_csv = write_combined_csv_per_midpoint(
                all_results_meta, output_dir, organize_by
            )
            all_exported_files.extend(combined_csv)

        if output_config.get("export_combined_npz_per_midpoint", True):
            combined_npz = write_combined_npz_per_midpoint(
                all_results_meta, output_dir, organize_by
            )
            all_exported_files.extend(combined_npz)

        generate_summary = output_config.get("generate_summary", True)
        summary_result: Dict[str, Any] = {}

        if generate_summary:
            summary_result = write_summary_from_metadata(
                all_results_meta,
                output_dir,
                write_midpoint_summary=output_config.get("export_midpoint_summary", True),
                write_all_picks=output_config.get("export_all_picks", True),
                write_combined_npz=output_config.get("export_combined_npz", False),
            )
            all_exported_files.extend(summary_result["files"])

        if include_images:
            npz_files = [m["npz_path"] for m in all_results_meta if m.get("npz_path")]
            if npz_files:
                self._report_progress(total_files, total_files, "Rendering images...")
                from ..output.export import export_dispersion_image
                from ..processing.batch_processor import DispersionResult as DR

                for npz_path in npz_files:
                    try:
                        with np.load(npz_path, allow_pickle=True) as npz_data:
                            res = DR(
                                frequencies=npz_data["frequencies"],
                                velocities=npz_data["velocities"],
                                power=npz_data["power"],
                                picked_velocities=npz_data["picked_velocities"],
                                wavelengths=npz_data["wavelengths"],
                                midpoint=float(npz_data["midpoint"]),
                                subarray_config=str(npz_data["subarray_config"]),
                                shot_file=str(npz_data.get("shot_file", "")),
                                source_offset=float(npz_data["source_offset"]),
                                source_position=float(
                                    npz_data.get("source_position", 0.0)
                                ),
                                direction=str(npz_data["direction"]),
                                method=str(npz_data["method"]),
                                metadata=_load_npz_metadata(npz_data),
                            )
                        png_path = npz_path.replace(".npz", ".png")
                        img_p = image_params.copy()
                        img_p.setdefault("auto_velocity_limit", True)
                        img_p.setdefault("auto_frequency_limit", True)
                        export_dispersion_image(res, png_path, **img_p)
                        all_exported_files.append(png_path)
                        del res
                    except Exception as exc:
                        warnings.warn(f"Failed to render image from {npz_path}: {exc}")

        midpoints = sorted({m["midpoint"] for m in all_results_meta})

        summary = {
            "status": "success",
            "n_results": len(all_results_meta),
            "n_midpoints": len(midpoints),
            "midpoints": midpoints,
            "files": all_exported_files,
            "organize_by": organize_by,
            "summary": summary_result.get("summary", {}),
            "workflow": self.name,
            "survey_name": self.survey_name,
            "method": method,
            "strategy": plan.strategy.value,
            "n_assignments": len(plan.assignments),
            "assignment_plan_description": plan.describe(),
            "n_shots_loaded": total_files,
        }

        self._report_progress(total_files, total_files, "Complete!")
        return summary


def run_assigned_masw(
    config_path: str,
    output_dir: Optional[str] = None,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
) -> Dict[str, Any]:
    """Convenience function to run the assignment-based MASW workflow."""
    workflow = AssignedMASWWorkflow(config_path)
    if progress_callback:
        workflow.set_progress_callback(progress_callback)
    return workflow.run(output_dir=output_dir)
