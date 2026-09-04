# AGENTS_DOCS_ENV.md

This document contains guidelines related to post-development documentation (such as writing READMEs) and the local development environment (managing virtual environments). These rules have been separated from the constantly injected rules (`AGENTS.md`) to save tokens during agent execution.

---

## 1. README and Documentation Rules

- **Avoid Tautology**: Avoid trivial, tautological, or repetitive explanations in README documents or CLI option descriptions (e.g., "A is A").
  - *Bad example: `--dialect: The dialect to be used.`*
  - *Good example: `--dialect: The target database engine syntax and format (e.g., duckdb, postgres) where the generated queries will be executed.`*
- **Provide Detailed Documentation**: Write comprehensive documentation in Korean, including detailed explanations of key terms, concrete execution mechanisms, and practical examples, so that users can clearly understand the tools' roles, input domain meanings, and scope of configurations.

---

## 2. Python Virtual Environment and Workspace Management Rules

- **Isolate Subproject Virtual Environments**: Each subproject (e.g., `llm_api`, `sql_to_dbt_yml_api`) has its own virtual environment (e.g., `venv312` or `.venv`) inside its respective directory. Do not install packages or run utilities unrelated to the subproject's functionality inside the subproject's virtual environment.
- **Workspace Configuration**: In a multi-root workspace structure where multiple subprojects exist, create a `{workspace_name}.code-workspace` configuration file at the workspace root for integrated management and clear workspace switching.

