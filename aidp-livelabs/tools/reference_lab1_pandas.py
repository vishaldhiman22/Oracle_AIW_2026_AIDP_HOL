# Validation-only reference implementation from before the native Spark lineage revision.
# Not a learner notebook; never deploy this file to AIDP. It supplies an independent
# pandas baseline for business-result regression checks and local Lab 2 tests.
# %% [markdown]
# # Lab 1: Build the unified lakehouse foundation in AIDP
# Alex, Seer's data engineer, receives five extracts from CRM, Fusion ERP,
# Primavera, and field inspections. Preserve the raw records, standardize the
# suppliers, reconcile business identifiers, and publish Austin delivery context.
#
# **Time:** 40 minutes. **Prerequisites:** follow `docs/00-setup.md`.
# This notebook contains Python transformations; Spark handles source reads and
# managed Delta persistence in AIDP. The 23-row fixture is intentionally processed
# on the driver with pandas. A hard size limit prevents accidental large collects.
# For larger data, replace pandas transforms with distributed Spark DataFrames.

# %% [markdown]
# ## Task 1: Attach compute and load configuration
# Import the two IPYNB files into `/Workspace/Shared/seer-aidp-livelabs/notebooks`.
# Upload the support files under `/Workspace/Shared/seer-aidp-livelabs`.
# Create the catalog, schemas, and volumes in setup before running these cells.
# `lab` is a workshop helper for configuration, paths, table access, and run
# evidence. It is not an AIDP built-in. Bronze ingestion below uses Spark directly.

# %%
import os, sys, json, hashlib
from pathlib import Path
from decimal import Decimal
import pandas as pd
LAB_HOME = Path(os.environ.get("SEER_LAB_HOME", "/Workspace/Shared/seer-aidp-livelabs"))
sys.path.insert(0, str(LAB_HOME / "tools/test_support"))
from seer_runtime import Lab, FILES, now, digest, standardize_suppliers
lab = Lab("Lab1_Unified_Lakehouse_Foundation", globals().get("spark"), globals().get("oidlUtils"))
print({"catalog": lab.config["catalog"], "source_root": lab.config["source_root"], "run_id": lab.run_id})

# %% [markdown]
# ## Task 2: Read source files into Bronze
# Read each CSV with Spark and save it as a managed Delta table in Bronze.
# `header=True` uses the first line as column names; `inferSchema=False` keeps
# source values as strings. Empty fields are represented as empty strings.
# `FILES` lists the five feeds and their expected row counts; `lab.path()` resolves
# each filename within the configured source volume. Source files stay unchanged.
# **Rerun behavior:** `mode("overwrite")` replaces each workshop Bronze snapshot.
# These snapshots refresh only when you rerun ingestion.

# %%
bronze_schema = f"{lab.config['catalog']}.{lab.config['schemas']['bronze']}"
for entity, (relative, _) in FILES.items():
    source_path = str(lab.path(relative))
    bronze_table = f"{bronze_schema}.{entity}_raw"
    source_df = spark.read.csv(
        source_path, header=True, inferSchema=False, mode="FAILFAST"
    ).fillna("")
    source_df.write.format("delta").mode("overwrite").saveAsTable(bronze_table)
    print(f"Loaded {source_path} -> {bronze_table}")

# %% [markdown]
# ### Check the Bronze tables and record source provenance
# Read back the five saved tables, check row counts and source keys, and record
# file hashes and extraction timestamps. `lab.read()` returns a bounded pandas
# DataFrame for the following small-data transformations. A failed check stops
# progression to Silver; it does not roll back the Bronze snapshots just written.
# File hashes identify source bytes, not OCI object version IDs.

