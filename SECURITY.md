# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 1.0.x   | ✅ |

## Reporting a Vulnerability

If you discover a security vulnerability, please:

1. **Do NOT** open a public issue
2. Email the maintainers directly (see repository settings)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Response Time

- Initial response: within 48 hours
- Status update: within 7 days
- Fix timeline: depends on severity

## Security Considerations

This is an embedded firmware project with BLE connectivity:

- **BLE Security**: Device uses default BLE security. For production use, consider enabling BLE pairing/bonding.
- **No Network**: The device does not connect to the internet directly.
- **Local Control**: All control commands are local via BLE.

## Best Practices

- Do not expose the device to untrusted networks
- Use in controlled environments
- Review code before deploying to production devices
