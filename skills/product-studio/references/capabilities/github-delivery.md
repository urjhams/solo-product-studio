# github-delivery

Purpose: convert an approved plan into repository-aware, dependency-aware work items.

Inputs: approved artifact, repository, existing issues/milestones/labels, provider capabilities.

Outputs: repository summary, duplicate analysis, milestone/label proposals, dependency graph, issues with goal/context/scope/acceptance/testing/dependencies/out-of-scope/artifact references, publish status and references.

Gate: proposal is reviewed before publishing unless immediate publishing was explicitly requested. Local export must preserve all metadata.
