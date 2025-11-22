"""
MIT License

Copyright (c) 2023 Jean-Paul Gavini

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
# *
# * Minimal helper class for managing ip whitelist and blacklist
# *

from typing import Dict, Any


class Cerbere:
    """
    IP-based access control manager.

    Manages IP whitelists, blacklists, and automatic banning based on
    failed authentication attempts.

    Attributes:
        trials: Maximum failed attempts before IP is banned
        blacklist: Dictionary of banned IP addresses
        whitelist: Dictionary of trusted IP addresses (never banned)
        suspect: Dictionary tracking failed attempts per IP
    """
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize Cerbere with configuration.

        Args:
            config: Configuration dictionary containing:
                - max_tries: Maximum failed attempts before ban
                - blacklist: List of IPs to block
                - whitelist: List of IPs to trust
        """
        self.trials: int = config["max_tries"]
        self.blacklist: Dict[str, bool] = {}
        self.whitelist: Dict[str, bool] = {}
        self.suspect: Dict[str, int] = {}

        for ip in config["blacklist"]:
            self.blacklist[ip] = True

        for ip in config["whitelist"]:
            self.whitelist[ip] = True

    def blacklisted(self, ip: str) -> bool:
        """
        Check if an IP address is blacklisted.

        Args:
            ip: IP address to check

        Returns:
            True if IP is blacklisted, False otherwise
        """
        return ip in self.blacklist

    def whitelisted(self, ip: str) -> bool:
        """
        Check if an IP address is whitelisted.

        Args:
            ip: IP address to check

        Returns:
            True if IP is whitelisted, False otherwise
        """
        return ip in self.whitelist

    def watch(self, ip: str) -> bool:
        """
        Track failed authentication attempts and ban if threshold exceeded.

        Whitelisted IPs are never banned. For non-whitelisted IPs,
        increments the failure counter and bans the IP if it exceeds
        the configured maximum tries.

        Args:
            ip: IP address to track

        Returns:
            True if IP was just banned, False otherwise
        """
        if ip not in self.whitelist:
            if not ip in self.suspect:
                self.suspect[ip] = 0

            self.suspect[ip] += 1

            if self.suspect[ip] >= self.trials:
                self.blacklist[ip] = True
                return True

        return False
