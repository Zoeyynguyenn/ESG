# Bootstrap Quick Commands

Run these commands from the `ai-workflows` chat.

## Maintain existing project

```text
/start maintain E:/Documents/projects/ai-trend-radar
```

## Create new project (auto bootstrap minimal files)

```text
/start create E:/Documents/projects/ai-price
```

## End current target session

```text
/end
```

## Switch target safely

```text
/switch maintain E:/Documents/projects/ai-trend-radar
/switch create E:/Documents/projects/ai-price
```

Safety behavior:
1. Confirm current active target
2. Ask confirmation before switching
3. Echo write boundary for new target
