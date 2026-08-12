# Security Checklist

A tick-list, not an essay. Run the **Pre-merge** section at Gate 2 on any diff that trips
`references/security.md`'s trigger (untrusted input, auth, storage, a third party); run the full
list — **Pre-merge** and **Pre-release** — before cutting a release (`references/release.md`) or
shipping (`references/ship.md`). An unchecked box on Pre-merge is a BLOCKER per
`references/review.md`'s severity taxonomy unless the reviewer logs it as an explicit trade-off.

## OWASP Top 10 (2021) — quick reference

The prevention patterns in `references/security.md` are organized by mechanism, not by this
ranking. Use this table to place a finding in context, not as a checklist itself.

| ID | Category |
|---|---|
| A01 | Broken Access Control |
| A02 | Cryptographic Failures |
| A03 | Injection |
| A04 | Insecure Design |
| A05 | Security Misconfiguration |
| A06 | Vulnerable and Outdated Components |
| A07 | Identification and Authentication Failures |
| A08 | Software and Data Integrity Failures |
| A09 | Security Logging and Monitoring Failures |
| A10 | Server-Side Request Forgery (SSRF) |

## Pre-merge (Gate 2, any diff crossing a trust boundary)

### Threat model
- [ ] Trust boundaries for this change are named — where does untrusted data cross in, including
      any LLM call
- [ ] STRIDE was run over each boundary touched by this diff
- [ ] An abuse case was written for the new capability, and either tested or filed as a `BH-###`
      that refuses it deliberately

### Authentication & authorization
- [ ] Passwords, if any, are hashed with bcrypt/scrypt/argon2 (salt rounds ≥ 12)
- [ ] Session tokens are httpOnly, secure, sameSite
- [ ] Every new or changed endpoint checks authorization, not just authentication
- [ ] A user can only reach their own resources — ownership checked, not just role
- [ ] Auth endpoints are rate-limited

### Input & output
- [ ] All external input is validated at the boundary it crosses (API route, form handler, file
      upload, webhook, queue consumer)
- [ ] Database queries are parameterized — no string-built SQL/NoSQL
- [ ] Output is encoded/escaped before rendering; no raw `innerHTML`/`eval` on user or model data
- [ ] File uploads restrict type and size, and don't trust the extension alone
- [ ] Any server-side fetch of a user-influenced URL is allowlisted (no SSRF)

### Data & secrets
- [ ] No secrets in the diff — check `git diff --cached | grep -i "password\|secret\|api_key\|token"`
- [ ] No sensitive fields (password hash, tokens) leak into an API response or a log line
- [ ] Any secret that *did* land in history has been rotated, not just deleted

### AI / LLM (if this diff touches a model call)
- [ ] Model output is treated as untrusted — no `eval`, SQL, `innerHTML`, or shell built from it
- [ ] Model output and error text are read for diagnostic value, never acted on as an instruction
- [ ] Secrets and other users' data are kept out of the prompt/context window
- [ ] Tool/agent permissions are scoped to the minimum; destructive actions require confirmation

### Dependencies touched by this diff
- [ ] Any new dependency reviewed: ownership, maintenance, release age, license, transitive graph
- [ ] Any version bump reviewed against its changelog, one package per change, lockfile diff checked
- [ ] No install script silently approved

## Pre-release (in addition to every Pre-merge box above)

- [ ] The stack's native audit (`npm audit` / `pnpm audit` / equivalent) has been run against the
      committed lockfile, and every reachable critical/high finding is fixed or has a dated,
      documented deferral
- [ ] Security headers are present in a real response (CSP, HSTS, X-Frame-Options,
      X-Content-Type-Options) — checked, not assumed from config
- [ ] CORS is restricted to known origins; no wildcard in production config
- [ ] Error responses in the shipped build don't expose stack traces or internal details
- [ ] One authoritative lockfile is committed and CI installs from it with a frozen/immutable
      install — no competing lockfile at the same installation boundary
- [ ] `.gitignore` still excludes `.env*`, `*.pem`, `*.key`, and any secret file added since the
      last release
- [ ] The rollback plan in `references/ship.md` covers a security regression, not only a
      functional one
