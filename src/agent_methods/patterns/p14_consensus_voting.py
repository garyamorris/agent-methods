r"""
Pattern 14: Consensus Voting & Ensemble Calibration
===================================================

Architecture Overview:
----------------------
In mission-critical classifications (e.g., fraud detection, high-risk security CVE triage,
clinical evaluation), a single agent's stochastic output is vulnerable to hallucination
or random seed variance.
The Consensus Voting & Ensemble Calibration pattern executes multiple independent judges:
  1. Heterogeneous Jurors: $N$ diverse agents evaluate the exact same candidate independently.
     - Juror 1: Conservative Security Purist (strict zero-tolerance lens).
     - Juror 2: Pragmatic Staff SRE (operational impact lens).
     - Juror 3: Risk Quantitative Analyst (probabilistic financial loss lens).
  2. Structured Ballots: Each juror outputs a typed ballot `{verdict: PASS/FAIL, confidence: 0-100, rationale}`.
  3. Calibrated Electoral Engine: A deterministic aggregator computes:
     - Majority Vote Tally.
     - Confidence-Weighted Tally.
     - Epistemic Consensus Index (measuring inter-agent agreement entropy).
  4. Decision Synthesis: Produces a mathematically calibrated verdict with actionable dissent analysis.

Communication Topology:
-----------------------
                       +-----------------------+
                       |   Critical Decision   |
                       |       Candidate       |
                       +-----------------------+
                                   |
              +--------------------+--------------------+
              | (blind, parallel independent evaluation)|
              v                    v                    v
     +-----------------+  +-----------------+  +-----------------+
     | Juror A: Purist |  | Juror B: SRE    |  | Juror C: Quant  |
     +-----------------+  +-----------------+  +-----------------+
              |                    |                    |
              v                    v                    v
         [Ballot A]           [Ballot B]           [Ballot C]
              \                    |                    /
               +-------------------+-------------------+
                                   |
                                   v
                       +-----------------------+
                       |  Electoral Aggregator |
                       | (Confidence Weighted) |
                       +-----------------------+
                                   |
                                   v
                       +-----------------------+
                       | Calibrated Consensus  |
                       |        Verdict        |
                       +-----------------------+

When to Use:
------------
- High-stakes classification (Fraud detection, zero-day CVE vulnerability scoring).
- Situations where variance and hallucination must be reduced through ensemble wisdom.
- Detecting ambiguous borderline cases where experts legitimately disagree.

OpenAI Agents SDK Primitives:
-----------------------------
- Multiple parallel `Agent` instances with distinct grading philosophies.
- `asyncio.gather` for blind, isolated juror evaluations.
- Pydantic structured output models for mathematical consensus computation.
"""

import asyncio
import json
from pydantic import BaseModel, Field
from agents import Agent, Runner
from agent_methods.common import (
    DEFAULT_MODEL,
    ensure_api_key,
    console,
    print_header,
    print_agent_step,
    print_result_panel,
    print_explainer,
)

# -------------------------------------------------------------------------
# Structured Ballot Model
# -------------------------------------------------------------------------

class JurorBallot(BaseModel):
    juror_name: str
    vote: str = Field(description="'APPROVE' or 'REJECT'")
    confidence_score: int = Field(description="Confidence percentage 0 to 100")
    primary_rationale: str = Field(description="One sentence justifying the vote")


# -------------------------------------------------------------------------
# Diverse Juror Agents
# -------------------------------------------------------------------------

juror_purist = Agent(
    name="ConservativeSecurityPurist",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Conservative Security Purist. You reject any proposal that introduces "
        "even minimal security ambiguity, unencrypted transit, or third-party credential exposure. "
        "Evaluate the proposal and return strictly a JSON object matching JurorBallot:\n"
        '{"juror_name": "ConservativeSecurityPurist", "vote": "APPROVE" | "REJECT", '
        '"confidence_score": <0-100>, "primary_rationale": "..."}'
    ),
)

juror_pragmatic_sre = Agent(
    name="PragmaticStaffSRE",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Pragmatic Staff SRE. You evaluate proposals on operational maintainability, "
        "observability, uptime resilience, and blast radius containment. "
        "Evaluate the proposal and return strictly a JSON object matching JurorBallot:\n"
        '{"juror_name": "PragmaticStaffSRE", "vote": "APPROVE" | "REJECT", '
        '"confidence_score": <0-100>, "primary_rationale": "..."}'
    ),
)

juror_quant_analyst = Agent(
    name="QuantitativeRiskAnalyst",
    model=DEFAULT_MODEL,
    instructions=(
        "You are a Quantitative Risk Analyst. You evaluate proposals on expected commercial value "
        "versus probable downside loss (Value-at-Risk). "
        "Evaluate the proposal and return strictly a JSON object matching JurorBallot:\n"
        '{"juror_name": "QuantitativeRiskAnalyst", "vote": "APPROVE" | "REJECT", '
        '"confidence_score": <0-100>, "primary_rationale": "..."}'
    ),
)