# %%
raw, inventory = {}, []
for entity, (relative, expected) in FILES.items():
    df = lab.read("bronze", entity + "_raw")
    assert len(df) == expected, f"{entity}: expected {expected} fixture records, got {len(df)}"
    assert df.source_record_id.ne("").all() and df.source_record_id.is_unique
    raw[entity] = df
    lab.write_count += len(df)  # Include direct Spark writes in run evidence.
    source_time = df.extracted_at.min() if "extracted_at" in df else None
    inventory.append(dict(source_object=relative, physical_path=str(lab.path(relative)),
                          storage_format="CSV", record_count=len(df), source_sha256=digest(lab.path(relative)),
                          source_extracted_at=source_time, loaded_at=now(),
                          ingestion_batch_id=df.ingestion_batch_id.iloc[0], run_id=lab.run_id))
inventory = pd.DataFrame(inventory)
lab.write("bronze", "source_record_inventory", inventory, {"record_count": "long"})
display(inventory)
assert int(inventory.record_count.sum()) == 23

# %% [markdown]
# ## Task 3: Standardize eight supplier source records
# Apply Seer's supplier normalization rules: standardize Atlas abbreviations,
# qualification codes, AISC certifications, and Texas location spellings.
# Standardization preserves eight rows; entity matching happens later.
# Authoring-only reference; learners use the inline notebook transformation.

# %%
standardized = standardize_suppliers(raw["suppliers"])
lab.write("silver", "supplier_standardized_demo", standardized)
display(standardized.sort_values("source_record_id"))

# %% [markdown]
# ## Task 4: Validate against an independent answer key
# Compare the results with an independently authored supplier reference.
# Check names, qualifications, certifications, and locations for all eight rows.
# A mismatch requires investigation before proceeding to supplier reconciliation.

# %%
expected = pd.read_csv(LAB_HOME / "reference/supplier_expected.csv", keep_default_na=False)
fields = ["canonical_supplier_name", "qualification_status", "normalized_certification", "normalized_location"]
comparison = standardized.merge(expected, on="source_record_id", suffixes=("", "_expected"), validate="one_to_one")
comparison["validation_status"] = comparison.apply(lambda r: "MATCH" if all(r[f] == r[f + "_expected"] for f in fields) else "REVIEW", axis=1)
display(comparison[["source_record_id", "canonical_supplier_name", "validation_status"]])
assert len(comparison) == 8 and comparison.validation_status.eq("MATCH").all()

# %% [markdown]
# ## Task 5: Reconcile suppliers without hiding disagreements
# Known source-name variants become six supplier entities. IDs are stable hashes
# of the canonical name for this fixture; production master-data IDs should be
# independent of names. A REQUEST_INFORMATION or REVIEW_REQUIRED source prevents
# an APPROVED source from silently winning. Westbridge retains its conflict.

# %%
supplier_rows = []
for name, group in standardized.groupby("canonical_supplier_name", sort=True):
    statuses = set(group.qualification_status)
    qualification = ("REVIEW_REQUIRED" if "REVIEW_REQUIRED" in statuses else
                     "REQUEST_INFORMATION" if "REQUEST_INFORMATION" in statuses else "APPROVED")
    supplier_rows.append(dict(supplier_id="SUP-" + hashlib.sha256(name.encode()).hexdigest()[:12].upper(),
                              canonical_supplier_name=name, qualification_status=qualification,
                              compliance_status="REVIEW_REQUIRED" if group.normalized_certification.eq("MISSING").any() else "EVIDENCE_PRESENT",
                              matched_source_count=len(group), source_system_count=group.source_system.nunique(),
                              reconciliation_status="CONFLICT_RETAINED" if len(statuses) > 1 else "MATCHED",
                              source_record_ids=json.dumps(sorted(group.source_record_id)),
                              certifications=json.dumps(sorted(set(group.normalized_certification)))))
suppliers = pd.DataFrame(supplier_rows)
source_map = standardized.merge(suppliers[["supplier_id", "canonical_supplier_name"]], on="canonical_supplier_name", validate="many_to_one")
lab.write("silver", "suppliers", suppliers, {"matched_source_count": "long", "source_system_count": "long"})
lab.write("silver", "supplier_source_mappings", source_map)
display(suppliers)
assert len(suppliers) == 6

