# Monitoring and Visibility

The ideation-claude pipeline includes comprehensive monitoring and visibility features to track evaluation progress, performance metrics, and generate detailed reports.

## Features

- **Real-time Progress Tracking**: Visual progress bars and status updates
- **Phase-level Metrics**: Track duration, API calls, and status for each phase
- **Performance Metrics**: Total duration, API usage, token consumption
- **JSON Metrics Export**: Detailed metrics saved to JSON files
- **Rich Terminal Output**: Beautiful formatted tables and progress indicators (when `rich` is available)
- **Fallback Mode**: Simple text-based logging when `rich` is not available

## Usage

### Basic Usage

Enable metrics collection with the `--metrics` flag:

```bash
ideation-claude --metrics "Your startup idea"
```

### Metrics Output

When `--metrics` is enabled, the system will:

1. **Display real-time progress** with progress bars (if `rich` is installed)
2. **Show phase-by-phase status** updates
3. **Generate metrics JSON file** in `metrics/` directory
4. **Print summary table** at the end with:
   - Final score and status
   - Total duration
   - API call counts
   - Phase breakdown

### Metrics JSON Structure

Metrics are saved to `metrics/{topic}_metrics.json` with the following structure:

```json
{
  "topic": "AI-powered personal finance assistant",
  "threshold": 5.0,
  "start_time": "2024-01-15T10:30:00",
  "end_time": "2024-01-15T10:35:23",
  "total_duration": 323.45,
  "final_score": 6.5,
  "eliminated": false,
  "orchestrator_mode": "direct",
  "total_api_calls": 9,
  "total_tokens_used": 125000,
  "phases": {
    "research": {
      "status": "completed",
      "duration": 45.2,
      "api_calls": 1,
      "tokens_used": 15000,
      "error": null
    },
    "competitor_analysis": {
      "status": "completed",
      "duration": 38.5,
      "api_calls": 1,
      "tokens_used": 12000,
      "error": null
    }
    // ... more phases
  }
}
```

## Phase Tracking

The monitoring system tracks these phases:

1. **Research** - Market trends and pain points
2. **Competitor Analysis** - Competitive landscape
3. **Market Sizing** - TAM/SAM/SOM estimation
4. **Resource Scout** - Technical feasibility
5. **Hypothesis** - Lean Startup assumptions
6. **Customer Discovery** - Mom Test planning
7. **Scoring** - 8-criteria evaluation
8. **Pivot** - Alternative suggestions (if eliminated)
9. **Report** - Final report generation

## Visual Output

### With Rich (Recommended)

When `rich` is installed, you'll see:

- **Progress bars** for each phase
- **Formatted tables** for metrics summary
- **Color-coded status** indicators
- **Time estimates** and elapsed time

### Without Rich

The system falls back to simple text-based output:

```
[Monitoring] Starting evaluation: Your startup idea
[Monitoring] Threshold: 5.0
[Monitoring] Mode: direct

[Phase] Research: Starting...
[Phase] Research: Completed (45.23s)
[Phase] Competitor Analysis: Starting...
...
```

## Integration with CI/CD

Metrics JSON files can be used in CI/CD pipelines for:

- **Performance tracking** over time
- **Cost analysis** (API calls, tokens)
- **Quality metrics** (scores, pass rates)
- **Alerting** on failures or slow phases

Example GitHub Actions usage:

```yaml
- name: Upload metrics
  uses: actions/upload-artifact@v4
  with:
    name: evaluation-metrics
    path: metrics/*.json
```

## Programmatic Access

You can load and analyze metrics programmatically:

```python
import json
from pathlib import Path

# Load metrics
metrics_file = Path("metrics/your_idea_metrics.json")
metrics = json.loads(metrics_file.read_text())

# Analyze
print(f"Total duration: {metrics['total_duration']}s")
print(f"API calls: {metrics['total_api_calls']}")
print(f"Final score: {metrics['final_score']}")

# Find slowest phase
phases = metrics['phases']
slowest = max(phases.items(), key=lambda x: x[1]['duration'] or 0)
print(f"Slowest phase: {slowest[0]} ({slowest[1]['duration']}s)")
```

## Dependencies

The monitoring system requires:

- **rich** (optional but recommended): For beautiful terminal output
  ```bash
  pip install rich
  ```

If `rich` is not installed, the system automatically falls back to simple text logging.

## Configuration

Metrics output directory can be configured via environment variable:

```bash
export IDEATION_METRICS_DIR=/path/to/metrics
```

Default: `./metrics/`

## Troubleshooting

### No progress bars showing

- Ensure `rich` is installed: `pip install rich`
- Check that `--metrics` flag is used
- Verify terminal supports rich formatting

### Metrics JSON not generated

- Check write permissions on metrics directory
- Ensure evaluation completed successfully
- Look for error messages in console output

### Performance issues

- Monitor API call counts in metrics
- Check phase durations for bottlenecks
- Review token usage for cost optimization

