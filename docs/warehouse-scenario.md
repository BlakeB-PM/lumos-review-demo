# Warehouse fixture

Use `--scenario warehouse` on the connector, report and reset commands. This fixture has different grants, exceptions and unresolved questions, served by the same workflow and UI as the default data.

The optional personal workspace inbox can provide leads for checking scoped exceptions and current responsibility. It is evidence, not a prescribed conclusion. Expired or missing approvals should remain unresolved until supported. The reviewer can defer those grants.

To exercise an evidence change after preview, run:

```sh
python server/src/main.py advance-snapshot --scenario warehouse
```

The affected grant requires a fresh proposal and confirmation; valid rows in the original batch can still record. Text-only and panel-capable hosts use the same tools. No starter phrase resets state.
