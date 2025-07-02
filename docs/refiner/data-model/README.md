# eCR Refiner Data Model - v0 Proposal

The goal of this document is to provide a baseline for what the Refiner's v0 data model will look like. While this may change over time, the goal is to give us a starting place.

Please see the DBML code below, which can be viewed and modified at [https://dbdiagram.io/d](https://dbdiagram.io/d).

[Syntax for DBML can be found here](https://dbml.dbdiagram.io/home).

```
// Use DBML to define your database structure
// Docs: https://dbml.dbdiagram.io/docs

Table jurisdiction {
  id integer [primary key]
  name text
  created_at timestamp
}

Table user {
  id integer [primary key]
  jurisdiction_id integer
  email text [unique, not null]
  created_at timestamp
}

Table condition {
  id integer [primary key]
  snomed_code text
  name text
}

Table condition_group {
  id integer [primary key]
  name text [not null]
  jurisdiction_id integer
}

Table condition_group_condition {
  condition_group_id integer
  condition_id integer

  indexes {
    (condition_group_id, condition_id) [pk]
  }
}

Table grouper {
  id integer [primary key]
  display_name text
  loinc_codes jsonb
  snomed_codes jsonb
  icd10_codes jsonb
  rxnorm_codes jsonb
}

Table tes_rs_grouper {
  grouper_id integer
  snomed_code text
}

Table filter {
  id integer [primary key]
  condition_group_id integer
  jurisdiction_id integer
  display_name text
  loinc_codes jsonb
  snomed_codes jsonb
  icd10_codes jsonb
  rxnorm_codes jsonb
  is_active boolean [default: true, not null]
}


Table filter_grouper {
  filter_id integer
  grouper_id integer

  indexes {
    (filter_id, grouper_id) [pk]
  }
}

Ref: filter.condition_group_id - condition_group.id
Ref: jurisdiction.id < filter.jurisdiction_id

Ref: tes_rs_grouper.grouper_id < grouper.id
Ref: jurisdiction.id > user.jurisdiction_id
Ref: filter.id < filter_grouper.filter_id
Ref: grouper.id < filter_grouper.grouper_id
Ref: condition_group_condition.condition_group_id > condition_group.id
Ref: condition_group_condition.condition_id > condition.id
Ref: jurisdiction.id < condition_group.jurisdiction_id
```
