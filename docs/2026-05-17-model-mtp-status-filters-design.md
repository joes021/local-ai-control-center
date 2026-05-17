# Model MTP Status And Filters Design

## Goal

Make model cards and model filtering clearer by showing whether a model has MTP support, does not have MTP support, or has unknown MTP status.

This is especially important for Unsloth and Qwen model variants where the user wants to quickly distinguish:

- models without MTP
- models with MTP
- models where MTP status is unknown

## User-Facing Changes

### Model Card Metadata

Each model card will display a new field:

- `MTP status: bez MTP`
- `MTP status: ima MTP`
- `MTP status: nepoznato`

This should appear alongside the other model detail fields such as size, disk usage, GPU threshold, and RAM guidance.

### New Filters

The `Models` filter bar will gain three new filters:

- `Bez MTP`
- `Ima MTP`
- `Nepoznato MTP`

These filters should work the same way as the existing filters:

- `Svi`
- `Skinuti`
- `Aktivni`

The selected filter applies across all groups:

- curated
- local
- huggingFace
- unsloth

The filtered result should be reflected in both:

- `Rezultati filtera`
- grouped sections below

## Metadata Rules

The backend will normalize MTP status to one of three values:

- `no-mtp`
- `has-mtp`
- `unknown`

The frontend will render these as:

- `bez MTP`
- `ima MTP`
- `nepoznato`

## Classification Rules

### `bez MTP`

Use this status when we know the model is explicitly non-MTP.

Examples:

- Unsloth models from the non-MTP GGUF repo
- curated models explicitly marked as non-MTP
- models whose source metadata is explicitly marked as non-MTP

### `ima MTP`

Use this status when we know the model is explicitly an MTP variant.

Examples:

- models from MTP-specific repos
- models whose filename or source metadata explicitly marks them as MTP

### `nepoznato`

Use this when we do not have a reliable signal.

Examples:

- manually added local GGUF files
- old custom registry entries with no MTP metadata
- Hugging Face or other external models without enough source labeling

## Scope Boundaries

This change is a metadata and UX improvement only.

It must not:

- block model add/download/activate/delete flows
- change recommendation logic by itself
- change runtime behavior by itself

It only affects:

- model metadata presentation
- filtering behavior

## Suggested Data Shape

Each model entry should carry:

- `mtpStatus: "no-mtp" | "has-mtp" | "unknown"`
- `mtpStatusLabel: "bez MTP" | "ima MTP" | "nepoznato"`

This keeps backend logic explicit and frontend rendering simple.

## Implementation Notes

### Backend

Update model normalization/build logic to set MTP metadata for:

- curated models
- Unsloth recommended models
- custom Hugging Face models
- custom local models

Primary signal order:

1. explicit metadata field
2. known source/repo classification
3. filename hint
4. fallback to `unknown`

### Frontend

Update:

- `ModelEntry` type
- model card rendering
- filter state and filtering logic
- `Rezultati filtera` view

## Success Criteria

The feature is successful when:

1. every visible model shows an MTP status
2. the user can filter by:
   - `Bez MTP`
   - `Ima MTP`
   - `Nepoznato MTP`
3. Unsloth non-MTP models appear correctly under `Bez MTP`
4. MTP variants appear correctly under `Ima MTP`
5. models without enough metadata fall under `Nepoznato MTP`
