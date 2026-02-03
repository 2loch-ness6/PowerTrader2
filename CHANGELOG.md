# Changelog

All notable changes to PowerTrader2 will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Phase 1: Stabilization - Security, Reliability & Monitoring

This phase transforms PowerTrader2 from a prototype into a production-safe trading system.

## [1.1.0] - 2026-02-03

### Added - Security Hardening

#### API Credential Encryption
- **NEW**: Secure credential storage using OS-level keyring
  - macOS: Credentials stored in Keychain
  - Windows: Credentials stored in Windows Credential Manager
  - Linux: Credentials stored in Secret Service
- **NEW**: `credentials_manager.py` module for secure credential management
- **NEW**: `migrate_credentials.py` script for one-time migration from plaintext files
- Automatic fallback to plaintext files for backward compatibility
- Clear warning messages when using plaintext credentials

#### File Integrity Checks
- **NEW**: `integrity_checker.py` module for SHA-256 checksum verification
- Model files are verified on load to detect tampering
- Checksums automatically updated after training
- CLI flag `--rebuild-checksums` for legitimate model updates

### Added - Reliability Fixes

#### Order Reconciliation Improvements
- **NEW**: Timeout mechanism for order reconciliation (default: 5 minutes)
- **NEW**: Exponential backoff with retry logic (max 10 retries)
- **NEW**: `_handle_stuck_orders()` method for stuck order handling
- Stuck orders saved to `problematic_orders.json` for manual review
- Trader now starts despite stuck orders (no longer blocks indefinitely)
- Detailed logging of stuck order information

#### API Rate Limiting
- **NEW**: `api_rate_limiter.py` module with exponential backoff
- Rate limiting: 60 calls per minute (configurable)
- HTTP 429 error handling with Retry-After header support
- Automatic 5-minute trading pause after repeated rate limit violations
- Per-request exponential backoff: 1s → 2s → 4s → 8s → 16s

#### Price Cache TTL
- **NEW**: Time-to-live (TTL) for price cache entries (default: 5 seconds)
- `_get_cached_price()` method for cache validation
- Expired cache entries automatically rejected
- Warning messages when using cached data
- Clear indicators for cache age and expiration

#### Safe File I/O
- **NEW**: `safe_file_io.py` module for atomic file operations
- Cross-platform atomic writes with proper fsync
- Windows-specific handling for atomic operations
- File locking support using `filelock` library
- Prevents corruption during concurrent access or crashes

### Changed

#### pt_trader.py
- Updated credential loading to try keyring first, fall back to plaintext
- Added timeout and retry logic to `_reconcile_pending_orders()`
- Added `_handle_stuck_orders()` method for stuck order management
- Added `_get_cached_price()` method with TTL validation
- Updated `_atomic_write_json()` to use `safe_file_io` module
- Updated `_append_jsonl()` to use `safe_file_io` module
- Added `_cache_ttl_seconds` configuration parameter
- Improved error messages and logging throughout

### Dependencies

#### Added
- `keyring` - OS-level credential storage
- `prometheus-client` - Metrics export (for future monitoring features)
- `filelock` - Safe concurrent file access

#### Already Present
- `requests` - HTTP client
- `psutil` - System utilities
- `matplotlib` - Plotting
- `colorama` - Terminal colors
- `cryptography` - Encryption primitives
- `PyNaCl` - Cryptographic signing
- `kucoin-python` - KuCoin API (legacy)

### Documentation

#### Added
- `SECURITY.md` - Security best practices and vulnerability reporting
- `MONITORING.md` - Comprehensive monitoring guide
- `CHANGELOG.md` - This file

### Security

- ✅ API credentials now stored encrypted in OS keyring
- ✅ Plaintext credential files securely overwritten before deletion
- ✅ Model files protected with SHA-256 integrity checks
- ✅ Rate limiting prevents API abuse and account suspension
- ✅ File operations use atomic writes to prevent corruption
- ✅ File locking prevents concurrent access issues

### Fixed

- **Critical**: Order reconciliation no longer blocks indefinitely
- **Critical**: Price cache now expires to prevent stale data usage
- **Critical**: File writes are now atomic on Windows
- **High**: API calls properly rate-limited to prevent 429 errors
- **Medium**: Stuck orders no longer prevent trader from starting

## Planned for Future Releases

### Phase 1 Remaining (Monitoring & Observability)
- [ ] Structured JSON logging with rotation
- [ ] Prometheus metrics endpoint on port 8000
- [ ] Health check HTTP endpoint on port 8080
- [ ] Grafana dashboard template
- [ ] Docker Compose for monitoring stack

### Phase 2 (TBD)
- Performance optimizations
- Additional trading strategies
- Enhanced GUI features
- Mobile app integration
- Cloud deployment support

## Notes

### Breaking Changes
- None - all Phase 1 changes are backward compatible
- Existing plaintext credentials continue to work with warnings
- Existing trade data and models are fully compatible

### Migration Guide

#### Upgrading from Pre-1.1.0

1. **Update dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Migrate credentials (recommended):**
   ```bash
   python migrate_credentials.py
   ```

3. **Verify migration:**
   ```bash
   python pt_trader.py
   # Should show: "✓ Loaded API credentials from secure keyring"
   ```

4. **Optional: Generate model checksums:**
   ```bash
   python pt_trainer.py --rebuild-checksums
   ```

### Testing
- All changes tested on Windows 10/11 and Ubuntu 20.04
- Backward compatibility verified with existing trade data
- Rate limiting tested with simulated API load
- File integrity checks tested with corrupted files
- Order reconciliation timeout tested with mock API

### Known Issues
- None currently

## Contact

For questions about this release:
- GitHub Issues: https://github.com/2loch-ness6/PowerTrader2/issues
- See README.md for contact information

---

[Unreleased]: https://github.com/2loch-ness6/PowerTrader2/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/2loch-ness6/PowerTrader2/releases/tag/v1.1.0
