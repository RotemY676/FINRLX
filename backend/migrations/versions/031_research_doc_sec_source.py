"""Phase 18.3 — research_documents source + SEC EDGAR metadata.

Extends the Phase 17.0 table so the same row can hold both
operator-uploaded PDFs and SEC-auto-fetched 10-K / 10-Q filings.

What this adds:
  - `source` (String(20), NOT NULL, default 'upload') — existing
    rows backfill to 'upload' via server_default.
  - `sec_accession_no` (String(32), nullable) — SEC's globally
    unique filing ID, used as the dedup key for sec_auto rows.
  - `sec_form` (String(20), nullable) — denormalized "10-K"/"10-Q"
    for FE badges without joining to an EDGAR cache.
  - `sec_period_of_report` (Date, nullable) — reporting period end,
    used by the FE to sort quarters in calendar order.
  - `external_url` (String(1024), nullable) — pointer to the original
    at sec.gov. We don't cache the raw HTML locally (per the Phase 18
    storage decision); this is the "Open at SEC" link.
  - Composite UNIQUE INDEX on (ticker, sec_accession_no) for idempotent
    re-ingest. Postgres + SQLite both treat NULLs as DISTINCT in
    composite unique constraints, so multiple uploads (sec_accession_no
    NULL) coexist while sec_auto rows are deduped per ticker.

What this changes:
  - `storage_path` becomes nullable. sec_auto rows don't have a local
    file (storage_path NULL), only an external_url. Operator uploads
    still set it as before. The application layer enforces "uploads
    have storage_path, sec_auto rows have external_url" — the DB
    only enforces that ONE of them exists per row would require a
    check constraint, which we skip for forward compatibility (a
    future source like `news_auto` may have neither).

Both Postgres and SQLite handle this via Alembic's batch_alter_table
(SQLite needs the table rebuild for the storage_path nullability flip;
Postgres doesn't, but batch mode is a no-op on Postgres so this is
safe everywhere).

Revision string MUST be <=32 chars per the migration-030 lesson; this
one is 28 chars.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "031_research_doc_sec_source"
down_revision: Union[str, None] = "030_doc_analyses_budget"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("research_documents") as batch:
        # Add the new columns. `source` is NOT NULL with a server default
        # so existing rows backfill cleanly to 'upload' without a manual
        # UPDATE step. The other three are nullable (they're populated
        # only when an EDGAR auto-ingest job inserts the row).
        batch.add_column(
            sa.Column(
                "source",
                sa.String(20),
                nullable=False,
                server_default="upload",
            )
        )
        batch.add_column(sa.Column("sec_accession_no", sa.String(32), nullable=True))
        batch.add_column(sa.Column("sec_form", sa.String(20), nullable=True))
        batch.add_column(sa.Column("sec_period_of_report", sa.Date(), nullable=True))
        batch.add_column(sa.Column("external_url", sa.String(1024), nullable=True))

        # storage_path was NOT NULL in migration 029. Relax for sec_auto
        # rows that have no local file. Existing upload rows keep their
        # values; their non-null storage_path is preserved.
        batch.alter_column("storage_path", existing_type=sa.String(512), nullable=True)

        # Composite UNIQUE index serves two purposes:
        #   (1) Dedup: re-running auto-ingest for the same ticker+
        #       accession is a no-op (the INSERT errors and the caller
        #       skips). Sqlite + Postgres treat NULL as distinct, so
        #       operator uploads (accession NULL) coexist freely.
        #   (2) Lookup: the FE's "list sec_auto docs for ticker X"
        #       query gets a clean index scan via the leading column.
        batch.create_index(
            "uq_research_documents_sec_dedup",
            ["ticker", "sec_accession_no"],
            unique=True,
        )


def downgrade() -> None:
    with op.batch_alter_table("research_documents") as batch:
        batch.drop_index("uq_research_documents_sec_dedup")
        # Put storage_path back to NOT NULL. Any sec_auto rows with NULL
        # storage_path inserted while this migration was live would
        # break the downgrade — so we backfill them to an empty string
        # first. That's lossy (we lose the "this was an external doc"
        # signal at the row level) but the columns we're about to drop
        # also carry that signal, so the downgrade is internally
        # consistent: after rollback the row simply looks like a normal
        # upload with no file content.
        batch.execute(
            "UPDATE research_documents SET storage_path = '' WHERE storage_path IS NULL"
        )
        batch.alter_column("storage_path", existing_type=sa.String(512), nullable=False)
        batch.drop_column("external_url")
        batch.drop_column("sec_period_of_report")
        batch.drop_column("sec_form")
        batch.drop_column("sec_accession_no")
        batch.drop_column("source")
