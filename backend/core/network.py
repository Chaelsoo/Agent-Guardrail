import ipaddress
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Always-blocked hosts / ranges
# ---------------------------------------------------------------------------

_METADATA_HOSTS = {
    "169.254.169.254",   # AWS / GCP / Azure IMDS
    "metadata.google.internal",
    "169.254.170.2",     # ECS metadata
}

_PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),   # shared address space (CGN)
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_always_blocked(host: str) -> bool:
    if host in _METADATA_HOSTS:
        return True
    try:
        addr = ipaddress.ip_address(host)
        return any(addr in net for net in _PRIVATE_NETWORKS)
    except ValueError:
        return False


def _extract_host(url: str) -> str:
    """Return the hostname from a URL string, or the raw string on failure."""
    try:
        parsed = urlparse(url if "://" in url else f"http://{url}")
        return (parsed.hostname or url).lower()
    except Exception:
        return url.lower()


def _domain_matches(domain: str, candidate: str) -> bool:
    """True if candidate is, or is a subdomain of, domain."""
    candidate = candidate.lstrip(".")
    domain = domain.lstrip(".")
    return candidate == domain or candidate.endswith(f".{domain}")


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

@dataclass
class NetworkDecision:
    blocked: bool
    flagged: bool
    blocked_url: Optional[str] = None
    flagged_url: Optional[str] = None
    reason: Optional[str] = None


def evaluate_urls(
    urls: List[str],
    allowlist: List[str],
    denylist: List[str],
) -> NetworkDecision:
    """Evaluate a list of URLs against the network policy.

    Returns the first adverse decision found, or a clean pass if all URLs
    are acceptable.
    """
    for url in urls:
        host = _extract_host(url)

        # 1. Always block private / metadata addresses
        if _is_always_blocked(host):
            return NetworkDecision(
                blocked=True,
                flagged=False,
                blocked_url=url,
                reason=f"Private or metadata address blocked: {host}",
            )

        # 2. Explicit denylist
        if any(_domain_matches(d, host) for d in denylist):
            return NetworkDecision(
                blocked=True,
                flagged=False,
                blocked_url=url,
                reason=f"Domain in denylist: {host}",
            )

        # 3. Not in allowlist → warn (only when allowlist is non-empty)
        if allowlist and not any(_domain_matches(a, host) for a in allowlist):
            return NetworkDecision(
                blocked=False,
                flagged=True,
                flagged_url=url,
                reason=f"URL not in allowlist: {url}",
            )

    return NetworkDecision(blocked=False, flagged=False)
