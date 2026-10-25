# Pattern 14: Consensus Voting & Ensemble Calibration

## Concept Overview
In mission-critical classifications (fraud detection, high-risk security CVE triage, clinical evaluation), a single agent's stochastic output is vulnerable to hallucination or random seed variance. The Consensus Voting & Ensemble Calibration pattern executes multiple independent judges:
1. **Heterogeneous Jurors**: $N$ diverse agents evaluate the exact same candidate independently (Conservative Security Purist, Pragmatic Staff SRE, Quantitative Risk Analyst).
2. **Structured Ballots**: Each juror outputs a typed ballot `{verdict: PASS/FAIL, confidence: 0-100, rationale}`.
3. **Calibrated Electoral Engine**: A deterministic aggregator computes:
   - Majority Vote Tally.
   - Confidence-Weighted Tally.
   - Epistemic Consensus Index (measuring inter-agent agreement entropy).
4. **Decision Synthesis**: Produces a mathematically calibrated verdict with actionable dissent analysis.

```mermaid
flowchart TD
    Proposal([High-Risk Proposal]) --> Blind{Parallel Blind Voting}
    Blind --> JurorA[Conservative Security Purist]
    Blind --> JurorB[Pragmatic Staff SRE]
    Blind --> JurorC[Quantitative Risk Analyst]
    JurorA --> BallotA[Ballot A: REJECT (95%)]
    JurorB --> BallotB[Ballot B: APPROVE (70%)]
    JurorC --> BallotC[Ballot C: REJECT (80%)]
    BallotA --> Aggregator[Electoral Aggregator]
    BallotB --> Aggregator
    BallotC --> Aggregator
    Aggregator --> Verdict([Calibrated Consensus Dossier])
```

## When to Use
- High-stakes classification (Fraud detection, zero-day CVE vulnerability scoring).
- Situations where variance and hallucination must be reduced through ensemble wisdom.
- Detecting ambiguous borderline cases where experts legitimately disagree.