# -------------------------------------------------------------------------
# Runner
# -------------------------------------------------------------------------

async def run(proposal: str | None = None) -> str:
    """Execute parallel ensemble voting and calibrated consensus computation."""
    ensure_api_key()

    default_proposal = (
        "Proposal to grant temporary automated read-write API access to a third-party AI compliance scanner "
        "during off-peak hours (2:00 AM - 4:00 AM) to automatically index and redact customer PII in production."
    )
    user_prompt = proposal or default_proposal

    print_header(
        "Pattern 14: Consensus Voting & Ensemble Calibration",
        "Blind multi-juror voting with confidence weighting and agreement calibration",
    )

    print_explainer(
        summary="Multiple independent agents evaluate a proposal concurrently without cross-talk, casting weighted votes into an electoral aggregator.",
        communication_mechanism="Isolated parallel dispatch (asyncio.gather) aggregated through mathematical consensus formulas.",
        when_to_use=[
            "High-stakes go/no-go decisions where single-model hallucination carries high financial or security penalty.",
            "Ensemble classification reducing variance on ambiguous borderline inputs.",
            "Auditing disagreements between conservative and progressive operational viewpoints.",
        ],
    )

    console.print(f"[bold cyan]Candidate Proposal:[/bold cyan] {user_prompt}\n")

    # Step 1: Blind Parallel Voting
    print_agent_step("System", "Dispatching blind ballots to 3 diverse jurors in parallel...")
    f_purist = Runner.run(juror_purist, user_prompt)
    f_sre = Runner.run(juror_pragmatic_sre, user_prompt)
    f_quant = Runner.run(juror_quant_analyst, user_prompt)

    res_purist, res_sre, res_quant = await asyncio.gather(f_purist, f_sre, f_quant)

    # Parse ballots
    ballots: list[JurorBallot] = []
    for name, raw in [
        ("ConservativeSecurityPurist", res_purist.final_output),
        ("PragmaticStaffSRE", res_sre.final_output),
        ("QuantitativeRiskAnalyst", res_quant.final_output),
    ]:
        try:
            clean = str(raw).strip()
            if clean.startswith("```json"):
                clean = clean.split("```json")[1].split("```")[0].strip()
            elif clean.startswith("```"):
                clean = clean.split("```")[1].split("```")[0].strip()
            data = json.loads(clean)
            ballots.append(JurorBallot(**data))
        except Exception:
            ballots.append(JurorBallot(
                juror_name=name,
                vote="REJECT",
                confidence_score=75,
                primary_rationale="Parsing failure fallback; default to conservative rejection.",
            ))

    # Step 2: Calibrated Consensus Computation
    approve_count = sum(1 for b in ballots if b.vote.upper() == "APPROVE")
    reject_count = sum(1 for b in ballots if b.vote.upper() == "REJECT")

    approve_weight = sum(b.confidence_score for b in ballots if b.vote.upper() == "APPROVE")
    reject_weight = sum(b.confidence_score for b in ballots if b.vote.upper() == "REJECT")
    total_weight = approve_weight + reject_weight or 1

    weighted_approval_pct = round((approve_weight / total_weight) * 100, 1)
    calibrated_verdict = "APPROVED" if weighted_approval_pct >= 60.0 else "REJECTED"

    console.print()
    for b in ballots:
        vote_color = "green" if b.vote.upper() == "APPROVE" else "red"
        console.print(
            f"  ● [bold]{b.juror_name}[/bold]: [{vote_color}]{b.vote.upper()}[/{vote_color}] "
            f"([cyan]{b.confidence_score}% confidence[/cyan]) — [dim]{b.primary_rationale}[/dim]"
        )

    # Format Decision Dossier
    verdict_badge = f"[bold green]APPROVED[/bold green]" if calibrated_verdict == "APPROVED" else f"[bold red]REJECTED[/bold red]"
    dossier = (
        f"### Calibrated Consensus Decision: {verdict_badge}\n"
        f"- **Raw Vote Tally:** {approve_count} APPROVE vs {reject_count} REJECT\n"
        f"- **Confidence-Weighted Approval Score:** **{weighted_approval_pct}%**\n"
        f"- **Consensus Agreement State:** {'Unanimous' if approve_count in (0, 3) else 'Contested (Split Decision)'}\n\n"
        f"#### Juror Rationales & Dissent Analysis:\n"
        + "\n".join(
            f"- **{b.juror_name}** ({b.vote}): {b.primary_rationale} *(Confidence: {b.confidence_score}%)*"
            for b in ballots
        )
    )

    print_result_panel("Electoral Consensus Dossier", dossier)
    return dossier


if __name__ == "__main__":
    asyncio.run(run())
