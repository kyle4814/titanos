schema: titanos_incident
version: "1.0"
status: draft
purpose: "incident contract"
required:
  - id
  - version
  - status
  - inputs
  - outputs
  - dependencies
  - evidence
  - limitations
states:
  - proposed
  - active
  - verified
  - superseded
validation:
  - schema_valid
  - provenance_present
  - acceptance_criteria_present
  - audit_event_present
