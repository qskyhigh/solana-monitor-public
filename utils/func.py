def update_metric(metric, value, labels=None):
    """
    Update Prometheus metric with optional labels and log the update if value is not None.

    :param metric: Prometheus metric to update
    :param value: Value to set for the metric
    :param labels: Optional dictionary of labels for the metric
    """
    if value is not None:
        if labels:
            # If labels are provided, update metric with multiple labels
            metric.labels(**labels).set(value)
        else:
            # Update metric without labels
            metric.set(value)
