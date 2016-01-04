# MongoMetrics

MongoMetrics is an exercise in aggregating arbitrary metrics using [MongoDB](http://www.mongodb.org/). Metrics are read from STDIN and stored as documents in Mongo. Aggregations occur at a configurable interval on a per-metric basis. A metric may have one or more dimensions, around which aggregations will pivot, as well as one or more aggregatable values. Each aggregatable value may be configured to aggregate using one or more of the aggregation types **sum**, **min**, **max**, or **avg**. Output aggregations will be issued one line per metric-type/aggregatable-measure.

## Input/Output

Input is expected to come in with the form: [metric_type],[timestamp],[columns]. The value delimiter is configurable Input is also expected to arrive in near-chronological order. Data which arrives out-of-order (reads: late) triggeres a re-aggregation of the interval group and issues an UPDATE statement.

Output is produced of the form [metric\_aggregation\_type],[record\_type],[aggregation\_count],[interval\_group],[aggregations]

Record types are one of INSERT or UPDATE. UPDATEs are emited when an out-of-order record is detected. Aggregation count is the number of records that have been aggregated in the row. Interval groups are calculated by dividing the original record's timestamp by the metric type's interval. For instance, a timestamp of 1362533371 with an interval of 1h (3600s) will be in interval group 378481.

### Example Input/Output
``` shell

# Input:
MetricType,1362533371,dim1,dim2,measure1,measure2
MetricType,1362533480,dim1,dim2,measure1,measure2
MetricType,1362534321,dim1,dim2,measure1,measure2
MetricType,1362534411,dim1,dim2,measure1,measure2

# Output
MetricTypeMeasure1,INSERT,4,378481,dim1,dim2,measure1_sum,measure1_min,measure1_max
MetricTypeMeasure2,INSERT,4,378481,dim1,dim2,measure2_avg

```

## Requirements

* Ruby (1.8.7)
* Bundler (1.2.1)
* Mongo (2.2.3)

## Mongo Configuration

``` yaml

# config/database.yml
defaults: &defaults
  adapter: mongodb
  database: mongometrics
  host: 127.0.0.1
  port: 27017

development:
  <<: *defaults

```

## Metrics Configuration

Metric input is configured with a [YAML](http://www.yaml.org/) file. Root elements represent arbitrary _types_ of data. Each metric type has four children, _interval_, _columns_, _dimensions_, and _measures_. _interval_ is a human-readable string that represents a quantity of time. Metrics will be stored with an interval group ID tied to this value; aggregations key off of the metric type, interval group, and metric dimensions. _columns_ is the complete ordered list of expected character-separated values to expect for a given metric. _dimensions_ is the ordered list of non-aggregatable metadata. _meausres_ is the ordered list of aggregatable data. Each item in the list of _measures_ is one of **sum**, **min**, **max**, or **avg**. Adding one of these to the configuration will produce an additional output column with the given aggregation.

Ex.

``` yaml

# config/metric_types.yml
metric_type:
  interval: 1h
  columns:
    - col1
    - col2
    - col3
  dimensions:
    - col1
  measures:
    - col2:
      - sum
    - col3:
      - min
      - max
      - avg

```

## Usage

``` shell

$ ./mgm --help
usage: mgm [--line-delimiter=<regex_string>] [--input-delimiter=<character>] [--output-delimiter=<character>]

    -h, --help                       Displays this message
    -n, --line-delimiter DELIMITER   Regular Expression denoting new data row
    -i, --input-delimiter DELIMITER  Delimiter of STDIN data
    -o, --output-delimiter DELIMITER Delimiter of STDOUT data
    -v, --[no-]verbose               Toggle logging to STDOUT

$ bundle exec mgm < input_stream.out

```

``` ruby

#!/usr/bin/env ruby

# ./mgm
require 'mongo_metrics'

# ...

# Configure Environment
MongoMetrics::Config.mongo
MongoMetrics::Config.metrics

# MongoMetrics GO
mux = MongoMetrics::MUXStream.new
mux.read

```
