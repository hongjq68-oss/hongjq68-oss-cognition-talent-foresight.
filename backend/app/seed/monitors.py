"""Starter discovery monitors: one per scarce capability the banking scenario needs, phrased as public-work searches."""

def M(id, name, cap, market, **queries):
    return dict(id=id, name=name, capability_id=cap, market=market, queries=queries)


MONITORS = [
    M("m-agent-evals-sg", "Agent & eval builders (Singapore)", "agentic_systems", "SG",
      github="llm agent evaluation", hn="agent evals", devto="agents", arxiv="LLM agent evaluation"),
    M("m-cobol-apac", "COBOL / mainframe modernisers", "legacy_modernisation", None,
      github="cobol", hn="cobol", devto="cobol", arxiv="COBOL code translation"),
    M("m-devplatform-sg", "Developer-platform builders (Singapore)", "dev_productivity", "SG",
      github="developer platform", hn="developer tools", devto="platformengineering"),
    M("m-appsec-apac", "AppSec remediation tooling builders", "appsec_remediation", None,
      github="vulnerability remediation", hn="security scanner", devto="appsec"),
    M("m-japan-devtools", "Japan devtools & agent builders", "agentic_systems", "JP",
      github="llm agent", devto="japanese"),
]
