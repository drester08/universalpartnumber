PRAGMA foreign_keys = ON;

CREATE TABLE organizations (
  organization_id TEXT PRIMARY KEY,
  legal_name TEXT NOT NULL,
  organization_type TEXT NOT NULL CHECK (organization_type IN ('manufacturer','publisher','standards_body','distributor','other')),
  website_url TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sources (
  source_id TEXT PRIMARY KEY,
  publisher_name TEXT NOT NULL,
  title TEXT NOT NULL,
  source_url TEXT NOT NULL UNIQUE,
  source_type TEXT NOT NULL CHECK (source_type IN ('standard','dictionary','classification','catalog','datasheet','webpage','database','other')),
  authority_tier INTEGER NOT NULL CHECK (authority_tier BETWEEN 1 AND 4),
  access_state TEXT NOT NULL CHECK (access_state IN ('public','registration','subscription','purchase','unknown')),
  license_state TEXT NOT NULL CHECK (license_state IN ('open','attribution','restricted','review_required','unknown')),
  license_url TEXT,
  ingestion_status TEXT NOT NULL CHECK (ingestion_status IN ('metadata_only','license_verified','license_review','reference_only','blocked')),
  version_label TEXT,
  publication_date TEXT,
  retrieved_at TEXT NOT NULL,
  notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE source_artifacts (
  artifact_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  artifact_url TEXT NOT NULL,
  media_type TEXT,
  local_path TEXT,
  sha256 TEXT,
  retrieved_at TEXT NOT NULL,
  retrieval_state TEXT NOT NULL CHECK (retrieval_state IN ('retrieved','remote_only','blocked','superseded')),
  notes TEXT NOT NULL DEFAULT '',
  CHECK (retrieval_state != 'retrieved' OR (local_path IS NOT NULL AND sha256 IS NOT NULL)),
  UNIQUE (source_id, artifact_url)
);

CREATE TABLE domains (
  domain_id TEXT PRIMARY KEY,
  label TEXT NOT NULL UNIQUE,
  scope_note TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('seed','reviewed','retired'))
);

CREATE TABLE external_classes (
  class_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  external_code TEXT NOT NULL,
  preferred_label TEXT NOT NULL,
  definition TEXT,
  parent_class_id TEXT REFERENCES external_classes(class_id),
  version_label TEXT,
  UNIQUE (source_id, external_code, version_label)
);

CREATE TABLE properties (
  property_id TEXT PRIMARY KEY,
  source_id TEXT REFERENCES sources(source_id),
  external_code TEXT,
  preferred_label TEXT NOT NULL,
  definition TEXT NOT NULL,
  value_kind TEXT NOT NULL CHECK (value_kind IN ('text','number','boolean','code','range')),
  identity_role TEXT NOT NULL CHECK (identity_role IN ('defining','conditional','descriptive','unknown')),
  UNIQUE (source_id, external_code)
);

CREATE TABLE controlled_values (
  controlled_value_id TEXT PRIMARY KEY,
  property_id TEXT NOT NULL REFERENCES properties(property_id),
  canonical_code TEXT NOT NULL,
  preferred_label TEXT NOT NULL,
  definition TEXT NOT NULL,
  lifecycle_state TEXT NOT NULL CHECK (lifecycle_state IN ('active','deprecated')),
  CHECK (length(trim(canonical_code)) > 0),
  CHECK (length(trim(preferred_label)) > 0),
  CHECK (length(trim(definition)) > 0),
  UNIQUE (property_id, canonical_code),
  UNIQUE (controlled_value_id, property_id)
);

CREATE TABLE identity_profiles (
  profile_id TEXT PRIMARY KEY,
  domain_id TEXT NOT NULL REFERENCES domains(domain_id),
  class_label TEXT NOT NULL,
  version_label TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('draft','reviewed','retired')),
  scope_note TEXT NOT NULL,
  reviewed_at TEXT,
  UNIQUE (domain_id, class_label, version_label)
);

