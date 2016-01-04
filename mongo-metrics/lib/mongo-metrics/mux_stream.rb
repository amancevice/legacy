# Copyright (c) 2013 ICRL
#
# See the file license.txt for copying permission.

module MongoMetrics
  class MUXStream

    DEFAULT_LINE_DELIMITER = /[\r\n]/
    DEFAULT_DELIMITER = ','

    METRIC_TYPE_NOT_FOUND_ERROR = "MetricTypeNotFound"
    MALFORMED_INPUT_ERROR = "MalformedInput"

    def initialize( opts={ :input_delimiter => DEFAULT_DELIMITER, :output_delimiter => DEFAULT_DELIMITER, :line_delimiter => DEFAULT_LINE_DELIMITER} )
      @delimiter_line = opts[:line_delimiter]
      @delimiter_in   = opts[:input_delimiter]
      @delimiter_out  = opts[:output_delimiter]
    end

    def build_aggregate( aggregate_class, metric_class, interval_group, dimensions, measure )
      aggregate                = aggregate_class.new
      aggregate.type           = aggregate_class.class.to_s
      aggregate.interval_group = interval_group

      aggregate_metrics = metric_class.aggregate interval_group, dimensions, measure
      aggregate_metrics.each do |result|
        result.each do |key, value|
          if key == '_id'
            count_clause = {:interval_group => interval_group}
            value.each do |dim,val|
              aggregate.send((dim+'=').to_sym, val)
              count_clause[dim.to_sym] = val
            end
            aggregate.count = metric_class.count count_clause
          else
            aggregate.send((key+'=').to_sym, value)
          end
        end
      end
      aggregate.save

      aggregate
    end # end build_aggregate

    def read
      $stdin.read.split(@delimiter_line).each do |line|
        columns         = CSV.parse_line line, @delimiter_in
        type, timestamp = columns[0..1]
        columns         = columns[2..-1]

        # Write line to exceptions file if metric not definied
        if !$metric_types.has_key? type
          $exceptions.write METRIC_TYPE_NOT_FOUND_ERROR+@delimiter_in+line+"\n"
          next
        elsif $metric_types[type][:columns].count != columns.count
          $exceptions.write MALFORMED_INPUT_ERROR+@delimiter_in+line+"\n"
          next
        end

        # Map columns
        metric_type = $metric_types[type]
        metric_map  = {}
        metric_type[:columns].zip(columns).map{|key,val| metric_map[key] = val }

        # Build MongoMapper::Document
        interval_group        = timestamp.to_i / metric_type[:interval].to_i
        metric_class          = metric_type[:metric_class]
        metric                = metric_class.new
        metric.type           = type
        metric.timestamp      = timestamp
        metric.interval_group = interval_group
        metric_map.map{|col,val| metric.send((col+'=').to_sym, val) }

        max_metric = metric_class.first :order => "interval_group desc"
        metric.save; next if max_metric.nil? # Catches the first metric in the DB

        # Continue if the current metric is in the latest interval group
        if interval_group == max_metric.interval_group
          metric.save
          next

        # Aggregate if the current metric is a newer interval group
        elsif interval_group > max_metric.interval_group
          write_type = 'INSERT'
          aggregate_interval_group = max_metric.interval_group

        # Update if the current metric is in an older interval group
        # This is a way of handling out-of-order metrics.
        elsif interval_group < max_metric.interval_group
          write_type = 'UPDATE'
          aggregate_interval_group = interval_group
        end

        # Write to STDOUT
        metric_type[:aggregate_classes].zip(metric_type[:measures]).each do |aggregate_class,measure|
          aggregate = build_aggregate(aggregate_class, metric_class, aggregate_interval_group, metric_type[:dimensions], measure)
          write write_type, aggregate, metric_type[:dimensions], measure
        end

        metric.save
      end
    end # end read

    def write( write_type, aggregate, dimensions, measure )
      output =  [aggregate.class.to_s, write_type, aggregate.count, aggregate.interval_group]
      output += dimensions.map{|dim| aggregate.send dim.to_sym }
      measure.each do |name, methods|
        methods.each do |method|
          output << aggregate.send((name+'_'+method).to_sym)
        end
      end
      $stdout.write output.join(@delimiter_out)+"\n"
    end # end write
  end
end
