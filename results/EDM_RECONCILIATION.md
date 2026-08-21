# Official source reconciliation — APR vs EDM

The APR spill-count line and Yorkshire Water's current EDM summary are both official publications, but they are versioned through different reporting processes. This check does not silently overwrite one with the other.

- Comparable years: **3**
- Exact matches: **2**
- Years requiring review: **[2025]**
- Largest absolute difference: **156 spills**
- Largest relative difference: **0.303%**

A mismatch is treated as a data-governance event, not a modelling error. The pipeline keeps both values, source identifiers and retrieval date so downstream users can choose the appropriate publication for their decision context.
