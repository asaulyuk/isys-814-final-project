# Analysis Methodology

The project analyzes an exploratory 15-response survey about the strategic role of IT. The public repository reports only aggregate results.

## Metrics

The core quantitative measures are:

- IT strategy importance
- IT competitive impact
- IT-business alignment
- IT strategy involvement
- IT responsiveness
- IT delivery effectiveness

## Gaps

Two gap measures summarize the main pattern:

- Strategy-impact gap = IT strategy importance mean minus IT competitive impact mean
- Alignment-responsiveness gap = IT-business alignment mean minus IT responsiveness mean

Note: strategy importance is measured on a 1-5 scale, while competitive impact is measured on a 1-4 scale. The gap is useful as a directional class-project signal, not as a normalized effect size.

## Segmentation

Organizations are classified using:

- `it_strategy_importance`
- `contribute_achieving_competitive_advantage`

Rules:

- Strategic IT: high IT strategy importance and high competitive impact
- Support IT: lower IT strategy importance and lower competitive impact
- Constrained IT: all other valid cases

The resulting aggregate distribution is:

- Strategic IT: 1 response
- Constrained IT: 8 responses
- Support IT: 6 responses

## Privacy Boundary

The public repository intentionally excludes row-level survey data, raw exports, local analysis workbooks, and detailed interview materials. This keeps the analysis transparent at the aggregate level without publishing respondent-level records.