# %% [markdown]
# ## Task 6: Conform assets and preserve unresolved references
# The downloaded files use ERP, Primavera and field asset aliases. This tiny
# fixture contains one asset per project, so a project-based crosswalk is explicit
# and bounded. Austin's canonical `STR-AUS-STEEL-01` is corroborated by its PDF.
# The other canonical asset IDs are workshop-authored reference values.
# This is a fixture mapping rule, not probabilistic entity resolution.

# %%
asset_ids = {"AUS-BANK-01": "STR-AUS-STEEL-01", "HOU-MIXED-02": "LAB-HOU-STEEL-02", "HAR-SEISMIC-03": "LAB-HAR-BRACE-03"}
assert raw["assets"].project_reference.is_unique
assets = raw["assets"].rename(columns={"project_reference": "project_id", "asset_name": "canonical_asset_name", "asset_category": "asset_type", "financial_status": "normalized_status"}).copy()
assets["asset_id"] = assets.project_id.map(asset_ids)
assert assets.asset_id.notna().all()
projects = raw["schedules"][["project_reference", "project_name"]].drop_duplicates().rename(columns={"project_reference": "project_id"})
assert projects.project_id.is_unique
assets = assets.merge(projects, on="project_id", validate="one_to_one")
aliases = []
for entity in ["assets", "purchasing", "schedules", "inspections"]:
    for _, r in raw[entity][["project_reference", "asset_reference"]].drop_duplicates().iterrows():
        aliases.append(dict(project_id=r.project_reference, source_asset_id=r.asset_reference,
                            asset_id=asset_ids[r.project_reference], source_feed=entity,
                            match_method="ONE_ASSET_PER_PROJECT_FIXTURE"))
aliases = pd.DataFrame(aliases).drop_duplicates()
assets["source_system_count"] = assets.project_id.map(aliases.groupby("project_id").source_feed.nunique())
assets["reconciliation_status"] = "EXPLICIT_FIXTURE_CROSSWALK"
lab.write("silver", "assets", assets, {"source_system_count": "long"})
lab.write("silver", "asset_source_mappings", aliases)

# %%
supplier_lookup = source_map[["source_record_id", "supplier_id"]].rename(columns={"source_record_id": "supplier_reference"})
po = raw["purchasing"].merge(supplier_lookup, on="supplier_reference", how="left", validate="many_to_one")
po["project_id"] = po.project_reference
po["asset_id"] = po.project_reference.map(asset_ids)
po["amount_cents"] = po.amount.map(lambda v: int(Decimal(v) * 100))
assert po.currency_code.eq("USD").all(), "Never sum mixed currencies without an explicit FX conversion"
lab.write("silver", "purchase_orders", po, {"amount_cents": "long"})
inspection = raw["inspections"].copy()
inspection["project_id"] = inspection.project_reference
inspection["asset_id"] = inspection.project_reference.map(asset_ids)
lab.write("silver", "inspections", inspection)
milestones = raw["schedules"].copy()
milestones["project_id"] = milestones.project_reference
milestones["asset_id"] = milestones.project_reference.map(asset_ids)
lab.write("silver", "milestones", milestones)
quarantine = []
for _, r in standardized.iterrows():
    if r.normalized_certification == "MISSING" or r.qualification_status == "REVIEW_REQUIRED":
        quarantine.append(dict(source_record_id=r.source_record_id, source_system=r.source_system,
                               failed_rule="SUPPLIER_EVIDENCE", failure_reason="Missing certification or qualification requires review",
                               quarantine_status="OPEN", severity="WARNING"))
for _, r in po.loc[po.supplier_id.isna()].iterrows():
    quarantine.append(dict(source_record_id=r.source_record_id, source_system="FUSION_ERP",
                           failed_rule="SUPPLIER_REFERENCE", failure_reason="No supplier source mapping for " + r.supplier_reference,
                           quarantine_status="OPEN", severity="ERROR"))
