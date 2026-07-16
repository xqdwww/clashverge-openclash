# Security Policy

## Reporting

After a public repository exists, report vulnerabilities privately through its
GitHub Security Advisory form. Do not attach a real proxy configuration,
subscription URL, server address, credential, or router detail to a public
issue.

## Data boundary

Conversion is local and makes no network request. Proxy objects are passed
through and may contain credentials, so generated output must still be treated
as sensitive. The CLI avoids printing proxy values and writes output with mode
`0600` where the operating system supports it.

The parser uses PyYAML's safe construction model, rejects duplicate keys, and
limits input files to 5 MiB and YAML aliases to 50. These limits reduce, but do
not eliminate, resource-exhaustion risk from untrusted local files.

Only supported synthetic reproductions should be shared with maintainers.
