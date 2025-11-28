Security Policy — LUMIN / ODG / ACI4A

This document defines the official security and responsible disclosure policy for LUMIN, the deterministic ethical-governance engine based on the ODG and ACI4A architectures, developed and maintained by AHALASeC.
LUMIN is safety-critical infrastructure. Any vulnerability may have civilizational-scale implications. All security reports are treated with maximum seriousness and confidentiality.

1. Supported Versions
Security patches are provided for:
→ The latest stable release of the LUMIN engine
→ Core ODG / ACI4A framework
→ VSI subsystem
→ Security-relevant documentation

Older branches receive fixes only if the vulnerability is judged severe or existential in nature.

2. Reporting a Vulnerability
Never open a public GitHub issue for security problems.
Report privately via one of the following channels (in order of preference):

→ Email: comercial@ahalasec.com (PGP key available on request)
→ GitHub Private Vulnerability Reporting (Security tab → “Report a vulnerability”), when available

Include as much of the following as possible:
→ Clear description and title
→ Steps to reproduce
→ Proof-of-concept or exploit code (if safe to share)
→ Estimated impact and attack vector
→ Affected component(s) and version
→ Environment details (OS, Python version, backend LLM, etc.)
→ Whether the issue compromises determinism, ledger integrity, FSM axioms, or ethical governance

You can expect an acknowledgment within 48 hours (usually faster).

3. What Qualifies as a Security Vulnerability

Report anything that can compromise the system’s ethical, symbolic, or deterministic integrity.

Governance Bypass
→ Bypassing or weakening the Safeguard layer
→ Modifying or disabling FSM axioms
→ Triggering unintended state transitions
→ Inducing alignment drift or ethical deterioration

Ledger & Symbolic State Integrity
→ Corruption or tampering of memory ledgers
→ Integrity check failures
→ Symbolic rehydration failures
→ Unauthorized ledger manipulation

Execution Pipeline

→ Bypass of any ODG layer (MIE Guardian, Safeguard, VSI, Smoother, etc.)
→ Missed detection of high-risk intent
→ Non-deterministic ethical outcomes under identical conditions

External Interfaces
→ Injection attacks
→ Model-adapter exploits
→ Authentication or authorization flaws
→ Insecure API endpoints (current or future)

Systemic Risk
→ Predictable manipulation patterns
→ Dialogue escalation
→ Collapse of coherence under adversarial scenarios

When in doubt — report it.

4. Non-Security Issues
→ Use standard GitHub Issues for:
→ Documentation mistakes
→ Installation errors
→ Cosmetic bugs
→ Performance issues
→ Non-deterministic behavior originating from external LLMs

5. Responsible Disclosure Process

AHALASeC follows a strict responsible disclosure protocol:
→ Researcher reports privately
→ AHALASeC triage validates the issue
→ A fix is developed and internally audited
→ Coordinated public release (patch + advisory)
→ Credit is given to the reporter (unless anonymity is requested)

Public disclosure before an official fix is strictly prohibited.

6. Core Security Principles

All patches, PRs, and architecture changes must respect:
→ Radical transparency
→ Strict determinism
→ Full auditability
→ Symbolic reasoning over statistical heuristics
→ Civilizational safety over convenience
→ Zero tolerance for silent or undocumented failures

LUMIN is not ordinary software.
It is ethical infrastructure for the post-LLM era.

7. Contact and Urgent Reports

→ Primary contact: comercial@ahalasec.com
For urgent or high-severity vulnerabilities, use the subject line:

URGENT — ODG/ACI4A Critical Vulnerability

Summary

This policy protects the integrity, determinism, and civilizational alignment of LUMIN.
By following it, researchers and contributors defend the future of governable artificial intelligence.

Developed and enforced by
AHALASeC — Autonomous Human-Aligned Logic Architecture Laboratory for Safety, Ethics, and Civilization
