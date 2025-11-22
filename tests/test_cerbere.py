"""
Tests for the Cerbere IP access control module.
"""

import pytest
from cerbere import Cerbere


class TestCerbereInitialization:
    """Test Cerbere initialization and configuration."""

    def test_init_with_empty_lists(self):
        """Test initialization with empty whitelist and blacklist."""
        config = {
            "max_tries": 3,
            "whitelist": [],
            "blacklist": []
        }
        c = Cerbere(config)

        assert c.trials == 3
        assert c.blacklist == {}
        assert c.whitelist == {}
        assert c.suspect == {}

    def test_init_with_blacklist(self):
        """Test initialization with blacklisted IPs."""
        config = {
            "max_tries": 5,
            "whitelist": [],
            "blacklist": ["192.168.1.100", "10.0.0.1"]
        }
        c = Cerbere(config)

        assert c.trials == 5
        assert "192.168.1.100" in c.blacklist
        assert "10.0.0.1" in c.blacklist
        assert len(c.blacklist) == 2

    def test_init_with_whitelist(self):
        """Test initialization with whitelisted IPs."""
        config = {
            "max_tries": 3,
            "whitelist": ["127.0.0.1", "192.168.1.1"],
            "blacklist": []
        }
        c = Cerbere(config)

        assert "127.0.0.1" in c.whitelist
        assert "192.168.1.1" in c.whitelist
        assert len(c.whitelist) == 2


class TestBlacklistCheck:
    """Test blacklist checking functionality."""

    def test_blacklisted_ip_returns_true(self):
        """Test that blacklisted IPs are correctly identified."""
        config = {
            "max_tries": 3,
            "whitelist": [],
            "blacklist": ["10.0.0.1"]
        }
        c = Cerbere(config)

        assert c.blacklisted("10.0.0.1") is True

    def test_non_blacklisted_ip_returns_false(self):
        """Test that non-blacklisted IPs return False."""
        config = {
            "max_tries": 3,
            "whitelist": [],
            "blacklist": ["10.0.0.1"]
        }
        c = Cerbere(config)

        assert c.blacklisted("192.168.1.1") is False


class TestWhitelistCheck:
    """Test whitelist checking functionality."""

    def test_whitelisted_ip_returns_true(self):
        """Test that whitelisted IPs are correctly identified."""
        config = {
            "max_tries": 3,
            "whitelist": ["192.168.1.1"],
            "blacklist": []
        }
        c = Cerbere(config)

        assert c.whitelisted("192.168.1.1") is True

    def test_non_whitelisted_ip_returns_false(self):
        """Test that non-whitelisted IPs return False."""
        config = {
            "max_tries": 3,
            "whitelist": ["192.168.1.1"],
            "blacklist": []
        }
        c = Cerbere(config)

        assert c.whitelisted("10.0.0.1") is False


class TestWatchAndBan:
    """Test the watch and ban functionality."""

    def test_watch_bans_after_max_tries(self):
        """Test that IPs are banned after exceeding max tries."""
        config = {
            "max_tries": 3,
            "whitelist": [],
            "blacklist": []
        }
        c = Cerbere(config)

        # First two attempts should not ban
        assert c.watch("192.168.1.100") is False
        assert c.watch("192.168.1.100") is False

        # Third attempt should trigger ban
        assert c.watch("192.168.1.100") is True
        assert c.blacklisted("192.168.1.100") is True

    def test_watch_tracks_suspect_count(self):
        """Test that failed attempts are tracked correctly."""
        config = {
            "max_tries": 5,
            "whitelist": [],
            "blacklist": []
        }
        c = Cerbere(config)

        c.watch("10.0.0.1")
        assert c.suspect["10.0.0.1"] == 1

        c.watch("10.0.0.1")
        assert c.suspect["10.0.0.1"] == 2

        c.watch("10.0.0.1")
        assert c.suspect["10.0.0.1"] == 3

    def test_whitelisted_ip_never_banned(self):
        """Test that whitelisted IPs are never banned."""
        config = {
            "max_tries": 3,
            "whitelist": ["192.168.1.1"],
            "blacklist": []
        }
        c = Cerbere(config)

        # Many failures should not ban whitelisted IP
        for _ in range(10):
            result = c.watch("192.168.1.1")
            assert result is False

        assert c.blacklisted("192.168.1.1") is False

    def test_multiple_ips_tracked_independently(self):
        """Test that different IPs are tracked independently."""
        config = {
            "max_tries": 3,
            "whitelist": [],
            "blacklist": []
        }
        c = Cerbere(config)

        c.watch("192.168.1.1")
        c.watch("192.168.1.2")
        c.watch("192.168.1.1")

        assert c.suspect["192.168.1.1"] == 2
        assert c.suspect["192.168.1.2"] == 1

    def test_ban_on_exact_threshold(self):
        """Test that ban occurs exactly at threshold."""
        config = {
            "max_tries": 1,
            "whitelist": [],
            "blacklist": []
        }
        c = Cerbere(config)

        # First attempt should immediately ban
        assert c.watch("10.0.0.1") is True
        assert c.blacklisted("10.0.0.1") is True


class TestInstanceIsolation:
    """Test that multiple instances don't share state."""

    def test_multiple_instances_have_separate_state(self):
        """Test that different Cerbere instances have independent state."""
        config1 = {
            "max_tries": 3,
            "whitelist": [],
            "blacklist": ["10.0.0.1"]
        }
        config2 = {
            "max_tries": 5,
            "whitelist": ["192.168.1.1"],
            "blacklist": []
        }

        c1 = Cerbere(config1)
        c2 = Cerbere(config2)

        # Different max_tries
        assert c1.trials == 3
        assert c2.trials == 5

        # Different blacklists
        assert c1.blacklisted("10.0.0.1") is True
        assert c2.blacklisted("10.0.0.1") is False

        # Different whitelists
        assert c1.whitelisted("192.168.1.1") is False
        assert c2.whitelisted("192.168.1.1") is True

    def test_watch_state_not_shared_between_instances(self):
        """Test that watch state is not shared between instances."""
        config = {
            "max_tries": 3,
            "whitelist": [],
            "blacklist": []
        }

        c1 = Cerbere(config)
        c2 = Cerbere(config)

        # Add suspect to c1
        c1.watch("10.0.0.1")

        # c2 should not have this suspect
        assert "10.0.0.1" in c1.suspect
        assert "10.0.0.1" not in c2.suspect
