# -*- coding: utf-8 -*-
# /usr/bin/env python3

import pytest
from app.utils.link_utils import extract_site_name, KNOWN_SITES

# --- Test Cases for Known Sites ---

# Dynamically generate test cases for all entries in KNOWN_SITES
known_sites_test_cases = []
for domain, site_name in KNOWN_SITES.items():
    # Primary domain
    known_sites_test_cases.append((f"https://{domain}/some/path", site_name))
    known_sites_test_cases.append((f"http://{domain}/other?query=123", site_name))
    # With www.
    known_sites_test_cases.append((f"https://www.{domain}/another_page.html", site_name))
    # Scheme-less (should be handled by urlparse if a default scheme is assumed by caller,
    # but extract_site_name itself might receive it with a scheme already)
    # For robustness, we assume URLs will have schemes when passed to extract_site_name
    # Test with uppercase domain
    known_sites_test_cases.append((f"HTTPS://{domain.upper()}/CASE/TEST", site_name))

# Specific cases for sites with alternative domains or common mobile prefixes
# YouTube
known_sites_test_cases.extend([
    ("https://youtube.com/watch?v=xyz", "YouTube"),
    ("http://youtu.be/xyz", "YouTube"),
    ("https://www.youtube.com/channel/abc", "YouTube"),
])
# Twitter
known_sites_test_cases.extend([
    ("https://twitter.com/user/status/123", "Twitter"),
    ("http://x.com/another_user", "Twitter"),
    ("https://www.x.com/explore", "Twitter"),
])
# Weibo
known_sites_test_cases.extend([
    ("https://weibo.com/12345", "Weibo"),
    ("http://weibo.cn/detail/67890", "Weibo"),
    ("https://m.weibo.cn/user/000", "Weibo"), # Common mobile prefix
])
# Kuaishou (already has live.kuaishou.com in KNOWN_SITES)
known_sites_test_cases.extend([
    ("https://kuaishou.com/short-video/test", "Kuaishou"),
    ("http://live.kuaishou.com/profile/user1", "Kuaishou"),
    ("https://www.live.kuaishou.com/room/123", "Kuaishou"),
])


@pytest.mark.parametrize("url, expected_site_name", known_sites_test_cases)
def test_extract_site_name_known_sites(url, expected_site_name):
    assert extract_site_name(url) == expected_site_name

# --- Test Cases for Unknown Sites ---

unknown_sites_test_cases = [
    # Simple two-part domains
    ("http://customsite.com/page", "Customsite"),
    ("https://another.org", "Another"),
    ("http://example.net/resource?id=1", "Example"),
    # With www. prefix
    ("https://www.unknownplatform.io/path", "Unknownplatform"),
    ("http://www.myblog.info/article/1", "Myblog"),
    # With other subdomains
    ("https://blog.personalpage.me/post-title", "Personalpage"),
    ("http://news.megacorp.biz/latest", "Megacorp"),
    ("https://API.somedeveloper.DEV/v1/docs", "Somedeveloper"), # Test with uppercase TLD
    # Domains with ccTLDs like .co.uk, .com.au
    ("http://mybusiness.co.uk/about", "Mybusiness"),
    ("https://newsportal.com.au/story", "Newsportal"),
    ("http://www.another.org.nz/info", "Another"),
    ("https://elections.gov.in", "Elections"), # .gov.in
    # Domains with three parts where the last two are short (e.g. org.cn)
    ("https://my.company.org.cn/page", "Company"),
    ("http://archive.museum.gov.uk/item", "Museum"),
    # Single-word domains
    ("http://intranet/dashboard", "intranet"),
    ("https://localhost/api/users", "localhost"),
    # Case variations for unknown sites
    ("HTTP://MyDomain.COM/Path", "Mydomain"),
    ("https://WWW.MixedCase.NET", "Mixedcase"),
]

@pytest.mark.parametrize("url, expected_site_name", unknown_sites_test_cases)
def test_extract_site_name_unknown_sites(url, expected_site_name):
    assert extract_site_name(url) == expected_site_name

# --- Test Cases for Edge Cases ---

edge_cases_test_cases = [
    # URLs with port numbers
    ("http://localhost:8000/path", "localhost"),
    ("https://testsite.com:1234/resource", "Testsite"), # testsite.com is not in KNOWN_SITES
    ("https://www.another-example.org:8080/", "Another-example"),
    ("https://youtube.com:443/watch?v=vid", "YouTube"), # Known site with port
    ("http://x.com:80/user", "Twitter"), # Known site with port
    # IP Address URLs
    ("http://192.168.0.1/index.html", "192.168.0.1"),
    ("https://127.0.0.1:5000/api", "127.0.0.1"),
    ("http://[::1]/dashboard", "[::1]"), # IPv6 localhost
    ("https://[2001:db8::1]:8080/path", "[2001:db8::1]"), # IPv6 with port
    # URLs with unusual but valid characters (urlparse should handle these)
    # (No specific cases added as urlparse is robust; function relies on netloc)
    # Domain with hyphen
    ("https://my-cool-site.online/blog", "My-cool-site"),
    ("http://www.another-hyphenated.co.jp/page", "Another-hyphenated"),
    # Test .org.cn like case where first part is short
    ("https://abc.org.cn/a/b", "Abc"), # Should take 'abc' as per current logic for unknown .org.cn
]

@pytest.mark.parametrize("url, expected_site_name", edge_cases_test_cases)
def test_extract_site_name_edge_cases(url, expected_site_name):
    assert extract_site_name(url) == expected_site_name

# --- Test Cases for Invalid or Unhandled Inputs ---

invalid_inputs_test_cases = [
    ("", None),
    ("bad-url-format", None),
    ("http//example.com", None), # Malformed scheme
    ("https:/example.com", None), # Also malformed
    ("://example.com", None), # No scheme
    ("file:///C:/Users/test/file.txt", None), # No netloc
    ("data:text/plain,Hello%2C%20World!", None), # No netloc
    (None, None),
    # FTP scheme (should still parse netloc if present)
    ("ftp://download.server.com/file.zip", "Server"),
    ("ftps://secure.server.org/data", "Server"),
    ("sftp://user@files.example.dev/path", "Example"),
    # URLs that urlparse might return an empty netloc for after stripping, e.g., only scheme
    ("http://", None),
    ("https://", None),
]

@pytest.mark.parametrize("url, expected_site_name", invalid_inputs_test_cases)
def test_extract_site_name_invalid_inputs(url, expected_site_name):
    assert extract_site_name(url) == expected_site_name

print("test_link_utils.py created with tests for extract_site_name.")
