# Nexus
Modular Django + DRF backend with FBV-based API architecture, serving as the single source of truth for multiple independently deployed frontends.

## View Architecture

This module follows a **Function-Based View (FBV)** pattern for explicit, 
predictable request handling. Each view is a discrete, single-purpose 
function decorated with DRF's `@api_view` and `@permission_classes`, 
avoiding the implicit behavior and inheritance overhead of class-based views.

**Rationale for FBVs:**
- Explicit control flow — no hidden `dispatch()` chains or MRO resolution
- Simpler unit testing — each endpoint is a pure function, easy to mock/isolate
- Lower cognitive overhead for small-to-medium endpoint logic
- Preferred for endpoints with non-standard or highly custom request handling

Views are grouped per Django app under `views.py`, with shared logic 
extracted into `utils.py` and reusable request validation handled via 
custom `decorators.py`.
