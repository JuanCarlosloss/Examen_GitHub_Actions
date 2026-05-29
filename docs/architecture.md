# System Architecture

This monorepo follows a clean, decoupled structure:

```
[ Frontend (Node.js) ]  <---->  [ Backend (Node.js) ]
         ^                               ^
         |                               |
         +------- Provisioned by --------+
                         |
               [ Infraestructura (TF) ]
```

## Performance Guidelines
- All Node.js components must define distinct dependencies and separate lockfiles.
- Reusable workflows and action caching are used to ensure minimal build durations.
