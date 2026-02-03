# Monitoring Guide

## Overview

PowerTrader2 includes comprehensive monitoring and observability features to help you track performance, diagnose issues, and ensure reliable operation.

## Logging

### Log Levels

PowerTrader2 uses Python's standard logging framework with the following levels:

- **DEBUG**: Detailed information for diagnosing problems
- **INFO**: General informational messages about normal operation
- **WARNING**: Warning messages about potential issues
- **ERROR**: Error messages when something goes wrong
- **CRITICAL**: Critical issues that may cause the system to stop

### Log Files

Logs are stored in the `logs/` directory:

```
logs/
├── trader.log      # Trading bot logs
├── thinker.log     # AI prediction logs
├── trainer.log     # Model training logs
└── hub.log         # GUI logs
```

### Log Rotation

Logs are automatically rotated to prevent disk space issues:

- Maximum size per file: 50 MB
- Number of backup files: 5
- Total maximum disk usage: ~250 MB per log file

### Viewing Logs

**From Command Line:**
```bash
# View latest logs
tail -f logs/trader.log

# Search logs for errors
grep "ERROR" logs/trader.log

# View logs from today
grep "$(date +%Y-%m-%d)" logs/trader.log
```

**From GUI:**
The PowerTrader Hub includes a log viewer tab where you can:
- View live log output
- Filter by log level
- Search for specific messages
- Export logs for analysis

## Metrics

### Available Metrics

PowerTrader2 exposes the following metrics in Prometheus format:

#### Trading Metrics

- `powertrader_trades_total{symbol, side}` - Total number of trades executed
- `powertrader_position_value_usd{symbol}` - Current position value in USD
- `powertrader_pnl_realized_usd` - Total realized profit/loss
- `powertrader_pnl_unrealized_usd` - Current unrealized profit/loss

#### Performance Metrics

- `powertrader_api_latency_seconds{endpoint}` - API call latency histogram
- `powertrader_api_calls_total{endpoint, status}` - Total API calls by endpoint
- `powertrader_api_errors_total{endpoint, error_type}` - API errors

#### System Health Metrics

- `powertrader_uptime_seconds` - Time since trader started
- `powertrader_cache_hits_total` - Price cache hits
- `powertrader_cache_misses_total` - Price cache misses
- `powertrader_stuck_orders_total` - Number of stuck orders detected

### Accessing Metrics

Metrics are exposed on an HTTP endpoint:

```bash
curl http://localhost:8000/metrics
```

Output example:
```
# HELP powertrader_trades_total Total trades
# TYPE powertrader_trades_total counter
powertrader_trades_total{symbol="BTC",side="buy"} 42
powertrader_trades_total{symbol="BTC",side="sell"} 38
...
```

## Health Checks

### Health Check Endpoint

PowerTrader2 provides a health check endpoint at:

```bash
curl http://localhost:8080/health
```

**Healthy Response (HTTP 200):**
```json
{
  "healthy": true,
  "timestamp": "2026-02-03T18:38:34Z",
  "checks": {
    "api_connectivity": {
      "status": "ok",
      "last_successful_call": "2026-02-03T18:38:30Z",
      "seconds_since": 4
    },
    "model_freshness": {
      "status": "ok",
      "last_training": "2026-02-03T10:15:00Z",
      "hours_since": 8.4
    },
    "order_status": {
      "status": "ok",
      "pending_orders": 0,
      "stuck_orders": 0
    },
    "account_balance": {
      "status": "ok",
      "balance": 5432.10
    }
  }
}
```

**Unhealthy Response (HTTP 503):**
```json
{
  "healthy": false,
  "timestamp": "2026-02-03T18:38:34Z",
  "checks": {
    "api_connectivity": {
      "status": "error",
      "last_successful_call": "2026-02-03T17:30:00Z",
      "seconds_since": 4114,
      "message": "No successful API call in over 60 seconds"
    },
    ...
  }
}
```

### Health Check Criteria

The system is considered unhealthy if any of the following conditions are met:

- API connectivity: Last successful call > 60 seconds ago
- Model freshness: Last training > 24 hours ago
- Order status: Orders pending > 10 minutes
- Account balance: Balance < $100

## Monitoring with Prometheus and Grafana

### Quick Start

1. **Start the monitoring stack:**
   ```bash
   docker-compose up -d
   ```

2. **Access the dashboards:**
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3000 (default credentials: admin/admin)

