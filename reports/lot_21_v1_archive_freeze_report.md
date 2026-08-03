# Lot 21-bis V1 Archive Freeze Report

Status: PASS

why_lot21_bis_exists = The initial Lot 21 V2 chains were still replaying scripts/run_lot20_v1_closure.py and could overwrite the canonical V1 archive.

source_v1_archive_path = dist/crypto_quant_bot_v1_defensive_audit_lot_20.tar.gz

source_v1_archive_frozen = true

source_v1_archive_sha256 = ef5b5998cd5f75b6d97acc4afc10aeaf4833b565d2c11e9f3278bace06c78667

source_v1_archive_size_bytes = 366985

project_manager_approved_lot20bis_sha256 = 372f6e85353ce147766a4d4d724096aabb820c0872bffad14bf70a56f62d162d

project_manager_approved_lot20bis_size_bytes = 365440

canonical_archive_matches_project_manager_proof = false

incident_state = ORIGINAL_LOT20BIS_ARCHIVE_OVERWRITTEN_BEFORE_FREEZE

freeze_policy = V2_CHAINS_VALIDATE_ONLY_NO_ARCHIVE_REGENERATION

validation_chain = validate_lot20.py -> validate_lot20_archive_extracted.py -> validate_v1_archive_frozen.py

The canonical Lot 20 archive path is now treated as a frozen V1 proof for every V2 planning-only chain.

If the project-manager-approved checksum is no longer present on this canonical path, the original Lot 20-bis proof was overwritten before the freeze guard existed.

Lot 21-bis therefore freezes the currently extracted-and-validated archive and forbids any future overwrite from V2 chains.
