# Triggerfish Core

Go-based graph core for Triggerfish LSP. Communicates over STDIO using newline-delimited JSON.

## Build

```bash
go build -o triggerfish-core ./cmd/triggerfish-core
```

## Health Check

```bash
echo '{"id":"1","method":"health","params":{}}' | ./triggerfish-core
```
