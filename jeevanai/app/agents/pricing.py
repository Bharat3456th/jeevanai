import ipaddress
import json
import re
import socket
from typing import Optional, Tuple
from urllib.parse import urlparse

_NAT64 = ipaddress.ip_network("64:ff9b::/96")


def _public_ip(ip):
    """NAT64 (64:ff9b::/96) address me chhupa asli IPv4 nikaalo aur wahi jaancho."""
    if isinstance(ip, ipaddress.IPv6Address):
        if ip in _NAT64:
            ip = ipaddress.IPv4Address(int(ip) & 0xFFFFFFFF)
        elif ip.ipv4_mapped:
            ip = ip.ipv4_mapped
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
                or ip.is_multicast or ip.is_unspecified)

def is_safe_url(url: str) -> bool:
    """Block SSRF: only http(s) to public IP addresses."""
    p = urlparse(url or "")
    if p.scheme not in ("http", "https") or not p.hostname:
        return False
    try:
        for info in socket.getaddrinfo(p.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if not _public_ip(ip):
                return False
    except (socket.gaierror, ValueError):
        return False
    return True


def _num(v) -> Optional[float]:
    try:
        return float(str(v).replace(",", "").strip())
    except ValueError:
        return None


def parse_price(html: str) -> Optional[Tuple[float, str]]:
    """Find (price, currency) via JSON-LD, then meta tags. None when not found."""
    for blob in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', html, flags=re.S | re.I):
        try:
            stack = [json.loads(blob)]
        except ValueError:
            continue
        while stack:
            o = stack.pop()
            if isinstance(o, list):
                stack.extend(o)
            elif isinstance(o, dict):
                for key in ("price", "lowPrice"):
                    if key in o and _num(o[key]) is not None:
                        return _num(o[key]), str(o.get("priceCurrency", ""))
                stack.extend(v for v in o.values() if isinstance(v, (dict, list)))
    m = re.search(r'property=["\'](?:product|og):price:amount["\'][^>]*content=["\']([\d.,]+)', html, flags=re.I)
    if not m:
        m = re.search(r'itemprop=["\']price["\'][^>]*content=["\']([\d.,]+)', html, flags=re.I)
    if m and _num(m.group(1)) is not None:
        cur = re.search(r'property=["\'](?:product|og):price:currency["\'][^>]*content=["\'](\w+)', html, flags=re.I)
        return _num(m.group(1)), cur.group(1) if cur else ""
    return None
