# Import Graph Report

Date: 2025-10-16T22:58:29.071422


## Hotspots


### Top fan-in (modules most depended on)

- agents: 5
- api: 4
- scripts: 3
- jarvis2: 2
- metrics_storage: 1
- tests: 1

### Top fan-out (modules with many dependencies)

- tests: 5
- agents: 3
- api: 3
- scripts: 3
- metrics_storage: 2

## Cycles

- agents -> api -> agents
- api -> scripts -> api
- agents -> api -> scripts -> agents