CREATE TABLE identity_profile_properties (
  profile_id TEXT NOT NULL REFERENCES identity_profiles(profile_id),
  property_id TEXT NOT NULL REFERENCES properties(property_id),
  requirement TEXT NOT NULL CHECK (requirement IN ('required','conditional','descriptive')),
  comparison_rule TEXT NOT NULL CHECK (comparison_rule IN ('exact','normalized_exact','numeric_exact','set_equal','contextual')),
  sequence_number INTEGER NOT NULL,
  rationale TEXT NOT NULL,
  PRIMARY KEY (profile_id, property_id)
);

CREATE TABLE units (
  unit_id TEXT PRIMARY KEY,
  unece_code TEXT UNIQUE,
  symbol TEXT NOT NULL,
  name TEXT NOT NULL,
  quantity_kind TEXT,
  conversion_factor TEXT,
  conversion_offset TEXT
);

CREATE TABLE numeric_comparison_rules (
  rule_id TEXT PRIMARY KEY,
  profile_id TEXT NOT NULL REFERENCES identity_profiles(profile_id),
  property_id TEXT NOT NULL REFERENCES properties(property_id),
  comparison_method TEXT NOT NULL CHECK (comparison_method = 'absolute_or_relative'),
  quantity_kind TEXT NOT NULL,
  absolute_tolerance_base TEXT NOT NULL,
  relative_tolerance TEXT NOT NULL,
  version_label TEXT NOT NULL,
  rationale TEXT NOT NULL,
  UNIQUE (profile_id, property_id),
  CHECK (CAST(absolute_tolerance_base AS REAL) >= 0),
  CHECK (CAST(relative_tolerance AS REAL) >= 0)
);

CREATE TABLE items_of_supply (
  item_id TEXT PRIMARY KEY,
  upn TEXT UNIQUE,
  profile_id TEXT NOT NULL REFERENCES identity_profiles(profile_id),
  preferred_name TEXT NOT NULL,
  lifecycle_state TEXT NOT NULL CHECK (lifecycle_state IN ('candidate','under_review','issued','deprecated','withdrawn')),
  fingerprint_version TEXT,
  identity_fingerprint TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reviewed_at TEXT,
  CHECK (upn IS NULL OR (
    length(upn) = 19
    AND substr(upn, 1, 5) = 'UPN1-'
    AND substr(upn, 18, 1) = '-'
    AND substr(upn, 6, 12) NOT GLOB '*[^0-9]*'
    AND substr(upn, 19, 1) GLOB '[0-9]'
  )),
  CHECK (lifecycle_state != 'issued' OR (upn IS NOT NULL AND reviewed_at IS NOT NULL))
);

CREATE TABLE upn_allocations (
  allocation_id TEXT PRIMARY KEY,
  sequence_number INTEGER NOT NULL UNIQUE CHECK (sequence_number BETWEEN 1 AND 999999999999),
  upn TEXT NOT NULL UNIQUE,
  item_id TEXT NOT NULL UNIQUE REFERENCES items_of_supply(item_id),
  allocated_by TEXT NOT NULL,
  allocated_at TEXT NOT NULL,
  allocation_state TEXT NOT NULL CHECK (allocation_state IN ('reserved','active','retired'))
);

CREATE TABLE item_reviews (
  item_review_id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL REFERENCES items_of_supply(item_id),
  decision TEXT NOT NULL CHECK (decision IN ('approved','rejected','needs_evidence')),
  rationale TEXT NOT NULL,
  reviewer TEXT NOT NULL,
  decided_at TEXT NOT NULL,
  policy_version TEXT NOT NULL,
  independence_attested INTEGER NOT NULL CHECK (independence_attested IN (0, 1)),
  CHECK (decision != 'approved' OR independence_attested = 1)
);

CREATE TABLE manufacturer_parts (
  manufacturer_part_id TEXT PRIMARY KEY,
  manufacturer_id TEXT NOT NULL REFERENCES organizations(organization_id),
  profile_id TEXT NOT NULL REFERENCES identity_profiles(profile_id),
  manufacturer_part_number TEXT NOT NULL,
  normalized_part_number TEXT NOT NULL,
  manufacturer_name TEXT,
  lifecycle_state TEXT NOT NULL CHECK (lifecycle_state IN ('active','obsolete','unknown')),
  UNIQUE (manufacturer_id, normalized_part_number)
);

