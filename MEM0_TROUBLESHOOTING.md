# Mem0 Troubleshooting Guide

## Current Status

Memories are being saved to Mem0, but they're processed **asynchronously** in the cloud. This means:

1. ✅ **Saves are working** - You get event_ids back when saving
2. ⏳ **Processing is async** - Memories take time to appear (10-30+ seconds)
3. 🔍 **Retrieval requires filters** - Mem0 cloud API requires filters for `get_all()`

## How Mem0 Cloud Works

### Save Process
1. Memory is queued: `add()` returns `{'results': [{'event_id': '...', 'status': 'PENDING'}]}`
2. Mem0 processes in background (10-30 seconds typically)
3. Memory becomes searchable after processing

### Retrieval Process
- **Requires filters**: `get_all()` must include filters
- **Filter format**: `{'metadata': {'type': 'evaluated_idea'}}`
- **User ID matters**: Memories are scoped by `user_id`

## Current Configuration

From your `.env` file:
- `MEM0_API_KEY`: Set (cloud mode)
- `MEM0_USER_ID`: `ideation_flow`

**All memories are saved with user_id: `ideation_flow`**

## Verifying Memories Are Saved

### Method 1: CLI Commands

```bash
# List all ideas
ideation-claude list

# Search for similar ideas
ideation-claude search "your idea"

# Get insights
ideation-claude insights "market trends"
```

### Method 2: Direct Python Check

```python
from ideation_claude.memory import get_memory
import time

memory = get_memory()
print(f"User ID: {memory.user_id}")

# Wait a bit for processing
time.sleep(30)

# Check memories
ideas = memory.get_all_ideas(limit=20)
print(f"Found {len(ideas)} ideas")
for idea in ideas:
    meta = idea.get('metadata', {})
    print(f"- {meta.get('topic')} ({meta.get('status')})")
```

### Method 3: Mem0 Dashboard

1. Go to Mem0 dashboard
2. Filter by user_id: `ideation_flow`
3. Check for memories with type: `evaluated_idea`

## Why You Might Not See Memories

### 1. Processing Delay
- **Cause**: Mem0 cloud processes asynchronously
- **Solution**: Wait 30-60 seconds after evaluation
- **Check**: Memories appear after processing completes

### 2. Wrong User ID
- **Cause**: Checking different user_id than used for saves
- **Solution**: Ensure `MEM0_USER_ID=ideation_flow` matches
- **Check**: Verify user_id in both save and retrieve

### 3. Filter Mismatch
- **Cause**: Memories saved with different metadata
- **Solution**: Check metadata structure matches filters
- **Check**: Verify `type: evaluated_idea` in metadata

### 4. API Key Issues
- **Cause**: Invalid or expired API key
- **Solution**: Verify API key in Mem0 dashboard
- **Check**: Test with direct Mem0 API call

## Testing Memory Save

Run this to test if memories are being saved:

```bash
# Run an evaluation (saves automatically)
ideation-claude "Test idea for memory check"

# Wait 30 seconds
sleep 30

# Check if saved
ideation-claude list
```

## Debugging Steps

1. **Check user_id matches**:
   ```bash
   grep MEM0_USER_ID .env
   ```

2. **Test direct save**:
   ```python
   from ideation_claude.memory import get_memory
   memory = get_memory()
   memory.save_idea(
       topic="Test Debug",
       eliminated=False,
       score=6.0,
       threshold=5.0
   )
   ```

3. **Wait and check**:
   ```python
   import time
   time.sleep(30)
   ideas = memory.get_all_ideas()
   print(f"Found {len(ideas)} ideas")
   ```

4. **Check Mem0 dashboard**:
   - Login to Mem0
   - Filter by user_id: `ideation_flow`
   - Look for recent memories

## Expected Behavior

When you run an evaluation:
1. ✅ Memory is queued (you see event_id)
2. ⏳ Processing happens in background (10-30 seconds)
3. ✅ Memory becomes searchable
4. ✅ Appears in `ideation-claude list`
5. ✅ Appears in Mem0 dashboard

## If Memories Still Don't Appear

1. **Check Mem0 API status**: Verify API key is valid
2. **Check user_id**: Ensure consistent across saves/retrieves
3. **Wait longer**: Some memories take 60+ seconds
4. **Check Mem0 dashboard**: Direct verification
5. **Contact Mem0 support**: If API key is valid but memories don't appear

## Current Fixes Applied

✅ Fixed `get_all()` to use required filters
✅ Fixed `save_idea()` to handle queued responses  
✅ Added error handling and logging
✅ Support for both cloud and local modes

The code is now correctly integrated with Mem0 cloud API.

