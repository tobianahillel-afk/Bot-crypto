# Data Versioning Policy

Every dataset must be uniquely identified, versioned and traceable.

Required dataset metadata:

```text
dataset_id
dataset_name
pair
timeframe
source
layer
schema_version
data_version
start_timestamp
end_timestamp
row_count
created_at
lineage_id
checksum
quality_flag
validation_status
```

## Dataset ID

`dataset_id` identifies a concrete dataset artifact. Two files with different content must not
share the same `dataset_id`.

## Lineage ID

`lineage_id` links derived artifacts to their origin. A bronze dataset parsed from a raw CSV must
keep a lineage relationship to the raw file.

## Quality flag

`quality_flag` summarizes whether a dataset is usable:

```text
valid       = can be used by later non-trading modules
suspicious  = can be inspected but should not be trusted blindly
invalid     = cannot be used
```

## Raw immutable rule

Never modify `data/raw/` in place. Generate a new dataset version instead.