3. **Import the PowerTrader2 dashboard:**
   - Open Grafana
   - Go to Dashboards → Import
   - Upload `monitoring/grafana_dashboard.json`

### Manual Setup

If you prefer to set up manually without Docker:

#### Prometheus

1. Install Prometheus: https://prometheus.io/download/

2. Configure `prometheus.yml`:
   ```yaml
   global:
     scrape_interval: 15s
   
   scrape_configs:
     - job_name: 'powertrader'
       static_configs:
         - targets: ['localhost:8000']
   ```

3. Start Prometheus:
   ```bash
   prometheus --config.file=prometheus.yml
   ```

#### Grafana

1. Install Grafana: https://grafana.com/grafana/download

2. Add Prometheus data source:
   - URL: http://localhost:9090
   - Access: Server (default)

3. Import the dashboard from `monitoring/grafana_dashboard.json`

### Dashboard Panels

The PowerTrader2 Grafana dashboard includes:

1. **Trades Per Hour** - Line chart showing trading activity
2. **Win Rate** - Percentage of profitable trades (rolling 24h)
3. **Realized P&L** - Cumulative profit/loss over time
4. **API Latency** - p50, p95, p99 latency percentiles
5. **Active Positions** - Table of current holdings
6. **Error Rate** - Errors per minute from logs

### Alerting

Set up alerts in Grafana to be notified of issues:

**Example: High Error Rate Alert**
```
Alert: PowerTrader High Error Rate
Condition: rate(powertrader_api_errors_total[5m]) > 0.1
Message: PowerTrader is experiencing more than 6 errors per minute
```

**Example: Low Balance Alert**
```
Alert: PowerTrader Low Balance
Condition: powertrader_account_balance_usd < 100
Message: Account balance has fallen below $100
```

## Performance Monitoring

### Key Metrics to Watch

1. **API Call Success Rate**
   - Target: > 99%
   - Action if below: Check network connectivity, API status

2. **Average Trade Latency**
   - Target: < 5 seconds
   - Action if above: Check API rate limits, network latency

3. **Cache Hit Rate**
   - Target: > 80%
   - Action if below: May indicate API instability

4. **Stuck Orders**
   - Target: 0
   - Action if > 0: Review `problematic_orders.json`, check API

### Troubleshooting

#### High API Latency

Possible causes:
- Network issues
- API rate limiting (check for 429 errors)
- Robinhood API degradation

Actions:
- Check rate limiter statistics
- Review API error logs
- Verify network connectivity

#### Stuck Orders

Possible causes:
- Order in pending state too long
- API timeout during order placement
- Network interruption

Actions:
- Review `hub_data/problematic_orders.json`
- Check Robinhood web/app for order status
- Cancel or manually resolve orders if needed

#### Cache Expiry Issues

Possible causes:
- TTL too aggressive
- API returning errors frequently
- Network instability

Actions:
- Increase `_cache_ttl_seconds` if needed
- Check API error rate
- Verify network stability

## Custom Monitoring

### Adding Custom Metrics

To add your own metrics:

```python
from metrics_exporter import TradingMetrics

metrics = TradingMetrics()

# Add a counter
metrics.custom_counter = Counter('my_custom_counter', 'Description')
metrics.custom_counter.inc()

# Add a gauge
metrics.custom_gauge = Gauge('my_custom_gauge', 'Description')
metrics.custom_gauge.set(42)
```

### Exporting to Other Systems

The Prometheus metrics format is widely supported. You can export to:

- **Datadog**: Use Datadog's Prometheus integration
- **New Relic**: Use New Relic's Prometheus integration
- **AWS CloudWatch**: Use CloudWatch Prometheus integration
- **Custom systems**: Parse the `/metrics` endpoint

## Best Practices

1. **Monitor Continuously**: Set up automated checks, don't rely on manual inspection
2. **Set Up Alerts**: Configure alerts for critical issues (stuck orders, API errors)
3. **Review Logs Regularly**: Check logs at least daily for warnings and errors
4. **Track Trends**: Monitor P&L trends to understand strategy performance
5. **Test Monitoring**: Periodically verify alerts fire correctly
6. **Archive Logs**: Keep historical logs for analysis and debugging
7. **Document Incidents**: Record issues and resolutions for future reference

## Support

For monitoring-related questions:
- Check the troubleshooting section above
- Review logs for error messages
- Search GitHub issues for similar problems
- Open a new issue with logs and metrics attached

---

Last updated: 2026-02-03