CREATE TABLE supplier_offers (
  supplier_offer_id TEXT PRIMARY KEY,
  supplier_id TEXT NOT NULL REFERENCES organizations(organization_id),
  manufacturer_part_id TEXT REFERENCES manufacturer_parts(manufacturer_part_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  seller_sku TEXT NOT NULL,
  normalized_sku TEXT NOT NULL,
  offered_name TEXT NOT NULL,
  brand_name TEXT,
  order_quantity REAL CHECK (order_quantity IS NULL OR order_quantity > 0),
  order_unit TEXT NOT NULL CHECK (order_unit IN ('piece','meter','pack','box','case','pallet','unknown')),
  package_level TEXT NOT NULL CHECK (package_level IN ('each','pack','box','case','pallet','unknown')),
  lifecycle_state TEXT NOT NULL CHECK (lifecycle_state IN ('active','obsolete','unknown')),
  UNIQUE (supplier_id, normalized_sku)
);

CREATE TABLE supplier_offer_identifiers (
  supplier_offer_id TEXT NOT NULL REFERENCES supplier_offers(supplier_offer_id),
  scheme TEXT NOT NULL CHECK (scheme IN ('gtin','ean','upc','other')),
  identifier_value TEXT NOT NULL,
  identifier_authority TEXT NOT NULL,
  identifier_scope TEXT NOT NULL CHECK (identifier_scope IN ('each','pack','box','case','pallet','unknown')),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
  PRIMARY KEY (supplier_offer_id, scheme, identifier_value, identifier_authority)
);

CREATE TABLE manufacturer_part_identifiers (
  manufacturer_part_id TEXT NOT NULL REFERENCES manufacturer_parts(manufacturer_part_id),
  scheme TEXT NOT NULL CHECK (scheme IN ('manufacturer_part_number','gtin','upc','ean','other')),
  identifier_value TEXT NOT NULL,
  identifier_authority TEXT NOT NULL,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  is_primary INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0, 1)),
  PRIMARY KEY (manufacturer_part_id, scheme, identifier_value, identifier_authority)
);

CREATE TABLE external_identifiers (
  external_identifier_id TEXT PRIMARY KEY,
  namespace TEXT NOT NULL,
  identifier_value TEXT NOT NULL,
  issuing_authority TEXT NOT NULL,
  identifier_scope TEXT NOT NULL CHECK (identifier_scope IN ('item_of_supply','classification','organization','unknown')),
  verification_state TEXT NOT NULL CHECK (verification_state IN ('unverified','authority_verified','rejected')),
  verified_source_id TEXT REFERENCES sources(source_id),
  verified_at TEXT,
  notes TEXT NOT NULL DEFAULT '',
  CHECK (verification_state != 'authority_verified' OR (verified_source_id IS NOT NULL AND verified_at IS NOT NULL)),
  UNIQUE (namespace, identifier_value)
);

CREATE TABLE manufacturer_part_external_references (
  reference_id TEXT PRIMARY KEY,
  manufacturer_part_id TEXT NOT NULL REFERENCES manufacturer_parts(manufacturer_part_id),
  external_identifier_id TEXT NOT NULL REFERENCES external_identifiers(external_identifier_id),
  relationship TEXT NOT NULL CHECK (relationship IN ('claimed_same_item','cross_reference','related','unknown')),
  assertion_source_id TEXT NOT NULL REFERENCES sources(source_id),
  review_state TEXT NOT NULL CHECK (review_state IN ('unreviewed','accepted','rejected')),
  observed_at TEXT NOT NULL,
  notes TEXT NOT NULL DEFAULT '',
  UNIQUE (manufacturer_part_id, external_identifier_id, assertion_source_id)
);