quarantine = pd.DataFrame(quarantine)
lab.write("silver", "quarantined_records", quarantine)
display(quarantine)
# ERP-VEN-2105 is absent from the supplier CSV. Never invent a match to Coastal.
assert set(po.loc[po.supplier_id.isna(), "supplier_reference"]) == {"ERP-VEN-2105"}

# %% [markdown]
# ## Task 7: Assemble Silver events and Gold project context
# Aggregate each one-to-many source before combining it, so two POs, two
# milestones, and two inspections cannot multiply Austin's committed cost.
# Milestone selection is explicit for this workshop; all other rows remain in
# Silver. Readiness here is operational context, not a construction approval.

# %%
event_activities = {"AUS-BANK-01": "A44018", "HOU-MIXED-02": "A33011", "HAR-SEISMIC-03": "A22007"}
context_rows, event_rows, event_mappings = [], [], []
for _, asset in assets.iterrows():
    project_id = asset.project_id
    orders = po.loc[po.project_id.eq(project_id)]
    checks = inspection.loc[inspection.project_id.eq(project_id)]
    activity = milestones.loc[milestones.project_id.eq(project_id) & milestones.activity_id.eq(event_activities[project_id])].iloc[0]
    supplier_keys = orders.supplier_id.dropna().unique()
    supplier = suppliers.loc[suppliers.supplier_id.isin(supplier_keys)]
    inspection_status = "FAIL" if checks.result_status.eq("FAIL").any() else "REQUEST_INFO" if checks.result_status.eq("REQUEST_INFO").any() else "PASS"
    supplier_name = " | ".join(sorted(supplier.canonical_supplier_name)) or "UNRESOLVED"
    readiness = "CONTEXT_AVAILABLE" if inspection_status == "PASS" and orders.supplier_id.notna().all() and supplier.qualification_status.eq("APPROVED").all() else "REVIEW_REQUIRED"
    event_id = "EVENT-" + project_id + "-" + activity.activity_id
    po_status = " | ".join(sorted(set(orders.po_status)))
    context_rows.append(dict(project_id=project_id, asset_id=asset.asset_id, project_name=asset.project_name,
                              asset_name=asset.canonical_asset_name, supplier_name=supplier_name,
                              current_milestone=activity.activity_name, milestone_status=activity.milestone_status,
                              purchase_order_status=po_status, inspection_status=inspection_status,
                              committed_cost_cents=int(orders.amount_cents.sum()), currency_code="USD",
                              purchase_order_count=len(orders), inspection_count=len(checks),
                              decision_readiness=readiness, source_extracted_at=inventory.source_extracted_at.dropna().min(),
                              last_successful_refresh=now(), run_id=lab.run_id))
    event_rows.append(dict(event_id=event_id, project_id=project_id, asset_id=asset.asset_id, project_name=asset.project_name,
                           asset_name=asset.canonical_asset_name, event_type=activity.activity_name,
                           planned_date=activity.planned_date, actual_date=activity.actual_date,
                           supplier_name=supplier_name, financial_status=asset.normalized_status,
                           inspection_status=inspection_status))
    records = [("assets", asset.source_record_id), ("schedules", activity.source_record_id)]
    records += [("purchasing", x) for x in orders.source_record_id]
    records += [("inspections", x) for x in checks.source_record_id]
    records += [("suppliers", x) for x in source_map.loc[source_map.supplier_id.isin(supplier_keys), "source_record_id"]]
    for feed, record_id in records:
        event_mappings.append(dict(source_object=FILES[feed][0], source_record_id=record_id,
                                   canonical_event_id=event_id, project_id=project_id,
                                   match_method="EXPLICIT_FIXTURE_CONTEXT_ASSOCIATION",
                                   scope="Related context; not every row is the delivery transaction"))
