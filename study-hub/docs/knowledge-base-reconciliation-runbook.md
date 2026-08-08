# Knowledge Base Reconciliation Runbook

1. Create a current dry-run report:

   ```powershell
   $env:PYTHONIOENCODING='utf-8'
   py -3 backend/scripts/reconcile_knowledge_base.py
   ```

2. Review the generated `backend/data/operations/reconciliation-*.json`. Do not approve any unresolved document or any cross-namespace short-link/long-link comparison.

3. After explicit approval, create a separate JSON file containing exactly the approved keys:

   ```json
   { "approved_source_keys": ["douyin:short:ZWW0XlOlwdM"] }
   ```

4. Apply the reviewed selection. The script runs `PRAGMA integrity_check`, creates `backend/data/backups/study_hub-before-reconciliation-*.db`, then changes only approved duplicate rows to `archived_duplicate`.

   ```powershell
   py -3 backend/scripts/reconcile_knowledge_base.py --apply --approved-report path/to/approved.json
   ```

5. Verify the new dry-run has no remaining duplicate group for each approved key. To restore, use the backup database or change the archived rows back to `document_status='active'` and rebuild their vectors before exposing them again.
