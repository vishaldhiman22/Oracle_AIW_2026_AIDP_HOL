"""Historical classifier reference for authoring tests, not learner notebooks.

No external inference service or embedding model is used here. Training history
is explicitly synthetic. Model probabilities are demonstration outputs only.
"""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
from seer_runtime import digest, now

FEATURES = ["days_to_planned_date", "open_po_fraction", "inspection_fail_flag",
            "inspection_info_flag", "supplier_review_flag", "unresolved_supplier_flag",
            "milestone_not_started_flag", "milestone_at_risk_flag", "log_committed_cost"]
DOCS = [
    ("atlas_supplier_framework_agreement.pdf", "SUPPLIER_AGREEMENT"),
    ("austin_receiving_inspection_report.pdf", "RECEIVING_INSPECTION"),
    ("austin_structural_engineering_specification.pdf", "ENGINEERING_SPECIFICATION"),
]


def fingerprint(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def current_features(context, milestones, orders, suppliers, as_of, run_id):
    """One row per unfinished milestone due in 1-30 days at the fixture clock.

    The provided extracts are one historical snapshot, not event history. Gold
    rows preserve that scope; changing the clock cannot create new observations.
    """
    clock = pd.Timestamp(as_of).normalize()
    planned = pd.to_datetime(milestones.planned_date, utc=True)
    days = (planned - clock).dt.days
    eligible = milestones.actual_date.fillna("").eq("") & milestones.milestone_status.ne("COMPLETE") & days.between(1, 30)
    rows = []
    for idx, milestone in milestones.loc[eligible].iterrows():
        c = context.loc[context.project_id.eq(milestone.project_id) & context.asset_id.eq(milestone.asset_id)]
        assert len(c) == 1
        c = c.iloc[0]
        po = orders.loc[orders.project_id.eq(c.project_id) & orders.asset_id.eq(c.asset_id)]
        linked = suppliers.loc[suppliers.supplier_id.isin(po.supplier_id.dropna())]
        unresolved = po.supplier_id.isna().any()
        review = unresolved or linked.qualification_status.ne("APPROVED").any() or linked.compliance_status.ne("EVIDENCE_PRESENT").any()
        rows.append(dict(project_id=c.project_id, asset_id=c.asset_id, milestone_id=milestone.activity_id,
            project_name=c.project_name, milestone_name=milestone.activity_name, planned_date=milestone.planned_date,
            prediction_as_of=as_of, days_to_planned_date=int(days.loc[idx]),
            open_po_fraction=float(po.po_status.ne("RECEIVED").mean()) if len(po) else 1.0,
            inspection_fail_flag=int(c.inspection_status == "FAIL"), inspection_info_flag=int(c.inspection_status == "REQUEST_INFO"),
            supplier_review_flag=int(review), unresolved_supplier_flag=int(unresolved),
            milestone_not_started_flag=int(milestone.milestone_status == "NOT_STARTED"),
            milestone_at_risk_flag=int(milestone.milestone_status == "AT_RISK"),
            log_committed_cost=float(np.log1p(c.committed_cost_cents / 100)),
            committed_cost_cents=int(c.committed_cost_cents), source_extracted_at=c.source_extracted_at,
            data_origin="PROVIDED_HISTORICAL_FIXTURE", last_successful_refresh=now(), run_id=run_id))
    result = pd.DataFrame(rows)
    if result.empty:
        raise ValueError("No eligible milestone; inspect fixture clock and source dates, not wall-clock dates")
    assert not result.duplicated(["project_id", "asset_id", "milestone_id"]).any()
    feature_matrix(result)
    return result


def feature_matrix(frame):
    values = frame[FEATURES].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("Missing/nonfinite feature: resolve evidence or explicitly redesign missing-value handling")
    if not frame.days_to_planned_date.between(1, 30).all() or not frame.open_po_fraction.between(0, 1).all():
        raise ValueError("Feature outside workshop prediction horizon/range")
    for name in FEATURES[2:8]:
        if not frame[name].isin([0, 1]).all():
            raise ValueError(name)
    return values


def synthetic_history(seed=234582, count=1800):
    """Generate reproducible stochastic teaching data, never represented as real.

    Probabilistic outcomes depend on observed factors plus an unobserved shock.
    Neither the generator probability nor the shock is returned as a feature.
    Each milestone has exactly one snapshot, so no repeated entity crosses splits.
    """
    rng = np.random.default_rng(seed)
    as_of = pd.Timestamp("2024-01-01", tz="UTC") + pd.to_timedelta(rng.integers(0, 821, count), unit="D")
    days = rng.integers(1, 31, count)
    fails = rng.binomial(1, .18, count)
    info = (1 - fails) * rng.binomial(1, .25, count)
    unresolved = rng.binomial(1, .09, count)
    review = np.maximum(unresolved, rng.binomial(1, .28, count))
    not_started = rng.binomial(1, .30, count)
    at_risk = (1 - not_started) * rng.binomial(1, .22, count)
    open_fraction = rng.choice([0., .25, .5, .75, 1.], count)
    log_cost = rng.uniform(np.log1p(150000), np.log1p(5000000), count)
    log_odds = (-1.8 + 1.4 * fails + .65 * info + .7 * review + .8 * unresolved
                + .9 * not_started + .8 * at_risk + 1.5 * open_fraction - .045 * days
                + .12 * (log_cost - 13.7) + rng.normal(0, .55, count))
    late = rng.binomial(1, sigmoid(log_odds))
    delay = np.where(late == 1, rng.integers(1, 22, count), -rng.integers(0, 4, count))
    planned = as_of + pd.to_timedelta(days, unit="D")
    actual = planned + pd.to_timedelta(delay, unit="D")
    result = pd.DataFrame(dict(milestone_id=[f"SYN-M{i:05d}" for i in range(count)],
        prediction_as_of=as_of.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        planned_date=planned.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        actual_completion_date=actual.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        label_available_at=pd.DatetimeIndex(np.maximum(planned.asi8, actual.asi8), tz="UTC").strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        days_to_planned_date=days, open_po_fraction=open_fraction, inspection_fail_flag=fails,
        inspection_info_flag=info, supplier_review_flag=review, unresolved_supplier_flag=unresolved,
        milestone_not_started_flag=not_started, milestone_at_risk_flag=at_risk, log_committed_cost=log_cost,
        late_flag=late, data_origin="SYNTHETIC_TRAINING_ONLY", generator_version="seer-history-v1", generator_seed=seed))
    assert result.milestone_id.is_unique
    assert ((pd.to_datetime(result.actual_completion_date, utc=True) > pd.to_datetime(result.planned_date, utc=True)).astype(int) == result.late_flag).all()
    feature_matrix(result)
    return result.sort_values(["prediction_as_of", "milestone_id"]).reset_index(drop=True)


def chronological_split(history, cutoff="2026-01-01T00:00:00+00:00"):
    as_of = pd.to_datetime(history.prediction_as_of, utc=True)
    available = pd.to_datetime(history.label_available_at, utc=True)
    cutoff = pd.Timestamp(cutoff)
    # Delta reads need not preserve row order. Sort before fitting/fingerprinting.
    train = history.loc[(as_of < cutoff) & (available < cutoff)].sort_values(["prediction_as_of", "milestone_id"]).reset_index(drop=True)
    test = history.loc[as_of >= cutoff].sort_values(["prediction_as_of", "milestone_id"]).reset_index(drop=True)
    if len(train) < 100 or len(test) < 50 or train.late_flag.nunique() != 2 or test.late_flag.nunique() != 2:
        raise ValueError("Insufficient training/holdout rows or class coverage")
    assert not set(train.milestone_id) & set(test.milestone_id)
    return train, test, len(history) - len(train) - len(test)


def sigmoid(values):
    # Clipping protects floating-point arithmetic, not a probability calibration.
    return 1. / (1. + np.exp(-np.clip(values, -35, 35)))


def fit_classifier(train, regularization=.01, max_iterations=100):
    """L2 logistic regression using Newton steps; preprocessing fit on train only.

    Objective = mean binary log-loss + regularization * ||slopes||^2 / 2.
    This transparent NumPy implementation avoids another compiled dependency.
    It is a teaching model, not a replacement for a production ML framework.
    """
    x = feature_matrix(train)
    y = train.late_flag.to_numpy(dtype=float)
    if set(np.unique(y)) != {0., 1.}:
        raise ValueError("Training needs both label classes")
    mean, scale = x.mean(axis=0), x.std(axis=0)
    scale[scale == 0] = 1
    design = np.column_stack([np.ones(len(x)), (x - mean) / scale])
    weights = np.zeros(design.shape[1])
    penalty = np.diag([0.] + [regularization] * len(FEATURES))
    for iteration in range(max_iterations):
        p = sigmoid(design @ weights)
        gradient = design.T @ (p - y) / len(y) + penalty @ weights
        hessian = (design.T * (p * (1 - p))) @ design / len(y) + penalty
        step = np.linalg.solve(hessian, gradient)
        weights -= step
        if np.linalg.norm(step) < 1e-8:
            break
    else:
        raise RuntimeError("Classifier did not converge")
    payload = dict(algorithm="L2_LOGISTIC_REGRESSION_NUMPY_V1", feature_names=FEATURES,
        mean=mean.tolist(), scale=scale.tolist(), weights=weights.tolist(),
        regularization=regularization, iterations=iteration + 1, training_rows=len(train),
        training_data_sha256=fingerprint(train.to_dict("records")),
        data_origin="SYNTHETIC_TRAINING_ONLY", production_validated=False)
    payload["model_version"] = "seer-delay-" + fingerprint(payload)[:16]
    return payload


def predict(model, frame):
    if model["feature_names"] != FEATURES:
        raise ValueError("Feature contract/model mismatch")
    x = feature_matrix(frame)
    z = (x - np.asarray(model["mean"])) / np.asarray(model["scale"])
    return sigmoid(np.column_stack([np.ones(len(x)), z]) @ np.asarray(model["weights"]))


def metrics(labels, probabilities, threshold=.5):
    y, p = np.asarray(labels, dtype=int), np.asarray(probabilities, dtype=float)
    assert set(np.unique(y)) == {0, 1} and np.isfinite(p).all() and ((p >= 0) & (p <= 1)).all()
    predicted = p >= threshold
    tp, fp = int(((y == 1) & predicted).sum()), int(((y == 0) & predicted).sum())
    fn, tn = int(((y == 1) & ~predicted).sum()), int(((y == 0) & ~predicted).sum())
    positive, negative = p[y == 1], p[y == 0]
    # Pairwise ROC AUC including ties; bounded workshop holdout, not big-data code.
    auc = float(((positive[:, None] > negative).sum() + .5 * (positive[:, None] == negative).sum()) / (len(positive) * len(negative)))
    return dict(roc_auc=auc, brier_score=float(np.mean((p - y) ** 2)), accuracy=float((predicted == y).mean()),
        precision=tp / max(tp + fp, 1), recall=tp / max(tp + fn, 1),
        true_positive=tp, false_positive=fp, false_negative=fn, true_negative=tn,
        rows=len(y), threshold=threshold)


def reason_signals(row):
    """Observed context flags, NOT causal explanations or feature attribution."""
    mapping = {"inspection_fail_flag": "Failed inspection recorded", "inspection_info_flag": "Inspection information requested",
               "supplier_review_flag": "Supplier evidence requires review", "unresolved_supplier_flag": "Supplier mapping unresolved",
               "milestone_not_started_flag": "Milestone not started", "milestone_at_risk_flag": "Source milestone marked at risk"}
    result = [text for key, text in mapping.items() if row[key] == 1]
    if row.open_po_fraction > 0:
        result.append("Some purchase orders are not received; association is project/asset-level")
    return json.dumps(result)


def stage_documents(lab):
    """Copy hash-verified fixture PDFs; page counts come from a verified manifest.

    No PDF parsing package is needed on Spark. The authoring validation checks
    page counts with pypdf locally. Changed source bytes require a new reviewed
    manifest, never a silent reuse of counts or KB ingestion evidence.
    """
    pdf_manifest = {item["document_name"]: item for item in json.loads(
        (lab.root / "reference/pdf-manifest.json").read_text())}
    destination = lab.out / "austin-project"
    destination.mkdir(parents=True, exist_ok=True)
    expected_names = {name for name, _ in DOCS}
    if any(p.name not in expected_names for p in destination.iterdir()):
        raise ValueError("KB source folder contains unexpected entries; review its scope before ingestion")
    rows = []
    for name, kind in DOCS:
        source, target = lab.path("documents/" + name), destination / name
        sha = digest(source)
        verified = pdf_manifest[name]
        if sha != verified["sha256"] or not isinstance(verified["page_count"], int) or verified["page_count"] < 1:
            raise ValueError("PDF differs from the verified fixture manifest: " + name + "; review and regenerate its hash/page count")
        if target.exists() and digest(target) != sha:
            raise ValueError("A different PDF version already exists at " + str(target) + "; review versions before replacing it")
        if not target.exists():
            shutil.copyfile(source, target)
        assert digest(target) == sha
        rows.append(dict(document_name=name, document_type=kind, project_id="AUS-BANK-01", asset_id="STR-AUS-STEEL-01",
            content_sha256=sha, page_count=verified["page_count"], volume_path=str(target),
            source_modified_at=None, object_version=None, last_successful_refresh=now(), run_id=lab.run_id))
    inventory = pd.DataFrame(rows)
    manifest = inventory[["document_name", "content_sha256"]].sort_values("document_name").to_dict("records")
    return inventory, fingerprint(manifest), destination


def kb_evidence_status(evidence, manifest_sha256, source_folder, clock=None):
    """Check a learner's UI attestation. Does NOT call or verify the KB service."""
    clock = pd.Timestamp(clock or now())
    reasons = []
    required = ["knowledge_base_key", "data_source_key", "ingestion_run_id", "native_status", "verified_by"]
    if not evidence:
        return {"status": "NOT_RECORDED", "check_passed": False, "reasons": ["No knowledge-base ingestion evidence supplied"], "verification_method": "NONE"}
    if any(not isinstance(evidence.get(key), str) or not evidence[key].strip() for key in required):
        reasons.append("Missing actual identifiers/status/reviewer")
    if evidence.get("normalized_status") != "SUCCEEDED":
        reasons.append("Ingestion not recorded as successful")
    if evidence.get("source_manifest_sha256") != manifest_sha256 or evidence.get("source_folder") != str(source_folder):
        reasons.append("Evidence does not match this source manifest/folder")
    try:
        completed, verified = pd.Timestamp(evidence["completed_at"]), pd.Timestamp(evidence["verified_at"])
        if completed.tzinfo is None or verified.tzinfo is None or not completed <= verified <= clock + pd.Timedelta(minutes=5):
            reasons.append("Invalid evidence timestamp ordering/timezone")
    except (KeyError, ValueError, TypeError):
        reasons.append("Missing or invalid ingestion/review timestamps")
    return {"status": "RECORDED_SUCCESS_NOT_API_VERIFIED" if not reasons else "INVALID_OR_INCOMPLETE",
            "check_passed": not reasons, "reasons": reasons, "verification_method": "MANUAL_UI_ATTESTATION"}
