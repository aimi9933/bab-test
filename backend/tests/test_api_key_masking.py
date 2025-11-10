"""Tests for API key masking functionality."""

import pytest
from backend.app.services.providers import mask_api_key
from backend.app.db.models import ExternalAPI


class TestApiKeyMasking:
    """Test the API key masking functionality."""

    def test_mask_api_key_short_key(self):
        """Test masking of very short API keys."""
        # Very short key
        assert mask_api_key("1234") == "***"
        
        # Short key with prefix (8 chars, so prefix_len = 8 // 4 = 2)
        assert mask_api_key("sk-1234") == "sk***34"

    def test_mask_api_key_normal_key(self):
        """Test masking of normal-length API keys."""
        # 15 character key (prefix_len = 15 // 4 = 3)
        key = "sk-1234567890ab"
        expected = "sk-***...***90ab"
        assert mask_api_key(key) == expected
        
        # 32 character key (prefix_len = 32 // 4 = 8, but min(6, 8) = 6)
        key = "sk-1234567890abcdef1234567890abcdef"
        expected = "sk-123***...***cdef"
        assert mask_api_key(key) == expected

    def test_mask_api_key_long_key(self):
        """Test masking of long API keys."""
        # 64 character key (prefix_len = 64 // 4 = 16, but min(6, 16) = 6)
        key = "sk-1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        expected = "sk-123***...***cdef"
        assert mask_api_key(key) == expected

    def test_mask_api_key_empty_and_none(self):
        """Test masking of empty and None values."""
        assert mask_api_key("") == ""
        assert mask_api_key(None) == ""

    def test_mask_api_key_preserves_prefix(self):
        """Test that API key prefixes are preserved."""
        keys = [
            "sk-1234567890abcdef",
            "pk_live_1234567890abcdef",
            "Bearer1234567890abcdef",
            "1234567890abcdef"
        ]
        
        for key in keys:
            masked = mask_api_key(key)
            assert "***...***" in masked
            # Note: for very short keys, masked version might be longer due to ***...***
            assert masked.endswith(key[-4:])

    def test_provider_model_api_key_masked_property(self):
        """Test the ExternalAPI model's api_key_masked property."""
        from backend.app.core.security import encrypt_api_key
        
        # Create a mock provider with encrypted API key
        provider = ExternalAPI(
            name="Test Provider",
            base_url="https://api.example.com",
            api_key_encrypted=encrypt_api_key("sk-1234567890abcdef"),
            models=["gpt-4"],
            is_active=True
        )
        
        # Test that the masked property works
        masked = provider.api_key_masked
        assert "***...***" in masked
        assert masked.endswith("cdef")
        assert "sk-" in masked

    def test_provider_model_api_key_masked_property_invalid_encryption(self):
        """Test masking when decryption fails."""
        # Create a provider with invalid encrypted data
        provider = ExternalAPI(
            name="Test Provider", 
            base_url="https://api.example.com",
            api_key_encrypted="invalid_encrypted_data",
            models=["gpt-4"],
            is_active=True
        )
        
        # Should return generic mask when decryption fails
        assert provider.api_key_masked == "***...***"

    def test_provider_response_schema_includes_masked_key(self):
        """Test that ProviderRead schema includes api_key_masked field."""
        from backend.app.schemas.provider import ProviderRead
        
        # Create a provider response
        provider_data = {
            "id": 1,
            "name": "Test Provider",
            "base_url": "https://api.example.com",
            "models": ["gpt-4"],
            "is_active": True,
            "status": "online",
            "latency_ms": 100.0,
            "last_tested_at": None,
            "consecutive_failures": 0,
            "is_healthy": True,
            "created_at": None,
            "updated_at": None,
            "api_key_masked": "sk-***...***cdef"
        }
        
        # This should not raise any validation errors
        provider = ProviderRead(**provider_data)
        assert provider.api_key_masked == "sk-***...***cdef"
        
        # Test that it's optional
        provider_data.pop("api_key_masked")
        provider = ProviderRead(**provider_data)
        assert provider.api_key_masked is None