context = pd.DataFrame(context_rows)
lab.write("silver", "project_events", pd.DataFrame(event_rows))
lab.write("silver", "source_record_mappings", pd.DataFrame(event_mappings))
lab.write("gold", "project_context", context, {"committed_cost_cents": "long", "purchase_order_count": "long", "inspection_count": "long"})
display(context)
austin = context.loc[context.project_id.eq("AUS-BANK-01")].iloc[0]
assert austin.committed_cost_cents == 167390000
assert austin.purchase_order_count == 2 and austin.inspection_count == 2
assert not context.duplicated(["project_id", "asset_id"]).any()

# %% [markdown]
# ## Task 8: Publish Gold features for upcoming milestone predictions
# PROJECT_CONTEXT describes the selected delivery event. A separate feature product
# includes ALL unfinished milestones due in 1-30 days at the historical fixture
# clock, rather than mistaking Austin's completed delivery for its next activity.
# Labels and actual completion dates are never model inputs. All three projects
# get an upcoming milestone; Austin's is now A44022 (frame erection).

# %%
from seer_predictions import FEATURES, current_features
features = current_features(context, milestones, po, suppliers, lab.config["fixture_as_of"], lab.run_id)
feature_types = {c: "double" for c in FEATURES}
feature_types["committed_cost_cents"] = "long"
lab.write("gold", "milestone_features", features, feature_types)
display(features[["project_id", "milestone_id", "planned_date"] + FEATURES])
assert set(features.milestone_id) == {"A44022", "A33011", "A22007"}

# %% [markdown]
# ## Task 9: Inspect quality and transformation lineage
# These are notebook-produced evidence tables, not built-in AIDP system views.
# Catalog lineage is inspected separately in the AIDP UI where supported.

# %%
quality = pd.DataFrame([
    dict(layer_name="BRONZE", rule_name="Fixture row counts", records_evaluated=23, records_failed=0, status="PASS"),
    dict(layer_name="SILVER", rule_name="Supplier standardization reference", records_evaluated=8, records_failed=0, status="PASS"),
    dict(layer_name="SILVER", rule_name="Supplier evidence", records_evaluated=8, records_failed=len(quarantine.loc[quarantine.failed_rule.eq("SUPPLIER_EVIDENCE")]), status="WARNING"),
    dict(layer_name="SILVER", rule_name="Purchase supplier mapping", records_evaluated=4, records_failed=int(po.supplier_id.isna().sum()), status="WARNING"),
    dict(layer_name="GOLD", rule_name="Unique project asset key", records_evaluated=3, records_failed=0, status="PASS"),
])
quality["evaluated_at"], quality["run_id"] = now(), lab.run_id
lab.write("gold", "data_quality_results", quality, {"records_evaluated": "long", "records_failed": "long"})
lineage = pd.DataFrame([dict(target_object=lab.table_name("gold", "project_context"), source_object=lab.table_name("silver", name),
                              transformation_name="Lab1: preaggregate then join by project and asset", run_id=lab.run_id, completed_at=now())
                        for name in ["assets", "suppliers", "purchase_orders", "milestones", "inspections"]])
lineage = pd.concat([lineage, pd.DataFrame([dict(target_object=lab.table_name("gold", "milestone_features"),
    source_object=lab.table_name(layer, name), transformation_name="Lab1: historical 1-30 day milestone feature snapshot",
    run_id=lab.run_id, completed_at=now()) for layer, name in [("gold", "project_context"), ("silver", "milestones"),
    ("silver", "purchase_orders"), ("silver", "suppliers")]])], ignore_index=True)
lab.write("gold", "lineage_summary", lineage)
display(quality)
lab.finish()

# %% [markdown]
# ## Checkpoint
# You should have 23 raw rows, eight MATCH results, six conformed suppliers,
# three project/asset rows and four visible exceptions. Austin's committed cost
# is $1,673,900.00, including its two POs. Open the Bronze, Silver and Gold
# schemas in AIDP Catalog; inspect columns, data preview and available lineage.
# Continue to Lab 2 to train a classifier, score milestones, prepare a PDF
# knowledge base and run the two-task workflow with readiness checks.