CREATE TABLE external_identifier_evidence (
  evidence_id TEXT PRIMARY KEY,
  external_identifier_id TEXT NOT NULL REFERENCES external_identifiers(external_identifier_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  evidence_role TEXT NOT NULL CHECK (evidence_role IN ('definition','supplier_assertion','secondary_corroboration','authority_record')),
  source_locator TEXT NOT NULL,
  observed_at TEXT NOT NULL,
  notes TEXT NOT NULL DEFAULT '',
  UNIQUE (external_identifier_id, source_id, evidence_role)
);

CREATE TABLE manufacturer_part_reviews (
  review_id TEXT PRIMARY KEY,
  manufacturer_part_id TEXT NOT NULL REFERENCES manufacturer_parts(manufacturer_part_id),
  decision TEXT NOT NULL CHECK (decision IN ('accepted','rejected','needs_evidence')),
  rationale TEXT NOT NULL,
  reviewer TEXT NOT NULL,
  decided_at TEXT NOT NULL,
  policy_version TEXT NOT NULL
);

CREATE TABLE observations (
  observation_id TEXT PRIMARY KEY,
  manufacturer_part_id TEXT REFERENCES manufacturer_parts(manufacturer_part_id),
  item_id TEXT REFERENCES items_of_supply(item_id),
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  source_locator TEXT NOT NULL,
  observed_name TEXT,
  observed_part_number TEXT,
  observed_at TEXT NOT NULL,
  raw_payload_sha256 TEXT,
  review_state TEXT NOT NULL CHECK (review_state IN ('unreviewed','accepted','rejected','superseded')),
  CHECK (manufacturer_part_id IS NOT NULL OR item_id IS NOT NULL)
);

CREATE TABLE specification_values (
  specification_id TEXT PRIMARY KEY,
  observation_id TEXT NOT NULL REFERENCES observations(observation_id),
  property_id TEXT NOT NULL REFERENCES properties(property_id),
  raw_value TEXT NOT NULL,
  normalized_text TEXT,
  normalized_number TEXT,
  unit_id TEXT REFERENCES units(unit_id),
  qualifier TEXT,
  UNIQUE (observation_id, property_id, raw_value),
  UNIQUE (specification_id, property_id)
);

CREATE TABLE specification_value_mappings (
  mapping_id TEXT PRIMARY KEY,
  specification_id TEXT NOT NULL,
  property_id TEXT NOT NULL,
  controlled_value_id TEXT NOT NULL,
  mapping_basis TEXT NOT NULL CHECK (
    mapping_basis IN ('source_exact','manufacturer_definition','standard_crosswalk','expert_interpretation')
  ),
  mapping_state TEXT NOT NULL CHECK (mapping_state IN ('proposed','approved','rejected')),
  rationale TEXT NOT NULL,
  proposed_by TEXT NOT NULL,
  proposed_at TEXT NOT NULL,
  reviewer TEXT,
  reviewed_at TEXT,
  policy_version TEXT NOT NULL,
  CHECK (length(trim(rationale)) > 0),
  CHECK (length(trim(proposed_by)) > 0),
  CHECK (length(trim(policy_version)) > 0),
  FOREIGN KEY (specification_id, property_id)
    REFERENCES specification_values(specification_id, property_id),
  FOREIGN KEY (controlled_value_id, property_id)
    REFERENCES controlled_values(controlled_value_id, property_id),
  UNIQUE (specification_id, controlled_value_id),
  CHECK (
    mapping_state != 'approved'
    OR (
      reviewer IS NOT NULL
      AND reviewed_at IS NOT NULL
      AND reviewer != proposed_by
    )
  )
);

CREATE TABLE aliases (
  alias_id TEXT PRIMARY KEY,
  item_id TEXT NOT NULL REFERENCES items_of_supply(item_id),
  alias_type TEXT NOT NULL CHECK (alias_type IN ('common_name','trade_name','legacy_number','external_identifier','translation')),
  alias_value TEXT NOT NULL,
  language_code TEXT,
  source_id TEXT REFERENCES sources(source_id),
  UNIQUE (item_id, alias_type, alias_value, language_code)
);

CREATE TABLE match_candidates (
  match_candidate_id TEXT PRIMARY KEY,
  left_part_id TEXT NOT NULL REFERENCES manufacturer_parts(manufacturer_part_id),
  right_part_id TEXT NOT NULL REFERENCES manufacturer_parts(manufacturer_part_id),
  algorithm_version TEXT NOT NULL,
  score REAL NOT NULL CHECK (score BETWEEN 0 AND 1),
  blocking_keys TEXT NOT NULL,
  generated_at TEXT NOT NULL,
  CHECK (left_part_id < right_part_id),
  UNIQUE (left_part_id, right_part_id, algorithm_version)
);

CREATE TABLE pair_screenings (
  screening_id TEXT PRIMARY KEY,
  left_part_id TEXT NOT NULL REFERENCES manufacturer_parts(manufacturer_part_id),
  right_part_id TEXT NOT NULL REFERENCES manufacturer_parts(manufacturer_part_id),
  profile_id TEXT NOT NULL REFERENCES identity_profiles(profile_id),
  algorithm_version TEXT NOT NULL,
  blocking_keys TEXT NOT NULL,
  compared_properties TEXT NOT NULL,
  matched_properties TEXT NOT NULL,
  conflicting_properties TEXT NOT NULL,
  missing_properties TEXT NOT NULL,
  score REAL NOT NULL CHECK (score BETWEEN 0 AND 1),
  result TEXT NOT NULL CHECK (result IN ('candidate','hard_conflict','insufficient_evidence')),
  generated_at TEXT NOT NULL,
  CHECK (left_part_id < right_part_id),
  UNIQUE (left_part_id, right_part_id, algorithm_version)
);

CREATE TABLE equivalence_decisions (
  decision_id TEXT PRIMARY KEY,
  match_candidate_id TEXT NOT NULL REFERENCES match_candidates(match_candidate_id),
  decision TEXT NOT NULL CHECK (decision IN ('same_item','different_item','insufficient_evidence')),
  rationale TEXT NOT NULL,
  reviewer TEXT NOT NULL,
  decided_at TEXT NOT NULL,
  policy_version TEXT NOT NULL
);

CREATE TABLE item_memberships (
  item_id TEXT NOT NULL REFERENCES items_of_supply(item_id),
  manufacturer_part_id TEXT NOT NULL REFERENCES manufacturer_parts(manufacturer_part_id),
  equivalence_decision_id TEXT REFERENCES equivalence_decisions(decision_id),
  part_review_id TEXT REFERENCES manufacturer_part_reviews(review_id),
  valid_from TEXT NOT NULL,
  valid_to TEXT,
  CHECK ((equivalence_decision_id IS NOT NULL) != (part_review_id IS NOT NULL)),
  PRIMARY KEY (item_id, manufacturer_part_id, valid_from)
);

CREATE UNIQUE INDEX idx_active_membership_part
  ON item_memberships(manufacturer_part_id) WHERE valid_to IS NULL;

CREATE TABLE application_interchangeability (
  interchangeability_id TEXT PRIMARY KEY,
  from_item_id TEXT NOT NULL REFERENCES items_of_supply(item_id),
  to_item_id TEXT NOT NULL REFERENCES items_of_supply(item_id),
  application_context TEXT NOT NULL,
  decision TEXT NOT NULL CHECK (decision IN ('approved','not_approved','conditional','unknown')),
  constraints_text TEXT NOT NULL,
  source_id TEXT REFERENCES sources(source_id),
  reviewer TEXT,
  reviewed_at TEXT,
  CHECK (from_item_id != to_item_id)
);

CREATE TABLE ingestion_runs (
  run_id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL REFERENCES sources(source_id),
  started_at TEXT NOT NULL,
  completed_at TEXT,
  software_version TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('running','completed','failed','partial')),
  records_seen INTEGER NOT NULL DEFAULT 0,
  records_accepted INTEGER NOT NULL DEFAULT 0,
  records_rejected INTEGER NOT NULL DEFAULT 0,
  error_summary TEXT
);

CREATE INDEX idx_observations_source ON observations(source_id);
CREATE INDEX idx_specs_property ON specification_values(property_id);
CREATE INDEX idx_parts_normalized_number ON manufacturer_parts(normalized_part_number);
CREATE INDEX idx_items_fingerprint ON items_of_supply(identity_fingerprint);
