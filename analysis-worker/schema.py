"""Versioned SceneBid analysis contract."""
SCHEMA_VERSION = "1.0"
TIMELINE_UNIT = "seconds"

def overlap(a_start, a_end, b_start, b_end):
    return a_start < b_end and b_start < a_end

def group_shots(shots, annotations, transcript):
    """Conservative grouping: adjacent shots share a segment only when their
    model categories/advertiser agree. Otherwise retain shot-level unknowns.
    This is deliberately an inference, not a commercial chapter detector.
    """
    segments = []
    for i, shot in enumerate(shots):
        ann = annotations[i] if i < len(annotations) else {}
        categories = set(ann.get("categories") or [])
        advertiser = ann.get("advertiser")
        if segments:
            previous = segments[-1]
            prev_categories = previous["_categories"]
            prev_advertiser = previous["_advertiser"]
            compatible = (categories and prev_categories and categories & prev_categories) or (
                advertiser and prev_advertiser and advertiser == prev_advertiser)
            if compatible:
                previous["end_sec"] = shot["end_sec"]
                previous["shot_ids"].append(shot["id"])
                previous["_categories"] |= categories
                continue
        segments.append({
            "id": f"segment-{len(segments)+1:05d}",
            "kind": "predicted_commercial" if categories or advertiser else "unknown",
            "start_sec": shot["start_sec"], "end_sec": shot["end_sec"],
            "boundary_source": "automatic_grouping",
            "boundary_evidence": ["Adjacent shot annotations share inferred categories or advertiser."]
                if segments and compatible else ["Shot-level fallback; insufficient grouping evidence."],
            "shot_ids": [shot["id"]], "_categories": categories,
            "_advertiser": advertiser,
        })
    for segment in segments:
        segment.pop("_categories", None)
        segment.pop("_advertiser", None)
    return segments

