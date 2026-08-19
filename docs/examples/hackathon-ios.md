# Native iOS hackathon

Input: `I have four hours to build a native iOS city travel app.`

Expected recommendation: Hackathon Mode. The QA session narrows one travel decision, defines one hero moment, selects mock-first implementation, allows one critical integration, creates a four-hour MVP Build Plan with a written demo script, and offers implementation, save, export, or GitHub delivery.

The confirmed answers compile to this, and every gate downstream reads it rather than the word "hackathon":

```json
{
  "version": "workflow_profile/v1",
  "mode": "hackathon",
  "risk_tier": "low",
  "delivery_target": "local_demo",
  "planning": {"spec_gate": "warn", "max_behaviors": 9},
  "design": {"gate": "advisory"},
  "development": {"slicing": "flow", "refactor_phase": false, "pull_request_required": false, "merge_policy": "ask"},
  "testing": {"automated_required": "smoke", "manual_required": true, "coverage_target": null, "ci_required": false},
  "review": {"independent_required": false, "lane": "none"},
  "deployment": {"allowed": false},
  "safety_floor": ["demo-data-labeled-as-fake", "input-validation-on-demo-path", "secrets-out-of-repo"],
  "revisit_when": "the event is over"
}
```

Concretely: an open ambiguity warns instead of blocking the brief, the spec is capped at nine behaviors, a passing self review clears the checkpoint, `workflow-init` emits the single-job CI stub rather than the full ladder, the generated card says git is a recovery mechanism rather than demanding a PR per task, and no deployment is planned or permitted. What it does *not* relax is the safety floor — the itinerary fixtures are visibly fake, the API key stays out of the repository, and the demo path validates its inputs.

Note the platform call this produces. `references/platform-decision.md`'s Hackathon override measures minutes to a running app on the demo device including setup, so native SwiftUI wins here only because the demoer is already on a Mac with Xcode — the same idea from someone without that toolchain gets Expo.

Reproduce it with:

```bash
python3 scripts/init_project.py "City Travel MVP" --mode hackathon
python3 scripts/workflow_profile.py --mode hackathon
```
